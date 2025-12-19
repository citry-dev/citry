/// Python interface for the citry_html_transform crate.
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyString, PyTuple};

use citry_html_transform::{HtmlTransformerConfig, transform_html as transform_html_rust};

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
) -> PyResult<Py<PyAny>> {
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
            let html_obj = PyString::new(py, &html).as_any().clone();
            let dict_obj = captured_dict.as_any().clone();
            let result = PyTuple::new(py, vec![html_obj, dict_obj])?;
            Ok(result.into_any().unbind())
        }
        Err(e) => Err(PyValueError::new_err(e.to_string())),
    }
}
