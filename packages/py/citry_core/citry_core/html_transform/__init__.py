from citry_core import _rust

# Re-export the Rust functions as plain callables, so call sites type-check
# correctly.
mark_html = _rust.html_transform.mark_html
browser_fragment_matches_elements = _rust.html_transform.browser_fragment_matches_elements
browser_fragment_matches_nodes = _rust.html_transform.browser_fragment_matches_nodes
scan_output_html = _rust.html_transform.scan_output_html
static_html_node_count = _rust.html_transform.static_html_node_count
transform_html = _rust.html_transform.transform_html
validate_html_fragment_boundary = _rust.html_transform.validate_html_fragment_boundary


__all__ = [
    "browser_fragment_matches_elements",
    "browser_fragment_matches_nodes",
    "mark_html",
    "scan_output_html",
    "static_html_node_count",
    "transform_html",
    "validate_html_fragment_boundary",
]
