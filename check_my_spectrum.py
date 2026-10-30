"""Edit my_spectrum() to call your code, then run this file with Python 3.

Only NumPy and h5py are needed. The reference spectrum is already in the repo.
"""
from pathlib import Path
import sys

import h5py
import numpy as np

REFERENCE = Path(__file__).resolve().parent / 'tables/expanded/f_region_440.2MHz.h5'
TOLERANCE = 1e-6


def my_spectrum(frequency_hz):
    """Replace the line below with a call to your spectrum calculator.

    Use these physical inputs:
      Radar frequency: 440.2e6 Hz, monostatic backscatter (k = 4*pi*f_r/c).
      Electron density: 1e11 m^-3.
      Electron temperature: 2000 K; ion temperature: 1000 K.
      Ions: 100% singly charged O+, mass exactly 16 atomic mass units.
      Magnetic field, all collision rates and all species drifts: zero.
      Distributions: isotropic Maxwellian.

    Evaluate at the supplied frequency_hz array, including negative frequencies
    and the finite zero-frequency limit. Return one real array of total power
    spectral density (ion + electron terms), per electron per Hz. For a spectrum
    proportional to electron density, divide by 1e11. Convert a density per
    radian/s to per Hz by multiplying by 2*pi. Do not normalize the peak or area.
    """
    # If your calculator runs in another language, save its output to HDF5
    # and replace the raise below with these two lines (uncommented):
    # with h5py.File('my_spectrum.h5') as result:
    #     return result['S_total'][:]
    raise NotImplementedError('Replace this line with your calculation and return its spectrum.')


def comparison_error(spectrum, reference):
    """Compare matching real, finite, nonnegative PSD arrays without rescaling."""
    spectrum = np.asarray(spectrum)
    if spectrum.shape != reference.shape:
        raise ValueError(f'Return one array with shape {reference.shape}; received {spectrum.shape}.')
    if np.iscomplexobj(spectrum) or not np.isfinite(spectrum).all():
        raise ValueError('The power spectrum must be real and finite, including at zero frequency.')
    if np.any(spectrum < 0):
        raise ValueError('The power spectrum must be nonnegative.')
    return np.max(np.abs(spectrum - reference)) / max(np.max(spectrum), np.max(reference))


def main():
    with h5py.File(REFERENCE) as table:
        frequency_hz = table['frequency_hz'][:]
        reference = table['Kinetic/S_total'][:]
    try:
        spectrum = my_spectrum(frequency_hz)
    except NotImplementedError:
        print('First edit my_spectrum() in check_my_spectrum.py to call your calculator.')
        return 2
    difference = comparison_error(spectrum, reference)
    passed = difference <= TOLERANCE
    print(f'{"PASS" if passed else "FAIL"}: error = {difference:.3e}; tolerance = {TOLERANCE:.0e}')
    print('Case: F region, 440.2 MHz; reference: Kinetic; no fitted scaling.')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
