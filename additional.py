"""Prepare shared inputs, run Python adapters, and collect expanded HDF5 tables."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import sys
import h5py
import numpy as np
import scipy
from compare import ROOT, NAMES, error
from metadata import attach
from provenance import source_info, stamp
from additional_sources import SOURCES, checkout, record


def text_attr(value):
    return value.decode('utf-8') if isinstance(value, bytes) else value


def cases():
    for category in ['comparison','extended']:
        for path in sorted((ROOT/'tables'/category).glob('*.h5')):
            if path.name=='summary.h5': continue
            with h5py.File(path) as h:
                case=json.loads(h.attrs['parameters_json'])
                case['frequency_hz']=h['frequency_hz'][:]
            yield category,path,case


def prepare():
    for name in SOURCES: checkout(name)
    with h5py.File(ROOT/'.cache/additional_inputs.h5','w') as h:
        for category,path,case in cases():
            g=h.create_group('cases/'+case['name'])
            attach(g,case)
            g.attrs['parameters_json']=json.dumps({k:v for k,v in case.items() if k!='frequency_hz'})
            g.attrs['ion_names']=','.join(i[0] for i in case['ions'])
            g['ion_masses_u']=[i[1] for i in case['ions']]
            g['ion_fractions']=[i[2] for i in case['ions']]
            g['frequency_hz']=case['frequency_hz']


def python_run(selected=None):
    from additional_python import RUNNERS, Unsupported
    target=ROOT/'.cache/additional_python.h5'
    with h5py.File(target,'a') as h:
        for category,path,case in cases():
            for name,runner in RUNNERS.items():
                if selected and name not in selected: continue
                key=case['name']+'/'+name
                if key in h: del h[key]
                g=h.create_group(key)
                try:
                    print(case['name'],name,flush=True)
                    low=runner(case,False); high=runner(case,True)
                    if not np.isfinite(high).all(): raise ValueError('Nonfinite spectrum')
                    g['S_total']=high; g['coarse_S_total']=low
                    g.attrs['convergence_error']=error(low,high)
                    g.attrs['status']='computed'
                    print('convergence',g.attrs['convergence_error'],flush=True)
                except Unsupported as exc:
                    g.attrs['status']='unsupported'; g.attrs['reason']=str(exc)
                except Exception as exc:
                    g.attrs['status']='error'; g.attrs['reason']=str(exc)
                    print(type(exc).__name__,str(exc),flush=True)
                g.attrs['python_version']=platform.python_version()
                g.attrs['numpy_version']=np.__version__; g.attrs['scipy_version']=scipy.__version__
                g.attrs['adapter_sha256']=hashlib.sha256((ROOT/'additional_python.py').read_bytes()).hexdigest()
                for k,v in record(name).items(): g.attrs[k]=v
                h.flush()


def collect():
    rawpaths=[ROOT/'.cache'/('additional_'+lang+'.h5') for lang in ['python','r','julia']]
    outdir=ROOT/'tables/expanded'; outdir.mkdir(parents=True,exist_ok=True)
    for category,path,case in cases():
        with h5py.File(path) as old,h5py.File(outdir/path.name,'w') as h:
            origin=old['refined'] if 'refined' in old else old
            for k,v in old.attrs.items(): h.attrs[k]=v
            h.attrs['category']=category
            h['frequency_hz']=case['frequency_hz']
            names=list(NAMES) if category=='comparison' else list(origin['code_names'].asstr()[:])
            records={n:dict(origin['provenance'][n].attrs) for n in names}
            for name in names:
                old.copy(origin[name],h,name=name)
                h[name].attrs['status']='computed'
                for k,v in origin.attrs.items():
                    if k.startswith('generator_'): h[name].attrs['origin_'+k]=v
            status=h.create_group('availability')
            for name in ['Martinez','Sandbem']:
                state=status.create_group(name)
                state.attrs['status']='not_run'
                state.attrs['reason']='MATLAB execution cancelled at user request after license failures; no spectrum evaluated.'
            for rawpath in rawpaths:
                with h5py.File(rawpath) as raw:
                    for name,g in raw[case['name']].items():
                        state=status.create_group(name)
                        for k,v in g.attrs.items(): state.attrs[k]=text_attr(v)
                        if text_attr(g.attrs['status'])!='computed': continue
                        expected=record(name)
                        for k in ['git_commit','code_sha256']:
                            assert text_attr(g.attrs[k])==expected[k],(name,k)
                        adapter={'Nicolls':'additional_python.py','Skolar':'additional_python.py',
                                 'inscar':'additional_python.py','Virtanen':'additional_r.R',
                                 'Buchert':'additional_julia.jl'}[name]
                        adapter_info=source_info(ROOT/adapter)
                        assert text_attr(g.attrs['adapter_sha256'])==adapter_info['code_sha256'],name
                        raw.copy(g,h,name=name)
                        for k,v in g.attrs.items(): h[name].attrs[k]=text_attr(v)
                        for k,v in adapter_info.items(): h[name].attrs['adapter_'+k]=v
                        h[name].attrs['convergence_status']=('checked' if g.attrs['convergence_error']<=1e-6 else 'unresolved') if 'convergence_error' in g.attrs else 'not_assessed'
                        if name=='Virtanen':
                            native=ROOT/'.cache/ISspectrum/src/spec_worker.c'
                            assert text_attr(g.attrs['native_code_sha256'])==hashlib.sha256(native.read_bytes()).hexdigest()
                        attach(h[name],case)
                        names.append(name); records[name]=expected
                        if 'S_total' not in h[name]: raise ValueError(name)
            arrays=[h[n+'/S_total'][:] for n in names]
            assert all(a.shape==case['frequency_hz'].shape and np.isfinite(a).all() for a in arrays)
            h['code_names']=np.array(names,dtype=h5py.string_dtype())
            h['pairwise_error']=np.array([[error(a,b) for b in arrays] for a in arrays])
            h.attrs['pass_tolerance']=1e-6
            stamp(h,records,'additional.py')
            print(case['name'],names,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['prepare','python','collect'])
    p.add_argument('--code',action='append',choices=['Nicolls','Skolar','inscar'])
    args=p.parse_args()
    if args.action=='prepare': prepare()
    elif args.action=='python': python_run(args.code)
    else: collect()
