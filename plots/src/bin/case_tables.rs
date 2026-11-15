// Render each expanded comparison's numeric results from HDF5 with Rustplotlib.
use anyhow::Result;
use hdf5::{File, types::VarLenUnicode};
use rustplotlib::*;
use std::{fs, path::Path};

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    let mut paths: Vec<_> = fs::read_dir(root.join("tables/expanded"))?
        .map(|x| x.unwrap().path()).filter(|p| p.extension().is_some_and(|s| s=="h5")).collect();
    paths.sort();
    for path in paths {
        let h = File::open(&path)?;
        let stem = path.file_stem().unwrap().to_str().unwrap();
        let names: Vec<_> = h.dataset("code_names")?.read_raw::<VarLenUnicode>()?
            .into_iter().map(|s| s.as_str().to_string()).collect();
        let n = names.len();
        let height = 34. + (n as f64+1.)*7.5;
        let mut fig = Figure::new(IntendedUse::Custom { width_mm: 190., font_pt: 9. });
        fig.height_mm = height;
        let mut panel = Panel::new(Rect::new(5., 17., 180., (n as f64+1.)*7.5),
                                   Axes::new([0., 1.], [0., n as f64+1.], "", ""));
        panel.axes_visible = false;
        let xx = [0.14, 0.42, 0.63, 0.82];
        for (j, header) in ["Code", "Difference", "Refinement", "Symmetry"].iter().enumerate() {
            panel.label_at(*header, [xx[j], n as f64+0.5]);
        }
        let reference = h.dataset("Kinetic/S_total")?.read_raw::<f64>()?;
        let peak = reference.iter().copied().fold(0_f64, f64::max);
        for (i, name) in names.iter().enumerate() {
            let y = n as f64-0.5-i as f64;
            let g = h.group(name)?;
            let values = g.dataset("S_total")?.read_raw::<f64>()?;
            let other_peak = values.iter().copied().fold(0_f64, f64::max);
            let diff = values.iter().zip(&reference).map(|(a,b)|(a-b).abs())
                .fold(0_f64,f64::max)/peak.max(other_peak);
            let symmetry = values.iter().zip(values.iter().rev()).map(|(a,b)|(a-b).abs())
                .fold(0_f64,f64::max)/other_peak;
            let convergence = g.attr("convergence_error").ok()
                .and_then(|a|a.read_scalar::<f64>().ok());
            panel.label_at(name.clone(), [xx[0],y]);
            let content = if name=="Kinetic" {"reference".into()} else {format!("{diff:.2e}")};
            let label = panel.label_at(content,[xx[1],y]);
            label.color = (if diff<=1e-6 {"#176d53"} else {"#a33531"}).into();
            panel.label_at(convergence.map(|x|format!("{x:.2e}")).unwrap_or("--".into()),[xx[2],y]);
            panel.label_at(format!("{symmetry:.2e}"),[xx[3],y]);
            let mut rule=Line::new(vec![[0.01,y-0.5],[0.99,y-0.5]],"#d9dfe2");
            rule.width_pt=0.3; panel.push(Layer::Line(rule));
        }
        let mut rule=Line::new(vec![[0.01,n as f64],[0.99,n as f64]],"#526775");
        rule.width_pt=0.8; panel.push(Layer::Line(rule));
        fig.panels.push(panel);
        let out=root.join("figures");
        fig.save(out.join(format!("{stem}_table.svg")))?;
        fig.save(out.join(format!("{stem}_table.png")))?;
    }
    Ok(())
}
