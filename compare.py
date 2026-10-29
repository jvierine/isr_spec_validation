"""Generate independent code tables and a measured pairwise agreement matrix.

Adapters change units/limits, never fit amplitudes or shift frequencies.
Upstream source files remain unmodified. See DETAILS.md for conventions.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import types

import h5py
import numpy as np
import scipy
from scipy import constants as c, integrate

import calculate
from models import kinetic
from metadata import attach

ROOT = Path(__file__).resolve().parent
JUHA_REV = '9c743981bc9e0340a219dfac4685509a38d7f93d'
JOHN_REV = '76265c6478aafa3f5bdb918dd44e6f6d2473a832'
NAMES = ['Analytic', 'Vierinen', 'Swoboda', 'Kinetic']
TOL = 1e-6


def source(repo, revision, name):
    dest = ROOT / '.cache' / name
    if not (dest / '.git').exists():
        subprocess.run(['git', 'clone', repo, str(dest)], check=True)
    subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', revision], check=True)
    return dest


def load_juha(path):
    spec = importlib.util.spec_from_file_location('vierinen_reference', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # SciPy >= 1.14 requires x by keyword; keep this local to this module.
    mod.si = types.SimpleNamespace(simpson=lambda y, x: integrate.simpson(y, x=x))
    original = mod.gordoyev2

    def quadrature(*args, **kwargs):
        if kwargs.get('B', 0.0) == 0.0:
            kwargs['displacement_func'] = mod.gaussian_disp
        return original(*args, **kwargs)

    mod.gordoyev2 = quadrature
    return mod


def vierinen(mod, case, points):
    f = case['frequency_hz']
    # Conductivity formulation cancels omega^2. Evaluate its removable DC
    # limit at 1e-5 Hz; repeat at 1e-6 Hz in the convergence calculation.
    omega = 2 * np.pi * np.where(f == 0, 1e-5 if points == 10000 else 1e-6, f)
    p = dict(n_e=case['ne'], freq=case['radar_hz'], t_i=[case['ti']]*len(case['ions']),
             t_e=case['te'], m_i=[x[1] for x in case['ions']],
             ion_fractions=[x[2] for x in case['ions']],
             alpha=90-case['theta'], B=case['B'])
    total = mod.isr_spectrum(omega, p, n_points=points, ni_points=points) / case['ne']
    # Despite its name, False retains electron-source noise and drops ion noise.
    electron = mod.isr_spectrum(omega, p, n_points=points, ni_points=points,
                               include_electron_component=False) / case['ne']
    return np.array([total-electron, electron, total])


def swoboda(Specinit, case, match_mass=True):
    mass_unit = c.atomic_mass / c.m_p if match_mass else 1.0
    rows = [[case['ne']*frac, case['ti'], 0, 1, mass*mass_unit, 0, 0, case.get('nu_i',0.)]
            for _, mass, frac in case['ions']]
    rows.append([case['ne'], case['te'], 0, -1, 1, 0, 0, case.get('nu_e',0.)])
    obj = Specinit(centerFrequency=case['radar_hz'], bMag=case['B'],
                   f=case['frequency_hz'], alphamax=91 if case['B'] else 30)
    _, (ion, electron) = obj.getspec(np.array(rows), alphadeg=90-case['theta'],
                                    seplines=True)
    return np.array([ion, electron, ion+electron]) / case['ne']


def ours(case):
    electrons = [kinetic.Species('e', case['ne'], case['te'], c.m_e, -c.e, case.get('nu_e',0.))]
    ions = [kinetic.Species(name, case['ne']*frac, case['ti'], mass*c.atomic_mass, c.e, case.get('nu_i',0.))
            for name, mass, frac in case['ions']]
    result = kinetic.density_spectrum(case['frequency_hz'], kinetic.radar_k(case['radar_hz']),
                                     electrons, ions, B=case['B'], theta_deg=case['theta'])
    return np.array([result[x] for x in ['ion', 'electron', 'total']])


def error(a, b):
    """Symmetric maximum error relative to the larger peak, no fitted scaling."""
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        return np.inf
    return np.max(np.abs(a-b)) / max(np.max(np.abs(a)), np.max(np.abs(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--juha', type=Path)
    ap.add_argument('--john', type=Path)
    args = ap.parse_args()
    jp = args.juha or source('https://github.com/jvierine/isr_analysis', JUHA_REV, 'vierinen') / 'isr_spec.py'
    sp = args.john or source('https://github.com/jswoboda/ISRSpectrum', JOHN_REV, 'swoboda')
    juha = load_juha(jp)
    sys.path.insert(0, str(sp))
    from ISRSpectrum.ISRSpectrum import Specinit
    outdir = ROOT / 'tables' / 'comparison'
    outdir.mkdir(parents=True, exist_ok=True)
    cases = []
    for mhz in [440.2, 930.0]:
        for name, ne, ti, te, ions in calculate.CASES:
            cases.append(dict(name=f'{name}_{mhz:g}MHz', ne=ne, ti=ti, te=te, ions=ions,
                              radar_hz=mhz*1e6, B=0., theta=0., frequency_hz=calculate.FREQUENCY_HZ))
    worst = np.zeros((4, 4))
    components = np.zeros((4, 4, 3))
    convergence, mass_errors = [], []
    for case in cases:
        print(case['name'], flush=True)
        analytic = np.array(calculate.spectrum(case['radar_hz'], case['ne'], case['ti'],
                                               case['te'], case['ions'], case['frequency_hz']))
        low = vierinen(juha, case, 10000)
        high = vierinen(juha, case, 20000)
        john = swoboda(Specinit, case)
        rawmass = swoboda(Specinit, case, False)
        values = [analytic, high, john, ours(case)]
        conv = [error(a,b) for a,b in zip(low, high)]
        convergence.append(conv)
        mass_errors.append(error(rawmass[-1], john[-1]))
        matrix = np.array([[error(a[-1], b[-1]) for b in values] for a in values])
        cm = np.array([[[error(aa,bb) for aa,bb in zip(a,b)] for b in values] for a in values])
        worst = np.maximum(worst, matrix)
        components = np.maximum(components, cm)
        with h5py.File(outdir / (case['name']+'.h5'), 'w') as h:
            attach(h,case)
            h.attrs['parameters_json'] = json.dumps({k:v for k,v in case.items() if k != 'frequency_hz'})
            h.attrs['spectrum_units'] = 'Hz^-1 per electron; no peak or area normalization'
            h.attrs['scipy_version'] = scipy.__version__
            h.attrs['numpy_version'] = np.__version__
            h.attrs['vierinen_commit'] = JUHA_REV
            h.attrs['swoboda_commit'] = JOHN_REV
            for name, path in [('vierinen', jp), ('kinetic', ROOT/'models/kinetic.py'), ('analytic', ROOT/'calculate.py')]:
                h.attrs[name+'_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            h['frequency_hz'] = case['frequency_hz']
            for name, value in zip(NAMES, values):
                g = h.create_group(name)
                attach(g,case)
                for component, val in zip(['S_ion','S_electron','S_total'], value):
                    g[component] = val
            h['pairwise_error'] = matrix
            h['pairwise_component_error'] = cm
            h['Vierinen_10000_points'] = low
            h['Vierinen_convergence_error'] = conv
            h['Swoboda_unconverted_mass_input'] = rawmass
        print('maximum pairwise:', np.max(matrix), 'quadrature:', max(conv), flush=True)
    with h5py.File(outdir/'summary.h5', 'w') as h:
        for case in cases: attach(h.create_group('case_parameters/'+case['name']),case)
        h['code_names'] = np.array(NAMES, dtype=h5py.string_dtype())
        h['case_names'] = np.array([x['name'] for x in cases], dtype=h5py.string_dtype())
        h['worst_pairwise_error'] = worst
        h['worst_component_error'] = components
        h['vierinen_convergence_error'] = convergence
        h['unconverted_swoboda_mass_error'] = mass_errors
        h.attrs['pass_tolerance'] = TOL
    print('MATRIX', worst, 'COMPONENT MAX', np.max(components), 'MASS', mass_errors, flush=True)
    write_readme(worst)


def write_readme(matrix):
    lines = ['# ISR spectrum validation', '',
             'Spectrum tables generated with four different codes:', '',
             '| Code | Source |', '|---|---|',
             '| Analytic | [This repository](calculate.py): Maxwellian Gordeyev integral |',
             f'| Vierinen | [Juha Vierinen, isr_analysis/isr_spec.py](https://github.com/jvierine/isr_analysis/blob/{JUHA_REV}/isr_spec.py) |',
             f'| Swoboda | [John Swoboda, ISRSpectrum](https://github.com/jswoboda/ISRSpectrum/tree/{JOHN_REV}) |',
             '| Kinetic | [Snapshot of the Vlasov–Boltzmann project calculation](models/kinetic.py) |', '',
             '**Pairwise agreement:** worst error across six collisionless, unmagnetized ion-line cases',
             '(F region, molecular ions and topside; 440.2 and 930 MHz).', '',
             '🟩 agrees (error ≤ 10⁻⁶); 🟥 disagrees. Error = maximum absolute difference',
             'divided by the larger spectrum peak. No fitted scaling.', '',
             '| Code | '+' | '.join(NAMES)+' |', '|---|'+'---:|'*len(NAMES)]
    for i, name in enumerate(NAMES):
        cells = ['—' if i == j else f'{"🟩" if matrix[i,j] <= TOL else "🟥"} {matrix[i,j]:.2e}' for j in range(len(NAMES))]
        lines.append('| '+name+' | '+' | '.join(cells)+' |')
    lines += ['', '[HDF5 tables](tables/comparison/) contain every code’s spectrum and comparison results.',
              'Mass units, spectrum units and zero-frequency limits are matched explicitly;',
              '[details and reproduction](DETAILS.md).', '',
              'Magnetic, collision and plasma-line checks: [initial and refined results](EXTENDED_RESULTS.md).', '']
    (ROOT/'README.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
