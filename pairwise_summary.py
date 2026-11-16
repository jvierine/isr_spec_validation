"""Compute shared-case pairwise errors from HDF5 without fitted scaling."""
from pathlib import Path

import h5py
import numpy as np

from compare import ROOT, error

NAMES = ['Analytic', 'Vierinen', 'Swoboda', 'Kinetic', 'Buchert',
         'Virtanen', 'Martinez', 'Nicolls', 'Sandbem', 'Skolar', 'inscar', 'EISCAT']


def inputs(scope):
    expanded = sorted((ROOT / 'tables' / 'expanded').glob('*.h5'))
    if scope == 'ionline':
        return [p for p in expanded if any(p.stem.startswith(prefix)
                for prefix in ['f_region_', 'molecular_', 'topside_'])]
    return expanded + [ROOT / 'tables' / 'octave' / (name + '.h5') for name in
                       ['near_perp_1deg_lower_hybrid', 'near_perp_unmagnetized_control']]


def main():
    target = ROOT / 'tables' / 'pairwise_summary.h5'
    with h5py.File(target, 'w') as out:
        out['code_names'] = np.asarray(NAMES, dtype=h5py.string_dtype())
        out.attrs['metric'] = 'max abs(A-B) / max(max abs(A), max abs(B))'
        out.attrs['pass_tolerance'] = 1e-6
        for scope in ['ionline', 'all']:
            paths = inputs(scope)
            assert len(paths) == (6 if scope == 'ionline' else 13)
            worst = np.full((len(NAMES), len(NAMES)), np.nan)
            count = np.zeros((len(NAMES), len(NAMES)), dtype=np.int32)
            worst_case = np.full((len(NAMES), len(NAMES)), '', dtype=object)
            for path in paths:
                with h5py.File(path) as h:
                    spectra = {name: h[name + '/S_total'][:] for name in NAMES if name in h}
                    external = ROOT / 'tables/eiscat' / path.name
                    if 'EISCAT' not in spectra and external.exists():
                        with h5py.File(external) as e:
                            np.testing.assert_array_equal(e['frequency_hz'][:], h['frequency_hz'][:])
                            spectra['EISCAT'] = e['EISCAT/S_total'][:]
                    for i, a in enumerate(NAMES):
                        for j in range(i + 1, len(NAMES)):
                            b = NAMES[j]
                            if a not in spectra or b not in spectra:
                                continue
                            measured = error(spectra[a], spectra[b])
                            assert np.isfinite(measured)
                            count[i, j] += 1
                            count[j, i] += 1
                            if np.isnan(worst[i, j]) or measured > worst[i, j]:
                                worst[i, j] = worst[j, i] = measured
                                worst_case[i, j] = worst_case[j, i] = path.stem
            np.testing.assert_array_equal(count, count.T)
            np.testing.assert_allclose(worst, worst.T, equal_nan=True)
            g = out.create_group(scope)
            g['worst_error'] = worst
            g['shared_case_count'] = count
            g['worst_case'] = np.asarray(worst_case, dtype=h5py.string_dtype())
            g['case_names'] = np.asarray([p.stem for p in paths], dtype=h5py.string_dtype())
            print(scope, 'cases', len(paths), 'pairs', np.count_nonzero(np.triu(count, 1)))


if __name__ == '__main__':
    main()
