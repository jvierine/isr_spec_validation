"""Collisionless Maxwellian ISR spectra, Kudeki and Milla (2011), Part I.

All frequencies are in Hz. Spectra are per electron, per Hz.
The ion line and electron contribution are kept separate.
"""
from pathlib import Path

import h5py
import numpy as np
from scipy.special import dawsn

# SI constants. Ion masses below are explicitly defined in atomic mass units.
kB = 1.380649e-23
e = 1.602176634e-19
eps0 = 8.8541878128e-12
me = 9.1093837139e-31
amu = 1.66053906892e-27
c = 299792458.0

# name, electron density / m^-3, Ti / K, Te / K, (ion, mass / u, number fraction)
CASES = [
    ('f_region', 1e11, 1000.0, 2000.0, [('O+', 16.0, 1.0)]),
    ('molecular', 1e11, 500.0, 500.0,
     [('O2+', 32.0, 0.5), ('NO+', 30.0, 0.3), ('N2+', 28.0, 0.2)]),
    ('topside', 5e10, 1500.0, 3000.0,
     [('O+', 16.0, 0.5), ('H+', 1.0, 0.5)]),
]
FREQUENCY_HZ = np.arange(-100000.0, 100000.1, 250.0)
REFERENCE = 'Kudeki and Milla (2011), Part I, doi:10.1109/TGRS.2010.2057252'


def gordeyev(omega, k, temperature, mass):
    """Integral of exp(-k^2 kB T t^2 / (2 m)) exp(-i omega t), t >= 0."""
    width = k * np.sqrt(2.0 * kB * temperature / mass)
    theta = omega / width
    return (np.sqrt(np.pi) * np.exp(-theta**2) - 2j * dawsn(theta)) / width


def spectrum(radar_hz, ne, ti, te, ions, frequency_hz):
    """S_ion, S_electron, S_total in Hz^-1 per electron; no area normalization."""
    assert np.isclose(sum(fraction for _, _, fraction in ions), 1.0)
    k = 4.0 * np.pi * radar_hz / c
    omega = 2.0 * np.pi * np.asarray(frequency_hz)
    ge = gordeyev(omega, k, te, me)
    chi_e = ne * e**2 / (eps0 * kB * te * k**2) * (1.0 - 1j * omega * ge)
    chi_i = np.zeros_like(ge)
    free_i = np.zeros_like(omega)
    for _, mass_u, fraction in ions:
        gi = gordeyev(omega, k, ti, mass_u * amu)
        chi_i += ne * fraction * e**2 / (eps0 * kB * ti * k**2) * (1.0 - 1j * omega * gi)
        free_i += fraction * 2.0 * gi.real
    dielectric = 1.0 + chi_e + chi_i
    ion = abs(chi_e / dielectric)**2 * free_i
    electron = abs((1.0 + chi_i) / dielectric)**2 * 2.0 * ge.real
    return ion, electron, ion + electron


def write_tables():
    directory = Path(__file__).parent / 'tables'
    directory.mkdir(exist_ok=True)
    for radar_mhz in [440.2, 930.0]:
        for name, ne, ti, te, ions in CASES:
            ion, electron, total = spectrum(radar_mhz * 1e6, ne, ti, te, ions, FREQUENCY_HZ)
            assert np.isfinite(total).all() and (total >= 0).all()
            np.testing.assert_allclose(total, total[::-1], rtol=1e-13)
            stem = f'{name}_{radar_mhz:g}MHz'
            composition = '; '.join(f'{species}: {fraction:g} at {mass:g} u'
                                    for species, mass, fraction in ions)
            header = (f'{name}; radar {radar_mhz:g} MHz; ne {ne:g} m^-3; Ti {ti:g} K; Te {te:g} K\n'
                      f'{composition}\n'
                      'B = 0 T; collision rates = 0 s^-1; bulk velocity = 0 m/s\n'
                      'S_ion, S_electron, S_total: Hz^-1 per electron; not normalized to unit area\n'
                      'frequency_Hz          S_ion             S_electron        S_total')
            np.savetxt(directory / f'{stem}.txt',
                       np.column_stack([FREQUENCY_HZ, ion, electron, total]),
                       fmt=['%12.1f', '% .12e', '% .12e', '% .12e'], header=header)
            with h5py.File(directory / f'{stem}.h5', 'w') as h:
                h.attrs['radar_frequency_hz'] = radar_mhz * 1e6
                h.attrs['electron_density_m3'] = ne
                h.attrs['ion_temperature_k'] = ti
                h.attrs['electron_temperature_k'] = te
                h.attrs['magnetic_field_t'] = 0.0
                h.attrs['collision_frequency_s'] = 0.0
                h.attrs['bulk_velocity_m_s'] = 0.0
                h.attrs['composition'] = composition
                h.attrs['reference'] = REFERENCE
                h['frequency_hz'] = FREQUENCY_HZ
                h['frequency_hz'].attrs['units'] = 'Hz'
                for key, values in [('S_ion', ion), ('S_electron', electron), ('S_total', total)]:
                    h[key] = values
                    h[key].attrs['units'] = 'Hz^-1 per electron'


if __name__ == '__main__':
    write_tables()
