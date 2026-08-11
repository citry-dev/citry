//! Checked Fluent catalogs used by Citry's i18n extension.
//!
//! [`CatalogCompiler`] owns the full checked project graph. The smaller
//! [`TextCatalog`] remains as a strict compatibility helper for callers that
//! intentionally need one expression-free source unit.

mod compiler;
mod format;

pub use compiler::{CatalogCompiler, Failure as CompilerError, I18nRuntime, SCHEMA_VERSION};

use std::collections::{BTreeMap, BTreeSet};
use std::sync::Arc;

use fluent_bundle::FluentResource;
use fluent_bundle::concurrent::FluentBundle;
use fluent_syntax::ast::{Entry, Pattern, PatternElement};
use icu_locale::{Locale, LocaleCanonicalizer};
use thiserror::Error;
use unic_langid::LanguageIdentifier;

/// One catalog compile or format failure.
#[derive(Debug, Error)]
pub enum CatalogError {
    /// The locale cannot be used by Fluent.
    #[error("invalid Fluent locale {locale:?}: {message}")]
    InvalidLocale { locale: String, message: String },
    /// Fluent rejected the authored source.
    #[error("invalid Fluent source in {origin}: {message}")]
    InvalidSource { origin: String, message: String },
    /// The expression-free `TextCatalog` helper received an expression.
    #[error(
        "unsupported Fluent expression in {origin}, message {message_id:?}{attribute}; TextCatalog accepts only text values and attributes"
    )]
    UnsupportedExpression {
        origin: String,
        message_id: String,
        attribute: AttributeDisplay,
    },
    /// The expression-free `TextCatalog` helper received a term.
    #[error(
        "unsupported Fluent term {term_id:?} in {origin}; use CatalogCompiler for linked terms"
    )]
    UnsupportedTerm { origin: String, term_id: String },
    /// One source repeats a public message ID.
    #[error("duplicate Fluent message ID {message_id:?} in {origin}")]
    DuplicateMessage { origin: String, message_id: String },
    /// One message repeats an attribute.
    #[error("duplicate Fluent attribute {attribute:?} on message {message_id:?} in {origin}")]
    DuplicateAttribute {
        origin: String,
        message_id: String,
        attribute: String,
    },
    /// A catalog contains a bidi control that Citry does not own.
    #[error("authored bidi-control character in {origin}, message {message_id:?}{attribute}")]
    AuthoredBidiControl {
        origin: String,
        message_id: String,
        attribute: AttributeDisplay,
    },
    /// Fluent refused the already checked resource.
    #[error("could not install Fluent source {origin}: {message}")]
    ResourceConflict { origin: String, message: String },
    /// The public ID is absent.
    #[error("unknown Fluent message ID {message_id:?}")]
    UnknownMessage { message_id: String },
    /// The requested value or attribute is absent.
    #[error("message {message_id:?} has no {output}")]
    UnknownOutput { message_id: String, output: String },
    /// Fluent failed while executing a checked text-only pattern.
    #[error("could not format Fluent message {message_id:?}: {message}")]
    Format { message_id: String, message: String },
}

/// Display helper that keeps error text readable without storing formatted strings.
#[derive(Debug)]
pub struct AttributeDisplay(Option<String>);

impl std::fmt::Display for AttributeDisplay {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let Some(attribute) = &self.0 {
            write!(formatter, ".{attribute}")
        } else {
            Ok(())
        }
    }
}

/// Public shape extracted from one text-only message.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MessageEntry {
    /// Stable public message ID.
    pub id: String,
    /// Whether the message has a main value.
    pub has_value: bool,
    /// Sorted attribute names.
    pub attributes: Vec<String>,
}

/// One compiled source unit.
pub struct TextCatalog {
    origin: String,
    entries: BTreeMap<String, MessageEntry>,
    bundle: FluentBundle<Arc<FluentResource>>,
}

