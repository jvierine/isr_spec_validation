"""Combine measured avaruus kernel timings into one HDF5 speed table."""
from datetime import datetime, timezone
import hashlib

import h5py
import numpy as np

from compare import ROOT, error

ORDER = ['Analytic', 'Vierinen', 'Swoboda', 'Kinetic', 'Buchert',
         'Virtanen', 'Martinez', 'Nicolls', 'Sandbem', 'Skolar', 'inscar', 'EISCAT']
INPUTS = {
    'python': ROOT / 'tables/speed_f_region_440.2MHz.h5',
    'r': ROOT / 'tables/speed_virtanen.h5',
    'julia': ROOT / 'tables/speed_buchert.h5',
    'octave': ROOT / 'tables/octave/f_region_440.2MHz.h5',
    'eiscat': ROOT / 'tables/eiscat/f_region_440.2MHz.h5',
    'rust': ROOT / 'tables/rust/f_region_440.2MHz.h5',
}
SOURCE = {name: lang for lang, names in {
    'python': ['Analytic', 'Swoboda', 'Kinetic', 'Nicolls', 'Skolar', 'inscar'],
    'r': ['Virtanen'], 'julia': ['Buchert'],
    'octave': ['Martinez', 'Sandbem'],
    'eiscat': ['EISCAT'],
    'rust': ['Vierinen'],
}.items() for name in names}


def main():
    target = ROOT / 'tables/speed_standard_f_region.h5'
    with h5py.File(INPUTS['python']) as py, h5py.File(INPUTS['r']) as rr, \
         h5py.File(INPUTS['julia']) as jj, h5py.File(INPUTS['octave']) as oo, \
         h5py.File(INPUTS['eiscat']) as ee, \
         h5py.File(INPUTS['rust']) as rust, \
         h5py.File(ROOT / 'tables/expanded/f_region_440.2MHz.h5') as expanded, \
         h5py.File(target, 'w') as out:
        sources = {'python': py, 'r': rr, 'julia': jj, 'octave': oo, 'eiscat': ee, 'rust': rust}
        model = py.attrs['cpu_model']
        assert model == oo.attrs['cpu_model']
        out.attrs['host'] = 'avaruus'
        out.attrs['cpu_model'] = model
        out.attrs['cpu_affinity'] = '0'
        out.attrs['threads_per_call'] = 1
        out.attrs['case_name'] = 'f_region_440.2MHz'
        out.attrs['spectrum_units'] = 'Hz^-1 per electron'
        out.attrs['utc_created'] = datetime.now(timezone.utc).isoformat()
        out.attrs['benchmark_protocol'] = ('warmed kernels, in-process calls, CPU 0, '
            'single-thread numerical libraries; no startup, compilation, or HDF5 I/O; '
            'R uses seven batches of 100 calls; Rust uses 31 alternating batches of 100 calls '
            'with thread CPU and wall clocks; other runtimes use seven calls')
        out['code_names'] = np.asarray(ORDER, dtype=h5py.string_dtype())
        out['frequency_hz'] = expanded['frequency_hz'][:]
        out.attrs['ne_m3'] = 1e11
        out.attrs['te_K'] = 2000.
        out.attrs['ti_K'] = 1000.
        out.attrs['ion'] = 'O+, 16 u, fraction 1'
        out.attrs['radar_hz'] = 440.2e6
        out.attrs['magnetic_field_T'] = 0.
        out.attrs['source_product'] = 'tables/expanded/f_region_440.2MHz.h5'
        for name in ORDER:
            kind = SOURCE[name]
            src = sources[kind][name]
            if kind in ('octave','eiscat'):
                assert src.attrs['status'] == 'computed'
            vals = src['elapsed_s'][:]
            assert np.isfinite(vals).all() and (vals > 0).all()
            median = float(np.median(vals))
            np.testing.assert_allclose(median, src.attrs['median_elapsed_s'], rtol=1e-9)
            g = out.create_group(name)
            g['elapsed_s'] = vals
            for extra in ['cpu_elapsed_s','baseline_elapsed_s','baseline_cpu_elapsed_s',
                          'float32_trial_elapsed_s']:
                if extra in src:
                    src.copy(extra,g)
            g.attrs['median_elapsed_s'] = median
            g.attrs['min_elapsed_s'] = float(vals.min())
            g.attrs['max_elapsed_s'] = float(vals.max())
            g.attrs['runtime'] = 'octave' if kind=='eiscat' else kind
            for extra in ['arithmetic','simd_backend','compiler','compiler_flags','batch_size',
                          'trial_count','baseline_median_s','optimization_speedup','max_relative_change',
                          'float32_trial_error','float32_trial_median_s','median_cpu_s',
                          'p10_elapsed_s','p90_elapsed_s','binary_sha256']:
                if extra in src.attrs:
                    g.attrs[extra]=src.attrs[extra]
            g.attrs['measurement_method'] = src.attrs.get('timing_scope',
                sources[kind].attrs.get('timing_scope',
                sources[kind].attrs.get('benchmark_mode', 'seven warmed in-process calls')))
            measured_error = (error(src['S_total'][:], expanded[name]['S_total'][:])
                              if kind in ('octave','eiscat','rust') else float(np.asarray(src.attrs['error_vs_saved']).item()))
            g.attrs['error_vs_saved'] = measured_error
            assert g.attrs['error_vs_saved'] <= 1e-6
            if name in expanded['provenance']:
                for key in ['git_url', 'git_commit', 'code_path', 'code_sha256']:
                    if key in expanded['provenance'][name].attrs:
                        g.attrs[key] = expanded['provenance'][name].attrs[key]
            if 'source_sha256' in src.attrs:
                g.attrs['benchmark_source_sha256'] = src.attrs['source_sha256']
            if kind in ('r', 'julia'):
                script = ROOT / ('benchmark_f_region.R' if kind == 'r' else 'benchmark_f_region.jl')
                g.attrs['benchmark_script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        reference = out['Kinetic'].attrs['median_elapsed_s']
        for name in ORDER:
            out[name].attrs['speed_relative_to_kinetic'] = reference / out[name].attrs['median_elapsed_s']
            out[name].attrs['time_relative_to_vierinen'] = out[name].attrs['median_elapsed_s']/out['Vierinen'].attrs['median_elapsed_s']
            print(name, out[name].attrs['median_elapsed_s'] * 1e3)


if __name__ == '__main__':
    main()
