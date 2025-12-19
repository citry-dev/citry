pub mod html_transform;
pub mod safe_eval;
pub mod template_parser;

use pyo3::prelude::*;

use crate::html_transform::transform_html;

/// Singular Python API that brings togther all the other Rust crates.
/// Each crate is exposed as a submodule.
#[pymodule]
fn citry_core_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // HTML transformer
    let html_transform_mod = PyModule::new(m.py(), "html_transform")?;
    m.add_submodule(&html_transform_mod)?;
    html_transform_mod.add_function(wrap_pyfunction!(transform_html, &html_transform_mod)?)?;

    // Safe eval
    let safe_eval_mod = PyModule::new(m.py(), "safe_eval")?;
    m.add_submodule(&safe_eval_mod)?;
    safe_eval_mod.add_function(wrap_pyfunction!(
        crate::safe_eval::safe_eval,
        &safe_eval_mod
    )?)?;

    Ok(())
}