impl TextCatalog {
    /// Parse, validate, and install one text-only Fluent source unit.
    pub fn compile(locale: &str, source: String, origin: String) -> Result<Self, CatalogError> {
        let mut canonical_locale =
            locale
                .parse::<Locale>()
                .map_err(|error| CatalogError::InvalidLocale {
                    locale: locale.to_owned(),
                    message: error.to_string(),
                })?;
        LocaleCanonicalizer::new_extended().canonicalize(&mut canonical_locale);
        // FluentBundle needs a language identifier and does not accept Unicode
        // locale extensions. Keep the full canonical locale in Citry's
        // LocaleContext, but give Fluent its canonical language/script/region
        // identity. Formatter services consume the extensions separately.
        let language = canonical_locale
            .id
            .to_string()
            .parse::<LanguageIdentifier>()
            .map_err(|error| CatalogError::InvalidLocale {
                locale: locale.to_owned(),
                message: error.to_string(),
            })?;
        let resource =
            FluentResource::try_new(source).map_err(|(_, errors)| CatalogError::InvalidSource {
                origin: origin.clone(),
                message: format!("{errors:?}"),
            })?;
        let entries = validate_resource(&resource, &origin)?;
        let mut bundle = FluentBundle::new_concurrent(vec![language]);
        bundle.set_use_isolating(false);
        bundle.add_resource(Arc::new(resource)).map_err(|errors| {
            CatalogError::ResourceConflict {
                origin: origin.clone(),
                message: format!("{errors:?}"),
            }
        })?;
        Ok(Self {
            origin,
            entries,
            bundle,
        })
    }

    /// The source-unit origin used in diagnostics.
    pub fn origin(&self) -> &str {
        &self.origin
    }

    /// Deterministic public message metadata.
    pub fn entries(&self) -> impl Iterator<Item = &MessageEntry> {
        self.entries.values()
    }

    /// Format one checked text-only value or attribute.
    pub fn format(
        &self,
        message_id: &str,
        attribute: Option<&str>,
    ) -> Result<String, CatalogError> {
        let entry = self
            .entries
            .get(message_id)
            .ok_or_else(|| CatalogError::UnknownMessage {
                message_id: message_id.to_owned(),
            })?;
        let message =
            self.bundle
                .get_message(message_id)
                .ok_or_else(|| CatalogError::UnknownMessage {
                    message_id: message_id.to_owned(),
                })?;
        let pattern = if let Some(attribute) = attribute {
            if entry
                .attributes
                .binary_search_by(|item| item.as_str().cmp(attribute))
                .is_err()
            {
                return Err(CatalogError::UnknownOutput {
                    message_id: message_id.to_owned(),
                    output: format!("attribute {attribute:?}"),
                });
            }
            message
                .get_attribute(attribute)
                .map(|value| value.value())
                .ok_or_else(|| CatalogError::UnknownOutput {
                    message_id: message_id.to_owned(),
                    output: format!("attribute {attribute:?}"),
                })?
        } else {
            if !entry.has_value {
                return Err(CatalogError::UnknownOutput {
                    message_id: message_id.to_owned(),
                    output: "main value".to_owned(),
                });
            }
            message.value().ok_or_else(|| CatalogError::UnknownOutput {
                message_id: message_id.to_owned(),
                output: "main value".to_owned(),
            })?
        };
        let mut errors = Vec::new();
        let value = self
            .bundle
            .format_pattern(pattern, None, &mut errors)
            .into_owned();
        if errors.is_empty() {
            Ok(value)
        } else {
            Err(CatalogError::Format {
                message_id: message_id.to_owned(),
                message: format!("{errors:?}"),
            })
        }
    }
}

