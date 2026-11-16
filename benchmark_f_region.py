"""Single-CPU in-process timing of the 440.2 MHz O+ F-region spectrum.

Run on avaruus. This writes HDF5, with timing and numerical checks against
the saved expanded comparison. Process startup, imports, and JIT warm-up are
excluded. No source code or legacy data are copied into Git.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'

import h5py
import numpy as np

from compare import ROOT, error, ours, swoboda
from call_settings import run_analytic
from additional_python import nicolls, skolar, inscar


def main():
    if platform.node().split('.')[0] != 'avaruus':
        raise RuntimeError('Benchmark must run on avaruus')
    os.sched_setaffinity(0, {0})
    path = ROOT / 'tables/expanded/f_region_440.2MHz.h5'
    with h5py.File(path) as h:
        case = json.loads(h.attrs['parameters_json'])
        case['frequency_hz'] = h['frequency_hz'][:]
        saved = {name: h[name + '/S_total'][:] for name in h['code_names'].asstr()[:]}

    sys.path.insert(0, str(ROOT / '.cache/swoboda'))
    from ISRSpectrum.ISRSpectrum import Specinit

    runners = {
        'Analytic': lambda: run_analytic(case)[-1],
        'Swoboda': lambda: swoboda(Specinit, case)[-1],
        'Kinetic': lambda: ours(case)[-1],
        'Nicolls': lambda: nicolls(case, True),
        'Skolar': lambda: skolar(case, True),
        'inscar': lambda: inscar(case, True),
    }
    outpath = ROOT / 'tables/speed_f_region_440.2MHz.h5'
    with h5py.File(outpath, 'w') as out:
        out.attrs['host'] = 'avaruus'
        out.attrs['cpu_model'] = next(line.split(':', 1)[1].strip()
            for line in Path('/proc/cpuinfo').read_text().splitlines()
            if line.startswith('model name'))
        out.attrs['cpu_affinity'] = '0'
        out.attrs['threads_per_call'] = 1
        out.attrs['timing_scope'] = 'full spectrum function; 1 warm-up; 7 timed calls; no process startup or HDF5 I/O'
        out.attrs['python_version'] = platform.python_version()
        out.attrs['case_name'] = 'f_region_440.2MHz'
        out['frequency_hz'] = case['frequency_hz']
        for name, runner in runners.items():
            print(name, flush=True)
            result = np.asarray(runner())
            assert result.shape == saved[name].shape and np.isfinite(result).all()
            discrepancy = error(result, saved[name])
            if discrepancy > 1e-6:
                raise RuntimeError(f'{name}: result differs from saved spectrum by {discrepancy}')
            elapsed = []
            for _ in range(7):
                start = time.perf_counter_ns()
                value = np.asarray(runner())
                elapsed.append((time.perf_counter_ns() - start) * 1e-9)
                assert error(value, result) <= 1e-9, name
            g = out.create_group(name)
            g['elapsed_s'] = elapsed
            g.attrs['median_elapsed_s'] = float(np.median(elapsed))
            g.attrs['min_elapsed_s'] = float(np.min(elapsed))
            g.attrs['max_elapsed_s'] = float(np.max(elapsed))
            g.attrs['error_vs_saved'] = discrepancy
            g.attrs['source_sha256'] = hashlib.sha256((ROOT / {
                'Analytic': 'calculate.py', 'Kinetic': 'models/kinetic.py',
                'Swoboda': '.cache/swoboda/ISRSpectrum/ISRSpectrum.py',
                'Nicolls': '.cache/isr_school/is_spectral_model/ismodel.py',
                'Skolar': '.cache/OO_Collisions/ISRSpectraFunctions.py',
                'inscar': '.cache/inscar-updated/src/inscar/__init__.py',
            }[name]).read_bytes()).hexdigest()
            out.flush()
            print(name, g.attrs['median_elapsed_s'], discrepancy, flush=True)


if __name__ == '__main__':
    main()
