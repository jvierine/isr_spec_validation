// Render measured speed results from HDF5; source provenance stays in data.
use anyhow::Result;
use hdf5::{types::VarLenUnicode, File};
use rustplotlib::*;
use std::path::Path;

fn elapsed(x: f64) -> String {
    if x >= 1. { format!("{x:.2} s") }
    else if x >= 0.01 { format!("{:.2} ms", x * 1e3) }
    else { format!("{:.3} ms", x * 1e3) }
}

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    let h = File::open(root.join("tables/speed_standard_f_region.h5"))?;
    let names: Vec<String> = h.dataset("code_names")?.read_raw::<VarLenUnicode>()?
        .into_iter().map(|s| s.as_str().to_string()).collect();
    let mut rows: Vec<_> = names.iter().map(|n| {
        let g = h.group(n).unwrap();
        (n.clone(), g.attr("median_elapsed_s").unwrap().read_scalar::<f64>().unwrap(),
         g.attr("min_elapsed_s").unwrap().read_scalar::<f64>().unwrap(),
         g.attr("max_elapsed_s").unwrap().read_scalar::<f64>().unwrap(),
         g.attr("runtime").unwrap().read_scalar::<VarLenUnicode>().unwrap().as_str().to_string())
    }).collect();
    rows.sort_by(|a,b| a.1.total_cmp(&b.1));
    let reference = h.group("Vierinen")?.attr("median_elapsed_s")?.read_scalar::<f64>()?;
    let mut fig = Figure::new(IntendedUse::Custom { width_mm: 195., font_pt: 9. });
    fig.height_mm = 145.;
    fig.labels.push(Label::new("Standard F-region O+ spectrum: execution time", 97.5, 6.));
    fig.labels.push(Label::new("440.2 MHz; 801 frequencies; single-thread avaruus, AMD EPYC 9754", 97.5, 14.));
    fig.labels.push(Label::new("Electron density 1e11 per cubic metre; Te 2000 K; Ti 1000 K; B=0", 97.5, 20.));
    let mut p = Panel::new(Rect::new(7., 26., 181., 101.), Axes::new([0.,1.],[0.,13.],"",""));
    p.axes_visible = false;
    let xx = [0.15,0.38,0.60,0.82];
    for (j,head) in ["Implementation","Runtime","Median per spectrum","Time / Vierinen"].iter().enumerate() {
        p.label_at(*head,[xx[j],12.5]);
    }
    for (i,(name,median,min,max,runtime)) in rows.iter().enumerate() {
        let y = 11.5-i as f64;
        p.label_at(name.clone(),[xx[0],y]);
        let label = match runtime.as_str() { "rust"=>"Rust (AVX2)", "python"=>"Python", "r"=>"R/C", "julia"=>"Julia", "octave"=>"Octave", _=>runtime };
        p.label_at(label,[xx[1],y]);
        p.label_at(elapsed(*median),[xx[2],y]);
        let ratio=median/reference;
        p.label_at(if ratio<100. {format!("{ratio:.2}x")} else {format!("{ratio:.2e}x")},[xx[3],y]);
        let _ = (min,max); // full spread retained in the HDF5 product
        let mut line=Line::new(vec![[0.01,y-0.5],[0.99,y-0.5]],"#d9dfe2");
        line.width_pt=0.3; p.push(Layer::Line(line));
    }
    let mut rule=Line::new(vec![[0.01,12.],[0.99,12.]],"#526775");
    rule.width_pt=0.8; p.push(Layer::Line(rule));
    fig.panels.push(p);
    fig.labels.push(Label::new("Median of warmed calls on CPU 0; startup and HDF5 I/O excluded",97.5,133.));
    fig.labels.push(Label::new("Outputs checked against saved spectra; documented numerical settings",97.5,140.));
    fig.save(root.join("figures/f_region_speed.svg"))?;
    fig.save(root.join("figures/f_region_speed.png"))?;
    Ok(())
}
