// Measured HDF5 spectra and timings rendered as vector/scalable tables.
// Code and checkout provenance stay in HDF5, not in the visible figures.
use anyhow::Result;
use hdf5::File;
use rustplotlib::*;
use std::path::Path;

const CASES: [(&str, &str); 13] = [
    ("f_region_440.2MHz", "F region, 440 MHz"),
    ("f_region_930MHz", "F region, 930 MHz"),
    ("molecular_440.2MHz", "Molecular, 440 MHz"),
    ("molecular_930MHz", "Molecular, 930 MHz"),
    ("topside_440.2MHz", "Topside, 440 MHz"),
    ("topside_930MHz", "Topside, 930 MHz"),
    ("magnetic_42deg", "Magnetic, 42 deg"),
    ("magnetic_85deg", "Magnetic, 85 deg"),
    ("neutral_bgk_42deg", "BGK, 42 deg"),
    ("neutral_bgk_parallel", "BGK, parallel"),
    ("plasma_lines", "Electron plasma lines"),
    ("near_perp_unmagnetized_control", "Near perp control, B=0"),
    ("near_perp_1deg_lower_hybrid", "1 deg from perp, B=50 uT"),
];
const CODES: [&str; 4] = ["Analytic", "Kinetic", "Martinez", "Sandbem"];

fn add_cell(panel: &mut Panel, content: String, x: f64, y: f64, color: &str) {
    panel.label_at(content, [x, y]).color = color.into();
}

fn table(root: &Path, timing: bool) -> Result<()> {
    let mut figure = Figure::new(IntendedUse::Custom { width_mm: 195., font_pt: 9. });
    figure.height_mm = 160.;
    let title = if timing { "Single-thread execution time" } else { "Spectrum difference from Kinetic" };
    figure.labels.push(Label::new(title, 97.5, 6.));
    figure.labels.push(Label::new("avaruus; AMD EPYC 9754; one pinned logical CPU per call", 97.5, 14.));
    let mut panel = Panel::new(Rect::new(5., 26., 185., 112.), Axes::new([0., 1.], [0., 14.], "", ""));
    panel.axes_visible = false;
    let x = [0.175, 0.46, 0.62, 0.77, 0.91];
    add_cell(&mut panel, "Case".into(), x[0], 13.5, "#203342");
    for (j, code) in CODES.iter().enumerate() {
        add_cell(&mut panel, (*code).into(), x[j+1], 13.5, "#203342");
    }
    for (i, (stem, label)) in CASES.iter().enumerate() {
        let y = 12.5 - i as f64;
        add_cell(&mut panel, (*label).into(), x[0], y, "#203342");
        let h = File::open(root.join("tables/octave").join(format!("{stem}.h5")))?;
        for (j, code) in CODES.iter().enumerate() {
            let content = if let Ok(g) = h.group(code) {
                if timing {
                    format!("{:.3}", g.attr("median_elapsed_s")?.read_scalar::<f64>()?*1e3)
                } else if *code == "Kinetic" {
                    "reference".into()
                } else {
                    format!("{:.2e}", g.attr("error_vs_kinetic")?.read_scalar::<f64>()?)
                }
            } else { "--".into() };
            let color = if !timing && content != "--" && content != "reference" {
                let e: f64 = content.parse().unwrap_or(f64::INFINITY);
                if e <= 1e-6 { "#176d53" } else { "#a33531" }
            } else { "#203342" };
            add_cell(&mut panel, content, x[j+1], y, color);
        }
        let mut line = Line::new(vec![[0.015, y-0.5], [0.985, y-0.5]], "#d9dfe2");
        line.width_pt = 0.35;
        panel.push(Layer::Line(line));
    }
    let mut line = Line::new(vec![[0.015, 13.], [0.985, 13.]], "#526775");
    line.width_pt = 0.8;
    panel.push(Layer::Line(line));
    figure.panels.push(panel);
    let foot = if timing {
        "Milliseconds; median of 7 warmed calls; interpreter startup and HDF5 I/O excluded"
    } else {
        "Maximum absolute difference / larger spectrum peak; green at or below 1e-6"
    };
    figure.labels.push(Label::new(foot, 97.5, 148.));
    let base = if timing { "octave_timing" } else { "octave_agreement" };
    let out = root.join("figures");
    figure.save(out.join(format!("{base}.svg")))?;
    figure.save(out.join(format!("{base}.png")))?;
    Ok(())
}

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    table(root, false)?;
    table(root, true)?;
    Ok(())
}
