pub mod marker;
pub mod transformer;

// Re-export the types and functions that users need
pub use marker::{mark_html, MarkedHtml, MarkedPlaceholder};
pub use transformer::{transform_html, HtmlTransformerConfig};
