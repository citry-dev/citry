from citry_core import _rust

# Re-export the Rust functions as plain callables, so call sites type-check
# correctly.
mark_html = _rust.html_transform.mark_html
transform_html = _rust.html_transform.transform_html


__all__ = ["mark_html", "transform_html"]
