/// Python interface for the citry_html_transform crate.
use std::collections::HashSet;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PyString, PyTuple};

use crate::panics::catch_panic;

use citry_html_transform::{
    ExpectedElementEvent, ExpectedNodeEvent, HtmlTransformerConfig,
    browser_fragment_matches_elements as browser_fragment_matches_elements_rust,
    browser_fragment_matches_nodes as browser_fragment_matches_nodes_rust,
    mark_html as mark_html_rust, scan_output_html as scan_output_html_rust,
    static_html_node_count as static_html_node_count_rust, transform_html as transform_html_rust,
    validate_html_fragment_boundary as validate_html_fragment_boundary_rust,
};
use citry_html_transform::{
    JAVASCRIPT_MIME_TYPES, JavascriptMode, OutputPolicyOptions, PolicyEvent, PolicyPass,
    check_output_html as check_output_html_rust, is_activation_attribute, is_javascript_url,
    is_native_event_attribute, is_url_attribute,
    script_type_is_executable as script_type_is_executable_rust,
};

#[pyfunction]
pub fn browser_fragment_matches_elements(
    html: &str,
    context: &str,
    expected: Vec<(bool, String, Vec<(String, Option<String>)>)>,
) -> bool {
    let expected = expected
        .into_iter()
        .map(|(opening, tag, attributes)| ExpectedElementEvent {
            opening,
            tag,
            attributes,
        })
        .collect::<Vec<_>>();
    browser_fragment_matches_elements_rust(html, context, &expected)
}

/// Check that the browser builds the expected nodes from an HTML fragment.
///
/// Each expected event is a `(kind, value, attributes)` tuple, in document
/// order:
///
/// - `("open", tag, attributes)`: an element whose children follow.
/// - `("close", tag, [])`: the end of the latest open element.
/// - `("shell", tag, attributes)`: an element whose contents Vue builds in
///   the browser, checked with any contents the server wrote there cut out
///   of `html`. `attributes` must include
///   `("data-allow-mismatch", "children")`, the browser must build it with
///   no child nodes, and no `close` follows it.
/// - `("comment", data, [])`: one of Vue's anchor comments, whose data is
///   `[`, `]`, `v-if`, or empty.
/// - `("text", value, [])`: whitespace-only text directly in the fragment
///   root.
///
/// Returns `False` when the browser's tree differs, including any comment or
/// root text that is not expected.
///
/// **Raises**
///
/// ValueError: If a kind is unknown, or a `close`, `comment`, or `text`
/// event carries attributes.
#[pyfunction]
pub fn browser_fragment_matches_nodes(
    html: &str,
    context: &str,
    expected: Vec<(String, String, Vec<(String, Option<String>)>)>,
) -> PyResult<bool> {
    let expected = expected
        .into_iter()
        .map(|(kind, value, attributes)| {
            let has_attributes = !attributes.is_empty();
            let event = match kind.as_str() {
                "open" => ExpectedNodeEvent::Open {
                    tag: value,
                    attributes,
                },
                "shell" => ExpectedNodeEvent::Shell {
                    tag: value,
                    attributes,
                },
                "close" if !has_attributes => ExpectedNodeEvent::Close { tag: value },
                "comment" if !has_attributes => ExpectedNodeEvent::Comment { data: value },
                "text" if !has_attributes => ExpectedNodeEvent::RootText { value },
                "close" | "comment" | "text" => {
                    return Err(PyValueError::new_err(format!(
                        "a {kind} event cannot carry attributes"
                    )));
                }
                _ => {
                    return Err(PyValueError::new_err(format!(
                        "unknown expected node kind {kind:?}"
                    )));
                }
            };
            Ok(event)
        })
        .collect::<PyResult<Vec<_>>>()?;
    Ok(browser_fragment_matches_nodes_rust(
        html, context, &expected,
    ))
}

/// Count the top-level nodes (elements, texts and comments) the browser
/// creates when Vue inserts `html` as one fixed block while it builds a page.
///
/// The browser parses the block inside a `<template>` element, so table
/// parts stay where they are written. Vue needs this count to adopt the
/// block's nodes when the server already wrote them into the page.
#[pyfunction]
pub fn static_html_node_count(html: &str) -> usize {
    static_html_node_count_rust(html)
}

