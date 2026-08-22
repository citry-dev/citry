use std::collections::{HashMap, HashSet};

use lazy_static::lazy_static;

use crate::parser_context::TagRules;

/// HTML void elements that can be self-closing (e.g., `<img/>`, `<br/>`)
/// These are elements that cannot have content according to HTML spec.
///
/// See https://developer.mozilla.org/en-US/docs/Glossary/Void_element
pub const HTML_VOID_ELEMENTS: &[&str] = &[
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
    "track", "wbr",
];

/// Whether `tag_name` names an HTML void element.
///
/// HTML tag identity is ASCII-case-insensitive even though the authored
/// spelling is preserved in the AST and rendered output.
pub fn is_html_void_element(tag_name: &str) -> bool {
    HTML_VOID_ELEMENTS
        .iter()
        .any(|candidate| tag_name.eq_ignore_ascii_case(candidate))
}

// Reserved tag name constants
// These provide a single source of truth for all reserved tag names.
//
// NOTE: There are also c-provide, c-css, c-js
//       that are not defined here in the parser/compiler logic,
//       because they don't influence the grammar, and can be implemented
//       as regular user-side components.
pub const C_IF_TAG: &str = "c-if";
pub const C_ELIF_TAG: &str = "c-elif";
pub const C_ELSE_TAG: &str = "c-else";
pub const C_FOR_TAG: &str = "c-for";
pub const C_EMPTY_TAG: &str = "c-empty";
pub const C_RAW_TAG: &str = "c-raw";
pub const C_FILL_TAG: &str = "c-fill";
pub const C_SLOT_TAG: &str = "c-slot";
pub const C_COMPONENT_TAG: &str = "c-component";
pub const C_ELEMENT_TAG: &str = "c-element";

/// Whether `tag_name` uses Citry's exact, lowercase component prefix.
pub fn has_citry_component_prefix(tag_name: &str) -> bool {
    tag_name.starts_with("c-")
}

/// Compare Citry component tags using an exact lowercase `c-` prefix and an
/// ASCII-case-insensitive component-name suffix.
pub fn citry_component_tag_eq(tag_name: &str, canonical: &str) -> bool {
    let Some(component_name) = tag_name.strip_prefix("c-") else {
        return false;
    };
    let Some(canonical_name) = canonical.strip_prefix("c-") else {
        return false;
    };

    component_name.eq_ignore_ascii_case(canonical_name)
}

/// Whether `attr_name` is the static target selector for a dynamic built-in.
///
/// `<c-element>` is an HTML-attribute boundary, so its `is` identity folds
/// ASCII case. `<c-component>` is a component-input boundary and therefore
/// keeps the selector's spelling case-sensitive like every other kwarg.
pub fn is_dynamic_target_static_attr(tag_name: &str, attr_name: &str) -> bool {
    if citry_component_tag_eq(tag_name, C_ELEMENT_TAG) {
        attr_name.eq_ignore_ascii_case("is")
    } else {
        citry_component_tag_eq(tag_name, C_COMPONENT_TAG) && attr_name == "is"
    }
}

/// Whether `attr_name` is the expression-valued target selector for a dynamic
/// built-in. See [`is_dynamic_target_static_attr`] for the casing boundary.
pub fn is_dynamic_target_expr_attr(tag_name: &str, attr_name: &str) -> bool {
    if citry_component_tag_eq(tag_name, C_ELEMENT_TAG) {
        attr_name
            .strip_prefix("c-")
            .is_some_and(|name| name.eq_ignore_ascii_case("is"))
    } else {
        citry_component_tag_eq(tag_name, C_COMPONENT_TAG) && attr_name == "c-is"
    }
}

// Citry client-runtime directives are evaluated by the browser integration,
// not as Python component inputs. These constants reserve the props
// spellings while generic attribute nodes preserve their authored source.
/// Direct client props expression authored on a component tag.
pub const CLIENT_PROPS_ATTR: &str = "$c-props";
/// Server-dynamic form whose Python result is the complete client expression.
pub const DYNAMIC_CLIENT_PROPS_ATTR: &str = "c-$c-props";

