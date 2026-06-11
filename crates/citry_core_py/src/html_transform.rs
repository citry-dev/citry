/// Python interface for the citry_html_transform crate.
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString, PyTuple};

use citry_html_transform::{
    HtmlTransformerConfig, mark_html as mark_html_rust, transform_html as transform_html_rust,
};

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
