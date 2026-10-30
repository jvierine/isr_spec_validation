"""Verify and summarize the separate inscar accuracy experiment."""
import hashlib
import json
import h5py
import numpy as np
from compare import ROOT,error
from additional_report import title


def main():
    lines=['# inscar accuracy follow-up','',
        'Increasing Gordeyev resolution helps, but cannot remove the discrepancy caused by the original approximate permittivity. '
        'Using standard SI permittivity and optional nonuniform Simpson quadrature brings all five compatible Maxwellian cases below the 10⁻⁶ threshold. '
        'No plasma parameters, amplitudes or frequency shifts were fitted.','',
        '**Proposed upstream change:** [inscar PR #537](https://github.com/engeir/inscar/pull/537), '
        '[tested commit](https://github.com/jvierine/inscar/commit/532412a). '
        'These are results from the proposed patch, not the pinned upstream release. The original README comparison and HDF5 tables are retained.','',
        '![inscar plasma line and Gordeyev resolution comparison](figures/inscar_accuracy.png)','',
        'Upper panel: positive plasma resonance, with the original 2.5 kHz sampling retained. '
        'Patched inscar uses standard permittivity and Simpson quadrature with 128,001 samples per species. '
        'Lower panel: error against Kinetic while varying only the quadrature sample count at fixed integration cutoff. '
        'Errors cover both original ±2–4 MHz windows, including 1,602 frequency samples.','',
        '## Full-grid results','',
        'All five cases use the original prescribed plasma parameters and frequency grids. The metric is '
        '`max(abs(A-B))/max(max(abs(A)),max(abs(B)))`. Grid sensitivity compares 64,001 with 128,001 samples at fixed cutoff; '
        'cutoff sensitivity independently increases the cutoff by 20% at 128,001 samples.','',
        '| Case | Original upstream error | Patched Simpson error | Grid sensitivity | Cutoff sensitivity |',
        '|---|---:|---:|---:|---:|']
    with h5py.File(ROOT/'diagnostics/inscar_accuracy.h5') as h:
        assert len(h['cases'])==5
        for name,g in h['cases'].items():
            path=ROOT/'tables/expanded'/(name+'.h5')
            assert hashlib.sha256(path.read_bytes()).hexdigest()==g.attrs['upstream_table_sha256']
            with h5py.File(path) as old:
                np.testing.assert_array_equal(g['frequency_hz'][:],old['frequency_hz'][:])
                np.testing.assert_array_equal(g['reference'][:],old['Kinetic/S_total'][:])
                np.testing.assert_array_equal(g['upstream_saved'][:],old['inscar/S_total'][:])
                assert json.loads(g.attrs['parameters_json'])==json.loads(old.attrs['parameters_json'])
            ref=g['reference'][:]
            for key,run in g.items():
                if not isinstance(run,h5py.Group): continue
                for data,attr in [('corrected','error_corrected'),('original_constant','error_original_constant')]:
                    values=run[data][:]
                    assert values.shape==ref.shape and np.isfinite(values).all()
                    assert values.min()>=-1e-10*max(values)
                    np.testing.assert_equal(error(values,ref),run.attrs[attr])
            fine=g['simpson_128001_15/corrected'][:]
            grid=error(fine,g['simpson_64001_15/corrected'][:])
            cutoff=error(fine,g['simpson_128001_18/corrected'][:])
            np.testing.assert_equal(grid,g.attrs['grid_refinement_error'])
            np.testing.assert_equal(cutoff,g.attrs['cutoff_refinement_error'])
            assert max(error(fine,ref),grid,cutoff)<1e-6
            lines.append(f'| {title(name)} | {error(g["upstream_saved"][:],ref):.3e} | {error(fine,ref):.3e} | {grid:.3e} | {cutoff:.3e} |')
        lines+=['','## Resolution and constant effects','','The original permittivity, `1e-9/(36*pi)`, is approximately 0.138% below '
            '`scipy.constants.epsilon_0`. The plasma-line denominator amplifies this difference. '
            'The paired constant experiments reuse identical Gordeyev responses, changing only the susceptibility prefactor through the public hook.','',
            '| Plasma-line quadrature | Samples per species | Original permittivity error | SI permittivity error |',
            '|---|---:|---:|---:|']
        g=h['cases/plasma_lines']
        for method in ['trapezoid','simpson']:
            for count in [32001,64001,128001,256001,512001,1024001]:
                key=f'{method}_{count}_15'
                if key in g:
                    a=g[key].attrs
                    lines.append(f'| {method} | {count:,} | {a["error_original_constant"]:.3e} | {a["error_corrected"]:.3e} |')
    lines+=['','## Numerical controls','',
        'The existing public `Particle` controls are `gordeyev_size` (number of samples), '
        '`gordeyev_upper_lim` (time cutoff) and `gordeyev_exp` (sampling-grid exponent). '
        '`Parameters.frequency_size` controls the output frequency grid, not Gordeyev resolution. '
        'The patch adds `gordeyev_method="simpson"`, retaining `"trapezoid"` as the default.','',
        'For these runs, each species uses exponent 3 and time cutoff '
        '`15/(abs(k)*sqrt(kB*T/m)*abs(cos(theta)))`; the cutoff check substitutes 18 for 15. '
        'The removable DC limit uses 10⁻⁴ Hz, as in the existing adapter. '
        'Zero field is represented by parallel geometry with a positive dummy field, whose perpendicular contribution vanishes exactly.','',
        'Enger’s [thesis](https://hdl.handle.net/10037/19542), §§4.1 and 4.3, '
        'discusses Simpson quadrature, nonuniform sampling, and increasing Gordeyev sampling from 80,000 to 800,000 points. '
        'The current pinned implementation uses trapezoidal quadrature. The new Simpson option follows that numerical approach; '
        'the permittivity correction is independently necessary for agreement at this threshold.','',
        'These finite-grid sensitivity checks are not error bounds or validation of arbitrary distributions. '
        'Only the five previously supported Maxwellian cases were rerun; mixture and neutral-BGK limitations remain.','',
        '## Reproduction and validation','',
        'The [HDF5 experiment](diagnostics/inscar_accuracy.h5) includes the full arrays, numerical settings, runtime versions, '
        'source commits and hashes. The [vector figure](figures/inscar_accuracy.svg) is also available.','',
        'Use a clean checkout of the tested PR commit. `PYTHONPATH` selects it without replacing the original pinned installation:',
        '', '```sh',
        'PYTHONPATH=/path/to/inscar/src NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=.cache/accuracy-run-cache conda run -n base python inscar_accuracy.py',
        'cargo run --release --locked --manifest-path plots/Cargo.toml --bin inscar_accuracy -- .',
        'conda run -n base python inscar_accuracy_report.py', '```','',
        'The report command verifies grid/parameter identity, preservation of upstream spectra, all saved error metrics and independent refinement checks. '
        'Upstream tests: 15 passed with a fresh Numba cache; the nine new accuracy tests also pass in repeated processes with a populated cache. '
        'A pre-existing cached velocity-integral crash reproduces on the unmodified upstream in this macOS/Python 3.13 environment and is documented in the PR.','']
    (ROOT/'INSCAR_ACCURACY.md').write_text('\n'.join(lines))
    print('Five full-grid cases, all diagnostic metrics, grid and cutoff sensitivity verified.')


if __name__=='__main__': main()
