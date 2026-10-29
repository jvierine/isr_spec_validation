"""Resolve numerical discrepancies without replacing either upstream integrator."""
import sys
import argparse
import json
import h5py
import numpy as np
from compare import ROOT, load_juha, vierinen, swoboda, error
from metadata import attach
from provenance import sources, read_sources, stamp


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--case')
    ap.add_argument('--john-only',action='store_true')
    args=ap.parse_args()
    provenance=sources()
    juha=load_juha(ROOT/'.cache/vierinen/isr_spec.py')
    original=juha.gordoyev2
    def longer(*args,**kwargs):
        kwargs['inf']=2*kwargs.get('inf',1e-3)
        return original(*args,**kwargs)
    juha.gordoyev2=longer
    sys.path.insert(0,str(ROOT/'.cache/swoboda'))
    from ISRSpectrum.ISRSpectrum import Specinit
    from ISRSpectrum.plugins import gordplugs
    namespace=gordplugs['default'].calcgordeyev.__func__.__globals__
    upstream=namespace['sommerfelderfrep']
    calls=[]
    refinement=4
    def quadrature(func,N,omega,b1,**kwargs):
        kwargs['errF']=1e-12
        result=upstream(func,N*refinement,omega,b1,**kwargs)
        calls.append((N*refinement,int(result[1]),result[2]))
        if not result[1]: raise RuntimeError('Swoboda quadrature failed to converge')
        return result
    namespace['sommerfelderfrep']=quadrature
    for path in sorted((ROOT/'tables/extended').glob('*.h5')):
        if args.case and path.stem!=args.case: continue
        print(path.stem,flush=True)
        with h5py.File(path,'r+') as h:
            case=json.loads(h.attrs['parameters_json'])
            case['frequency_hz']=h['frequency_hz'][:]
            used_sources=read_sources(h)
            used_sources['Swoboda']=provenance['Swoboda']
            values={'Kinetic':np.array([h['Kinetic/'+x][:] for x in ['S_ion','S_electron','S_total']])}
            refinement=4
            low=swoboda(Specinit,case)
            for refinement in [8,16,32,64,128]:
                values['Swoboda']=swoboda(Specinit,case)
                sc=error(low[-1],values['Swoboda'][-1])
                print('Swoboda N',100*refinement,'change',sc,flush=True)
                if sc<1e-8: break
                low=values['Swoboda']
            else: raise RuntimeError('Swoboda resolution refinement did not converge')
            jc=np.nan
            if 'Vierinen' in h:
                if args.john_only:
                    used_sources['Vierinen']=read_sources(h['refined'])['Vierinen']
                    values['Vierinen']=np.array([h['refined/Vierinen/'+x][:] for x in ['S_ion','S_electron','S_total']])
                    jc=h['refined'].attrs['vierinen_convergence_total']
                else:
                    used_sources['Vierinen']=provenance['Vierinen']
                    low=vierinen(juha,case,80000)
                    values['Vierinen']=vierinen(juha,case,160000)
                    jc=error(low[-1],values['Vierinen'][-1])
            if 'Analytic' in h:
                values['Analytic']=np.array([h['Analytic/'+x][:] for x in ['S_ion','S_electron','S_total']])
            if 'refined' in h: del h['refined']
            g=h.create_group('refined')
            attach(g,case)
            g.attrs['vierinen_time_window_multiplier']=2
            g.attrs['vierinen_points']=160000
            g.attrs['vierinen_convergence_total']=jc
            g.attrs['swoboda_quadrature_N']=100*refinement
            g.attrs['swoboda_errF']=1e-12
            g.attrs['swoboda_convergence_total']=sc
            g['swoboda_convergence_calls']=np.array(calls)
            calls.clear()
            names=list(values)
            g['code_names']=np.array(names,dtype=h5py.string_dtype())
            matrix=np.array([[error(a[-1],b[-1]) for b in values.values()] for a in values.values()])
            g['pairwise_error']=matrix
            for n,v in values.items():
                attach(g.create_group(n),case)
                for component,a in zip(['S_ion','S_electron','S_total'],v): g[n+'/'+component]=a
            stamp(g, {n:used_sources[n] for n in names}, 'refine.py')
            print(names,matrix,'convergence',sc,jc,flush=True)


if __name__=='__main__': main()
