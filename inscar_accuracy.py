"""Separate quadrature resolution from the permittivity correction in inscar.

Run with PYTHONPATH pointing to the clean PR checkout's src directory.
The original upstream comparison tables are retained unchanged.
"""
from pathlib import Path
import hashlib
import json
import platform
import time
import h5py
import numpy as np
import numba
import scipy
from scipy import constants as c
import inscar as lib
from compare import ROOT, error
from additional import cases
from provenance import source_info


def evaluate(case, count, method, cutoff=15.):
    f=case['frequency_hz'].copy(); f[f==0]=1e-4
    class Grid(lib.Parameters):
        @property
        def linear_frequency(self): return f
    p=Grid(radar_frequency=case['radar_hz'], magnetic_field_strength=case['B'] or 40e-6,
           aspect_angle=case['theta'] if case['B'] else 0.)
    sim=lib.SpectrumCalculation(); sim.set_params(p)
    k=abs(p.radar_wavenumber); co=abs(np.cos(p.aspect_angle)); responses={}
    for label,mass,T in [('ion',case['ions'][0][1]*c.atomic_mass,case['ti']),('electron',c.m_e,case['te'])]:
        particle=lib.Particle(mass=mass,temperature=T,number_density=case['ne'],
            gordeyev_size=count,gordeyev_exp=3,gordeyev_method=method,
            gordeyev_upper_lim=cutoff/(k*np.sqrt(c.k*T/mass)*co))
        function=lib.IntMaxwell()
        getattr(sim,'set_'+label)(particle)
        getattr(sim,'set_'+label+'_integration_function')(function)
        responses[label]=sim._calculate_f_function(particle,function)
    # Cache the computed responses so the paired constant test uses identical F.
    sim.set_calculate_f_function(lambda part,func:responses['electron' if part.mass==c.m_e else 'ion'])
    _,corrected=sim.calculate_spectrum()
    original=sim._susceptibility
    # Reconstruct the original permittivity through the public susceptibility hook.
    old_epsilon=1e-9/(36*np.pi)
    sim.set_susceptibility_function(lambda part,func:original(part,func)*np.sqrt(c.epsilon_0/old_epsilon))
    _,old_constant=sim.calculate_spectrum()
    return corrected*2*np.pi/case['ne'],old_constant*2*np.pi/case['ne']


def main():
    numba.set_num_threads(1)
    module=Path(lib.__file__).resolve().parent
    assert hasattr(lib.Particle(),'gordeyev_method'), 'Use the PR checkout via PYTHONPATH'
    records={name:source_info(module/name) for name in ['config.py','numba_integration.py','spectrum_calculation.py']}
    dest=ROOT/'diagnostics/inscar_accuracy.h5'; dest.parent.mkdir(exist_ok=True)
    with h5py.File(dest,'w') as h:
        for name,record in records.items():
            g=h.create_group('provenance/'+name)
            for k,v in record.items(): g.attrs[k]=v
        for k,v in source_info(ROOT/'inscar_accuracy.py').items(): h.attrs['generator_'+k]=v
        h.attrs['python_version']=platform.python_version();h.attrs['numpy_version']=np.__version__
        h.attrs['scipy_version']=scipy.__version__;h.attrs['numba_version']=numba.__version__
        h.attrs['epsilon_0_standard']=c.epsilon_0;h.attrs['epsilon_0_original']=1e-9/(36*np.pi)
        for _,path,case in cases():
            with h5py.File(ROOT/'tables/expanded'/path.name) as old:
                if 'inscar' not in old: continue
                g=h.create_group('cases/'+case['name']); g['frequency_hz']=case['frequency_hz']
                g.attrs['parameters_json']=old.attrs['parameters_json']
                ref=old['Kinetic/S_total'][:];g['reference']=ref;g['upstream_saved']=old['inscar/S_total'][:]
                g.attrs['upstream_table_sha256']=hashlib.sha256((ROOT/'tables/expanded'/path.name).read_bytes()).hexdigest()
            settings=[(n,'simpson',15.) for n in [32001,64001,128001]]+[(128001,'simpson',18.)]
            if case['name']=='plasma_lines': settings += [(n,'trapezoid',15.) for n in [64001,128001,256001,512001,1024001]]
            for n,method,cutoff in settings:
                start=time.monotonic(); corrected,native=evaluate(case,n,method,cutoff)
                run=g.create_group(f'{method}_{n}_{cutoff:g}')
                run['corrected']=corrected;run['original_constant']=native
                run.attrs['gordeyev_size']=n;run.attrs['gordeyev_exp']=3;run.attrs['cutoff_sigma']=cutoff
                run.attrs['method']=method;run.attrs['seconds']=time.monotonic()-start
                run.attrs['error_corrected']=error(corrected,ref);run.attrs['error_original_constant']=error(native,ref)
                assert np.isfinite(corrected).all() and corrected.min()>=-1e-10*corrected.max()
                print(case['name'],method,n,cutoff,'errors',error(corrected,ref),error(native,ref),flush=True);h.flush()
            fine=g['simpson_128001_15/corrected'][:]
            g.attrs['grid_refinement_error']=error(fine,g['simpson_64001_15/corrected'][:])
            g.attrs['cutoff_refinement_error']=error(fine,g['simpson_128001_18/corrected'][:])
            assert error(fine,ref)<1e-6
            assert g.attrs['grid_refinement_error']<1e-6 and g.attrs['cutoff_refinement_error']<1e-6


if __name__=='__main__': main()
