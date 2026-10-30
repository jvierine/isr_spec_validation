"""Additional 430-MHz tests; separate from the six-case README matrix."""
import sys
import json
import hashlib
import h5py
import numpy as np
import scipy
from compare import (ROOT, JUHA_REV, JOHN_REV, source, load_juha, vierinen,
                     swoboda, ours, error, calculate)
from metadata import attach
from provenance import sources, stamp


def main():
    juha = load_juha(source('https://github.com/jvierine/isr_analysis', JUHA_REV, 'vierinen')/'isr_spec.py')
    john = source('https://github.com/jswoboda/ISRSpectrum', JOHN_REV, 'swoboda')
    sys.path.insert(0, str(john))
    provenance = sources()
    from ISRSpectrum.ISRSpectrum import Specinit
    directory = ROOT/'tables'/'extended'
    directory.mkdir(exist_ok=True)
    base = dict(ne=1e11, ti=300., te=300., ions=[('NO+',30.,1.)],
                radar_hz=430e6, B=40e-6, theta=42., frequency_hz=np.arange(-20000.,20000.1,50.))
    cases = [dict(base,name='magnetic_42deg'), dict(base,name='magnetic_85deg',theta=85.),
             dict(base,name='neutral_bgk_42deg',nu_e=10000.,nu_i=1000.),
             dict(base,name='neutral_bgk_parallel',theta=0.,nu_e=10000.,nu_i=1000.),
             dict(base,name='plasma_lines',B=0.,theta=0.,te=4000.,ti=1000.,
                  frequency_hz=np.concatenate([np.arange(-4e6,-2e6+1,2500.),np.arange(2e6,4e6+1,2500.)]))]
    for case in cases:
        print(case['name'],flush=True)
        values = {'Kinetic':ours(case), 'Swoboda':swoboda(Specinit,case)}
        convergence = None
        if not case.get('nu_e'):
            values['Vierinen'] = vierinen(juha,case,20000)
            convergence = np.array([error(a,b) for a,b in zip(values['Vierinen'],vierinen(juha,case,40000))])
        if case['B'] == 0:
            values['Analytic'] = np.array(calculate.spectrum(case['radar_hz'],case['ne'],case['ti'],case['te'],case['ions'],case['frequency_hz']))
        names=list(values)
        matrix=np.array([[error(a[-1],b[-1]) for b in values.values()] for a in values.values()])
        with h5py.File(directory/(case['name']+'.h5'),'w') as h:
            attach(h,case)
            h.attrs['parameters_json']=json.dumps({k:v for k,v in case.items() if k!='frequency_hz'})
            h.attrs['spectrum_units']='Hz^-1 per electron; no fitted scaling'
            h.attrs['vierinen_commit']=JUHA_REV
            h.attrs['swoboda_commit']=JOHN_REV
            h.attrs['scipy_version']=scipy.__version__
            h.attrs['numpy_version']=np.__version__
            h.attrs['kinetic_sha256']=hashlib.sha256((ROOT/'models/kinetic.py').read_bytes()).hexdigest()
            h['frequency_hz']=case['frequency_hz']
            h['code_names']=np.array(names,dtype=h5py.string_dtype())
            h['pairwise_error']=matrix
            if convergence is not None: h['Vierinen_convergence_error']=convergence
            for name,array in values.items():
                attach(h.create_group(name),case)
                for component,a in zip(['S_ion','S_electron','S_total'],array): h[name+'/'+component]=a
            stamp(h, {n:provenance[n] for n in names}, 'extended.py')
        print(names,matrix,'convergence',convergence,flush=True)
    from report import write_extended_results
    write_extended_results()


if __name__=='__main__': main()
