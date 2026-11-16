"""Use native Rust for the active Vierinen entry; retain original archives."""
import h5py
import numpy as np

from compare import ROOT, error


def main():
    for path in sorted((ROOT/'tables/expanded').glob('*.h5')):
        source = ROOT/'tables/rust'/path.name
        with h5py.File(path,'r+') as h:
            names = list(h['code_names'].asstr()[:])
            if 'Vierinen' in h:
                del h['Vierinen']
            names = [n for n in names if n!='Vierinen']
            if 'Vierinen' in h['provenance']:
                del h['provenance/Vierinen']
            if 'Vierinen' in h['availability']:
                del h['availability/Vierinen']
            if source.exists():
                with h5py.File(source) as measured:
                    np.testing.assert_array_equal(h['frequency_hz'][:],measured['frequency_hz'][:])
                    measured.copy('Vierinen',h)
                    manifest=h['provenance'].create_group('Vierinen')
                    for key in ['git_url','git_commit','code_path','code_sha256']:
                        manifest.attrs[key]=measured['Vierinen'].attrs[key]
                    names.insert(1 if 'Analytic' in names else 0,'Vierinen')
            else:
                status=h['availability'].create_group('Vierinen')
                status.attrs['status']='unsupported'
                status.attrs['reason']='Vierinen Rust supports unmagnetized or parallel Maxwellian spectra and BGK collisions; oblique magnetic cases are not evaluated.'
            del h['code_names']
            h['code_names']=np.asarray(names,dtype=h5py.string_dtype())
            arrays=[h[n+'/S_total'][:] for n in names]
            del h['pairwise_error']
            h['pairwise_error']=np.asarray([[error(a,b) for b in arrays] for a in arrays])
            print(path.stem,'Rust computed' if source.exists() else 'Rust unsupported')


if __name__=='__main__':
    main()
