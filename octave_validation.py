"""Run pinned MATLAB ISR codes under Octave and retain spectra/timings in HDF5.

Execute on avaruus with one pinned logical CPU and single-thread BLAS. Timed
calls exclude interpreter startup, HDF5 I/O, and the one untimed warm-up.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

# Set numerical-library thread limits before importing NumPy/SciPy.
for _name in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
              'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
    os.environ[_name] = '1'

import h5py
import numpy as np

from compare import ROOT, error, ours
import calculate
from additional_sources import SOURCES

CODE = {'O+': 1, 'NO+': 2, 'O2+': 3, 'N2+': 4,
        'H+': 5, 'He+': 6, 'N+': 7}
RAW = ROOT / '.cache' / 'octave_validation'
OUT = ROOT / 'tables' / 'octave'
EXPECTED_HOST = 'avaruus'


def cases():
    for path in sorted((ROOT / 'tables' / 'expanded').glob('*.h5')):
        with h5py.File(path) as h:
            case = json.loads(h.attrs['parameters_json'])
            case['name'] = path.stem
            case['frequency_hz'] = h['frequency_hz'][:]
        yield case
    base = dict(ne=1e11, te=3000., ti=300., B=50e-6, theta=89.,
                radar_hz=930e6, ions=[('O+', 16., 1.)], nu_e=0., nu_i=0.,
                frequency_hz=np.arange(-20000., 20000.1, 25.))
    yield dict(base, name='near_perp_1deg_lower_hybrid')
    yield dict(base, name='near_perp_unmagnetized_control', B=0.)


def input_path(name):
    return RAW / 'inputs' / (name + '.h5')


def result_path(name, code):
    return RAW / 'results' / (name + '_' + code + '.h5')


def prepare():
    (RAW / 'inputs').mkdir(parents=True, exist_ok=True)
    (RAW / 'results').mkdir(parents=True, exist_ok=True)
    for case in cases():
        with h5py.File(input_path(case['name']), 'w') as h:
            for key in ['frequency_hz', 'radar_hz', 'ne', 'te', 'ti', 'B', 'theta']:
                h[key] = case[key]
            for key in ['nu_e', 'nu_i']:
                h[key] = case.get(key, 0.)
            h['ion_masses_u'] = [ion[1] for ion in case['ions']]
            h['ion_fractions'] = [ion[2] for ion in case['ions']]
            h['ion_codes'] = [CODE[ion[0]] for ion in case['ions']]
            h['amu'] = calculate.amu
            h['e'] = calculate.e
            if case['B'] > 0:
                h['gordmode'] = 1  # tightened Sommerfeld quadrature in Octave adapter
            h.attrs['parameters_json'] = json.dumps(
                {k: v for k, v in case.items() if k != 'frequency_hz'})


def check_host():
    host = platform.node().split('.')[0]
    if host != EXPECTED_HOST:
        raise RuntimeError(f'Benchmark host must be {EXPECTED_HOST}; got {host}')
    return host


def env_single_thread():
    env = os.environ.copy()
    for name in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                 'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
        env[name] = '1'
    return env


def run(repeats, cpu):
    host = check_host()
    os.sched_setaffinity(0, {cpu})
    assert os.sched_getaffinity(0) == {cpu}
    prepare()
    env = env_single_thread()
    for case in cases():
        name = case['name']
        for code in ['Martinez', 'Sandbem']:
            if code == 'Martinez' and (case['B'] or case.get('nu_e', 0.) or case.get('nu_i', 0.)):
                continue
            command = ['taskset', '-c', str(cpu), 'octave', '-q',
                       str(ROOT / 'octave' / 'run_case.m'), code,
                       str(input_path(name)), str(result_path(name, code)), str(repeats)]
            print(name, code, flush=True)
            proc = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode:
                print(proc.stderr[-2000:], flush=True)
                with h5py.File(result_path(name, code), 'w') as h:
                    h.attrs['status'] = 'error'
                    h.attrs['reason'] = proc.stderr[-2000:]
            else:
                with h5py.File(result_path(name, code), 'a') as h:
                    h.attrs['status'] = 'computed'
                    h.attrs['host'] = host
                    h.attrs['cpu_affinity'] = str(cpu)
                    h.attrs['threads_per_call'] = 1
                    h.attrs['octave_version'] = subprocess.check_output(
                        ['octave', '--version'], text=True, stderr=subprocess.DEVNULL).splitlines()[0]
                    h.attrs['timing_scope'] = 'full spectrum function call; warm-up and process startup excluded'
                    h.attrs['adapter_sha256'] = hashlib.sha256(
                        (ROOT / 'octave' / 'octave_kernel.m').read_bytes()).hexdigest()
            print('status', proc.returncode, flush=True)
        for code in ['Kinetic', 'Analytic']:
            if code == 'Analytic' and case['B']:
                continue
            func = ours if code == 'Kinetic' else lambda c: calculate.spectrum(
                c['radar_hz'], c['ne'], c['ti'], c['te'], c['ions'], c['frequency_hz'])
            func(case)
            elapsed = []
            result = None
            for _ in range(repeats):
                t0 = time.perf_counter_ns()
                result = func(case)
                elapsed.append((time.perf_counter_ns()-t0)*1e-9)
            with h5py.File(result_path(name, code), 'w') as h:
                h['frequency_hz'] = case['frequency_hz']
                h['S_total'] = np.asarray(result)[-1]
                h['elapsed_s'] = elapsed
                h.attrs['status'] = 'computed'
                h.attrs['host'] = host
                h.attrs['cpu_affinity'] = str(cpu)
                h.attrs['threads_per_call'] = 1
                h.attrs['timing_scope'] = 'full spectrum function call; warm-up and process startup excluded'


def data(h, name):
    # Octave's save -hdf5 wraps each variable in a value dataset.
    return h[name + '/value'][:] if name + '/value' in h else h[name][:]


def collect():
    OUT.mkdir(parents=True, exist_ok=True)
    host = check_host()
    for case in cases():
        name = case['name']
        with h5py.File(OUT / (name + '.h5'), 'w') as out:
            out['frequency_hz'] = case['frequency_hz']
            out.attrs['parameters_json'] = json.dumps(
                {k: v for k, v in case.items() if k != 'frequency_hz'})
            out.attrs['host'] = host
            model = next(line.split(':', 1)[1].strip()
                         for line in Path('/proc/cpuinfo').read_text().splitlines()
                         if line.startswith('model name'))
            out.attrs['cpu_model'] = model
            out.attrs['os_kernel'] = platform.release()
            out.attrs['benchmark_mode'] = 'one pinned logical CPU per call; sequential isolated code runs'
            out.attrs['spectrum_units'] = 'Hz^-1 per electron, no fitted scaling'
            reference = None
            for code in ['Kinetic', 'Analytic', 'Martinez', 'Sandbem']:
                path = result_path(name, code)
                if not path.exists():
                    continue
                with h5py.File(path) as raw:
                    g = out.create_group(code)
                    for key, value in raw.attrs.items():
                        g.attrs[key] = value
                    if raw.attrs['status'] != 'computed':
                        continue
                    freq = np.asarray(data(raw, 'frequency_hz')).ravel()
                    spectrum = np.asarray(data(raw, 'S_total')).ravel()
                    timings = np.asarray(data(raw, 'elapsed_s')).ravel()
                    assert np.array_equal(freq, case['frequency_hz']), (name, code)
                    assert spectrum.shape == freq.shape and np.isfinite(spectrum).all()
                    assert np.isfinite(timings).all() and (timings > 0).all()
                    g['S_total'] = spectrum
                    g['elapsed_s'] = timings
                    g.attrs['median_elapsed_s'] = np.median(timings)
                    g.attrs['min_elapsed_s'] = np.min(timings)
                    g.attrs['max_elapsed_s'] = np.max(timings)
                    if code == 'Kinetic':
                        reference = spectrum
                    else:
                        assert reference is not None
                        g.attrs['error_vs_kinetic'] = error(spectrum, reference)
                    g.attrs['symmetry_error'] = error(spectrum, spectrum[::-1])
                    if code in SOURCES:
                        repo, commit, folder, entry = SOURCES[code]
                        g.attrs['git_url'] = 'https://github.com/' + repo
                        g.attrs['git_commit'] = commit
                        g.attrs['code_path'] = entry
                        g.attrs['code_sha256'] = hashlib.sha256(
                            (ROOT / '.cache' / folder / entry).read_bytes()).hexdigest()
                    else:
                        source = ROOT / ('calculate.py' if code == 'Analytic' else 'models/kinetic.py')
                        g.attrs['git_url'] = 'https://github.com/jvierine/isr_spec_validation'
                        g.attrs['code_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            print(name, list(out), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run', 'collect'])
    parser.add_argument('--repeats', type=int, default=7)
    parser.add_argument('--cpu', type=int, default=0)
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'run': run(args.repeats, args.cpu)
    else: collect()
