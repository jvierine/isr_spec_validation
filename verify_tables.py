"""Check saved tables, recompute every pairwise metric, and check baseline gates."""
import h5py
import numpy as np
import hashlib
import re
import subprocess
from compare import error, NAMES, TOL, ROOT

REQUIRED=['ne_m3','te_K','ti_K','vi_m_s','B_T','nu_en_s_1','nu_ei_s_1','nu_in_s_1','angle_k_B_deg','f_r_MHz']


def verify_provenance():
    repos={'Analytic':ROOT,'Kinetic':ROOT,'Vierinen':ROOT/'.cache/vierinen',
           'Swoboda':ROOT/'.cache/swoboda'}
    for path in sorted((ROOT/'tables').rglob('*.h5')):
        with h5py.File(path) as h:
            for group in [h]+([h['refined']] if 'refined' in h else []):
                assert 'provenance' in group, (path,group.name)
                assert re.fullmatch('[0-9a-f]{40}',group.attrs['generator_git_commit'])
                assert group.attrs['generator_git_url']
                for name,record in group['provenance'].items():
                    attrs=record.attrs
                    assert re.fullmatch('[0-9a-f]{40}',attrs['git_commit'])
                    assert attrs['git_url'] and attrs['code_checkout_clean']
                    url=subprocess.check_output(['git','-C',str(repos[name]),'remote','get-url','origin'],text=True).strip()
                    assert attrs['git_url']==url,(path,name)
                    code=subprocess.check_output(['git','-C',str(repos[name]),'show',attrs['git_commit']+':'+attrs['code_path']])
                    assert hashlib.sha256(code).hexdigest()==attrs['code_sha256'],(path,name)
            def check_spectrum(name,obj):
                if isinstance(obj,h5py.Dataset) and name.split('/')[-1] in ['S_ion','S_electron','S_total']:
                    assert obj.attrs['git_url']
                    assert re.fullmatch('[0-9a-f]{40}',obj.attrs['git_commit'])
            h.visititems(check_spectrum)
            if path.parent==ROOT/'tables':
                header=path.with_suffix('.txt').read_text().splitlines()[:12]
                assert '# git_url = '+h.attrs['git_url'] in header
                assert '# git_commit = '+h.attrs['git_commit'] in header
    print('All HDF5 tables, spectra and text headers: Git URLs, full checkout commits and committed source hashes verified.')


def main():
    verify_provenance()
    worst=np.zeros((4,4))
    count=0
    for path in sorted((ROOT/'tables/comparison').glob('*.h5')):
        if path.name=='summary.h5': continue
        with h5py.File(path) as h:
            assert all(k in h.attrs for k in REQUIRED), path
            values=[]
            for name in NAMES:
                g=h[name]
                assert all(k in g.attrs for k in REQUIRED), (path,name)
                ion,electron,total=[g[x][:] for x in ['S_ion','S_electron','S_total']]
                assert np.isfinite(total).all(), (path,name)
                assert total.min() >= -1e-12*total.max(), (path,name)
                np.testing.assert_allclose(ion+electron,total,rtol=1e-13,atol=1e-25)
                np.testing.assert_allclose(total,total[::-1],rtol=1e-8,atol=1e-16*total.max())
                values.append(total)
            matrix=np.array([[error(a,b) for b in values] for a in values])
            np.testing.assert_array_equal(matrix,h['pairwise_error'][:])
            assert np.max(h['pairwise_component_error'][:]) < TOL
            assert np.max(h['Vierinen_convergence_error'][:]) < TOL
            # Verify baseline analytic numbers against the pre-existing tables.
            with h5py.File(ROOT/'tables'/path.name) as old:
                np.testing.assert_array_equal(h['frequency_hz'][:],old['frequency_hz'][:])
                np.testing.assert_array_equal(h['Analytic/S_total'][:],old['S_total'][:])
            worst=np.maximum(worst,matrix)
            count+=1
    assert count==6
    with h5py.File(ROOT/'tables/comparison/summary.h5') as h:
        np.testing.assert_array_equal(worst,h['worst_pairwise_error'][:])
    assert np.max(worst) < TOL
    print('Six baseline files: tables, components, symmetry, quadrature refinement, and matrix verified.')
    for path in sorted((ROOT/'tables/extended').glob('*.h5')):
        with h5py.File(path) as h:
            assert all(k in h.attrs for k in REQUIRED), path
            names=h['code_names'].asstr()[:]
            values=[h[n+'/S_total'][:] for n in names]
            matrix=np.array([[error(a,b) for b in values] for a in values])
            np.testing.assert_array_equal(matrix,h['pairwise_error'][:])
            assert np.isfinite(matrix).all()
            print(path.stem, 'initial PASS' if matrix.max()<=TOL else 'initial FAIL', matrix.max())
            if 'refined' in h:
                g=h['refined']
                names=g['code_names'].asstr()[:]
                values=[g[n+'/S_total'][:] for n in names]
                matrix=np.array([[error(a,b) for b in values] for a in values])
                np.testing.assert_array_equal(matrix,g['pairwise_error'][:])
                assert matrix.max() < TOL, path
                assert g.attrs['swoboda_convergence_total'] < TOL, path
                if 'Vierinen' in names: assert g.attrs['vierinen_convergence_total'] < TOL, path
                print(path.stem, 'refined PASS', matrix.max())


if __name__=='__main__': main()
