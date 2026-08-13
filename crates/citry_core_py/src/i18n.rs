//! Small ICU4X-backed locale primitives exposed to Python.

use citry_i18n::{
    CatalogCompiler as RustCatalogCompiler, CompilerError, I18nRuntime as RustCompiledCatalog,
    SCHEMA_VERSION, TextCatalog,
};
use icu_locale::{Direction, Locale, LocaleCanonicalizer, LocaleDirectionality};
use pyo3::create_exception;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

create_exception!(citry_core.i18n, I18nCompileError, PyValueError);

fn i18n_error_to_py(py: Python<'_>, error: CompilerError) -> PyErr {
    let py_error = I18nCompileError::new_err(error.to_string());
    let attach = || -> PyResult<()> {
        let value = py_error.value(py);
        value.setattr("code", error.code())?;
        value.setattr("diagnostic_json", error.diagnostic_json())?;
        Ok(())
    };
    match attach() {
        Ok(()) => py_error,
        Err(attachment_error) => attachment_error,
    }
}

fn parse_and_canonicalize(value: &str) -> PyResult<Locale> {
    if value.is_empty() {
        return Err(PyValueError::new_err("locale must not be empty"));
    }
    let mut locale = value.parse::<Locale>().map_err(|error| {
        PyValueError::new_err(format!(
            "invalid Unicode locale identifier {value:?}: {error}"
        ))
    })?;
    LocaleCanonicalizer::new_extended().canonicalize(&mut locale);
    Ok(locale)
}

/// Parse a strict Unicode BCP 47 locale identifier and apply CLDR aliases.
#[pyfunction]
pub fn canonicalize_locale(value: &str) -> PyResult<String> {
    Ok(parse_and_canonicalize(value)?.to_string())
}

/// Return the writing direction derived from a canonical locale's likely script.
#[pyfunction]
pub fn locale_direction(value: &str) -> PyResult<Option<&'static str>> {
    let locale = parse_and_canonicalize(value)?;
    let direction = LocaleDirectionality::new_extended().get(&locale.id);
    Ok(match direction {
        Some(Direction::LeftToRight) => Some("ltr"),
        Some(Direction::RightToLeft) => Some("rtl"),
        Some(_) => None,
        None => None,
    })
}

/// A checked expression-free source unit kept for compatibility.
#[pyclass(name = "TextCatalog")]
pub struct PyTextCatalog {
    catalog: TextCatalog,
}

#[pymethods]
impl PyTextCatalog {
    #[new]
    fn new(locale: &str, source: String, origin: String) -> PyResult<Self> {
        let catalog = TextCatalog::compile(locale, source, origin)
            .map_err(|error| PyValueError::new_err(error.to_string()))?;
        Ok(Self { catalog })
    }

    #[getter]
    fn origin(&self) -> &str {
        self.catalog.origin()
    }

    fn entries(&self) -> Vec<(String, bool, Vec<String>)> {
        self.catalog
            .entries()
            .map(|entry| (entry.id.clone(), entry.has_value, entry.attributes.clone()))
            .collect()
    }

    #[pyo3(signature = (message_id, attribute=None))]
    fn format(&self, message_id: &str, attribute: Option<&str>) -> PyResult<String> {
        self.catalog
            .format(message_id, attribute)
            .map_err(|error| PyValueError::new_err(error.to_string()))
    }
}

/// Stateful parser cache for one complete project catalog graph.
#[pyclass(name = "CatalogCompiler")]
pub struct PyCatalogCompiler {
    compiler: RustCatalogCompiler,
}

#[pymethods]
impl PyCatalogCompiler {
    #[new]
    fn new() -> Self {
        Self {
            compiler: RustCatalogCompiler::new(),
        }
    }

    fn compile(&self, py: Python<'_>, request_json: &str) -> PyResult<PyCompiledCatalog> {
        let artifact_json = self
            .compiler
            .compile(request_json)
            .map_err(|error| i18n_error_to_py(py, error))?;
        let catalog = RustCompiledCatalog::new(&artifact_json)
            .map_err(|error| i18n_error_to_py(py, error))?;
        Ok(PyCompiledCatalog {
            artifact_json,
            catalog,
        })
    }

