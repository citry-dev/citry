// Lints we accept for this transformer crate, matching the parser crate's
// posture (large error/enum variants, complex or wide signatures).
#![allow(clippy::result_large_err)]
#![allow(clippy::large_enum_variant)]
#![allow(clippy::type_complexity)]
#![allow(clippy::too_many_arguments)]

pub mod hydration_nesting;
pub mod hydration_structure;
pub mod marker;
pub mod output_policy;
pub mod output_scanner;
mod stack;
pub mod static_html;
pub mod transformer;

// Re-export the types and functions that users need
pub use hydration_nesting::{tokens_nest_in_browser, NestingToken};
pub use hydration_structure::{
    browser_fragment_matches_elements, browser_fragment_matches_nodes, ExpectedElementEvent,
    ExpectedNodeEvent,
};
pub use marker::{mark_html, MarkedHtml, MarkedPlaceholder};
pub use output_policy::{
    check_output_html, csp_attribute_problem, decode_html_attribute, is_activation_attribute,
    is_javascript_url, is_native_event_attribute, is_url_attribute, script_type_is_executable,
    CspAttributeProblem, Finding, JavascriptMode, OutputPolicyOptions, OutputPolicyReport,
    PolicyEvent, PolicyPass, RawElement, Rule, JAVASCRIPT_MIME_TYPES,
};
pub use output_scanner::{
    scan_output_html, validate_html_fragment_boundary, OutputAttribute, OutputTag,
};
pub use static_html::{
    static_html_in_context, static_html_node_count, StaticHtmlFacts, StaticHtmlUse,
};
pub use transformer::{transform_html, HtmlTransformerConfig};
