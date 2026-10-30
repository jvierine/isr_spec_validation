"""Adapters to upstream Python implementations, without fitting/scaling spectra.

Compatibility limits and fixed unit conversions are documented in NEW_CODES.md.
The native one-ion calculators are never averaged to manufacture a mixture.
"""
import importlib.util
import sys
from functools import lru_cache
import numpy as np
from scipy import constants as c
from compare import ROOT, error


class Unsupported(ValueError):
    pass


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache
def nicolls_module():
    root = ROOT/'.cache/isr_school/is_spectral_model'
    sys.path.insert(0, str(root))
    mod = load(root/'ismodel.py', 'nicolls_model')
    original = mod.ISspec.funcgv

    def integrand(self, t, params):
        alpha, phi, neutral, parallel, perpendicular = params
        # Exact zero-field limit; avoid 0 * sin(0)^2 / 0 in upstream.
        if phi == 0 and parallel == 0 and perpendicular == 0:
            return np.exp(-neutral*t-t*t/4)
        return original(self,t,params)
    mod.ISspec.funcgv = integrand
    original_integral = mod.sommerfeldIntegralM

    def checked_integral(func, x, *args, **kwargs):
        # Same integrator, bounded working memory, and enforce its success flag.
        results=[]; loops=[]
        for start in range(0,len(x),32):
            result, flag, loop = original_integral(func,x[start:start+32],*args,**kwargs)
            if flag != 1:
                raise RuntimeError(f'Nicolls integral did not converge: loop={loop}')
            results.append(result); loops.append(loop)
        return np.concatenate(results), 1, max(loops)
    mod.sommerfeldIntegralM = checked_integral
    return mod


def nicolls(case, refined=True):
    mod=nicolls_module()
    f=case['frequency_hz']; ni=len(case['ions'])
    # computeSpec uses a uniform grid; include the central gap for plasma lines,
    # then select the exact requested samples, without interpolation.
    df=float(np.min(np.diff(f)))
    inp=dict(Nion=ni,mi=[i[1] for i in case['ions']],B=case['B'],
             f0=case['radar_hz'],te=case['te'],alpha=case['theta'],ne=case['ne'],
             ti=[case['ti']]*ni,ni=[i[2] for i in case['ions']],ve=0.,vi=[0.]*ni,
             nuen=case.get('nu_e',0.),nuin=[case.get('nu_i',0.)]*ni)
    mode=[int(case['B']!=0),0,int(bool(case.get('nu_e',0) or case.get('nu_i',0)))]
    obj=mod.ISspec(inp,emode=mode,imode=mode,fmax=max(abs(f)),
                   Nfreq=int(round(2*max(abs(f))/df))+1,
                   czparams=(1e-20 if refined else 1e-16,262144,100,256 if refined else 128,32. if refined else 16.))
    # ACF calculation is not needed for a spectrum comparison.
    obj.spec2acf=lambda ff,ss:(np.array([]),np.array([]))
    ff,s,_,_=obj.computeSpec()
    idx=np.rint((f-ff[0])/df).astype(int)
    np.testing.assert_allclose(ff[idx],f,rtol=0,atol=1e-8)
    return np.asarray(s[idx],float)/case['ne']


@lru_cache
def skolar_module():
    return load(ROOT/'.cache/OO_Collisions/ISRSpectraFunctions.py','skolar_model')


def skolar(case, refined=True):
    if len(case['ions'])!=1:
        raise Unsupported('Native calcSpectra supports one ion species only.')
    mod=skolar_module(); k=4*np.pi*case['radar_hz']/c.c; w=2*np.pi*case['frequency_hz']
    angle=np.deg2rad(case['theta']) if case['B'] else 0.
    kp=k*np.cos(angle); kt=k*np.sin(angle)
    alpha=1/k/np.sqrt(c.epsilon_0*c.k*case['te']/case['ne']/c.e**2)
    parts=[]
    for mass,T,rate in [(case['ions'][0][1]*c.atomic_mass,case['ti'],case.get('nu_i',0.)),
                        (c.m_e,case['te'],case.get('nu_e',0.))]:
        vth=np.sqrt(2*c.k*T/mass)
        # At k_perp=0 only n=0 survives and the result is independent of Omega.
        gyro=c.e*case['B']/mass if case['B'] else 1.
        rho=vth/np.sqrt(2)/gyro
        nmax=int(np.ceil(12*np.sqrt(kt**2*rho**2)+40)) if kt else 0
        if refined and nmax: nmax*=2
        # Upstream M contains |U|^2/nu. Check the collisionless limit explicitly.
        nu=rate if rate else (1e-7 if refined else 1e-6)
        U=mod.calcU_Maxwellian(w,kp,kt,vth,nmax,rho,gyro,nu)
        M=mod.calcM_Maxwellian(w,kp,kt,vth,nmax,rho,gyro,nu,U)
        chi=mod.calcChi_Maxwellian(w,kp,kt,vth,nmax,rho,gyro,nu,alpha,U,case['te'],T)
        parts.append((M,chi))
    return mod.calcSpectra(parts[0][0],parts[1][0],parts[0][1],parts[1][1])


def inscar(case, refined=True):
    if len(case['ions'])!=1:
        raise Unsupported('Native SpectrumCalculation supports one ion species only.')
    if case.get('nu_e',0) or case.get('nu_i',0):
        raise Unsupported('The inspected collisional F function is not the number-conserving neutral BGK response tested here.')
    import inscar as lib
    import numba
    numba.set_num_threads(1)
    f=case['frequency_hz'].copy()
    f[f==0]=1e-4 if refined else 1e-3

    class Grid(lib.Parameters):
        @property
        def linear_frequency(self): return f

    # B is required positive. For B=0 isotropic Maxwellians, parallel geometry
    # removes the perpendicular term exactly, independent of the dummy B value.
    p=Grid(radar_frequency=case['radar_hz'],magnetic_field_strength=case['B'] or 40e-6,
           aspect_angle=case['theta'] if case['B'] else 0.)
    sim=lib.SpectrumCalculation(); sim.set_params(p)
    k=abs(p.radar_wavenumber); co=abs(np.cos(p.aspect_angle))
    for label,mass,T in [('ion',case['ions'][0][1]*c.atomic_mass,case['ti']),('electron',c.m_e,case['te'])]:
        # Truncate only after the parallel Gaussian has decayed by exp(-72).
        upper=12/(k*np.sqrt(c.k*T/mass)*co)
        points=(256001 if refined else 128001) if case['name']=='plasma_lines' else (64001 if refined else 32001)
        part=lib.Particle(mass=mass,temperature=T,number_density=case['ne'],
                          gordeyev_size=points,
                          gordeyev_upper_lim=upper*(1.25 if refined else 1.))
        getattr(sim,'set_'+label)(part)
        getattr(sim,'set_'+label+'_integration_function')(lib.IntMaxwell())
    _,s=sim.calculate_spectrum()
    # Upstream uses ne/(pi*omega): PSD per angular frequency -> per Hz.
    return s*(2*np.pi/case['ne'])


RUNNERS={'Nicolls':nicolls,'Skolar':skolar,'inscar':inscar}
