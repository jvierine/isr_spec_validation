"""Longitudinal density fluctuations derived from linear kinetic response.

Fourier convention exp(i*k.x-i*omega*t). S(f) is per Hz, normalized per
background electron: integral S(f) df = equal-time structure factor.
J = integral_0^infty <exp(-i*k.Delta x)> exp(i*omega*t) dt.
The BGK option is number conserving; it is not a Coulomb collision operator.
References: Salpeter (1960), Dougherty & Farley (1960), Longley et al. (2021).
"""
from dataclasses import dataclass
import numpy as np
from scipy.constants import e, m_e, epsilon_0, k as k_B, c, atomic_mass
from scipy.special import wofz, ive

@dataclass(frozen=True)
class Species:
    name: str
    density: float
    temperature: float
    mass: float
    charge: float
    collision_rate: float = 0.0  # s^-1, NOT cycles/s
    drift: float = 0.0  # along scattering vector (m/s), used only at B=0

    def __post_init__(self):
        if min(self.density,self.temperature,self.mass)<=0 or self.collision_rate<0:
            raise ValueError('density, temperature, mass must be positive; collision rate nonnegative')
        if self.charge==0: raise ValueError('charged species required')

    @property
    def sigma(self): return np.sqrt(k_B*self.temperature/self.mass)

    @property
    def wp2(self): return self.density*self.charge**2/(epsilon_0*self.mass)


def radar_k(radar_hz=430e6, doppler_hz=0.0):
    """Monostatic |k_s-k_i|, with optional signed scattered frequency shift."""
    if radar_hz <= 0 or np.any(np.asarray(doppler_hz) <= -radar_hz):
        raise ValueError('transmitted and received frequencies must be positive')
    return 2*np.pi*(2*radar_hz+np.asarray(doppler_hz))/c


def maxwellian_response(f_hz, k, species, B=0.0, theta_deg=0.0,
                        harmonic_tol=1e-12, nmax=None):
    """Return susceptibility and free-particle density PSD in Hz^-1.

    theta is angle between k and B, 0 parallel and 90 perpendicular.
    Exact perpendicular requires positive BGK rate: collisionless lines are
    distributions, not a finite continuous PSD. No hidden broadening.
    """
    if k<=0 or B<0 or not 0<=theta_deg<=180: raise ValueError('invalid k, B, or angle')
    if B and species.drift: raise NotImplementedError('magnetized drift requires vector distribution')
    w=2*np.pi*np.asarray(f_hz,dtype=float)-k*species.drift
    nu=species.collision_rate
    z=w+1j*nu
    if B==0:
        a=np.sqrt(2)*k*species.sigma
        J=np.sqrt(np.pi)/a*wofz(z/a)
    else:
        omega=abs(species.charge)*B/species.mass
        kp=k*abs(np.cos(np.deg2rad(theta_deg)))
        kt=k*abs(np.sin(np.deg2rad(theta_deg)))
        b=(kt*species.sigma/omega)**2
        if nmax is None:
            nmax=max(5,int(np.ceil(10*np.sqrt(b+1)+10)))
        orders=np.arange(-nmax,nmax+1)
        weights=ive(orders,b)
        if abs(weights.sum()-1)>harmonic_tol:
            raise ValueError('Bessel harmonics do not converge; increase nmax')
        J=np.zeros_like(z,dtype=complex)
        perpendicular=kp<1e-12*k
        if perpendicular and nu==0:
            raise ValueError('exact perpendicular collisionless spectrum has delta lines; specify physical collisions')
        for l,weight in zip(orders,weights):
            if perpendicular:
                J+=weight/(nu-1j*(w-l*omega))
            else:
                a=np.sqrt(2)*kp*species.sigma
                J+=weight*np.sqrt(np.pi)/a*wofz((z-l*omega)/a)
    J=J/(1-nu*J)
    chi=species.wp2/(k*species.sigma)**2*(1+1j*w*J)
    free=2*J.real
    if np.any(free < -1e-12*max(float(np.max(free)),1e-30)):
        raise ArithmeticError('negative free spectrum: cancellation or resolution failure')
    return chi, np.maximum(free,0)


def density_spectrum(f_hz,k,electrons,ions,B=0.0,theta_deg=0.0):
    """Full electron-density spectrum including electron and ion source terms.

    All electron components have charge -e and electron mass. Quasineutrality
    is enforced. Component noises add incoherently before collective dressing.
    """
    if not electrons or not ions: raise ValueError('electrons and ions required')
    if any(s.charge!=-e or s.mass!=m_e for s in electrons):
        raise ValueError('electron components must have charge -e and mass m_e')
    ne=sum(s.density for s in electrons)
    if not np.isclose(sum(s.density*s.charge/e for s in ions),ne,rtol=1e-8):
        raise ValueError('plasma must be quasineutral')
    ce=np.zeros_like(np.asarray(f_hz),dtype=complex); ci=ce.copy()
    qe=np.zeros_like(np.asarray(f_hz),dtype=float); qi=qe.copy()
    for s in electrons:
        chi,free=maxwellian_response(f_hz,k,s,B,theta_deg)
        ce+=chi; qe+=s.density/ne*free
    for s in ions:
        chi,free=maxwellian_response(f_hz,k,s,B,theta_deg)
        ci+=chi; qi+=(s.charge/e)**2*s.density/ne*free
    eps=1+ce+ci
    es=np.abs((1+ci)/eps)**2*qe
    ins=np.abs(ce/eps)**2*qi
    return {'total':es+ins,'electron':es,'ion':ins,'epsilon':eps,'chi_e':ce,'chi_i':ci}


def oxygen_plasma(ne=1e11,Te=2000.,Ti=1000.,nu_e=0.,nu_i=0.):
    return ([Species('e',ne,Te,m_e,-e,nu_e)],
            [Species('O+',ne,Ti,16*atomic_mass,e,nu_i)])