fn validate_resource(
    resource: &FluentResource,
    origin: &str,
) -> Result<BTreeMap<String, MessageEntry>, CatalogError> {
    let mut result = BTreeMap::new();
    for entry in resource.entries() {
        match entry {
            Entry::Message(message) => {
                let message_id = message.id.name.to_owned();
                if result.contains_key(&message_id) {
                    return Err(CatalogError::DuplicateMessage {
                        origin: origin.to_owned(),
                        message_id,
                    });
                }
                if let Some(pattern) = &message.value {
                    validate_pattern(pattern, origin, &message_id, None)?;
                }
                let mut attributes = BTreeSet::new();
                for attribute in &message.attributes {
                    let name = attribute.id.name.to_owned();
                    if !attributes.insert(name.clone()) {
                        return Err(CatalogError::DuplicateAttribute {
                            origin: origin.to_owned(),
                            message_id,
                            attribute: name,
                        });
                    }
                    validate_pattern(&attribute.value, origin, &message_id, Some(name.as_str()))?;
                }
                result.insert(
                    message_id.clone(),
                    MessageEntry {
                        id: message_id,
                        has_value: message.value.is_some(),
                        attributes: attributes.into_iter().collect(),
                    },
                );
            }
            Entry::Term(term) => {
                return Err(CatalogError::UnsupportedTerm {
                    origin: origin.to_owned(),
                    term_id: term.id.name.to_owned(),
                });
            }
            Entry::Junk { .. } => {
                return Err(CatalogError::InvalidSource {
                    origin: origin.to_owned(),
                    message: "source contains a Junk entry".to_owned(),
                });
            }
            Entry::Comment(_) | Entry::GroupComment(_) | Entry::ResourceComment(_) => {}
        }
    }
    Ok(result)
}

fn validate_pattern(
    pattern: &Pattern<&str>,
    origin: &str,
    message_id: &str,
    attribute: Option<&str>,
) -> Result<(), CatalogError> {
    for element in &pattern.elements {
        match element {
            PatternElement::TextElement { value } => {
                if value.chars().any(is_bidi_control) {
                    return Err(CatalogError::AuthoredBidiControl {
                        origin: origin.to_owned(),
                        message_id: message_id.to_owned(),
                        attribute: AttributeDisplay(attribute.map(str::to_owned)),
                    });
                }
            }
            PatternElement::Placeable { .. } => {
                return Err(CatalogError::UnsupportedExpression {
                    origin: origin.to_owned(),
                    message_id: message_id.to_owned(),
                    attribute: AttributeDisplay(attribute.map(str::to_owned)),
                });
            }
        }
    }
    Ok(())
}

fn is_bidi_control(value: char) -> bool {
    matches!(
        value,
        '\u{061c}'
            | '\u{200e}'
            | '\u{200f}'
            | '\u{202a}'
            | '\u{202b}'
            | '\u{202c}'
            | '\u{202d}'
            | '\u{202e}'
            | '\u{2066}'
            | '\u{2067}'
            | '\u{2068}'
            | '\u{2069}'
    )
}

#[cfg(test)]
mod tests {
    use super::{CatalogError, TextCatalog};

    #[test]
    fn compiles_and_formats_text_values_and_attributes() {
        let catalog = TextCatalog::compile(
            "en-US",
            "hello = Hello\n    .aria-label = Greeting".to_owned(),
            "card.ftl".to_owned(),
        )
        .expect("catalog should compile");
        assert_eq!(catalog.format("hello", None).unwrap(), "Hello");
        assert_eq!(
            catalog.format("hello", Some("aria-label")).unwrap(),
            "Greeting"
        );
    }

    #[test]
    fn text_catalog_rejects_expressions_owned_by_catalog_compiler() {
        let error = TextCatalog::compile(
            "en-US",
            "hello = Hello, { $name }.".to_owned(),
            "card.ftl".to_owned(),
        )
        .err()
        .expect("expression should fail");
        assert!(matches!(error, CatalogError::UnsupportedExpression { .. }));
    }

    #[test]
    fn accepts_canonical_locales_with_unicode_extensions() {
        let catalog = TextCatalog::compile(
            "hi-IN-u-nu-deva",
            "hello = namaste".to_owned(),
            "card.ftl".to_owned(),
        )
        .expect("locale extensions should not be passed to FluentBundle");
        assert_eq!(catalog.format("hello", None).unwrap(), "namaste");
    }
}