// The `#c-*` framework-metadata attribute channel.
//
// A `#c-*` attribute is an instruction to the framework about the node itself
// (how it is identified and morphed), not render data. The channel has exactly
// two members; any other `#c-*` name is a parse error (see
// docs/design/events.md section 5.1).
/// Prefix that marks an attribute as framework metadata (the grammar routes
/// names starting with this to their own rule).
pub const META_ATTR_PREFIX: &str = "#c-";
/// The keying attribute: `#c-key="expr"`. Expression-valued, server-evaluated.
pub const META_ATTR_KEY: &str = "#c-key";
/// The whole-subtree morph opt-out marker: bare `#c-ignore`.
pub const META_ATTR_IGNORE: &str = "#c-ignore";
/// The rendered attribute an element `#c-key` compiles to. Its value starts
/// with an empty scope segment and a colon. Component-tag keys instead travel
/// as ownership-graph invocation metadata and never use this DOM attribute.
pub const KEY_OUTPUT_ATTR: &str = "data-citry-key";
/// The rendered attribute `#c-ignore` compiles to (`data-citry-morph="ignore"`),
/// read by the client's morph hook.
pub const MORPH_OUTPUT_ATTR: &str = "data-citry-morph";
/// The value `#c-ignore` stamps into the morph output attribute.
pub const MORPH_OUTPUT_IGNORE_VALUE: &str = "ignore";

// Tagged ComponentNode metadata envelope values. These are runtime protocol
// literals in generated Python source, separate from rendered DOM attributes.
pub const COMPONENT_METADATA_LOCUS_RANGE: &str = "range";
pub const COMPONENT_METADATA_LOCUS_ELEMENT: &str = "element";
pub const COMPONENT_METADATA_ENTRY_KEY: &str = "key";
pub const COMPONENT_METADATA_ENTRY_MORPH: &str = "morph";

// Node class name constants
// These are the class/struct names that need to be defined in each language implementation.
// They represent the different types of nodes in the compiled template tree.
pub const EXPR_NODE: &str = "ExprNode";
pub const FOREIGN_NODE: &str = "ForeignNode";
pub const TEMPLATE_NODE: &str = "TemplateNode";
pub const COMPONENT_NODE: &str = "ComponentNode";
pub const IF_NODE: &str = "IfNode";
pub const FOR_NODE: &str = "ForNode";
pub const SLOT_NODE: &str = "SlotNode";
pub const FILL_NODE: &str = "FillNode";
pub const FILL_DATA_BINDING: &str = "FillDataBinding";
pub const C_BIND_ATTR: &str = "c-bind";
// Keeps the whole attribute region of an HTML start tag structured when it has
// a dynamic attribute or an extension-owned literal binding/output name. See
// compile_html_node.
pub const ELEMENT_ATTRS_NODE: &str = "ElementAttrsNode";
// Evaluates an explicit element `#c-key` and emits the complete composite
// attribute only when the expression produces a key. See compile_meta_attr_on_element.
pub const ELEMENT_KEY_NODE: &str = "ElementKeyNode";

// Attribute class name constants
// These are the class/struct names that need to be defined in each language implementation.
// They represent the different types of HTML attributes in the compiled template tree.
pub const EXPR_ATTR_NODE: &str = "ExprHtmlAttr";
pub const TEMPLATE_ATTR_NODE: &str = "TemplateHtmlAttr";
pub const STATIC_ATTR_NODE: &str = "StaticHtmlAttr";
pub const FOREIGN_ATTR_NODE: &str = "ForeignHtmlAttr";