    fn compile_link_unit(&self, py: Python<'_>, request_json: &str) -> PyResult<String> {
        self.compiler
            .compile_link_unit(request_json)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn analyze_source(&self, py: Python<'_>, path: &str, source: &str) -> PyResult<String> {
        self.compiler
            .analyze_source(path, source)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn clear(&self, py: Python<'_>) -> PyResult<()> {
        self.compiler
            .clear()
            .map_err(|error| i18n_error_to_py(py, error))
    }
}

/// Immutable checked project catalog and runtime.
#[pyclass(name = "CompiledCatalog")]
pub struct PyCompiledCatalog {
    artifact_json: String,
    catalog: RustCompiledCatalog,
}

#[pymethods]
impl PyCompiledCatalog {
    #[getter]
    fn schema_version(&self) -> u32 {
        SCHEMA_VERSION
    }

    #[getter]
    fn revision(&self) -> &str {
        self.catalog.revision()
    }

    #[getter]
    fn formats_revision(&self) -> &str {
        self.catalog.formats_revision()
    }

    fn artifact_json(&self) -> &str {
        &self.artifact_json
    }

    fn browser_artifact_json(
        &self,
        py: Python<'_>,
        locale: &str,
        request_json: &str,
    ) -> PyResult<String> {
        self.catalog
            .browser_artifact_json(locale, request_json)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn browser_parser_artifact_json(&self, py: Python<'_>, locale: &str) -> PyResult<String> {
        self.catalog
            .browser_parser_artifact_json(locale)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    #[pyo3(signature = (locale, message_id, args_json="{}", attribute=None))]
    fn format(
        &self,
        py: Python<'_>,
        locale: &str,
        message_id: &str,
        args_json: &str,
        attribute: Option<&str>,
    ) -> PyResult<String> {
        self.catalog
            .format(locale, message_id, args_json, attribute)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    #[pyo3(signature = (locale, message_id, args_json="{}", attribute=None))]
    fn resolve_json(
        &self,
        py: Python<'_>,
        locale: &str,
        message_id: &str,
        args_json: &str,
        attribute: Option<&str>,
    ) -> PyResult<String> {
        self.catalog
            .resolve_json(locale, message_id, args_json, attribute)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    #[pyo3(signature = (locale, message_id, args_json, slot_names_json, attribute=None))]
    fn resolve_rich_json(
        &self,
        py: Python<'_>,
        locale: &str,
        message_id: &str,
        args_json: &str,
        slot_names_json: &str,
        attribute: Option<&str>,
    ) -> PyResult<String> {
        self.catalog
            .resolve_rich_json(locale, message_id, args_json, slot_names_json, attribute)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_number(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        value: &str,
    ) -> PyResult<String> {
        self.catalog
            .format_number(locale, profile, value)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn parse_number_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> PyResult<String> {
        self.catalog
            .parse_number_json(locale, profile, input)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_percent(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        value: &str,
    ) -> PyResult<String> {
        self.catalog
            .format_percent(locale, profile, value)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn parse_percent_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> PyResult<String> {
        self.catalog
            .parse_percent_json(locale, profile, input)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_currency(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        value: &str,
        currency: &str,
    ) -> PyResult<String> {
        self.catalog
            .format_currency(locale, profile, value, currency)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_date(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        year: i32,
        month: u8,
        day: u8,
    ) -> PyResult<String> {
        self.catalog
            .format_date(locale, profile, year, month, day)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn parse_date_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> PyResult<String> {
        self.catalog
            .parse_date_json(locale, profile, input)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn parse_date_segments_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        year: &str,
        month: &str,
        day: &str,
    ) -> PyResult<String> {
        self.catalog
            .parse_date_segments_json(locale, profile, year, month, day)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_time(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        hour: u8,
        minute: u8,
        second: u8,
        nanosecond: u32,
    ) -> PyResult<String> {
        self.catalog
            .format_time(locale, profile, hour, minute, second, nanosecond)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn parse_time_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> PyResult<String> {
        self.catalog
            .parse_time_json(locale, profile, input)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    #[allow(clippy::too_many_arguments)]
    fn parse_time_segments_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        hour: &str,
        minute: &str,
        second: Option<&str>,
        day_period: Option<&str>,
    ) -> PyResult<String> {
        self.catalog
            .parse_time_segments_json(locale, profile, hour, minute, second, day_period)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    #[allow(clippy::too_many_arguments)]
    fn format_datetime(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        year: i32,
        month: u8,
        day: u8,
        hour: u8,
        minute: u8,
        second: u8,
        nanosecond: u32,
        time_zone: &str,
        offset_seconds: i32,
        epoch_seconds: i64,
    ) -> PyResult<String> {
        self.catalog
            .format_datetime(
                locale,
                profile,
                year,
                month,
                day,
                hour,
                minute,
                second,
                nanosecond,
                time_zone,
                offset_seconds,
                epoch_seconds,
            )
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn parse_datetime_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> PyResult<String> {
        self.catalog
            .parse_datetime_json(locale, profile, input)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    #[allow(clippy::too_many_arguments)]
    fn parse_datetime_segments_json(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        year: &str,
        month: &str,
        day: &str,
        hour: &str,
        minute: &str,
        second: Option<&str>,
        day_period: Option<&str>,
    ) -> PyResult<String> {
        self.catalog
            .parse_datetime_segments_json(
                locale, profile, year, month, day, hour, minute, second, day_period,
            )
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_relative_time(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        value: &str,
        unit: &str,
    ) -> PyResult<String> {
        self.catalog
            .format_relative_time(locale, profile, value, unit)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_list(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        values: Vec<String>,
    ) -> PyResult<String> {
        self.catalog
            .format_list(locale, profile, &values)
            .map_err(|error| i18n_error_to_py(py, error))
    }

    fn format_unit(
        &self,
        py: Python<'_>,
        locale: &str,
        profile: &str,
        value: &str,
        unit: &str,
    ) -> PyResult<String> {
        self.catalog
            .format_unit(locale, profile, value, unit)
            .map_err(|error| i18n_error_to_py(py, error))
    }
}
