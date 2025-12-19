# citry_core_py

This crate serves as the bridge between the Rust implementation and the Python package [`citry_core`](../../packages/py/citry_core/).

Once built with `maturin`, other Python packages can import this package as `citry_core`:

```py
from citry_core.html_transform import transform_html

transform_html('<div>test</div>', [], [])
```

**Important - Relationship to `citry_core` Python package:**

When this Rust crate is built into Python module, it is NOT the same as the Python package at
[`packages/py/citry_core/`](../../../packages/py/citry_core/).

Instead, the `packages/py/citry_core/` Python package internally uses this Rust crate to access the Rust API.

## Building

The Python bindings are defined using [PyO3](https://pyo3.rs/), and the package is built and released with [`maturin`](https://github.com/PyO3/maturin).

```bash
# From packages/py/citry_core/
maturin develop  # Development build
maturin build    # Production build
```

Maturin automatically:

1. Compiles this Rust crate as a Python extension module
2. Links it with the Python interpreter
3. Installs it in the Python environment

## Development

### Adding new crates

Each Rust crate exposed from `citry_core_py` is namespaced under a Python module.
So the API of each crate is neatly separated:

```py
from citry_core.html_transform import transform_html
from citry_core.safe_eval import safe_eval
```

This is achieved by defining the modules on the Rust side with PyO3, and then
populating _that_ module with functions and classes:

```rs
// Define Python submodule
let html_transform_mod = PyModule::new(m.py(), "html_transform")?;
m.add_submodule(&html_transform_mod)?;

// Populate submodule with crate-specific API
html_transform_mod.add_function(wrap_pyfunction!(transform_html, &html_transform_mod)?)?;
```
