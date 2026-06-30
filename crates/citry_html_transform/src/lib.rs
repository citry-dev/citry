// Lints we accept for this transformer crate, matching the parser crate's
// posture (large error/enum variants, complex or wide signatures).
#![allow(clippy::result_large_err)]
#![allow(clippy::large_enum_variant)]
#![allow(clippy::type_complexity)]
#![allow(clippy::too_many_arguments)]

pub mod marker;
pub mod transformer;

// Re-export the types and functions that users need
pub use marker::{mark_html, MarkedHtml, MarkedPlaceholder};
pub use transformer::{transform_html, HtmlTransformerConfig};
