"""Audit expanded arrays, source identities, coverage, and rendered artifacts."""
import hashlib
import json
import subprocess
import h5py
import numpy as np
from compare import ROOT, error
from additional import cases
from additional_sources import record
from rust_validation import pinned_source


def main():
    counts={n:0 for n in ['Buchert','Virtanen','Martinez','Nicolls','Sandbem','Skolar','inscar','EISCAT','Vierinen']}
    rust_source,rust_commit=pinned_source()
    for category,oldpath,case in cases():
        path=ROOT/'tables/expanded'/oldpath.name
        with h5py.File(path) as h,h5py.File(oldpath) as old:
            origin=old['refined'] if 'refined' in old else old
            np.testing.assert_array_equal(h['frequency_hz'][:],old['frequency_hz'][:])
            assert json.loads(h.attrs['parameters_json'])==json.loads(old.attrs['parameters_json'])
            names=h['code_names'].asstr()[:]; arrays=[]
            for name in names:
                g=h[name]; a=g['S_total'][:]; arrays.append(a)
                assert a.shape==h['frequency_hz'].shape and np.isfinite(a).all()
                assert a.min()>=-1e-12*a.max(),(path,name)
                np.testing.assert_equal(error(a,a[::-1]),g.attrs['symmetry_error'])
                if name=='Vierinen':
                    counts[name]+=1
                    assert g.attrs['implementation']=='RUISDAP Rust'
                    assert g.attrs['host']=='avaruus' and g.attrs['threads_per_call']==1
                    assert len(g['elapsed_s'])==31 and g.attrs['median_elapsed_s']>0
                    assert g.attrs['git_commit']==rust_commit
                    assert g.attrs['code_sha256']==hashlib.sha256(rust_source.read_bytes()).hexdigest()
                    assert g.attrs['adapter_sha256']==hashlib.sha256((ROOT/'rust/src/main.rs').read_bytes()).hexdigest()
                    assert g.attrs['max_relative_change']<=1e-9
                    assert g.attrs['error_vs_kinetic']<=1e-6
                    assert case['B']==0 or case['theta'] in (0,180)
                    with h5py.File(ROOT/'tables/rust'/path.name) as measured:
                        np.testing.assert_array_equal(a,measured['Vierinen/S_total'][:])
                elif name in origin:
                    np.testing.assert_array_equal(a,origin[name+'/S_total'][:])
                else:
                    counts[name]+=1
                    assert g.attrs['status']=='computed'
                    if name in ['Martinez','Sandbem']:
                        assert g.attrs['host']=='avaruus' and g.attrs['threads_per_call']==1
                        assert g.attrs['median_elapsed_s']>0
                        assert len(g['elapsed_s'])==7
                        assert hashlib.sha256((ROOT/'octave/octave_kernel.m').read_bytes()).hexdigest()==g.attrs['adapter_sha256']
                        assert hashlib.sha256((ROOT/'.cache'/('ISR_Model' if name=='Martinez' else 'ISRTS')/g.attrs['code_path']).read_bytes()).hexdigest()==g.attrs['code_sha256']
                        continue
                    if name=='EISCAT':
                        assert g.attrs['host']=='avaruus' and g.attrs['threads_per_call']==1
                        assert len(g['elapsed_s'])==7 and g.attrs['median_elapsed_s']>0
                        assert hashlib.sha256((ROOT/'octave/eiscat_case.m').read_bytes()).hexdigest()==g.attrs['adapter_sha256']
                        with h5py.File(ROOT/'tables/eiscat'/path.name) as measured:
                            np.testing.assert_array_equal(a,measured['EISCAT/S_total'][:])
                            assert g.attrs['code_sha256']==measured['EISCAT'].attrs['code_sha256']
                        continue
                    r=record(name)
                    for k,v in r.items():
                        measured=g.attrs[k]
                        if k=='git_url': measured=measured.removesuffix('.git'); v=v.removesuffix('.git')
                        assert measured==v,(path,name,k)
                    code=subprocess.check_output(['git','-C',str(ROOT),'show',g.attrs['adapter_git_commit']+':'+g.attrs['adapter_code_path']])
                    assert hashlib.sha256(code).hexdigest()==g.attrs['adapter_sha256']
                    if 'coarse_S_total' in g:
                        np.testing.assert_equal(error(a,g['coarse_S_total'][:]),g.attrs['convergence_error'])
                        assert g.attrs['convergence_status']==('checked' if g.attrs['convergence_error']<=1e-6 else 'unresolved')
                    if name=='inscar':
                        assert g.attrs['gordeyev_method']=='simpson' and g.attrs['gordeyev_size']==128001
                        for dataset,metric in [('cutoff_S_total','cutoff_convergence_error'),('dc_limit_S_total','dc_limit_error')]:
                            np.testing.assert_equal(error(a,g[dataset][:]),g.attrs[metric])
                            assert g.attrs[metric]<=1e-6
                        assert g.attrs['convergence_error']<=1e-6
                        assert error(a,h['Kinetic/S_total'][:])<=1e-6
            for n in counts:
                status='computed' if n in h else h['availability/'+n].attrs['status']
                assert status in ['computed','unsupported'],(path,n,status)
                assert (n in h)==(status=='computed')
            np.testing.assert_array_equal(h['pairwise_error'][:],[[error(a,b) for b in arrays] for a in arrays])
        for ext in ['png','svg']:
            figure=ROOT/'figures'/(oldpath.stem+'.'+ext)
            assert figure.stat().st_size>1000,figure
        print(oldpath.stem,'arrays, provenance, metrics and figures verified')
    assert counts=={'Buchert':9,'Virtanen':8,'Martinez':7,'Nicolls':11,'Sandbem':11,'Skolar':7,'inscar':5,'EISCAT':7,'Vierinen':8},counts
    print('Coverage:',counts)


if __name__=='__main__': main()
