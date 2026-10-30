// Input spectra and provenance are in HDF5. This renderer uses native
// Rustplotlib defaults and the existing Vlasov project/gallery series colors.
use anyhow::Result;
use hdf5::{File, types::VarLenUnicode};
use rustplotlib::*;
use std::{fs, path::Path};

const NAMES: [&str; 11] = ["Analytic","Vierinen","Swoboda","Kinetic","Buchert","Virtanen","Martinez","Nicolls","Sandbem","Skolar","inscar"];
const COLORS: [&str; 4] = ["#245774","#8b3940","#4c7566","#ac792e"];

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    let out = root.join("figures");
    fs::create_dir_all(&out)?;
    let mut paths: Vec<_> = fs::read_dir(root.join("tables/expanded"))?.map(|p| p.unwrap().path()).filter(|p| p.extension().is_some_and(|x| x=="h5")).collect();
    paths.sort();
    for path in paths {
        let h=File::open(&path)?;
        let name=path.file_stem().unwrap().to_str().unwrap();
        let f=h.dataset("frequency_hz")?.read_raw::<f64>()?;
        let names=h.dataset("code_names")?.read_raw::<VarLenUnicode>()?;
        let reference=h.dataset("Kinetic/S_total")?.read_raw::<f64>()?;
        let peak=reference.iter().copied().fold(0_f64, f64::max);
        let plasma=name=="plasma_lines";
        let divisor=if plasma {1e6} else {1e3};
        // Ion-line view includes all samples above 0.1% of the reference peak.
        // Full frequency arrays remain in HDF5; plasma lines show both windows.
        let limit=if plasma {f.iter().copied().map(f64::abs).fold(0.,f64::max)} else {
            f.iter().zip(&reference).filter(|(_,s)| **s>peak*0.001).map(|(x,_)| x.abs()).fold(0.,f64::max)*1.15
        };
        let mut series=Vec::new();
        for n in &names {series.push((n.as_str(),h.dataset(&format!("{n}/S_total"))?.read_raw::<f64>()?));}
        let ymax=series.iter().flat_map(|(_,v)|v.iter()).copied().fold(0_f64,f64::max)*1e6*1.08;
        let mut fig=Figure::new(IntendedUse::ArticleWide);
        fig.height_mm=152.;
        let xlabel=if plasma {r"$f\;[\mathrm{MHz}]$"} else {r"$f\;[\mathrm{kHz}]$"};
        let mut top=Panel::new(Rect::new(25.,34.,145.,57.),Axes::new([-limit/divisor,limit/divisor],[0.,ymax],xlabel,r"$S(f)\;[10^{-6}\,\mathrm{Hz}^{-1}\,\mathrm{electron}^{-1}]$"));
        let maxerr=series.iter().flat_map(|(_,v)|v.iter().zip(&reference).map(|(a,b)|(a-b).abs()/peak)).fold(1e-6_f64,f64::max);
        let mut axes=Axes::new([-limit/divisor,limit/divisor],[1e-16,10_f64.powf(maxerr.log10().ceil())],xlabel,r"$|S-S_{\rm Kinetic}|/\max S_{\rm Kinetic}$");
        axes.set_yscale(AxisScale::Log10)?;
        let mut bottom=Panel::new(Rect::new(25.,112.,145.,28.),axes);
        let mut entries=Vec::new();
        let step=f.windows(2).map(|p|p[1]-p[0]).fold(f64::INFINITY,f64::min);
        for (name,values) in series {
            let index=NAMES.iter().position(|n| *n==name).unwrap();
            let color=COLORS[index%4];
            let dash=match index/4 {0=>None,1=>Some("2 1".into()),_=>Some("0.5 1".into())};
            let mut points=Vec::new();let mut residual=Vec::new();
            for i in 0..f.len() {
                if i>0 && f[i]-f[i-1]>step*1.5 {points.push([f64::NAN,f64::NAN]);residual.push([f64::NAN,f64::NAN]);}
                points.push([f[i]/divisor,values[i]*1e6]);
                residual.push([f[i]/divisor,((values[i]-reference[i]).abs()/peak).max(1e-16)]);
            }
            let mut line=Line::new(points,color);line.dash=dash.clone();top.push(Layer::Line(line));
            if name!="Kinetic" {let mut line=Line::new(residual,color);line.dash=dash.clone();bottom.push(Layer::Line(line));}
            let mut key=LegendEntry::line(name,color);
            if let LegendSymbol::Line{dash:d,..}=&mut key.symbol {*d=dash;}
            entries.push(key);
        }
        let mut legend=Legend::new(entries);legend.columns=3;legend.position=LegendPosition::AboveCenter;
        top.legend=Some(legend);
        fig.panels.push(top);fig.panels.push(bottom);
        fig.save(out.join(format!("{name}.png")))?;
        fig.save(out.join(format!("{name}.svg")))?;
        println!("Rendered {name}");
    }
    Ok(())
}
