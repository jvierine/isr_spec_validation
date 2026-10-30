"""Render reports from measured spectra; Rustplotlib produces the figures separately."""
import json
import h5py
import numpy as np
from compare import ROOT, error
from additional_sources import SOURCES

NAMES=['Analytic','Vierinen','Swoboda','Kinetic','Buchert','Virtanen','Nicolls','Skolar','inscar']
TITLES={'f_region':'F region','molecular':'Molecular ions','topside':'Topside',
        'magnetic_42deg':'Magnetic field, 42° from B','magnetic_85deg':'Magnetic field, 85° from B',
        'neutral_bgk_42deg':'Neutral BGK collisions, 42° from B',
        'neutral_bgk_parallel':'Neutral BGK collisions, parallel to B',
        'plasma_lines':'Electron plasma lines'}


def title(name):
    for key,label in TITLES.items():
        if name==key: return label
        if name.startswith(key+'_'): return label+', '+name[len(key)+1:].replace('MHz',' MHz')
    return name


def value(x):
    return ('🟩' if x<=1e-6 else '🟥')+f' {x:.2e}'


def parameters(h):
    c=json.loads(h.attrs['parameters_json'])
    ions=', '.join(f'{n}: {fraction:g} ({mass:g} u)' for n,mass,fraction in c['ions'])
    return (f"ne = {c['ne']:g} m⁻³; Te = {c['te']:g} K; Ti = {c['ti']:g} K; "
            f"radar = {c['radar_hz']/1e6:g} MHz; B = {c['B']*1e6:g} μT; "
            f"angle(k,B) = {c['theta']:g}°; νen = {c.get('nu_e',0):g} s⁻¹; "
            f"νin = {c.get('nu_i',0):g} s⁻¹. Ions: {ions}. All species have zero drift.")


def case_lines(path):
    with h5py.File(path) as h:
        lines=[f'## {title(path.stem)}','',parameters(h),'',
               f'![{title(path.stem)}: spectrum and residuals](figures/{path.stem}.png)','',
               'Upper panel: absolute spectrum per electron. Lower panel: absolute difference from Kinetic, divided by its peak. '
               'Ion-line views focus on the spectral feature; full grids are retained in HDF5. '
               'The plasma-line view leaves the unsampled central interval blank. Residuals below 10⁻¹⁶ are clipped to that plotting floor.','',
               '| Code | Difference from Kinetic | Refinement change |','|---|---:|---:|']
        reference=h['Kinetic/S_total'][:]
        for name in NAMES:
            if name not in h: continue
            g=h[name]; diff=error(g['S_total'][:],reference)
            conv=g.attrs.get('convergence_error')
            refine=f'{conv:.2e}' if conv is not None else '—'
            if conv is not None and conv>1e-6: refine+=' (unresolved)'
            lines.append(f'| {name} | {"reference" if name=="Kinetic" else value(diff)} | {refine} |')
        lines+=['','A dash means no new refinement measurement in this run; it does not establish numerical convergence. '
                'A red result is a sampled-spectrum discrepancy, not a diagnosis of its cause. '
                'The refinement column compares the two recorded numerical settings.','',
                f'[Spectrum arrays and full pairwise matrix](tables/expanded/{path.name}) · [Vector figure](figures/{path.stem}.svg)','',
                '| Unavailable code | Status | Reason |','|---|---|---|']
        for name,g in h['availability'].items():
            if g.attrs['status']!='computed':
                lines.append(f"| {name} | {g.attrs['status']} | {g.attrs['reason']} |")
        lines+=['']
        return lines


def main():
    paths=sorted((ROOT/'tables/expanded').glob('*.h5'))
    assert len(paths)==11, 'Collect all eleven cases before rendering reports'
    baseline=[]; extended=[]; results={n:[] for n in NAMES}
    for p in paths:
        with h5py.File(p) as h:
            (baseline if h.attrs['category']=='comparison' else extended).append(p)
            for name in NAMES:
                if name in h: results[name].append((p.stem,error(h[name+'/S_total'][:],h['Kinetic/S_total'][:])))
    for filename,title_,items in [('COMPARISON_RESULTS.md','Unmagnetized ion-line comparisons',baseline),
                                  ('EXTENDED_RESULTS.md','Magnetic, collision and plasma-line comparisons',extended)]:
        lines=['# '+title_,'','🟩 sampled agreement ≤ 10⁻⁶; 🟥 discrepancy > 10⁻⁶. '
               'The table metric divides the maximum absolute difference by the larger spectrum peak. '
               'No fitted scaling or frequency shifts. See [adapter definitions and limitations](NEW_CODES.md).','']
        for p in items: lines+=case_lines(p)
        (ROOT/filename).write_text('\n'.join(lines))
    lines=['# ISR spectrum validation','','Nine implementations evaluated across eleven prescribed Maxwellian tests. '
           'Each test has a spectrum overlay and a residual panel. Martinez and Sandbem are listed but were not run after MATLAB license failures; Virtanen uses the working R/C implementation.','',
           '[Six ion-line tests and plots](COMPARISON_RESULTS.md) · [Five magnetic, collision and plasma-line tests and plots](EXTENDED_RESULTS.md)','',
           '## Coverage and measured agreement','','The threshold is 10⁻⁶. Errors use `max(abs(A-B))/max(max(abs(A)),max(abs(B)))`, '
           'with fixed physical unit conversions and no fitted scaling. Kinetic is the plotting reference, not an assertion of ground truth. '
           'Results apply only to the cases and frequency samples evaluated.','',
           '| Code | Cases evaluated | Worst difference from Kinetic | Worst case |','|---|---:|---:|---|']
    for name in NAMES:
        case,worst=max(results[name],key=lambda x:x[1])
        lines.append(f'| {name} | {len(results[name])}/11 | {"reference" if name=="Kinetic" else value(worst)} | {title(case)} |')
    lines+=['| Martinez | 0/11 | not run | MATLAB execution cancelled |',
            '| Sandbem (ISRTS) | 0/11 | not run | MATLAB execution cancelled |','',
            '**Convergence limitation:** inscar’s plasma-line spectrum changes by more than 10⁻⁶ between its recorded settings. '
            'Its plotted discrepancy is provisional. Native constants, approximations and floating-point precision differ among codes; '
            'these were retained rather than tuned to obtain agreement.','',
            '## Baseline pairwise agreement','','Worst error over the six unmagnetized ion-line tests. Each cell includes the number of shared cases; '
            'Skolar and inscar support the two single-ion cases in this adapter.','',
            '| Code | '+' | '.join(NAMES)+' |','|---|'+'---:|'*len(NAMES)]
    for a in NAMES:
        row=[]
        for b in NAMES:
            if a==b: row.append('—'); continue
            errs=[]
            for p in baseline:
                with h5py.File(p) as h:
                    if a in h and b in h: errs.append(error(h[a+'/S_total'][:],h[b+'/S_total'][:]))
            row.append(value(max(errs))+f' ({len(errs)})' if errs else 'N/A')
        lines.append('| '+a+' | '+' | '.join(row)+' |')
    lines+=['','[HDF5 arrays and pairwise matrices](tables/expanded/) retain the original grids and plasma parameters. '
            'The [original four-code data](tables/comparison/) and [original extended data](tables/extended/) remain available, including their earlier refinement checks.','',
            '[Reproduce the expanded runs and figures](NEW_CODES.md) · [Original methods](METHODS.md) · '
            '[Original four-code adapters](DETAILS.md) · [Catalog and archives](OTHER_CODES.md)','']
    (ROOT/'README.md').write_text('\n'.join(lines))


if __name__=='__main__': main()
