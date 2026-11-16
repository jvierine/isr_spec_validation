"""Measure native Vierinen Rust spectra and paired Rust optimization timings.

Run on avaruus; the Python process only bridges HDF5 to the Rust executable.
Only Rust spectrum calls are timed. All source identity is retained in HDF5.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess

import h5py
import numpy as np

from compare import ROOT, error
from octave_validation import cases


def pinned_source():
    cargo=str(Path.home()/'.cargo/bin/cargo')
    metadata=json.loads(subprocess.check_output([cargo,'metadata','--locked','--offline',
        '--format-version','1','--manifest-path',str(ROOT/'rust/Cargo.toml')],text=True))
    package=next(p for p in metadata['packages'] if p['name']=='guisdap-ion')
    spectrum_source=Path(package['manifest_path']).parent/'src/spectrum.rs'
    source_commit=package['source'].rsplit('#',1)[1]
    assert len(source_commit)==40
    return spectrum_source,source_commit


def main():
    assert platform.node().split('.')[0] == 'avaruus'
    os.sched_setaffinity(0, {0})
    binary = ROOT/'rust/target/release/isr-rust-validation'
    spectrum_source,source_commit=pinned_source()
    destination = ROOT/'tables/rust'
    destination.mkdir(parents=True, exist_ok=True)
    model = next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
                 if line.startswith('model name'))
    for case in cases():
        if case['B'] != 0 and case['theta'] not in (0.,180.):
            continue
        request = {k:v for k,v in case.items() if k not in ('name','B','frequency_hz')}
        # An isotropic Maxwellian with k parallel to B has exactly the same
        # longitudinal response as B=0, including the BGK operator here.
        request.update(b=0., frequency_hz=case['frequency_hz'].tolist(), trials=31, batch=100)
        proc = subprocess.run(['taskset','-c','0',str(binary)], input=json.dumps(request),
                              text=True,capture_output=True,check=True)
        result = json.loads(proc.stdout)
        spectrum = np.asarray(result['spectrum'])
        assert spectrum.shape == case['frequency_hz'].shape and np.isfinite(spectrum).all()
        times = np.asarray(result['elapsed_s'])
        baseline = np.asarray(result['baseline_elapsed_s'])
        assert times.shape == baseline.shape == (31,)
        assert np.isfinite(times).all() and (times>0).all() and (baseline>0).all()
        reference_path = ROOT/'tables/expanded'/(case['name']+'.h5')
        if not reference_path.exists():
            reference_path = ROOT/'tables/octave'/(case['name']+'.h5')
        with h5py.File(reference_path) as h:
            discrepancy = error(spectrum,h['Kinetic/S_total'][:])
        assert discrepancy < 1e-6, (case['name'],discrepancy)
        with h5py.File(destination/(case['name']+'.h5'),'w') as out:
            out['frequency_hz'] = case['frequency_hz']
            out.attrs['parameters_json'] = json.dumps({k:v for k,v in case.items() if k!='frequency_hz'})
            g = out.create_group('Vierinen')
            g['S_total'] = spectrum
            g['elapsed_s'] = times
            g['baseline_elapsed_s'] = baseline
            g['cpu_elapsed_s']=np.asarray(result['cpu_elapsed_s'])
            g['baseline_cpu_elapsed_s']=np.asarray(result['baseline_cpu_elapsed_s'])
            if result.get('float32_spectrum') is not None:
                trial=np.asarray(result['float32_spectrum'])
                assert np.isfinite(trial).all()
                g['float32_trial_S_total']=trial
                g['float32_trial_elapsed_s']=np.asarray(result['float32_elapsed_s'])
                g.attrs['float32_trial_error']=error(trial,spectrum)
                g.attrs['float32_trial_median_s']=float(np.median(result['float32_elapsed_s']))
                g.attrs['float32_trial_precision']='f32 widths, Gaussian and spectrum algebra; f64 Dawson then round to f32; not selected'
            for key,value in dict(status='computed',implementation='RUISDAP Rust',
                runtime='Rust',host='avaruus',cpu_model=model,cpu_affinity='0',threads_per_call=1,
                batch_size=100,trial_count=31,warm_up_calls=10,
                arithmetic='f64',simd_backend=result['backend'],
                geometry_mapping=('B=0 directly' if case['B']==0 else 'exact parallel-Maxwellian B=0 response'),
                median_elapsed_s=float(np.median(times)),min_elapsed_s=float(times.min()),
                max_elapsed_s=float(times.max()),baseline_median_s=float(np.median(baseline)),
                p10_elapsed_s=float(np.quantile(times,0.1)),p90_elapsed_s=float(np.quantile(times,0.9)),
                median_cpu_s=float(np.median(result['cpu_elapsed_s'])),
                optimization_speedup=float(np.median(baseline)/np.median(times)),
                max_relative_change=result['max_relative_change'],error_vs_kinetic=discrepancy,
                symmetry_error=error(spectrum,spectrum[::-1]),
                git_url='https://github.com/jvierine/ruisdap',
                git_commit=source_commit,
                code_path='crates/guisdap-ion/src/spectrum.rs',
                code_sha256=hashlib.sha256(spectrum_source.read_bytes()).hexdigest(),
                binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                adapter_sha256=hashlib.sha256((ROOT/'rust/src/main.rs').read_bytes()).hexdigest(),
                baseline_sha256=hashlib.sha256((ROOT/'rust/src/baseline.rs').read_bytes()).hexdigest(),
                baseline_git_commit='7bf2c45ec770af556da7edfdd1aa00ee267fa4ef',
                compiler=subprocess.check_output([str(Path.home()/'.cargo/bin/rustc'),'-Vv'],text=True),
                compiler_flags='release; thin LTO; codegen-units=1; portable target',
                timing_scope='median of 31 batches of 100 full Rust spectrum calls; alternating before/after order; allocation and state setup included; parsing/startup/HDF5/JIT excluded',
                spectrum_units='Hz^-1 per electron; full electron plus ion components').items():
                g.attrs[key] = value
        print(case['name'], 'Rust us',np.median(times)*1e6,'gain',np.median(baseline)/np.median(times),
              'error',discrepancy,flush=True)
        if result.get('float32_spectrum') is not None:
            print('float32 trial error',error(np.asarray(result['float32_spectrum']),spectrum),
                  'us',np.median(result['float32_elapsed_s'])*1e6,flush=True)


if __name__ == '__main__':
    main()
