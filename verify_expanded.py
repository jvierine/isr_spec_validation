"""Audit expanded arrays, source identities, coverage, and rendered artifacts."""
import hashlib
import json
import subprocess
import h5py
import numpy as np
from compare import ROOT, error
from additional import cases
from additional_sources import record


def main():
    counts={n:0 for n in ['Buchert','Virtanen','Nicolls','Skolar','inscar']}
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
                if name in origin:
                    np.testing.assert_array_equal(a,origin[name+'/S_total'][:])
                else:
                    counts[name]+=1
                    assert g.attrs['status']=='computed'
                    r=record(name)
                    for k,v in r.items(): assert g.attrs[k]==v,(path,name,k)
                    code=subprocess.check_output(['git','-C',str(ROOT),'show',g.attrs['adapter_git_commit']+':'+g.attrs['adapter_code_path']])
                    assert hashlib.sha256(code).hexdigest()==g.attrs['adapter_sha256']
                    if 'coarse_S_total' in g:
                        np.testing.assert_equal(error(a,g['coarse_S_total'][:]),g.attrs['convergence_error'])
                        assert g.attrs['convergence_status']==('checked' if g.attrs['convergence_error']<=1e-6 else 'unresolved')
            for n in ['Martinez','Sandbem']:
                assert h['availability/'+n].attrs['status']=='not_run' and n not in h
            for n in counts:
                status=h['availability/'+n].attrs['status']
                assert status in ['computed','unsupported'],(path,n,status)
                assert (n in h)==(status=='computed')
            np.testing.assert_array_equal(h['pairwise_error'][:],[[error(a,b) for b in arrays] for a in arrays])
        for ext in ['png','svg']:
            figure=ROOT/'figures'/(oldpath.stem+'.'+ext)
            assert figure.stat().st_size>1000,figure
        print(oldpath.stem,'arrays, provenance, metrics and figures verified')
    assert counts=={'Buchert':9,'Virtanen':8,'Nicolls':11,'Skolar':7,'inscar':5},counts
    print('Coverage:',counts)


if __name__=='__main__': main()