#[pyfunction]
pub fn validate_html_fragment_boundary(html: &str) -> PyResult<()> {
    validate_html_fragment_boundary_rust(html).map_err(PyValueError::new_err)
}

#[pyfunction]
pub fn scan_output_html(py: Python, html: &str) -> PyResult<Py<PyAny>> {
    let output = scan_output_html_rust(html)
        .into_iter()
        .map(|tag| {
            let item = PyDict::new(py);
            item.set_item("name", tag.name)?;
            item.set_item("start", tag.start)?;
            item.set_item("end", tag.end)?;
            item.set_item("name_start", tag.name_start)?;
            item.set_item("name_end", tag.name_end)?;
            item.set_item("element_end", tag.element_end)?;
            item.set_item("element_end_start", tag.element_end_start)?;
            item.set_item(
                "attributes",
                tag.attributes
                    .into_iter()
                    .map(|attr| {
                        (
                            attr.name,
                            attr.value,
                            attr.name_start,
                            attr.name_end,
                            attr.value_start,
                            attr.value_end,
                            attr.has_value,
                        )
                    })
                    .collect::<Vec<_>>(),
            )?;
            Ok(item)
        })
        .collect::<PyResult<Vec<_>>>()?;
    Ok(output.into_pyobject(py)?.into_any().unbind())
}

/// Splice attributes onto root-level tags and split the HTML around child
/// placeholder elements, in a single scan.
///
/// This is the serializer's fast path. Each attribute in `root_attributes` is
/// added (as `attr=""`) to every root-level (depth 0) tag. A placeholder is a
/// `<template>` element carrying `placeholder_attr` with a whitespace-only
/// body; the output is split around placeholders so the caller can join in
/// each child's finished HTML without scanning again.
///
/// Unlike `transform_html`, bytes outside root-level tags are copied through
/// verbatim (no re-serialization or normalization), and malformed markup is
/// treated as text rather than raising.
///
/// **Arguments**
///
/// * `html` (str) - The HTML string to mark. Can be a fragment or full document.
/// * `root_attributes` (List[str]) - Attribute names to add to root-level tags.
/// * `placeholder_attr` (str) - The attribute that identifies placeholder elements.
///
/// **Returns**
///
/// A tuple `(segments, placeholders)`:
/// - `segments` (List[str]): the marked HTML split around placeholders;
///   always exactly `len(placeholders) + 1` entries.
/// - `placeholders` (List[Tuple[str, str, List[str]]]): one entry per
///   placeholder, in document order: `(id, placeholder_html, added_attributes)`
///   where `id` is the placeholder attribute's value, `placeholder_html` is
///   the placeholder element's text (with any spliced attributes, for callers
///   that leave unknown ids in place), and `added_attributes` lists the
///   attributes spliced into it (non-empty only for root-level placeholders).
///
/// The marked HTML is `segments[0] + placeholders[0][1] + segments[1] + ...`.
///
/// **Example**
///
/// ```python
/// segments, placeholders = mark_html(
///     '<div><template c-render-id="c2"></template></div>',
///     ['data-cid-c1'],
///     'c-render-id',
/// )
/// # segments == ['<div data-cid-c1="">', '</div>']
/// # placeholders == [('c2', '<template c-render-id="c2"></template>', [])]
/// ```
#[pyfunction]
pub fn mark_html(
    py: Python,
    html: &str,
    root_attributes: Vec<String>,
    placeholder_attr: &str,
) -> PyResult<Py<PyTuple>> {
    let result = mark_html_rust(html, &root_attributes, placeholder_attr);

    let segments = result.segments;
    let placeholders: Vec<(String, String, Vec<String>)> = result
        .placeholders
        .into_iter()
        .map(|ph| (ph.id, ph.html, ph.added_attributes))
        .collect();

    let out = PyTuple::new(
        py,
        vec![
            segments.into_pyobject(py)?.into_any(),
            placeholders.into_pyobject(py)?.into_any(),
        ],
    )?;
    Ok(out.unbind())
}