/// Reserved special tags
pub const RESERVED_TAG_NAMES: &[&str] = &[
    C_IF_TAG,
    C_ELIF_TAG,
    C_ELSE_TAG,
    C_FOR_TAG,
    C_EMPTY_TAG,
    C_RAW_TAG,
    C_FILL_TAG,
    C_SLOT_TAG,
    // Note: following special tags allow `<c-fill>` inside them
    // because they are practically just custom components:
    // c-component, c-element, c-provide, c-js, c-css
    // (c-element allows only the default fill, per TAG_SLOT_RULES_DATA)
];

/// Fixed Citry attribute directives that tooling can document without an app.
///
/// Dynamic `c-*` attributes such as `c-class` are intentionally absent because
/// their suffix is an HTML attribute or component input rather than a fixed
/// parser-owned spelling.
pub const CITRY_DIRECTIVE_NAMES: &[&str] = &[
    C_IF_TAG,
    C_ELIF_TAG,
    C_ELSE_TAG,
    C_FOR_TAG,
    C_EMPTY_TAG,
    C_BIND_ATTR,
    META_ATTR_KEY,
    META_ATTR_IGNORE,
    CLIENT_PROPS_ATTR,
    DYNAMIC_CLIENT_PROPS_ATTR,
];

/// Fixed attributes whose meaning is owned by one reserved structural tag.
///
/// `<c-slot>` may also expose arbitrary user-named data fields. Those open
/// names are deliberately absent because tooling can document only the fixed
/// parser contract without a component schema.
pub const STRUCTURAL_TAG_ATTRIBUTE_NAMES: &[(&str, &[&str])] = &[
    (C_IF_TAG, &["cond"]),
    (C_ELIF_TAG, &["cond"]),
    (C_ELSE_TAG, &[]),
    (C_FOR_TAG, &["each"]),
    (C_EMPTY_TAG, &[]),
    (C_RAW_TAG, &[]),
    (
        C_FILL_TAG,
        &["name", "c-name", "data", "fallback", C_BIND_ATTR],
    ),
    (
        C_SLOT_TAG,
        &[
            "name",
            "c-name",
            "required",
            "c-required",
            C_BIND_ATTR,
            C_IF_TAG,
            C_ELIF_TAG,
            C_ELSE_TAG,
            C_FOR_TAG,
            C_EMPTY_TAG,
        ],
    ),
];

/// Whether an exact-prefix Citry tag has the identity of a reserved
/// structural tag, regardless of suffix casing.
pub fn is_reserved_citry_tag_identity(tag_name: &str) -> bool {
    has_citry_component_prefix(tag_name)
        && RESERVED_TAG_NAMES
            .iter()
            .any(|reserved| tag_name.eq_ignore_ascii_case(reserved))
}

/// Tag names that are forbidden in regular HTML tags
/// These are handled by special grammar rules (e.g., html_raw for "c-raw")
pub const FORBIDDEN_HTML_TAG_NAMES: &[&str] = &[C_RAW_TAG];

/// Control flow attribute groups for conflict validation.
///
/// Each inner array represents a group of mutually exclusive attributes.
/// A tag cannot have multiple attributes from the same group.
///
/// The order of the tags WITHIN THE GROUP can be arbitrary, except for the first item
/// in a group, which is the "primary" attribute.
///
/// However, the order of the groups themselves defines their priority
/// (first group == highest priority). This priority is used to determine which
/// control flow has precedence when there are multiple control flow attributes
/// on a single tag:
/// ```html
/// <main class="container" c-if="is_visible" c-for="item in items">
///   <div>Hello</div>
/// </main>
/// ```
///
/// In this case, the `<c-if>` attribute has precedence over the `<c-for>` attribute,
/// because the `<c-if>` is the first group (highest priority).
///
/// So the final output will be:
/// ```html
/// <c-if cond="is_visible">
///   <c-for each="item in items">
///     <main class="container">
///       <div>Hello</div>
///     </main>
///   </c-for>
/// </c-if>
/// ```
///
/// The ordering of the tags within the groups is defined in `TAG_ORDERING_RULES_DATA`.
///
/// E.g. this is valid ✅:
/// ```html
/// <div c-if="is_visible" c-for="item in items">
///   <div>Hello</div>
/// </div>
/// ```
///
/// But this is not ❌:
/// ```html
/// <div c-if="is_visible" c-elif="is_visible" c-for="item in items">
///   <div>Hello</div>
/// </div>
/// ```
pub const CONTROL_FLOW_GROUPS: &[&[&str]] = &[
    &[C_IF_TAG, C_ELIF_TAG, C_ELSE_TAG],
    &[C_FOR_TAG, C_EMPTY_TAG],
];

