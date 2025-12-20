# NOTE:
# By default, maturin auto-generates this file.
#
# However, due to the complexity of the project:
# - having multiple crates
# - Python-side code for some crates (like template parser or safe eval)
# - And splitting the Python API into submodules (html_transform, template_parser, safe_eval)
#
# Instead, we manually manage the Python-side API for each crate.
#
# This file is empty by design, because we namespace each Rust crate under its own Python module.
#
# Instead, the API for each crate is defined in a separate directory with `__init__.py` file,
# e.g. `citry_core/html_transform/__init__.py`.
#
# That way, the API for each crate is neatly separated:
# ```python
# from citry_core.html_transform import transform_html
# from citry_core.safe_eval import safe_eval
# from citry_core.template_parser import parse_tag
# ```
#
# ---
#
# The compiled Rust code is accessible as Python module `citry_core._rust`.
#
# But for the Python-side public API, each crate has its own directory with `__init__.py` file.
#
# Thus, to import from any crate, you do e.g.
# ```python
# from citry_core.html_transform import transform_html
# ```
#
