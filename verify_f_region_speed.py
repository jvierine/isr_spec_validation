"""Audit the published eleven-code F-region timing product."""
import h5py
import numpy as np

from compare import ROOT
from collect_f_region_speed import ORDER


def main():
    path = ROOT / 'tables/speed_standard_f_region.h5'
    with h5py.File(path) as h, h5py.File(ROOT / 'tables/expanded/f_region_440.2MHz.h5') as spectra:
        assert h.attrs['host'] == 'avaruus'
        assert h.attrs['threads_per_call'] == 1
        assert h.attrs['cpu_affinity'] == '0'
        assert 'AMD EPYC 9754' in h.attrs['cpu_model']
        assert list(h['code_names'].asstr()[:]) == ORDER
        np.testing.assert_array_equal(h['frequency_hz'][:], spectra['frequency_hz'][:])
        assert len(h['frequency_hz']) == 801
        for name in ORDER:
            g = h[name]
            times = g['elapsed_s'][:]
            assert len(times) == 7 and np.isfinite(times).all() and (times > 0).all()
            np.testing.assert_allclose(np.median(times), g.attrs['median_elapsed_s'], rtol=1e-12)
            np.testing.assert_allclose(times.min(), g.attrs['min_elapsed_s'], rtol=1e-12)
            np.testing.assert_allclose(times.max(), g.attrs['max_elapsed_s'], rtol=1e-12)
            assert g.attrs['error_vs_saved'] <= 1e-6, name
            assert len(g.attrs['git_commit']) == 40 and len(g.attrs['code_sha256']) == 64, name
            assert name in spectra and 'S_total' in spectra[name]
        ref = h['Kinetic'].attrs['median_elapsed_s']
        for name in ORDER:
            np.testing.assert_allclose(h[name].attrs['speed_relative_to_kinetic'],
                                       ref/h[name].attrs['median_elapsed_s'], rtol=1e-12)
    for ext in ['png', 'svg']:
        assert (ROOT / 'figures' / ('f_region_speed.' + ext)).stat().st_size > 1000
    print('Eleven avaruus CPU-0 timings, spectra, provenance, and Rustplotlib table verified')


if __name__ == '__main__':
    main()