lazy_static! {
    /// All control flow tags in a single set.
    ///
    /// These tags are "transparent" for <c-fill> validation - we skip over them when looking
    /// for a component or nested <c-fill> tags.
    ///
    /// E.g.:
    /// ```html
    /// <c-my-comp>
    ///   <c-for each="item in items">
    ///     <c-fill name="item"> </c-fill>
    ///   </c-for>
    ///   <c-fill name="footer"> </c-fill>
    /// </c-my-comp>
    /// ```
    ///
    /// This is computed from `CONTROL_FLOW_GROUPS` to ensure a single source of truth.
    pub static ref CONTROL_FLOW_TAGS: HashSet<&'static str> = {
        CONTROL_FLOW_GROUPS
            .iter()
            .flat_map(|group| group.iter().copied())
            .collect()
    };
}

#[cfg(test)]
mod tests {
    use super::{
        CITRY_DIRECTIVE_NAMES, CLIENT_PROPS_ATTR, CONTROL_FLOW_GROUPS, C_BIND_ATTR, C_FILL_TAG,
        C_SLOT_TAG, DYNAMIC_CLIENT_PROPS_ATTR, META_ATTR_IGNORE, META_ATTR_KEY, RESERVED_TAG_NAMES,
        STRUCTURAL_TAG_ATTRIBUTE_NAMES, TAG_ATTR_RULES_DATA,
    };
    use std::collections::{HashMap, HashSet};

    #[test]
    fn tooling_syntax_inventories_are_unique_and_cover_every_structural_tag() {
        let directives: HashSet<_> = CITRY_DIRECTIVE_NAMES.iter().copied().collect();
        assert_eq!(directives.len(), CITRY_DIRECTIVE_NAMES.len());

        let structural_tags: HashSet<_> = STRUCTURAL_TAG_ATTRIBUTE_NAMES
            .iter()
            .map(|(tag, _attributes)| *tag)
            .collect();
        assert_eq!(structural_tags.len(), STRUCTURAL_TAG_ATTRIBUTE_NAMES.len());
        assert_eq!(
            structural_tags,
            RESERVED_TAG_NAMES.iter().copied().collect()
        );

        for (_tag, attributes) in STRUCTURAL_TAG_ATTRIBUTE_NAMES {
            let unique: HashSet<_> = attributes.iter().copied().collect();
            assert_eq!(unique.len(), attributes.len());
        }
    }

    #[test]
    fn tooling_directives_match_the_parser_owned_groups_and_special_names() {
        // The language-tool inventory must move with every parser-owned fixed
        // directive, including the names handled outside control-flow lowering.
        let expected: HashSet<_> = CONTROL_FLOW_GROUPS
            .iter()
            .flat_map(|group| group.iter().copied())
            .chain([
                C_BIND_ATTR,
                META_ATTR_KEY,
                META_ATTR_IGNORE,
                CLIENT_PROPS_ATTR,
                DYNAMIC_CLIENT_PROPS_ATTR,
            ])
            .collect();
        assert_eq!(
            CITRY_DIRECTIVE_NAMES
                .iter()
                .copied()
                .collect::<HashSet<_>>(),
            expected
        );
    }

