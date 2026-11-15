// Near-perpendicular magnetic edge case against its unmagnetized control.
use anyhow::Result;
use hdf5::File;
use rustplotlib::*;
use std::path::Path;

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    let magnetic = File::open(root.join("tables/octave/near_perp_1deg_lower_hybrid.h5"))?;
    let control = File::open(root.join("tables/octave/near_perp_unmagnetized_control.h5"))?;
    let f = magnetic.dataset("frequency_hz")?.read_raw::<f64>()?;
    let kinetic = magnetic.dataset("Kinetic/S_total")?.read_raw::<f64>()?;
    let sandbem = magnetic.dataset("Sandbem/S_total")?.read_raw::<f64>()?;
    let unmag = control.dataset("Kinetic/S_total")?.read_raw::<f64>()?;
    let ymax = kinetic.iter().chain(&unmag).copied().fold(0_f64, f64::max)*1e6*1.12;
    let mut figure = Figure::new(IntendedUse::ArticleWide);
    figure.height_mm = 115.;
    let mut top = Panel::new(Rect::new(25., 15., 145., 75.),
        Axes::new([-20., 20.], [0., ymax], r"$f\;[\mathrm{kHz}]$",
            r"$S(f)\;[10^{-6}\,\mathrm{Hz}^{-1}\,\mathrm{electron}^{-1}]$"));
    let mut entries = Vec::new();
    for (name, values, color, dash) in [
        ("Kinetic, B=50 uT", &kinetic, "#245774", None),
        ("Sandbem, B=50 uT", &sandbem, "#a33531", Some("2 1".to_string())),
        ("Kinetic, B=0", &unmag, "#4c7566", Some("0.5 1".to_string())),
    ] {
        let points = f.iter().zip(values).map(|(x,y)| [x/1000., y*1e6]).collect();
        let mut line = Line::new(points, color);
        line.dash = dash.clone();
        top.push(Layer::Line(line));
        let mut key = LegendEntry::line(name, color);
        if let LegendSymbol::Line { dash: d, .. } = &mut key.symbol { *d = dash; }
        entries.push(key);
    }
    let mut legend = Legend::new(entries);
    legend.columns = 2;
    legend.position = LegendPosition::AboveCenter;
    top.legend = Some(legend);
    figure.panels.push(top);
    let out = root.join("figures");
    figure.save(out.join("near_perp_1deg.svg"))?;
    figure.save(out.join("near_perp_1deg.png"))?;
    Ok(())
}