/// Transform given HTML string.
///
/// This function performs the following transformations:
///
/// 1. **Add root attributes**: Attributes specified in `root_attributes` are added
///    only to root-level elements (elements at depth 0).
///
/// 2. **Add attributes to all elements**: Attributes specified in `all_attributes`
///    are added to every element in the HTML.
///
/// In addition, this transformer also:
///
/// 1. **Tracks added attributes**: If `track_added_attributes_for_tags_with_this_attribute`
///    is set, captures which attributes were added to elements that have the specified
///    attribute, returning a dictionary mapping attribute values to lists of attributes added to tag.
///
/// 2. **Validates end tags**: If `check_end_names` is enabled, validates that
///    closing tags match their corresponding opening tags.
///
/// **Arguments**
///
/// * `html` (str) - The HTML string to transform. Can be a fragment or full document.
/// * `root_attributes` (List[str]) - List of attribute names to add to root elements only.
/// * `all_attributes` (List[str]) - List of attribute names to add to all elements.
/// * `check_end_names` (bool, optional) - Whether to validate matching of end tags. Defaults to False.
/// * `track_added_attributes_for_tags_with_this_attribute` (str, optional) - If set, captures which attributes were added to elements with this attribute.
///
/// **Returns**
///
/// Returns a tuple containing:
/// - The transformed HTML string
/// - A dictionary mapping captured attribute values to lists of attributes that were added
///   to those elements. Only populated if `track_added_attributes_for_tags_with_this_attribute` is set, otherwise empty dict.
///
/// **Raises**
///
/// ValueError: If the HTML is malformed or cannot be parsed.
///
/// **Example**
///
/// ```python
/// html = '<div data-id="123"><p>Hello</p></div>'
/// html, captured = transform_html(html, ['data-root-id'], ['data-v-123'], track_added_attributes_for_tags_with_this_attribute='data-id')
/// print(captured)
/// # {'123': ['data-root-id', 'data-v-123']}
/// ```
#[pyfunction]
#[pyo3(signature = (html, root_attributes, all_attributes, check_end_names=None, track_added_attributes_for_tags_with_this_attribute=None))]
#[pyo3(
    text_signature = "(html, root_attributes, all_attributes, *, check_end_names=False, track_added_attributes_for_tags_with_this_attribute=None)"
)]
pub fn transform_html(
    py: Python,
    html: &str,
    root_attributes: Vec<String>,
    all_attributes: Vec<String>,
    check_end_names: Option<bool>,
    track_added_attributes_for_tags_with_this_attribute: Option<String>,
) -> PyResult<Py<PyTuple>> {
    let config = HtmlTransformerConfig::new(
        root_attributes,
        all_attributes,
        check_end_names.unwrap_or(false),
        track_added_attributes_for_tags_with_this_attribute,
    );

    match transform_html_rust(&config, html) {
        Ok((html, captured)) => {
            // Convert captured attributes to a Python dictionary
            let captured_dict = PyDict::new(py);
            for (id, attrs) in captured {
                captured_dict.set_item(id, attrs)?;
            }

            // Convert items to Bound<PyAny> for the tuple
            let html_obj = PyString::new(py, &html).into_any();
            let dict_obj = captured_dict.into_any();
            let result = PyTuple::new(py, vec![html_obj, dict_obj])?;
            Ok(result.unbind())
        }
        Err(e) => Err(PyValueError::new_err(e.to_string())),
    }
}

/// The `security_javascript` mode named by `value`, or `ValueError`.
fn javascript_mode(value: Option<&str>) -> PyResult<Option<JavascriptMode>> {
    match value {
        None => Ok(None),
        Some("warn") => Ok(Some(JavascriptMode::Warn)),
        Some("omit") => Ok(Some(JavascriptMode::Omit)),
        Some("forbid") => Ok(Some(JavascriptMode::Forbid)),
        Some(other) => Err(PyValueError::new_err(format!(
            "unknown security_javascript mode {other:?}"
        ))),
    }
}