    #[test]
    fn tooling_structural_attributes_match_parser_validation_rules() {
        // Most structural tags have closed validation rules. c-bind bypasses
        // those groups deliberately, so include it for c-fill before comparing.
        let documented: HashMap<_, HashSet<_>> = STRUCTURAL_TAG_ATTRIBUTE_NAMES
            .iter()
            .map(|(tag, attributes)| (*tag, attributes.iter().copied().collect()))
            .collect();
        for (tag, (allowed_groups, _required_groups)) in TAG_ATTR_RULES_DATA {
            if !RESERVED_TAG_NAMES.contains(tag) || *tag == C_SLOT_TAG {
                continue;
            }
            let mut operational: HashSet<_> = allowed_groups
                .expect("closed structural tags define allowed attributes")
                .iter()
                .flat_map(|group| group.iter().copied())
                .collect();
            if *tag == C_FILL_TAG {
                operational.insert(C_BIND_ATTR);
            }
            assert_eq!(documented.get(tag), Some(&operational));
        }

        // c-slot accepts open data names, but these fixed settings and control
        // directives are the parser-owned subset language tools can document.
        let slot_fixed: HashSet<_> = ["name", "c-name", "required", "c-required", C_BIND_ATTR]
            .into_iter()
            .chain(
                CONTROL_FLOW_GROUPS
                    .iter()
                    .flat_map(|group| group.iter().copied()),
            )
            .collect();
        assert_eq!(documented.get(C_SLOT_TAG), Some(&slot_fixed));
    }
}

/// Static definition of attribute validation rules for special tags
/// Format: (tag_name, (allowed_attrs, required_attrs))
/// - allowed_attrs: array of arrays of allowed attribute names. Each inner array is a "one of" group.
///   If None, any attributes allowed. If Some(vec![]), no attributes allowed.
///   If Some([["c-name", "name"]]), the tag can have either "c-name" OR "name", but not both.
/// - required_attrs: array of arrays. Each inner array is a "one of" group.
///   Each inner list means "one of" (at least one from each inner list must be present).
pub const TAG_ATTR_RULES_DATA: &[(&str, (Option<&[&[&str]]>, &[&[&str]]))] = &[
    // c-if: only "cond" allowed, also required
    (C_IF_TAG, (Some(&[&["cond"]]), &[&["cond"]])),
    // c-elif: only "cond" allowed, also required
    (C_ELIF_TAG, (Some(&[&["cond"]]), &[&["cond"]])),
    // c-else: no attrs allowed, nothing required
    (C_ELSE_TAG, (Some(&[]), &[])),
    // c-for: only "each" allowed, also required
    (C_FOR_TAG, (Some(&[&["each"]]), &[&["each"]])),
    // c-empty: nothing allowed, nothing required
    (C_EMPTY_TAG, (Some(&[]), &[])),
    // c-raw: nothing allowed, nothing required
    (C_RAW_TAG, (Some(&[]), &[])),
    // c-fill: any of ["name", "c-name", "data", "fallback", "c-bind"] allowed,
    //         but ["name", "c-name"] are mutually exclusive.
    //         also one of ["name", "c-name", "c-bind"] is required.
    (
        C_FILL_TAG,
        (
            Some(&[&["name", "c-name"], &["data"], &["fallback"]]),
            &[&["name", "c-name", C_BIND_ATTR]],
        ),
    ),
    // c-slot: any attributes allowed, nothing required. A slot with no "name",
    // "c-name", nor "c-bind" attribute is the default slot, named "default".
    (C_SLOT_TAG, (None, &[])),
    // c-component: any attributes allowed, but one of ["is", "c-is", "c-bind"] required
    (C_COMPONENT_TAG, (None, &[&["is", "c-is", C_BIND_ATTR]])),
    // c-element: any attributes allowed, but one of ["is", "c-is", "c-bind"] required
    (C_ELEMENT_TAG, (None, &[&["is", "c-is", C_BIND_ATTR]])),
    // NOTE: `<c-provide>`, `<c-js>`, and `<c-css>` are not included here
    // because they can be implemented as user-side components.
];

