"""Verify Rust source identity, scientific comparisons, and paired timings."""
import hashlib
import json

import h5py
import numpy as np

from compare import ROOT, error
from rust_validation import pinned_source


def main():
    source,commit=pinned_source()
    paths=sorted((ROOT/'tables/rust').glob('*.h5'))
    assert len(paths)==9
    for path in paths:
        with h5py.File(path) as h:
            g=h['Vierinen']
            case=json.loads(h.attrs['parameters_json'])
            assert case['B']==0 or case['theta'] in (0,180)
            assert g.attrs['implementation']=='RUISDAP Rust'
            assert g.attrs['git_commit']==commit
            assert g.attrs['code_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
            assert g.attrs['adapter_sha256']==hashlib.sha256((ROOT/'rust/src/main.rs').read_bytes()).hexdigest()
            assert g.attrs['baseline_sha256']==hashlib.sha256((ROOT/'rust/src/baseline.rs').read_bytes()).hexdigest()
            assert g.attrs['host']=='avaruus' and g.attrs['cpu_affinity']=='0'
            assert g.attrs['threads_per_call']==1 and g.attrs['arithmetic']=='f64'
            assert g.attrs['max_relative_change']<=1e-9
            values=g['S_total'][:]
            assert values.shape==h['frequency_hz'].shape and np.isfinite(values).all()
            assert (values>=0).all()
            reference_path=ROOT/'tables/expanded'/path.name
            if not reference_path.exists(): reference_path=ROOT/'tables/octave'/path.name
            with h5py.File(reference_path) as ref:
                np.testing.assert_array_equal(h['frequency_hz'][:],ref['frequency_hz'][:])
                discrepancy=error(values,ref['Kinetic/S_total'][:])
                np.testing.assert_equal(discrepancy,g.attrs['error_vs_kinetic'])
                assert discrepancy<=1e-6
            np.testing.assert_equal(error(values,values[::-1]),g.attrs['symmetry_error'])
            for dataset in ['elapsed_s','baseline_elapsed_s','cpu_elapsed_s','baseline_cpu_elapsed_s']:
                times=g[dataset][:]
                assert times.shape==(31,) and np.isfinite(times).all() and (times>0).all()
            wall=np.median(g['elapsed_s'][:])
            cpu=np.median(g['cpu_elapsed_s'][:])
            assert cpu/wall>0.5 and cpu/wall<1.1, (path,cpu,wall)
            np.testing.assert_equal(wall,g.attrs['median_elapsed_s'])
            np.testing.assert_equal(cpu,g.attrs['median_cpu_s'])
            np.testing.assert_allclose(np.median(g['baseline_elapsed_s'][:])/wall,g.attrs['optimization_speedup'])
            if 'float32_trial_S_total' in g:
                trial=g['float32_trial_S_total'][:]
                np.testing.assert_equal(error(trial,values),g.attrs['float32_trial_error'])
                assert g['float32_trial_elapsed_s'].shape==(31,)
                assert (g['float32_trial_elapsed_s'][:]>0).all()
            print(path.stem,'Rust accuracy, source and paired CPU/wall measurements verified')
    with h5py.File(ROOT/'tables/rust/f_region_440.2MHz.h5') as h:
        assert h['Vierinen'].attrs['simd_backend']=='AVX2'
        assert h['Vierinen'].attrs['optimization_speedup']>1
    with h5py.File(ROOT/'tables/pairwise_summary.h5') as h:
        names=list(h['code_names'].asstr()[:])
        assert len(names)==12
        for scope in ['ionline','all']:
            count=h[scope+'/shared_case_count'][:]
            matrix=h[scope+'/worst_error'][:]
            np.testing.assert_array_equal(count,count.T)
            np.testing.assert_allclose(matrix,matrix.T,equal_nan=True)
            assert np.all(count[np.triu_indices(12,1)]>0)
        i=names.index('Vierinen');j=names.index('Kinetic')
        assert h['ionline/shared_case_count'][i,j]==6
        assert h['all/shared_case_count'][i,j]==9
    print('Rust is correctly labelled Vierinen in all 66 implementation pairs')


if __name__=='__main__':
    main()
