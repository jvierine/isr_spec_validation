"""Add measured EISCAT GUISDAP spectra to expanded HDF5 products."""
import h5py
import numpy as np

from compare import ROOT, error


def main():
    source_dir = ROOT / 'tables/eiscat'
    for target in sorted((ROOT / 'tables/expanded').glob('*.h5')):
        source = source_dir / target.name
        with h5py.File(target, 'r+') as h:
            if not source.exists():
                state = h['availability'].require_group('EISCAT')
                state.attrs['status'] = 'unsupported'
                state.attrs['reason'] = 'EISCAT adapter evaluated collisionless unmagnetized cases only.'
                continue
            with h5py.File(source) as fresh:
                np.testing.assert_array_equal(fresh['frequency_hz'][:], h['frequency_hz'][:])
                if 'EISCAT' in h:
                    del h['EISCAT']
                fresh.copy('EISCAT', h)
                if 'EISCAT' in h['availability']:
                    del h['availability/EISCAT']
                manifest = h['provenance'].require_group('EISCAT')
                for key in ['git_url', 'git_commit', 'code_path', 'code_sha256',
                            'spec_sha256', 'pldfv_sha256', 'pldfvv_sha256']:
                    manifest.attrs[key] = fresh['EISCAT'].attrs[key]
                names = list(h['code_names'].asstr()[:])
                if 'EISCAT' not in names:
                    names.append('EISCAT')
                del h['code_names']
                h['code_names'] = np.asarray(names,dtype=h5py.string_dtype())
                arrays = [h[name + '/S_total'][:] for name in names]
                del h['pairwise_error']
                h['pairwise_error'] = np.asarray([[error(a,b) for b in arrays] for a in arrays])
                print(target.stem, 'EISCAT', fresh['EISCAT'].attrs['error_vs_kinetic'])


if __name__ == '__main__':
    main()
