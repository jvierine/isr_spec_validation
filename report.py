"""Render concise comparison reports from the measured HDF5 results."""
import h5py
from compare import ROOT,write_readme


def matrix_lines(g):
    names=g['code_names'].asstr()[:]
    m=g['pairwise_error'][:]
    lines=['| Code | '+' | '.join(names)+' |','|---|'+'---:|'*len(names)]
    for i,n in enumerate(names):
        cells=['—' if i==j else f'{"🟩" if x<=1e-6 else "🟥"} {x:.2e}' for j,x in enumerate(m[i])]
        lines.append('| '+n+' | '+' | '.join(cells)+' |')
    return lines+['']


def main():
    with h5py.File(ROOT/'tables/comparison/summary.h5') as h: write_readme(h['worst_pairwise_error'][:])
    lines=['# Additional comparisons','',
           'Same metric and 10⁻⁶ threshold as the README. Initial results are preserved; refined results change numerical resolution only.',
           'Angles are measured from B. Parameters describe validation cases, not fitted observations.','']
    for path in sorted((ROOT/'tables/extended').glob('*.h5')):
        with h5py.File(path) as h:
            lines+=['## '+path.stem,'',
                    f"ne = {h.attrs['ne_m3']:g} m⁻³; Te = {h.attrs['te_K']:g} K; Ti = {h.attrs['ti_K']:g} K; vi = {h.attrs['vi_m_s']:g} m/s; "
                    f"B = {h.attrs['B_T']*1e6:g} μT; angle(k,B) = {h.attrs['angle_k_B_deg']:g}°; f_r = {h.attrs['f_r_MHz']:g} MHz. "
                    f"νen = {h.attrs['nu_en_s_1']:g} s⁻¹; νei = {h.attrs['nu_ei_s_1']:g} s⁻¹; νin = {h.attrs['nu_in_s_1']:g} s⁻¹.",
                    '', '**Initial numerical settings**','']+matrix_lines(h)
            if 'refined' in h:
                g=h['refined']
                lines+=['**Refined numerical settings**','']+matrix_lines(g)
                lines += [f"Swoboda quadrature N = {g.attrs['swoboda_quadrature_N']}; last refinement changes the spectrum by {g.attrs['swoboda_convergence_total']:.2e} of peak.",'']
                if 'Vierinen' in g:
                    lines += [f"Vierinen: doubled time windows, 160,000 points; last point-count refinement changes the spectrum by {g.attrs['vierinen_convergence_total']:.2e} of peak.",'']
    (ROOT/'EXTENDED_RESULTS.md').write_text('\n'.join(lines))


if __name__=='__main__': main()
