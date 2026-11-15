"""Add measured Octave spectra to the existing expanded HDF5 comparisons."""
from pathlib import Path

import h5py
import numpy as np

from compare import ROOT, error


def main():
    source_dir = ROOT / 'tables' / 'octave'
    for source in sorted(source_dir.glob('*.h5')):
        target = ROOT / 'tables' / 'expanded' / source.name
        if not target.exists():
            continue  # new edge cases stay in their own HDF5 products
        with h5py.File(source) as fresh, h5py.File(target, 'r+') as h:
            assert np.array_equal(fresh['frequency_hz'][:], h['frequency_hz'][:])
            names = list(h['code_names'].asstr()[:])
            for code in ['Martinez', 'Sandbem']:
                if code not in fresh or fresh[code].attrs['status'] != 'computed':
                    if code in h['availability']:
                        g=h['availability'][code]
                        g.attrs['status']='unsupported'
                        g.attrs['reason']='The Octave adapter does not support this case physics.'
                    continue
                if code in h:
                    del h[code]
                g = h.create_group(code)
                fresh.copy(code + '/S_total', g, name='S_total')
                fresh.copy(code + '/elapsed_s', g, name='elapsed_s')
                for key, value in fresh[code].attrs.items():
                    g.attrs[key] = value
                g.attrs['convergence_status'] = 'not_assessed'
                if code not in names:
                    names.append(code)
                if code in h['availability']:
                    del h['availability'][code]
                manifest = h.require_group('provenance').require_group(code)
                for key in ['git_url', 'git_commit', 'code_path', 'code_sha256']:
                    manifest.attrs[key] = g.attrs[key]
            del h['code_names']
            h['code_names'] = np.asarray(names, dtype=h5py.string_dtype())
            arrays = [h[name + '/S_total'][:] for name in names]
            if 'pairwise_error' in h:
                del h['pairwise_error']
            h['pairwise_error'] = np.asarray([[error(a, b) for b in arrays] for a in arrays])
            assert all(np.isfinite(a).all() for a in arrays)
            print(source.stem, names)


if __name__ == '__main__':
    main()
