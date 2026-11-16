"""Run the installed EISCAT GUISDAP MATLAB spectrum under Octave on avaruus.

The legacy source and dispersion-function tables remain outside Git. Only
computed HDF5 spectra, numerical metrics, timing, and source hashes are saved.
"""
import hashlib
import os
from pathlib import Path
import platform
import subprocess

import h5py
import numpy as np

from compare import ROOT, error
from octave_validation import cases, prepare, data

SOURCE_URL = 'https://gitlab.com/eiscat/guisdap9.git'
OUT = ROOT / 'tables/eiscat'
RAW = ROOT / '.cache/eiscat_validation'


def supported(case):
    return case['B'] == 0 and case.get('nu_e', 0) == 0 and case.get('nu_i', 0) == 0


def source_root():
    raw = os.environ.get('EISCAT_GUISDAP_ROOT')
    if not raw:
        raise RuntimeError('Set EISCAT_GUISDAP_ROOT to the installed guisdap9 checkout')
    root = Path(raw).resolve()
    for relative in ['anal/guisdap_spec.m', 'anal/spec.m', 'anal/pldfi.m',
                     'matfiles/pldfv.mat', 'matfiles/pldfvv.mat']:
        if not (root / relative).is_file():
            raise FileNotFoundError(root / relative)
    return root


def git_commit(root):
    commit = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    assert len(commit) == 40
    return commit


def main():
    assert platform.node().split('.')[0] == 'avaruus'
    os.sched_setaffinity(0, {0})
    source = source_root()
    commit = git_commit(source)
    prepare()
    OUT.mkdir(parents=True,exist_ok=True)
    RAW.mkdir(parents=True,exist_ok=True)
    model = next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
                 if line.startswith('model name'))
    for case in cases():
        if not supported(case):
            continue
        name = case['name']
        rawpath = RAW / (name + '.h5')
        command = ['taskset','-c','0','octave','-q',str(ROOT/'octave/eiscat_case.m'),
                   str(ROOT/'.cache/octave_validation/inputs'/ (name + '.h5')),
                   str(rawpath),'7']
        subprocess.run(command,cwd=ROOT,env=os.environ.copy(),check=True)
        with h5py.File(rawpath) as raw:
            f = np.asarray(data(raw,'frequency_hz')).ravel()
            measured = np.asarray(data(raw,'S_total')).ravel()
            elapsed = np.asarray(data(raw,'elapsed_s')).ravel()
        assert np.array_equal(f,case['frequency_hz'])
        spectrum = measured / case['ne']  # GUISDAP output is density-scaled m^-3 s
        assert spectrum.shape == f.shape and np.isfinite(spectrum).all()
        assert elapsed.shape == (7,) and np.isfinite(elapsed).all() and (elapsed>0).all()
        expanded = ROOT/'tables/expanded'/ (name + '.h5')
        if expanded.exists():
            with h5py.File(expanded) as h:
                kinetic = h['Kinetic/S_total'][:]
            discrepancy = error(spectrum,kinetic)
        else:
            discrepancy = np.nan
        with h5py.File(OUT/(name+'.h5'),'w') as out:
            out['frequency_hz'] = f
            g = out.create_group('EISCAT')
            g['S_total'] = spectrum
            g['elapsed_s'] = elapsed
            g.attrs['status'] = 'computed'
            g.attrs['median_elapsed_s'] = float(np.median(elapsed))
            g.attrs['min_elapsed_s'] = float(elapsed.min())
            g.attrs['max_elapsed_s'] = float(elapsed.max())
            g.attrs['error_vs_kinetic'] = discrepancy
            g.attrs['symmetry_error'] = error(spectrum,spectrum[::-1])
            g.attrs['spectrum_units'] = 'Hz^-1 per electron; native density-scaled output divided by ne'
            g.attrs['git_url'] = SOURCE_URL
            g.attrs['git_commit'] = commit
            g.attrs['code_path'] = 'anal/guisdap_spec.m'
            for relative,key in [('anal/guisdap_spec.m','code_sha256'),
                                 ('anal/spec.m','spec_sha256'),('anal/pldfi.m','pldfi_sha256'),
                                 ('matfiles/pldfv.mat','pldfv_sha256'),
                                 ('matfiles/pldfvv.mat','pldfvv_sha256')]:
                g.attrs[key] = hashlib.sha256((source/relative).read_bytes()).hexdigest()
            g.attrs['adapter_sha256'] = hashlib.sha256((ROOT/'octave/eiscat_case.m').read_bytes()).hexdigest()
            g.attrs['host'] = 'avaruus'
            g.attrs['cpu_model'] = model
            g.attrs['cpu_affinity'] = '0'
            g.attrs['threads_per_call'] = 1
            g.attrs['octave_version'] = subprocess.check_output(['octave','--version'],text=True).splitlines()[0]
            g.attrs['timing_scope'] = 'full spectrum function; 1 warm-up; 7 timed calls; no startup or HDF5 I/O'
        print(name,discrepancy,np.median(elapsed),flush=True)


if __name__ == '__main__':
    main()