/// Run the strict-CSP and JavaScript-policy rules over finished HTML and
/// return what they found, for `citry/_output_policy.py`.
///
/// Returns `(events, cleaned_html)`. Each event is a tuple, in the order
/// the start tags appear:
///
/// - `("element", tag, token_start, name_start, name_end, element_end,
///   trusted, executable, has_manager_attribute, cids)` for every `script`
///   or `style` element a selected rule looks at;
/// - `(rule, tag, attribute, start, end, token_start, cids)` for each
///   attribute or element a rule reports.
///
/// `cleaned_html` is the page with every omit marker removed, or `None`
/// when there was none. Offsets are UTF-8 byte offsets.
#[pyfunction(name = "_check_output_html")]
#[pyo3(signature = (html, *, pre_extension, csp, javascript, marker_prefix, trusted_tag_starts, omit_handler_marker))]
pub fn check_output_html(
    py: Python<'_>,
    html: &str,
    pre_extension: bool,
    csp: bool,
    javascript: Option<&str>,
    marker_prefix: Option<&str>,
    trusted_tag_starts: HashSet<usize>,
    omit_handler_marker: Option<&str>,
) -> PyResult<(Py<PyList>, Option<String>)> {
    let options = OutputPolicyOptions {
        pass: if pre_extension {
            PolicyPass::PreExtension
        } else {
            PolicyPass::Settled
        },
        csp,
        javascript: javascript_mode(javascript)?,
        marker_prefix,
        trusted_tag_starts: &trusted_tag_starts,
        omit_handler_marker,
    };
    // A panic becomes an ordinary ValueError, so the validators report the
    // page as unreadable (and warn modes still serve it) instead of
    // `serialize()` aborting with PyO3's BaseException-derived error.
    let report = catch_panic(|| check_output_html_rust(html, &options))
        .map_err(|detail| PyValueError::new_err(format!("citry output check failed: {detail}")))?;
    let events = PyList::empty(py);
    for event in report.events {
        let item = match event {
            PolicyEvent::RawElement(element) => (
                "element",
                element.tag,
                element.token_start,
                element.name_start,
                element.name_end,
                element.element_end,
                element.trusted,
                element.executable,
                element.has_manager_attribute,
                PyTuple::new(py, element.cids)?,
            )
                .into_pyobject(py)?,
            PolicyEvent::Finding(finding) => (
                finding.rule.code(),
                finding.tag,
                finding.attribute,
                finding.start,
                finding.end,
                finding.token_start,
                PyTuple::new(py, finding.cids)?,
            )
                .into_pyobject(py)?,
        };
        events.append(item)?;
    }
    Ok((events.unbind(), report.cleaned_html))
}

/// Whether a `<script>` with this `type` value runs in the browser.
///
/// A lone surrogate in `value` reads as U+FFFD, which no MIME type
/// contains, so the answer is the one Python's string checks give.
#[pyfunction(name = "_script_type_is_executable")]
pub fn script_type_is_executable(value: &Bound<'_, PyString>) -> bool {
    script_type_is_executable_rust(&value.to_string_lossy())
}

// Bits of `_classify_dependency_attribute`'s answer.
const ACTIVATION_ATTRIBUTE: u8 = 1;
const NATIVE_EVENT_ATTRIBUTE: u8 = 2;
const JAVASCRIPT_URL: u8 = 4;

/// Classify one attribute of a structured `Script` or `Style` (a Python
/// value, not HTML, so it is not entity-decoded).
///
/// Returns bit flags: 1 for a Vue activation attribute (`v-`, `@`, `:`),
/// 2 for a native inline event attribute (`on*`), and 4 for a
/// `javascript:` URL in a URL attribute. `value` is `None` when the value
/// is not a string.
#[pyfunction(name = "_classify_dependency_attribute")]
#[pyo3(signature = (tag, name, value))]
pub fn classify_dependency_attribute(
    tag: &Bound<'_, PyString>,
    name: &Bound<'_, PyString>,
    value: Option<&Bound<'_, PyString>>,
) -> u8 {
    let tag = tag.to_string_lossy().to_ascii_lowercase();
    let name = name.to_string_lossy().to_ascii_lowercase();
    let mut flags = 0;
    if is_activation_attribute(&name) {
        flags |= ACTIVATION_ATTRIBUTE;
    }
    if is_native_event_attribute(&name) {
        flags |= NATIVE_EVENT_ATTRIBUTE;
    }
    if value.is_some_and(|value| {
        is_url_attribute(&tag, &name) && is_javascript_url(&value.to_string_lossy())
    }) {
        flags |= JAVASCRIPT_URL;
    }
    flags
}

/// Whether a URL starts with `javascript:`, read without entity decoding.
#[pyfunction(name = "_is_javascript_url")]
pub fn is_javascript_url_py(value: &Bound<'_, PyString>) -> bool {
    is_javascript_url(&value.to_string_lossy())
}

/// The MIME types that make a `<script>` a classic script.
pub fn javascript_mime_types(py: Python<'_>) -> PyResult<Bound<'_, PyFrozenSet>> {
    PyFrozenSet::new(py, JAVASCRIPT_MIME_TYPES)
}
