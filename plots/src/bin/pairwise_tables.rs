// Rustplotlib rendering of all measured implementation pairs. Matrix values
// and shared-case counts come directly from tables/pairwise_summary.h5.
use anyhow::Result;
use hdf5::{File, types::VarLenUnicode};
use rustplotlib::*;
use std::path::Path;

fn render(root: &Path, scope: &str) -> Result<()> {
    let h = File::open(root.join("tables/pairwise_summary.h5"))?;
    let names: Vec<_> = h.dataset("code_names")?.read_raw::<VarLenUnicode>()?
        .into_iter().map(|s| s.as_str().to_string()).collect();
    let n = names.len();
    let group = h.group(scope)?;
    let error = group.dataset("worst_error")?.read_raw::<f64>()?;
    let count = group.dataset("shared_case_count")?.read_raw::<i32>()?;
    let mut fig = Figure::new(IntendedUse::Custom { width_mm: 355., font_pt: 8.5 });
    fig.height_mm = 143.;
    let title = if scope == "ionline" {
        "Pairwise spectrum agreement: six unmagnetized ion-line cases"
    } else {
        "Pairwise spectrum agreement: all thirteen cases"
    };
    fig.labels.push(Label::new(title, 177.5, 6.));
    fig.labels.push(Label::new("Each cell: worst sampled difference (shared cases)", 177.5, 14.));
    let mut panel = Panel::new(Rect::new(5., 25., 345., 100.),
                               Axes::new([0., 14.], [0., 13.], "", ""));
    panel.axes_visible = false;
    for (j, name) in names.iter().enumerate() {
        panel.label_at(name.clone(), [2.4+j as f64, 12.5]);
    }
    for (i, name) in names.iter().enumerate() {
        let y = 11.5-i as f64;
        panel.label_at(name.clone(), [0.95, y]);
        for j in 0..n {
            let index = i*n+j;
            let value = error[index];
            let cases = count[index];
            let content = if i == j { "--".into() }
                          else if cases == 0 { "n/a".into() }
                          else { format!("{value:.1e} ({cases})") };
            let label = panel.label_at(content, [2.4+j as f64, y]);
            label.color = (if i == j || cases == 0 { "#62727c" }
                          else if value <= 1e-6 { "#176d53" }
                          else { "#a33531" }).into();
        }
        let mut rule = Line::new(vec![[0.12, y-0.5], [13.75, y-0.5]], "#d9dfe2");
        rule.width_pt = 0.3;
        panel.push(Layer::Line(rule));
    }
    let mut rule = Line::new(vec![[0.12, 12.], [13.75, 12.]], "#526775");
    rule.width_pt = 0.8;
    panel.push(Layer::Line(rule));
    fig.panels.push(panel);
    fig.labels.push(Label::new("Difference = max |A-B| / larger peak; green at or below 1e-6; no fitted scaling", 177.5, 135.));
    let base = format!("pairwise_{scope}");
    fig.save(root.join("figures").join(format!("{base}.svg")))?;
    fig.save(root.join("figures").join(format!("{base}.png")))?;
    Ok(())
}

fn main() -> Result<()> {
    let root = std::env::args().nth(1).unwrap_or(".".into());
    let root = Path::new(&root);
    render(root, "ionline")?;
    render(root, "all")?;
    Ok(())
}
