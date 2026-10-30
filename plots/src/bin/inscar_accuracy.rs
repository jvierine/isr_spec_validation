// Render the controlled inscar accuracy experiment from its HDF5 data product.
use anyhow::Result;
use hdf5::File;
use rustplotlib::*;
use std::path::Path;

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    let h = File::open(root.join("diagnostics/inscar_accuracy.h5"))?;
    let g = h.group("cases/plasma_lines")?;
    let f = g.dataset("frequency_hz")?.read_raw::<f64>()?;
    let reference = g.dataset("reference")?.read_raw::<f64>()?;
    let peak_index = (0..f.len()).filter(|&i| f[i]>0.).max_by(|&i,&j| reference[i].total_cmp(&reference[j])).unwrap();
    let center = f[peak_index];
    let mut fig = Figure::new(IntendedUse::ArticleWide);
    fig.height_mm=156.;
    let mut top = Panel::new(Rect::new(25.,25.,145.,57.), Axes::new(
        [(center-30000.)/1e6,(center+30000.)/1e6], [0.,reference[peak_index]*1.2e6],
        r"$f\;[\mathrm{MHz}]$", r"$S(f)\;[10^{-6}\,\mathrm{Hz}^{-1}\,\mathrm{electron}^{-1}]$"));
    let mut entries=Vec::new();
    for (name,path,color,dash) in [
        ("Original inscar","upstream_saved","#245774",None),
        ("Kinetic","reference","#ac792e",None),
        ("Patched inscar","simpson_128001_15/corrected","#4c7566",Some("2 1".into()))] {
        let v=g.dataset(path)?.read_raw::<f64>()?;
        let mut line=Line::new(f.iter().zip(v).filter(|(x,_)| **x>0.).map(|(x,y)|[*x/1e6,y*1e6]).collect(),color);
        line.dash=dash.clone(); top.push(Layer::Line(line));
        let mut e=LegendEntry::line(name,color);
        if let LegendSymbol::Line{dash:d,..}=&mut e.symbol {*d=dash;}
        entries.push(e);
    }
    let mut legend=Legend::new(entries);legend.columns=3;legend.position=LegendPosition::AboveCenter;top.legend=Some(legend);
    let mut axes=Axes::new([30000.,1100000.],[1e-9,1.],r"Gordeyev samples per species",r"Peak-normalized error");
    axes.set_xscale(AxisScale::Log10)?;axes.set_yscale(AxisScale::Log10)?;
    axes.xticks=vec![32001.,64001.,128001.,256001.,512001.,1024001.];
    axes.xticklabels=Some(["32k","64k","128k","256k","512k","1024k"].iter().map(|s|s.to_string()).collect());
    axes.yticks=vec![1e-9,1e-6,1e-3,1.];
    axes.yticklabels=Some(axes.yticks.iter().map(|y|format!("$10^{{{:.0}}}$",y.log10())).collect());
    let mut bottom=Panel::new(Rect::new(25.,116.,145.,28.),axes);
    let mut entries=Vec::new();
    for (name,method,attr,color) in [
        (r"Original $\epsilon_0$, trapezoid","trapezoid","error_original_constant","#245774"),
        (r"SI $\epsilon_0$, trapezoid","trapezoid","error_corrected","#8b3940"),
        (r"SI $\epsilon_0$, Simpson","simpson","error_corrected","#4c7566")] {
        let mut values=Vec::new();
        for n in [32001,64001,128001,256001,512001,1024001] {
            let path=format!("{method}_{n}_15");
            if g.link_exists(&path) {values.push([n as f64,g.group(&path)?.attr(attr)?.read_scalar::<f64>()?]);}
        }
        bottom.push(Layer::Line(Line::new(values,color)));
        entries.push(LegendEntry::line(name,color));
    }
    let mut legend=Legend::new(entries);legend.columns=2;legend.position=LegendPosition::AboveCenter;bottom.legend=Some(legend);
    fig.panels.push(top);fig.panels.push(bottom);
    fig.save(root.join("figures/inscar_accuracy.png"))?;
    fig.save(root.join("figures/inscar_accuracy.svg"))?;
    Ok(())
}
