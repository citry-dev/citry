from citry_core import _rust

# Re-export the Rust functions as plain callables, so call sites type-check
# correctly.
mark_html = _rust.html_transform.mark_html
scan_output_html = _rust.html_transform.scan_output_html
transform_html = _rust.html_transform.transform_html
validate_html_fragment_boundary = _rust.html_transform.validate_html_fragment_boundary


__all__ = ["mark_html", "scan_output_html", "transform_html", "validate_html_fragment_boundary"]
