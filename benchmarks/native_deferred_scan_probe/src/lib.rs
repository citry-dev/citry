//! Experimental discovery of deferred Python component tasks.

use pyo3::prelude::*;
use pyo3::types::{PyList, PyString, PyTuple};

struct Frame<'py> {
    parts: Bound<'py, PyList>,
    context: Bound<'py, PyAny>,
    index: usize,
    has_deferred: bool,
}

#[pyfunction]
fn scan<'py>(
    py: Python<'py>,
    render: &Bound<'py, PyAny>,
    types: &Bound<'py, PyTuple>,
) -> PyResult<Option<Bound<'py, PyList>>> {
    let render_type = types.get_item(0)?;
    let deferred_type = types.get_item(1)?;
    let region_part_type = types.get_item(2)?;
    let region_render_type = types.get_item(3)?;
    let placeholder_type = types.get_item(4)?;
    let position_type = types.get_item(5)?;
    let task_type = types.get_item(6)?;
    let merge_type = types.get_item(7)?;
    let markup_type = types.get_item(8)?;
    if !render.get_type().is(&render_type) && !render.get_type().is(&region_render_type) {
        return Ok(None);
    }
    let parts = render.getattr("parts")?;
    let Ok(parts) = parts.cast_exact::<PyList>() else {
        return Ok(None);
    };
    let mut stack = vec![Frame {
        parts: parts.clone(),
        context: render.getattr("context")?,
        index: 0,
        has_deferred: false,
    }];
    let tasks = PyList::empty(py);
    while let Some(frame) = stack.last_mut() {
        if frame.index >= frame.parts.len() {
            let finished = stack.pop().unwrap();
            if let Some(parent) = stack.last_mut()
                && finished.has_deferred
            {
                parent.has_deferred = true;
                if !finished.context.is(&parent.context) {
                    tasks.append(merge_type.call1((&parent.context, finished.context))?)?;
                }
            }
            continue;
        }
        let index = frame.index;
        frame.index += 1;
        let mut part = frame.parts.get_item(index)?;
        if part.is_exact_instance_of::<PyString>() || part.get_type().is(&markup_type) {
            continue;
        }
        if part.get_type().is(&deferred_type) {
            let position = position_type.call1((&frame.parts, index, &frame.context))?;
            tasks.append(task_type.call1((part, position))?)?;
            frame.has_deferred = true;
            continue;
        }
        // Bound wrapper chains separately: a malformed chain must reach Python's fallback.
        let mut wrappers = 0;
        while part.get_type().is(&region_part_type) || part.get_type().is(&region_render_type) {
            wrappers += 1;
            if wrappers > 256 {
                return Ok(None);
            }
            part = part.getattr("part")?;
        }
        if part.get_type().is(&render_type) {
            let nested_parts = part.getattr("parts")?;
            let Ok(nested_parts) = nested_parts.cast_exact::<PyList>() else {
                return Ok(None);
            };
            if stack.len() >= 256 {
                return Ok(None);
            }
            stack.push(Frame {
                parts: nested_parts.clone(),
                context: part.getattr("context")?,
                index: 0,
                has_deferred: false,
            });
        } else if !part.is_exact_instance_of::<PyString>()
            && !part.get_type().is(&markup_type)
            && !part.get_type().is(&placeholder_type)
            && !part.get_type().is(&deferred_type)
        {
            return Ok(None);
        }
    }
    Ok(Some(tasks))
}

#[pymodule]
fn citry_native_deferred_scan_probe(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(scan, module)?)?;
    Ok(())
}