/// Static definition of slot validation rules for special tags
/// Format: (tag_name, (allowed_slots, required_slots))
/// - allowed_slots: array of allowed slot names. If None, any slots allowed. If Some(&[]), no slots allowed.
/// - required_slots: array of required slot names.
pub const TAG_SLOT_RULES_DATA: &[(&str, (Option<&[&str]>, &[&str]))] = &[
    // c-component: any slots allowed, none required
    (C_COMPONENT_TAG, (None, &[])),
    // c-element: a plain HTML element has children but no named slots,
    // so only the "default" slot is allowed, none required
    (C_ELEMENT_TAG, (Some(&["default"]), &[])),
    // These cannot contain <c-fill> tags, not applicable for slot validation
    // c-if, c-elif, c-else, c-for, c-empty, c-raw, c-fill

    // NOTE: `<c-provide>`, `<c-js>`, and `<c-css>` are not included here
    // because they can be implemented as user-side components.
];

lazy_static! {
    pub static ref TAG_ATTR_RULES: HashMap<&'static str, TagRules> = {
        let mut rules = HashMap::new();

        // First, create a HashMap from slot rules for O(1) lookup
        let slot_rules_map: HashMap<&'static str, (Option<&[&str]>, &[&str])> = TAG_SLOT_RULES_DATA
            .iter()
            .map(|(tag, (allowed, required))| (*tag, (*allowed, *required)))
            .collect();

        // Process attribute rules
        for (tag, (allowed_groups, required_groups)) in TAG_ATTR_RULES_DATA.iter() {
            let allowed_attrs = allowed_groups.map(|groups| {
                groups
                    .iter()
                    .map(|group| group.iter().map(|s| s.to_string()).collect())
                    .collect()
            });
            let required_attrs = required_groups
                .iter()
                .map(|group| group.iter().map(|s| s.to_string()).collect())
                .collect();

            // Get slot rules for this tag (if any)
            let (allowed_slots, required_slots) = slot_rules_map
                .get(tag)
                .map(|(allowed, required)| {
                    (
                        allowed.map(|slots| slots.iter().map(|s| s.to_string()).collect()),
                        required.iter().map(|s| s.to_string()).collect(),
                    )
                })
                .unwrap_or((None, vec![]));

            rules.insert(
                *tag,
                TagRules {
                    allowed_attrs,
                    required_attrs,
                    allowed_slots,
                    required_slots,
                    slot_data_fields: Default::default(),
                },
            );
        }

        rules
    };
}

/// Static definition of tag ordering rules
/// Format: (tag_name, allowed_previous_tags)
/// - If a tag is not in this list, it can follow any tag.
/// - If a tag is in this list, it can only follow tags in the specified array.
///
/// E.g. `("c-elif", &["c-if", "c-elif"])` means `<c-elif>` can only follow `<c-if>` or `<c-elif>`.
///
/// The control flow tags can be also replaced with Vue-like shortcut control flow ATTRIBUTES:
/// ```html
/// <c-if cond="is_visible">
///   <div>Hello</div>
/// </c-if>
/// ```
///
/// Becomes:
/// ```html
/// <div c-if="is_visible">Hello</div>
/// ```
pub const TAG_ORDERING_RULES_DATA: &[(&str, &[&str])] = &[
    (C_ELIF_TAG, &[C_IF_TAG, C_ELIF_TAG]),
    (C_ELSE_TAG, &[C_IF_TAG, C_ELIF_TAG]),
    (C_EMPTY_TAG, &[C_FOR_TAG]),
];

// Tag ordering rules: maps tag names to the set of tag names they can follow.
// If a tag is not in this map, it can follow any tag.
// If a tag is in this map, it can only follow tags in the specified set.
// NOTE: Defined statically so it's only initialized once.
lazy_static! {
    pub static ref TAG_ORDERING_RULES: HashMap<&'static str, HashSet<&'static str>> = {
        TAG_ORDERING_RULES_DATA
            .iter()
            .map(|(tag, allowed_tags)| {
                let allowed_set: HashSet<&'static str> = allowed_tags.iter().copied().collect();
                (*tag, allowed_set)
            })
            .collect()
    };
}
