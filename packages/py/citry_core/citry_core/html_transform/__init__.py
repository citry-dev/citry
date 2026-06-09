from citry_core import _rust

# Re-export the Rust `transform_html` function as a plain callable, so call
# sites type-check correctly.
transform_html = _rust.html_transform.transform_html


__all__ = ["transform_html"]
