use std::collections::{BTreeMap, HashMap, HashSet};
use std::rc::Rc;

use pest::Parser;
use unicode_normalization::UnicodeNormalization;

use crate::ast::{
    remove_introduced_variables, Comment, Expr, FillDataField, FillDataPattern, HtmlAttr,
    HtmlAttrKind, HtmlEndTag, HtmlStartTag, Node, StaticNamedSlot, Template, TemplateElement, Text,
    Token,
};
use crate::constants::{
    citry_component_tag_eq, has_citry_component_prefix, is_dynamic_target_expr_attr,
    is_dynamic_target_static_attr, is_html_void_element, is_reserved_citry_tag_identity,
    CLIENT_PROPS_ATTR, CONTROL_FLOW_GROUPS, CONTROL_FLOW_TAGS, C_COMPONENT_TAG, C_ELEMENT_TAG,
    C_ELIF_TAG, C_ELSE_TAG, C_EMPTY_TAG, C_FILL_TAG, C_FOR_TAG, C_IF_TAG, C_RAW_TAG, C_SLOT_TAG,
    DYNAMIC_CLIENT_PROPS_ATTR, FORBIDDEN_HTML_TAG_NAMES, META_ATTR_IGNORE, META_ATTR_KEY,
    RESERVED_TAG_NAMES, TAG_ATTR_RULES, TAG_ORDERING_RULES,
};
use crate::error::{assert_rule, assert_rules, ParseError};
use crate::grammar::{GrammarParser, Rule};
use crate::lang::lang::{ForLoopVars, Lang, LangImpl};
use crate::lang::python::PYTHON_LANG;
use crate::parser_context::{ParserContext, TagRules};
use crate::utils::pest::unwrap_pair;
use crate::utils::template_fragment::template_fragment;

/// Result of processing an HTML tag
enum HtmlTagResult {
    /// Start tag - Will start new layer in stack. Carries the variables the tag
    /// introduces into its body scope and slots declared by nested-template
    /// attributes (computed alongside attribute enrichment).
    StartTag(ProcessedStartTag),
    /// End tag - Will close current layer in stack
    EndTag(HtmlEndTag),
    /// Self-closing tag - Will be added to current layer in stack
    /// without changing the stack.
    SelfClosing(Node, Vec<StaticNamedSlot>),
}

/// Private parser data produced while processing a start tag.
struct ProcessedStartTag {
    start_tag: HtmlStartTag,
    introduced_variables: Vec<Token>,
    attribute_slots: Vec<StaticNamedSlot>,
}

/// Parsed attributes plus slots declared inside their nested-template values.
struct ParsedHtmlAttributes {
    attrs: Vec<HtmlAttr>,
    slots: Vec<StaticNamedSlot>,
}

/// A parsed attribute and metadata that belongs to its containing template.
struct ParsedHtmlAttribute {
    attr: HtmlAttr,
    slots: Vec<StaticNamedSlot>,
}

/// Stack entry for tracking open HTML tags with bodies
///
/// This has the same fields as `Node::WithBody`, except for the `end_tag`
struct TagStackEntry {
    /// The start tag with attributes
    start_tag: HtmlStartTag,
    /// The body content (template elements inside the tag)
    body: Template,
    /// Variables this tag introduces into its body scope (loop targets for
    /// `c-for`, slot data/fallback for `c-fill`), computed once when the start
    /// tag is processed and carried here until the node is finalized at its end
    /// tag.
    introduced_variables: Vec<Token>,
    /// Slots declared inside nested-template attributes on the start tag.
    attribute_slots: Vec<StaticNamedSlot>,
}

/// Parse a complete template into a Template AST
///
/// **Arguments**
/// * `input` - The template string to parse
/// * `lang` - Optional language implementation - Specifies which language to use
///            for parsing expressions (e.g. Python, PHP, JS, ...).
///            Default is Python.
/// * `user_rules` - Optional user-defined validation rules
///
/// This is the V3 parser that supports HTML-compatible templates with:
/// - HTML tags and components (`<c-*>`)
/// - Template expressions `{{ ... }}`
/// - Template comments `{# ... #}`
/// - HTML comments `<!-- ... -->`
/// - `c-*` attributes for dynamic behavior
pub fn parse_template(
    input: &str,
    lang: Option<Lang>,
    user_rules: Option<&Rc<HashMap<String, TagRules>>>,
) -> Result<Template, ParseError> {
    // Resolve the language enum to an Rc<dyn LangImpl>
    let lang_impl = lang.unwrap_or(Lang::Python).to_lang_impl();
    parse_template_with_custom_lang(input, Some(&lang_impl), user_rules)
}

/// Parse a complete template into a Template AST with a custom language implementation.
///
/// This is same as `parse_template()`, but allows you to specify a custom language implementation,
/// instead of using pre-defined enum values.
///
/// **Arguments**
/// * `input` - The template string to parse
/// * `lang` - Optional language implementation - Specifies which language to use
///            for parsing expressions (e.g. Python, PHP, JS, ...)
///            Default is Python.
/// * `user_rules` - Optional user-defined validation rules
///
/// This is the V3 parser that supports HTML-compatible templates with:
/// - HTML tags and components (`<c-*>`)
/// - Template expressions `{{ ... }}`
/// - Template comments `{# ... #}`
/// - HTML comments `<!-- ... -->`
/// - `c-*` attributes for dynamic behavior
pub fn parse_template_with_custom_lang(
    input: &str,
    lang: Option<&Rc<dyn LangImpl>>,
    user_rules: Option<&Rc<HashMap<String, TagRules>>>,
) -> Result<Template, ParseError> {
    // NOTE: This function accepts references of Rc's to avoid consuming the Rc instances.
    // But if we receive None, we have to create a new Rc instance.
    // Thus we also clone the Rc internally, so that in both Some/None cases we end up
    // owning the Rc instances.
    let lang = lang
        .map(Rc::clone)
        .unwrap_or_else(|| Lang::Python.to_lang_impl());
    let rules = user_rules
        .map(Rc::clone)
        .unwrap_or_else(|| Rc::new(HashMap::new()));

    let context = ParserContext::for_source(input, &lang, &rules);
    parse_template_inner(input, &context)
}

/// Internal method to parse a template with a context that may have offsets
/// This is also used when parsing a nested template string,
/// e.g. `c-body="<>Hello {{ name }}<>"` or `c-body="<div>Hello {{ name }}</div>"`.
fn parse_template_inner(input: &str, context: &ParserContext) -> Result<Template, ParseError> {
    // Handle empty input early
    if input.is_empty() {
        return Ok(Template {
            elements: vec![],
            comments: vec![],
            used_variables: vec![],
            slots: vec![],
        });
    }

    let mut pairs = GrammarParser::parse(Rule::template, input)
        .map_err(|error| context.error_from_pest(error, "Failed to parse template: "))?;

    // Stack for tracking open HTML tags with bodies
    let mut tag_stack: Vec<TagStackEntry> = Vec::new();

    // There should be only one top-level template
    let template_pair = pairs
        .next()
        .ok_or_else(|| context.error_from_absolute_source("Template is empty".to_string()))?;
    assert_rule(&template_pair, Rule::template)?;

    // template -> template_element*
    let template_elements_with_comments = template_pair.into_inner();

    // Filter out template_elements whose child is a template_comment
    let (template_element_pairs, template_comments) =
        context.extract_comments_from_pairs(template_elements_with_comments)?;

    // Root template being built
    let mut root_template = Template {
        elements: vec![],
        comments: template_comments,
        used_variables: vec![],
        slots: vec![],
    };

    for template_element_pair in template_element_pairs {
        // Skip EOI (End Of Input) marker
        if template_element_pair.as_rule() == Rule::EOI {
            continue;
        }
        assert_rule(&template_element_pair, Rule::template_element)?;

        // Process the element
        process_template_element(
            template_element_pair,
            &mut tag_stack,
            &mut root_template,
            context,
        )?;
    }

    // Check for unclosed tags on the stack
    if !tag_stack.is_empty() {
        let last_unclosed_entry = tag_stack.last().unwrap();
        let last_unclosed_tag_name = &last_unclosed_entry.start_tag.name.content;
        return Err(context.error_from_token(
            &last_unclosed_entry.start_tag.token,
            format!(
                "Unclosed tag <{}>: expected </{}> before end of template",
                last_unclosed_tag_name, last_unclosed_tag_name
            ),
        ));
    }

    // Construction-time metadata is necessarily local. Recompute free
    // variables from the completed tree so loop/fill bindings mask only their
    // lexical bodies, then validate the no-shadow contract top-down.
    recompute_template_used_variables(&mut root_template);
    validate_template_variable_shadowing(&root_template, context)?;

    Ok(root_template)
}

fn process_template_element(
    element_pair: pest::iterators::Pair<Rule>,
    tag_stack: &mut Vec<TagStackEntry>,
    root_template: &mut Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    // template_element -> html_comment | html_directive | html_processing_instruction | html_tag
    //                     | template_expression | template_comment | text
    let element_span = element_pair.as_span();
    let inner = element_pair.into_inner().next().ok_or_else(|| {
        context.error_from_local_span(
            element_span,
            "template_element should always have an inner rule".to_string(),
        )
    })?;
    let inner_rule = inner.as_rule();

    match inner_rule {
        // HTML comments: treat as Text but also add as comment
        Rule::html_comment => {
            let template = get_current_template(tag_stack, root_template);
            let (text, comment) = process_html_comment(inner, context)?;
            template.elements.push(TemplateElement::Text(text));
            template.comments.push(comment);
        }
        // Template comments: NOT added as Text, only captured as comments
        Rule::template_comment => {
            let template = get_current_template(tag_stack, root_template);
            let comment = process_template_comment(inner, context)?;
            template.comments.push(comment);
        }
        // All of these are treated as plain text
        Rule::html_directive | Rule::html_processing_instruction | Rule::text => {
            let template = get_current_template(tag_stack, root_template);
            let text = process_text(inner, context)?;
            template.elements.push(TemplateElement::Text(text));
        }
        Rule::html_raw => {
            let template = get_current_template(tag_stack, root_template);
            let node = process_html_raw(inner, context)?;
            template.elements.push(TemplateElement::Node(node));
        }
        Rule::html_text_container => {
            let (node, attribute_slots) = process_html_text_container(inner, context)?;
            finalize_node(node, attribute_slots, tag_stack, root_template, context)?;
        }
        Rule::template_expression => {
            let template = get_current_template(tag_stack, root_template);
            let expr = process_template_expression(inner, context)?;
            // Propagate upwards
            template.used_variables.extend(expr.used_variables.clone());
            template.comments.extend(expr.comments.clone());
            template.elements.push(TemplateElement::Expr(expr));
        }
        Rule::html_tag => {
            // Handle HTML tags (start/end/self-closing)
            let tag_span = inner.as_span();
            let tag_result = process_html_tag(inner, context)?;
            match tag_result {
                // Push as body element of the current layer
                HtmlTagResult::SelfClosing(node, attribute_slots) => {
                    finalize_node(node, attribute_slots, tag_stack, root_template, context)?;
                }
                // Create new layer in the stack (unless it's a void element)
                HtmlTagResult::StartTag(ProcessedStartTag {
                    start_tag,
                    introduced_variables,
                    attribute_slots,
                }) => {
                    // Check if this is an HTML void element (br, img, input, etc.)
                    // These don't need closing tags and are treated as self-closing
                    let tag_name = start_tag.name.content.as_str();
                    if is_html_void_element(tag_name) {
                        // Collect used_variables from attrs, dropping any
                        // same-element introduced var (shorthand `c-for` loop
                        // target), mirroring the bodied/self-closing paths.
                        let used_variables = remove_introduced_variables(
                            start_tag
                                .attrs
                                .iter()
                                .flat_map(|attr| attr.used_variables.clone())
                                .collect(),
                            &introduced_variables,
                        );
                        // Treat void element as self-closing
                        let node = Node::SelfClosing {
                            used_variables,
                            comments: start_tag.comments.clone(),
                            start_tag,
                            introduced_variables,
                            contains_fills: false,
                        };
                        finalize_node(node, attribute_slots, tag_stack, root_template, context)?;
                    } else {
                        let body = Template {
                            elements: vec![],
                            comments: vec![],
                            used_variables: vec![],
                            slots: vec![],
                        };
                        tag_stack.push(TagStackEntry {
                            start_tag,
                            body,
                            introduced_variables,
                            attribute_slots,
                        });
                    }
                }
                // Close current layer in the stack
                HtmlTagResult::EndTag(end_tag) => {
                    let end_tag_name = &end_tag.name.content;

                    // Check if tag stack is empty
                    if tag_stack.is_empty() {
                        return Err(context.error_from_local_span(
                            tag_span,
                            format!(
                                "Unexpected closing tag '</{}>': no matching opening tag",
                                end_tag_name
                            ),
                        ));
                    }

                    // Check if end tag matches the current stack entry
                    let stack_entry = tag_stack.last().unwrap();
                    if !stack_entry
                        .start_tag
                        .name
                        .content
                        .eq_ignore_ascii_case(end_tag_name)
                    {
                        return Err(context.error_from_local_span(
                            tag_span,
                            format!(
                                "Mismatched tags: expected closing tag '</{}>', found '</{}>'",
                                stack_entry.start_tag.name.content, end_tag_name
                            ),
                        ));
                    }

                    // Pop current layer from stack
                    let TagStackEntry {
                        start_tag,
                        body,
                        introduced_variables,
                        attribute_slots,
                    } = tag_stack.pop().unwrap();

                    // `introduced_variables` was computed when the start tag was
                    // processed (see process_control_flow_metadata).
                    let node = Node::from_start_and_end_tags(
                        start_tag,
                        end_tag,
                        body,
                        introduced_variables,
                    );

                    finalize_node(node, attribute_slots, tag_stack, root_template, context)?;
                }
            }
        }
        _ => {
            return Err(context.error_from_local_span(
                inner.as_span(),
                format!("Unexpected template element rule: {:?}", inner_rule),
            ));
        }
    }
    Ok(())
}

/// Logic that runs when we construct a Node (either from SelfClosing, or finished with bodied Node).
fn finalize_node(
    mut node: Node,
    attribute_slots: Vec<StaticNamedSlot>,
    tag_stack: &mut [TagStackEntry],
    root_template: &mut Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    // Extract fill nodes and determine contains_fills
    let fill_nodes = match &node {
        Node::WithBody { body, .. } => extract_fill_nodes(body, false, false),
        Node::SelfClosing { .. } => vec![],
    };
    let contains_fills = !fill_nodes.is_empty();

    validate_node(&node, &fill_nodes, tag_stack, context)?;
    let parent_template = get_current_template(tag_stack, root_template);
    validate_node_against_parent(&node, parent_template, context)?;

    // Let components know how to handle body based on whether it contains fills
    node.set_contains_fills(contains_fills);

    // Extract slot if this is a <c-slot> tag
    if let Some(slot) = extract_slot_from_node(&node) {
        parent_template.slots.push(slot);
    }

    // Attribute values are authored before the body, so preserve that order
    // when carrying their statically named slots into the containing template.
    parent_template.slots.extend(attribute_slots);

    // Propagate slots from body upwards (if node has body)
    if let Node::WithBody { body, .. } = &node {
        parent_template.slots.extend(body.slots.clone());
    }

    // Propagate upwards
    parent_template.comments.extend(node.comments().clone());
    parent_template
        .used_variables
        .extend(node.used_variables().clone());
    parent_template.elements.push(TemplateElement::Node(node));

    Ok(())
}

/// Convert text pair to Text
fn process_text(
    text_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<Text, ParseError> {
    let token = context.create_token(&text_pair);
    Ok(Text { token })
}

/// Convert template comment pair to Comment
fn process_template_comment(
    comment_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<Comment, ParseError> {
    let token = context.create_token(&comment_pair);

    // Extract the content (without {# and #})
    // template_comment = "{#" ~ template_comment_content ~ "#}"
    // In a native text-container body's atomicity cascade Pest may suppress
    // the inner pair even though it keeps the outer template_comment pair.
    // The ASCII delimiters make the equivalent token safe to derive from the
    // already absolute outer token in that case.
    let value_token = match comment_pair.into_inner().next() {
        Some(template_comment_content) => {
            assert_rule(&template_comment_content, Rule::template_comment_content)?;
            context.create_token(&template_comment_content)
        }
        None => Token {
            content: token.content[2..token.content.len() - 2].to_string(),
            start_index: token.start_index + 2,
            end_index: token.end_index - 2,
            line_col: (token.line_col.0, token.line_col.1 + 2),
        },
    };

    Ok(Comment {
        token,
        value: value_token,
    })
}

/// Convert html_comment pair to Text and Comment
fn process_html_comment(
    comment_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<(Text, Comment), ParseError> {
    // html_comment = "<!--" ~ html_comment_content ~ "-->"
    let token = context.create_token(&comment_pair);

    // Extract the content (without <!-- and -->)
    let comment_content = unwrap_pair(comment_pair, Rule::html_comment_content)?;
    let value_token = context.create_token(&comment_content);

    let comment = Comment {
        token: token.clone(),
        value: value_token,
    };
    let text = Text { token };

    Ok((text, comment))
}

/// Convert template_expression pair to Expr
fn process_template_expression(
    expr_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<Expr, ParseError> {
    let expr_token = context.create_token(&expr_pair);
    let expr_span = expr_pair.as_span();

    // template_expression -> "{{" ~ WHITESPACE ~ python_expr ~ WHITESPACE ~ "}}"
    // Filter out WHITESPACE
    // NOTE: Not collecting comments in context because template comments are not allowed inside {{ ... }}.
    let (mut filtered_pairs, template_comments) =
        context.extract_comments_from_pairs(expr_pair.into_inner())?;

    // Find expression_content - It should be the only non-comment, non-spacing pair
    let python_expr_pair = filtered_pairs.next().ok_or_else(|| {
        context.error_from_local_span(
            expr_span,
            "python_expr should contain python_expr".to_string(),
        )
    })?;

    // Extract the value token (the content inside {{ ... }})
    let value_span = python_expr_pair.as_span();
    let value_token = context.create_token(&python_expr_pair);

    let (used_variables, python_comments) =
        process_expression(&value_token, Some(value_span), context)?;

    let mut comments = template_comments.clone();
    comments.extend(python_comments);

    Ok(Expr {
        token: expr_token,
        value: value_token,
        used_variables,
        comments,
    })
}

/// Process an expression using the language-specific implementation from the context.
fn process_expression(
    value_token: &Token,
    value_span: Option<pest::Span>,
    context: &ParserContext,
) -> Result<(Vec<Token>, Vec<Comment>), ParseError> {
    let transform_result = context
        .lang
        .parse_expression(&value_token.content)
        .map_err(|e| {
            let message = format!("Failed to parse expression: {}", e);
            if let Some(value_span) = value_span {
                context.error_from_local_span(value_span, message)
            } else {
                context.error_from_token(value_token, message)
            }
        })?;

    // Calculate offsets for adjusting token positions
    let index_offset = value_token.start_index;
    let (value_line, value_col) = value_token.line_col;
    // line_offset: value_line - 1 (because lines are 1-indexed)
    let line_offset = value_line - 1;
    // col_offset: value_col - 1 (because cols are 1-indexed)
    let col_offset = value_col - 1;

    let used_vars: Vec<Token> = transform_result
        .used_vars
        .into_iter()
        .map(|token| token.offset(index_offset, line_offset, col_offset))
        .collect();

    let comments: Vec<Comment> = transform_result
        .comments
        .into_iter()
        .map(|comment| Comment {
            token: comment.token.offset(index_offset, line_offset, col_offset),
            value: comment.value.offset(index_offset, line_offset, col_offset),
        })
        .collect();

    Ok((used_vars, comments))
}

/// Process a nested template string to extract nested template tags
fn process_template_string(
    template_token: &Token,
    parent_context: &ParserContext,
) -> Result<Template, ParseError> {
    let content = &template_token.content;

    // Tokens created by ParserContext already carry root-absolute coordinates.
    // Use that absolute origin directly: adding the parent's offsets again
    // would double-count every recursive template-attribute level.
    let (line, col) = template_token.line_col;
    let new_line_offset = line - 1;
    let new_col_offset = col - 1;
    let new_index_offset = template_token.start_index;

    let nested_context =
        parent_context.create_child_context(new_line_offset, new_col_offset, new_index_offset);

    // Parse the content as a template with updated offsets
    let template = parse_template_inner(content, &nested_context)?;
    Ok(template)
}

/// Process an HTML tag (start, end, or self-closing)
fn process_html_tag(
    tag_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<HtmlTagResult, ParseError> {
    // html_tag -> html_start_tag | html_end_tag | html_self_closing_tag
    let tag_span = tag_pair.as_span();
    let inner = tag_pair.into_inner().next().ok_or_else(|| {
        context.error_from_local_span(
            tag_span,
            "html_tag should contain a start, end, or self-closing tag".to_string(),
        )
    })?;
    let inner_rule = inner.as_rule();

    match inner_rule {
        Rule::html_start_tag => {
            let processed_start_tag = process_html_start_tag(inner, context)?;
            Ok(HtmlTagResult::StartTag(processed_start_tag))
        }
        Rule::html_end_tag => {
            let end_tag = process_html_end_tag(inner, context)?;
            Ok(HtmlTagResult::EndTag(end_tag))
        }
        Rule::html_self_closing_tag => {
            let (node, attribute_slots) = process_html_self_closing_tag(inner, context)?;
            Ok(HtmlTagResult::SelfClosing(node, attribute_slots))
        }
        _ => Err(context.error_from_local_span(
            inner.as_span(),
            format!("Unexpected HTML tag rule: {:?}", inner_rule),
        )),
    }
}

/// Process html_start_tag pair into HtmlStartTag
fn process_html_start_tag(
    start_tag_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<ProcessedStartTag, ParseError> {
    // html_start_tag = "<" ~ html_tag_name ~ (spacing_with_whitespace ~ html_attribute)* ~ spacing* ~ ">"
    let start_tag_span = start_tag_pair.as_span();
    let start_tag_token = context.create_token(&start_tag_pair);

    // Extract comments from spacing/spacing_with_whitespace pairs,
    // filtering them out and keeping only meaningful pairs (tag name, attributes).
    let (mut filtered_pairs, comments) =
        context.extract_comments_from_pairs(start_tag_pair.into_inner())?;

    // Get tag name
    let name_pair = filtered_pairs.next().ok_or_else(|| {
        context.error_from_local_span(
            start_tag_span,
            "html_start_tag should contain html_tag_name".to_string(),
        )
    })?;
    // Accept ordinary, <c-raw>, and native text-container tag-name rules.
    assert_rules(
        &name_pair,
        &[
            Rule::html_tag_name,
            Rule::html_raw_tag_name,
            Rule::html_script_tag_name,
            Rule::html_style_tag_name,
            Rule::html_textarea_tag_name,
            Rule::html_title_tag_name,
        ],
    )?;

    let name = context.create_token(&name_pair);
    let name_rule = name_pair.as_rule();

    // Check if this is a forbidden tag name (skip for html_raw_tag_name which is expected)
    if name_rule == Rule::html_tag_name && FORBIDDEN_HTML_TAG_NAMES.contains(&name.content.as_str())
    {
        return Err(context.error_from_local_span(
            name_pair.as_span(),
            format!(
                "Tag name '{}' is reserved and cannot be used as a regular HTML tag. Use the special syntax instead.",
                name.content
            ),
        ));
    }

    // Parse attributes from the remaining filtered pairs
    let ParsedHtmlAttributes {
        mut attrs,
        slots: attribute_slots,
    } = parse_html_attributes(filtered_pairs, context)?;

    // Enrich control-flow attributes and compute the variables this tag
    // introduces, in one pass (see process_control_flow_metadata).
    let introduced_variables =
        process_control_flow_metadata(&name.content, &start_tag_token, &mut attrs, context)?;

    let start_tag = HtmlStartTag {
        token: start_tag_token,
        name,
        attrs,
        is_self_closing: false,
        comments,
    };

    Ok(ProcessedStartTag {
        start_tag,
        introduced_variables,
        attribute_slots,
    })
}

/// Process an HTML end tag: validates and returns the end tag
/// The caller should pop from stack and use the popped data along with this end_tag
fn process_html_end_tag(
    end_tag_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<HtmlEndTag, ParseError> {
    // html_end_tag = "</" ~ html_tag_name ~ (spacing_with_whitespace ~ html_attribute)* ~ spacing* ~ ">"
    let end_tag_span = end_tag_pair.as_span();
    let end_tag_rule = end_tag_pair.as_rule();
    let end_tag_token = context.create_token(&end_tag_pair);

    // Extract comments from spacing/spacing_with_whitespace pairs,
    // filtering them out and keeping only meaningful pairs (tag name, attributes).
    let (mut filtered_pairs, comments) =
        context.extract_comments_from_pairs(end_tag_pair.into_inner())?;

    // Get tag name
    let name_pair = filtered_pairs.next().ok_or_else(|| {
        context.error_from_local_span(
            end_tag_span,
            format!("{:?} should contain tag name", end_tag_rule),
        )
    })?;
    assert_rules(
        &name_pair,
        &[
            Rule::html_tag_name,
            Rule::html_raw_tag_name,
            Rule::html_script_tag_name,
            Rule::html_style_tag_name,
            Rule::html_textarea_tag_name,
            Rule::html_title_tag_name,
        ],
    )?;

    let name = context.create_token(&name_pair);
    let name_rule = name_pair.as_rule();

    // Check if this is a forbidden tag name (skip for html_raw_tag_name which is expected)
    if name_rule == Rule::html_tag_name && FORBIDDEN_HTML_TAG_NAMES.contains(&name.content.as_str())
    {
        return Err(context.error_from_local_span(
            name_pair.as_span(),
            format!(
                "Tag name '{}' is reserved and cannot be used as a regular HTML tag. Use the special syntax instead.",
                name.content
            ),
        ));
    }

    // Check if end tag has any attributes, and raise error if so.
    // After comment extraction, only html_attribute pairs remain.
    let next_attr_pair = filtered_pairs.next();
    if let Some(attr_pair) = next_attr_pair {
        let attr_span = attr_pair.as_span();
        return Err(context.error_from_local_span(
            attr_span,
            format!("{:?} must not contain any attributes", end_tag_rule),
        ));
    }

    let end_tag = HtmlEndTag {
        token: end_tag_token,
        name,
        comments,
    };

    Ok(end_tag)
}

/// Process a self-closing HTML tag: create Node::SelfClosing
fn process_html_self_closing_tag(
    self_closing_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<(Node, Vec<StaticNamedSlot>), ParseError> {
    // html_self_closing_tag = "<" ~ html_tag_name ~ (spacing_with_whitespace ~ html_attribute)* ~ spacing* ~ "/" ~ ">"
    let self_closing_span = self_closing_pair.as_span();
    let self_closing_token = context.create_token(&self_closing_pair);

    // Extract comments from spacing/spacing_with_whitespace pairs,
    // filtering them out and keeping only meaningful pairs (tag name, attributes).
    let (mut filtered_pairs, comments_from_tag) =
        context.extract_comments_from_pairs(self_closing_pair.into_inner())?;

    // Get tag name
    let name_pair = filtered_pairs.next().ok_or_else(|| {
        context.error_from_local_span(
            self_closing_span,
            "html_self_closing_tag should contain html_tag_name".to_string(),
        )
    })?;
    assert_rule(&name_pair, Rule::html_tag_name)?;
    let name = context.create_token(&name_pair);

    // Check if this is a forbidden tag name
    if FORBIDDEN_HTML_TAG_NAMES.contains(&name.content.as_str()) {
        return Err(context.error_from_local_span(
            name_pair.as_span(),
            format!(
                "Tag name '{}' is reserved and cannot be used as a regular HTML tag. Use the special syntax instead.",
                name.content
            ),
        ));
    }

    // Parse attributes from the remaining filtered pairs
    let ParsedHtmlAttributes {
        mut attrs,
        slots: attribute_slots,
    } = parse_html_attributes(filtered_pairs, context)?;

    // Enrich control-flow attributes and compute the introduced variables in one
    // pass (see process_control_flow_metadata).
    let introduced_variables =
        process_control_flow_metadata(&name.content, &self_closing_token, &mut attrs, context)?;

    // A same-element introduced variable (a shorthand `c-for` loop target) is
    // bound for this node's own attributes, so it is removed from used_variables
    // just as the bodied path does (ast::from_start_and_end_tags). Without this,
    // `<path c-for="p in items" c-bind="p" />` would report `p` as both used and
    // introduced and trip the shadowing check.
    let used_variables = remove_introduced_variables(
        attrs
            .iter()
            .flat_map(|attr| attr.used_variables.clone())
            .collect(),
        &introduced_variables,
    );
    let comments_from_attrs = attrs.iter().flat_map(|attr| attr.comments.clone());
    let mut comments: Vec<Comment> = comments_from_tag.clone();
    comments.extend(comments_from_attrs);

    let start_tag = HtmlStartTag {
        token: self_closing_token,
        name,
        attrs,
        is_self_closing: true,
        comments: comments_from_tag,
    };

    Ok((
        Node::SelfClosing {
            start_tag,
            used_variables,
            introduced_variables,
            comments,
            contains_fills: false, // Self-closing nodes never have fills
        },
        attribute_slots,
    ))
}

/// Parse HTML attributes from Pest pairs
fn parse_html_attributes<'a>(
    attrs_pairs: impl Iterator<Item = pest::iterators::Pair<'a, Rule>>,
    context: &ParserContext,
) -> Result<ParsedHtmlAttributes, ParseError> {
    let mut attrs = Vec::new();
    let mut slots = Vec::new();

    // Collect all html_attribute pairs, skipping spacing
    for attr_pair in attrs_pairs {
        // Skip spacing_with_whitespace and spacing rules
        // These are generated because HTML tag rules are compound-atomic (${ })
        let rule = attr_pair.as_rule();
        if rule == Rule::spacing_with_whitespace || rule == Rule::spacing {
            continue;
        }

        let ParsedHtmlAttribute {
            attr,
            slots: attr_slots,
        } = parse_html_attribute(attr_pair, context)?;
        attrs.push(attr);
        slots.extend(attr_slots);
    }

    Ok(ParsedHtmlAttributes { attrs, slots })
}

/// Parse a single html_attribute into HtmlAttr
fn parse_html_attribute(
    attr_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<ParsedHtmlAttribute, ParseError> {
    assert_rule(&attr_pair, Rule::html_attribute)?;

    let attr_token = context.create_token(&attr_pair);
    let attr_span = attr_pair.as_span();

    // html_attribute = html_attribute_name ~ html_attribute_value?
    let mut inner: pest::iterators::Pairs<Rule> = attr_pair.into_inner();

    // Get attribute name. The grammar routes `#c-*` names to their own rule
    // (html_meta_attribute_name), so the framework-metadata channel is told
    // apart from ordinary attributes here by rule, not by string matching.
    let name_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            attr_span,
            "html_attribute should contain html_attribute_name".to_string(),
        )
    })?;
    assert_rules(
        &name_pair,
        &[Rule::html_attribute_name, Rule::html_meta_attribute_name],
    )?;
    let is_meta = name_pair.as_rule() == Rule::html_meta_attribute_name;
    let name_span = name_pair.as_span();
    let key = context.create_token(&name_pair);

    // Get attribute value (optional)
    let maybe_value_pair = inner.next();
    // html_attribute_value = (double_quoted_value | single_quoted_value | unquoted_value)
    let maybe_value_content_pair = maybe_value_pair.map(
        |pair| {
            let pair_span = pair.as_span();
            pair.into_inner().next().ok_or_else(|| {
                context.error_from_local_span(
                    pair_span,
                    "html_attribute_value should contain double_quoted_value, single_quoted_value, or unquoted_value".to_string(),
                )
            })
        }
    ).transpose()?;

    let (value, inner_value, quote_char) = match maybe_value_content_pair {
        // Quoted attribute, e.g. `key="value"` or `key='value'`
        Some(pair) if pair.as_rule() == Rule::double_quoted_value => {
            let value_token = context.create_token(&pair);
            let expr_token = value_token.clone().crop_cols(1, -1);
            (Some(value_token), Some(expr_token), Some('"'))
        }
        Some(pair) if pair.as_rule() == Rule::single_quoted_value => {
            let value_token = context.create_token(&pair);
            let expr_token = value_token.clone().crop_cols(1, -1);
            (Some(value_token), Some(expr_token), Some('\''))
        }
        // Unquoted attribute, e.g. `key=value`
        Some(pair) if pair.as_rule() == Rule::unquoted_value => {
            let value_token = context.create_token(&pair);
            let expr_token = value_token.clone();
            (Some(value_token), Some(expr_token), None)
        }
        // Boolean attribute (no value), e.g. `key`
        None => (None, None, None),
        Some(other) => {
            let value_span = other.as_span();
            return Err(context.error_from_local_span(
                value_span,
                format!(
                    "Expected double_quoted_value, single_quoted_value, or unquoted_value, got {:?}",
                    other
                ),
            ));
        }
    };

    // `c-else` and `c-empty` are presence-only branch markers. Accepting a
    // value here would silently discard it during control-flow lowering.
    if matches!(key.content.as_str(), C_ELSE_TAG | C_EMPTY_TAG) && inner_value.is_some() {
        return Err(context.error_from_local_span(
            attr_span,
            format!(
                "'{}' takes no value. Write it as a bare control-flow marker.",
                key.content
            ),
        ));
    }

    // Determine attribute kind based on key name and value
    // Clone inner_value since we need it later for HtmlAttr, but also need to use it for processing
    let inner_value_for_attr = inner_value.clone();
    let (kind, used_variables, comments, slots) = if is_meta {
        // Framework-metadata channel (`#c-*`). Exactly two members exist, and
        // an unknown name is an authoring mistake, so the error lists both.
        match key.content.as_str() {
            META_ATTR_KEY => {
                // `#c-key` holds a server-evaluated expression, riding the same
                // expression machinery as a `c-*` attribute value. A key is
                // always an expression, never a nested template, so there is no
                // template-value detection here.
                let has_expression = inner_value
                    .as_ref()
                    .is_some_and(|v| !v.content.trim().is_empty());
                if !has_expression {
                    return Err(context.error_from_local_span(
                        attr_span,
                        format!(
                            "'{}' must have an expression value whose result is the node's key, e.g. {}=\"item.id\".",
                            META_ATTR_KEY, META_ATTR_KEY
                        ),
                    ));
                }
                let (used_variables, comments) =
                    process_expression(inner_value.as_ref().unwrap(), None, context)?;
                (HtmlAttrKind::Meta, used_variables, comments, Vec::new())
            }
            META_ATTR_IGNORE => {
                // `#c-ignore` is a bare marker by design; a value (even an
                // empty one) has no meaning and is rejected rather than
                // silently dropped.
                if inner_value.is_some() {
                    return Err(context.error_from_local_span(
                        attr_span,
                        format!(
                            "'{}' takes no value. Write the bare marker ('{}') to opt the element subtree or component range out of morphing.",
                            META_ATTR_IGNORE, META_ATTR_IGNORE
                        ),
                    ));
                }
                (HtmlAttrKind::Meta, Vec::new(), Vec::new(), Vec::new())
            }
            other => {
                return Err(context.error_from_local_span(
                    name_span,
                    format!(
                        "Unknown '#c-*' attribute '{}'. The '#c-*' channel is reserved for framework metadata about the node, and has exactly two members: '{}' and '{}'.",
                        other, META_ATTR_KEY, META_ATTR_IGNORE
                    ),
                ));
            }
        }
    } else if key.content.starts_with("c-") {
        // Check if it's a template attribute. Fragment delimiters must enclose
        // the whole value. Otherwise the grammar, rather than a duplicate tag
        // name character whitelist, decides whether the final item is a real
        // closing, self-closing, raw, or HTML void tag.
        let (is_fragment, is_template) = inner_value
            .as_ref()
            .map(|inner_value| {
                let is_fragment = template_fragment(&inner_value.content).is_some();
                (
                    is_fragment,
                    is_fragment || is_tag_bounded_nested_template(&inner_value.content),
                )
            })
            .unwrap_or((false, false));

        if is_template {
            if matches!(key.content.as_str(), C_IF_TAG | C_ELIF_TAG) {
                return Err(context.error_from_local_span(
                    attr_span,
                    format!(
                        "'{}' condition must be an expression; template values are not allowed.",
                        key.content
                    ),
                ));
            }
            if key.content == C_FOR_TAG {
                return Err(context.error_from_local_span(
                    attr_span,
                    "'c-for' must contain a for-loop clause expression; template values are not allowed."
                        .to_string(),
                ));
            }

            // c-... attribute WITH nested template value.
            // If fragment, strip the <> and </> delimiters (and surrounding whitespace)
            // before parsing the inner content as a template.
            let template = if is_fragment {
                let iv = inner_value.as_ref().unwrap();
                let content = &iv.content;
                let fragment = template_fragment(content)
                    .expect("is_fragment is true only when fragment delimiters were found");
                let start_skip = fragment.inner_start as isize;
                let end_skip = -((content.len() - fragment.inner_end) as isize);
                let fragment_inner = iv.clone().crop_cols(start_skip, end_skip);
                process_template_string(&fragment_inner, context)?
            } else {
                process_template_string(inner_value.as_ref().unwrap(), context)?
            };
            let nested_bindings = collect_template_binding_tokens(&template, context);
            context.record_nested_template_bindings(&attr_token, nested_bindings);
            let comments = template.comments.clone();
            let used_variables = template.used_variables.clone();
            let slots = template.slots;
            (HtmlAttrKind::Template, used_variables, comments, slots)
        } else {
            // c-... attribute WITH expression value
            if let Some(ref inner_value_ref) = inner_value {
                let (used_variables, comments) =
                    process_expression(inner_value_ref, None, context)?;
                (
                    HtmlAttrKind::Expression,
                    used_variables,
                    comments,
                    Vec::new(),
                )
            // c-... attribute WITHOUT value
            } else {
                (HtmlAttrKind::Expression, Vec::new(), Vec::new(), Vec::new())
            }
        }
    } else {
        // Non-prefixed attributes are static, e.g. `class="static_value"`
        (HtmlAttrKind::Static, Vec::new(), Vec::new(), Vec::new())
    };

    Ok(ParsedHtmlAttribute {
        attr: HtmlAttr {
            token: attr_token,
            key,
            value,
            inner_value: inner_value_for_attr,
            quote_char,
            kind,
            comments,
            used_variables,
            fill_data_pattern: None,
        },
        slots,
    })
}

/// Whether a dynamic attribute value is bounded by real HTML tags.
///
/// The opening check keeps ordinary expressions out of the template path. The
/// final boundary is taken from the Pest grammar so this classifier accepts
/// exactly the same tag-name alphabet as top-level templates and cannot mistake
/// trailing text ending in `/>` for a self-closing tag.
fn is_tag_bounded_nested_template(content: &str) -> bool {
    let trimmed = content.trim();
    let starts_with_tag = trimmed.len() >= 2
        && trimmed.starts_with('<')
        && trimmed.as_bytes()[1].is_ascii_alphabetic();
    if !starts_with_tag {
        return false;
    }

    let Ok(mut pairs) = GrammarParser::parse(Rule::template, trimmed) else {
        return false;
    };
    let Some(template_pair) = pairs.next() else {
        return false;
    };
    let Some(last_element) = template_pair
        .into_inner()
        .rfind(|pair| pair.as_rule() == Rule::template_element)
    else {
        return false;
    };
    let Some(last_inner) = last_element.into_inner().next() else {
        return false;
    };

    match last_inner.as_rule() {
        Rule::html_raw | Rule::html_text_container => true,
        Rule::html_tag => {
            let Some(tag) = last_inner.into_inner().next() else {
                return false;
            };
            match tag.as_rule() {
                Rule::html_end_tag | Rule::html_self_closing_tag => true,
                Rule::html_start_tag => tag
                    .into_inner()
                    .find(|pair| pair.as_rule() == Rule::html_tag_name)
                    .is_some_and(|name| is_html_void_element(name.as_str())),
                _ => false,
            }
        }
        _ => false,
    }
}

/// Process an html_raw tag: <c-raw>...</c-raw>
/// Returns a Node::WithBody with the raw content as a single Text element
fn process_html_raw(
    raw_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<Node, ParseError> {
    // html_raw = html_raw_start_tag ~ html_raw_content ~ html_raw_end_tag
    let raw_span = raw_pair.as_span();
    let mut inner = raw_pair.into_inner();

    // Get start tag
    let start_tag_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            raw_span,
            "html_raw should contain html_raw_start_tag".to_string(),
        )
    })?;
    assert_rule(&start_tag_pair, Rule::html_raw_start_tag)?;
    // `<c-raw>` allows no attributes, so it introduces no variables.
    let ProcessedStartTag {
        start_tag,
        introduced_variables: _,
        attribute_slots: _,
    } = process_html_start_tag(start_tag_pair, context)?;

    // Get content
    let content_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            raw_span,
            "html_raw should contain html_raw_content".to_string(),
        )
    })?;
    assert_rule(&content_pair, Rule::html_raw_content)?;

    // Treat content as text
    let content_text = Text {
        token: context.create_token(&content_pair),
    };
    let body = Template {
        elements: vec![TemplateElement::Text(content_text)],
        comments: vec![],
        used_variables: vec![],
        slots: vec![],
    };

    // Get end tag
    let end_tag_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            raw_span,
            "html_raw should contain html_raw_end_tag".to_string(),
        )
    })?;
    assert_rule(&end_tag_pair, Rule::html_raw_end_tag)?;
    let end_tag = process_html_end_tag(end_tag_pair, context)?;

    let node = Node::from_start_and_end_tags(start_tag, end_tag, body, vec![]);

    // `<c-raw>` allows no attributes. Validate here because raw nodes are pushed
    // directly to the template and bypass the normal `validate_node` path.
    // Citry-owned attribute channels get their pointed placement checks before
    // the generic no-attributes diagnostic.
    validate_client_props_placement(&node, context)?;
    validate_attributes_present(&node, context)?;
    validate_meta_attr_placement(&node, context)?;

    Ok(node)
}

/// Process a native HTML text container (`script`, `style`, `textarea`, or
/// `title`). Tag-looking body text stays text, while Citry expressions and
/// template comments retain their normal meaning.
fn process_html_text_container(
    container_pair: pest::iterators::Pair<Rule>,
    context: &ParserContext,
) -> Result<(Node, Vec<StaticNamedSlot>), ParseError> {
    let container_span = container_pair.as_span();
    let variant = container_pair.into_inner().next().ok_or_else(|| {
        context.error_from_local_span(
            container_span,
            "html_text_container should contain one tag-specific rule".to_string(),
        )
    })?;

    let (container_rule, start_rule, content_rule, end_rule, text_rule) = match variant.as_rule() {
        Rule::html_script => (
            Rule::html_script,
            Rule::html_script_start_tag,
            Rule::html_script_content,
            Rule::html_script_end_tag,
            Rule::html_script_text,
        ),
        Rule::html_style => (
            Rule::html_style,
            Rule::html_style_start_tag,
            Rule::html_style_content,
            Rule::html_style_end_tag,
            Rule::html_style_text,
        ),
        Rule::html_textarea => (
            Rule::html_textarea,
            Rule::html_textarea_start_tag,
            Rule::html_textarea_content,
            Rule::html_textarea_end_tag,
            Rule::html_textarea_text,
        ),
        Rule::html_title => (
            Rule::html_title,
            Rule::html_title_start_tag,
            Rule::html_title_content,
            Rule::html_title_end_tag,
            Rule::html_title_text,
        ),
        rule => {
            return Err(context.error_from_local_span(
                variant.as_span(),
                format!("Unexpected HTML text-container rule: {:?}", rule),
            ));
        }
    };
    assert_rule(&variant, container_rule)?;
    let variant_span = variant.as_span();
    let mut inner = variant.into_inner();

    let start_tag_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            variant_span,
            "HTML text container should contain a start tag".to_string(),
        )
    })?;
    assert_rule(&start_tag_pair, start_rule)?;
    let ProcessedStartTag {
        start_tag,
        introduced_variables,
        attribute_slots,
    } = process_html_start_tag(start_tag_pair, context)?;

    let content_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            variant_span,
            "HTML text container should contain a body".to_string(),
        )
    })?;
    assert_rule(&content_pair, content_rule)?;
    let mut body = Template {
        elements: vec![],
        comments: vec![],
        used_variables: vec![],
        slots: vec![],
    };
    for body_pair in content_pair.into_inner() {
        match body_pair.as_rule() {
            rule if rule == text_rule => {
                body.elements
                    .push(TemplateElement::Text(process_text(body_pair, context)?));
            }
            Rule::template_expression => {
                let expr = process_template_expression(body_pair, context)?;
                body.used_variables.extend(expr.used_variables.clone());
                body.comments.extend(expr.comments.clone());
                body.elements.push(TemplateElement::Expr(expr));
            }
            Rule::template_comment => {
                body.comments
                    .push(process_template_comment(body_pair, context)?);
            }
            rule => {
                return Err(context.error_from_local_span(
                    body_pair.as_span(),
                    format!("Unexpected HTML text-container body rule: {:?}", rule),
                ));
            }
        }
    }

    let end_tag_pair = inner.next().ok_or_else(|| {
        context.error_from_local_span(
            variant_span,
            "HTML text container should contain an end tag".to_string(),
        )
    })?;
    assert_rule(&end_tag_pair, end_rule)?;
    let end_tag = process_html_end_tag(end_tag_pair, context)?;

    Ok((
        Node::from_start_and_end_tags(start_tag, end_tag, body, introduced_variables),
        attribute_slots,
    ))
}

// Decide which template to push items to
fn get_current_template<'a>(
    tag_stack: &'a mut [TagStackEntry],
    root_template: &'a mut Template,
) -> &'a mut Template {
    if let Some(stack_entry) = tag_stack.last_mut() {
        &mut stack_entry.body
    } else {
        root_template
    }
}

// //////////////////////////////////////////////////////////
// VALIDATION
// //////////////////////////////////////////////////////////

/// Validate a Node, its attributes, and its children.
fn validate_node(
    node: &Node,
    fill_nodes: &[FillNodeInfo],
    tag_stack: &[TagStackEntry],
    context: &ParserContext,
) -> Result<(), ParseError> {
    validate_citry_tag_spelling(node, context)?;
    validate_fill_placement(node, tag_stack, context)?;
    validate_client_props_placement(node, context)?;
    validate_attributes_present(node, context)?;
    validate_meta_attr_placement(node, context)?;
    validate_attribute_conflicts(node, context)?;
    validate_attribute_values(node, context)?;
    validate_fill_names(node, fill_nodes, context)?;
    Ok(())
}

/// Enforce the boundary between Citry syntax and ordinary/custom HTML.
///
/// The framework prefix is exactly lowercase `c-`. Once that prefix is
/// present, component-name identity is ASCII-case-insensitive, but reserved
/// structural tags must be authored in their canonical lowercase spelling so
/// their grammar and execution semantics remain explicit.
fn validate_citry_tag_spelling(node: &Node, context: &ParserContext) -> Result<(), ParseError> {
    validate_citry_tag_name_spelling(&node.start_tag().name, false, context)?;
    if let Node::WithBody { end_tag, .. } = node {
        validate_citry_tag_name_spelling(&end_tag.name, true, context)?;
    }
    Ok(())
}

fn validate_citry_tag_name_spelling(
    name: &Token,
    is_closing: bool,
    context: &ParserContext,
) -> Result<(), ParseError> {
    let tag_name = name.content.as_str();
    let bytes = tag_name.as_bytes();
    let looks_like_citry_prefix =
        bytes.len() >= 2 && bytes[0].eq_ignore_ascii_case(&b'c') && bytes[1] == b'-';
    let slash = if is_closing { "/" } else { "" };

    if looks_like_citry_prefix && !has_citry_component_prefix(tag_name) {
        return Err(context.error_from_token(
            name,
            format!(
                "Citry component tag prefixes are lowercase. Write '<{}c-{}>' instead of '<{}{}>'.",
                slash,
                &tag_name[2..],
                slash,
                tag_name
            ),
        ));
    }

    if let Some(canonical) = RESERVED_TAG_NAMES
        .iter()
        .find(|reserved| tag_name.eq_ignore_ascii_case(reserved))
    {
        if tag_name != *canonical {
            return Err(context.error_from_token(
                name,
                format!(
                    "Reserved Citry structural tags are lowercase. Write '<{}{canonical}>' instead of '<{}{}>'.",
                    slash, slash, tag_name
                ),
            ));
        }
    }

    Ok(())
}

/// Validate the two authored forms of Citry's client props directive.
///
/// The direct form carries a browser expression as inert text. The
/// server-dynamic form evaluates Python and supplies that complete browser
/// expression. Both belong only on component call sites; `<c-element>` and
/// ordinary tags render plain HTML and cannot own the directive.
fn validate_client_props_placement(node: &Node, context: &ParserContext) -> Result<(), ParseError> {
    let tag_name = node.tag_name();
    let is_component_boundary = is_component_boundary_tag(tag_name);

    for attr in node.attrs() {
        let name = attr.key.content.as_str();
        let is_case_variant = name.eq_ignore_ascii_case(CLIENT_PROPS_ATTR)
            || name.eq_ignore_ascii_case(DYNAMIC_CLIENT_PROPS_ATTR);
        if !is_case_variant {
            continue;
        }

        let (line, col) = attr.token.line_col;
        if name != CLIENT_PROPS_ATTR && name != DYNAMIC_CLIENT_PROPS_ATTR {
            return Err(context.error_from_token(
                &attr.token,
                format!(
                    "Citry client directive names are lowercase. Write '{}' or '{}' instead of '{}'.",
                    CLIENT_PROPS_ATTR, DYNAMIC_CLIENT_PROPS_ATTR, name
                ),
            ));
        }

        if name == CLIENT_PROPS_ATTR
            && !attr
                .inner_value
                .as_ref()
                .is_some_and(|value| !value.content.trim().is_empty())
        {
            return Err(context.error_from_token(
                &attr.token,
                format!(
                    "'{}' must have a non-empty client expression value, e.g. {}=\"{{ theme: currentTheme }}\".",
                    CLIENT_PROPS_ATTR, CLIENT_PROPS_ATTR
                ),
            ));
        }

        if !is_component_boundary {
            return Err(context.error_from_token(
                &attr.token,
                format!(
                    "'{}' is not supported on '<{}>' (line {}, column {}). It is a client props directive and belongs on a Citry component tag, including '<c-component>'.",
                    name, tag_name, line, col
                ),
            ));
        }
    }

    Ok(())
}

fn is_client_props_attr(name: &str) -> bool {
    name == CLIENT_PROPS_ATTR || name == DYNAMIC_CLIENT_PROPS_ATTR
}

fn is_component_boundary_tag(tag_name: &str) -> bool {
    has_citry_component_prefix(tag_name)
        && !citry_component_tag_eq(tag_name, C_ELEMENT_TAG)
        && !is_reserved_citry_tag_identity(tag_name)
}

fn is_component_boundary_handler_attr(name: &str) -> bool {
    let resolved = name.strip_prefix("c-").unwrap_or(name);
    resolved.starts_with('@') || resolved.starts_with("x-on:")
}

fn is_component_tag_client_binding_attr(name: &str) -> bool {
    is_client_props_attr(name) || is_component_boundary_handler_attr(name)
}

/// Validate where `#c-*` framework-metadata attributes may sit.
///
/// The general attribute rules (validate_attributes_present) deliberately skip
/// the `#c-*` channel (it is framework metadata, never one of the tag's
/// inputs), so this is the single place its placement is decided:
///
/// - `#c-key` and `#c-ignore` belong on plain HTML elements or component
///   identity tags. On an element they control ordinary morph behavior; on a
///   component tag they describe the child's DOM range. `<c-component>` is a
///   component identity tag, while `<c-element>` keeps ordinary selected-
///   element semantics.
/// - The reserved structural tags (`<c-if>`, `<c-for>`, `<c-slot>`,
///   `<c-fill>`, `<c-raw>`) render no identity of their own, so both metadata
///   members are rejected there.
fn validate_meta_attr_placement(node: &Node, context: &ParserContext) -> Result<(), ParseError> {
    let tag_name = node.tag_name();

    for attr in node.attrs() {
        if attr.kind != HtmlAttrKind::Meta {
            continue;
        }
        // Validation here runs on the built AST, where the span only covers
        // the attribute's own text, so the message itself carries the real
        // template position (`Token.line_col` is already offset-adjusted).
        let (line, col) = attr.token.line_col;
        match attr.key.content.as_str() {
            META_ATTR_KEY => {
                if is_reserved_citry_tag_identity(tag_name) {
                    return Err(context.error_from_token(
                        &attr.token,
                        format!(
                            "'{}' is not supported on '<{}>' (line {}, column {}). It belongs on a plain HTML element (the morph pairing key) or on a component tag (the key of the child instance).",
                            META_ATTR_KEY, tag_name, line, col
                        ),
                    ));
                }
            }
            META_ATTR_IGNORE => {
                if is_reserved_citry_tag_identity(tag_name) {
                    return Err(context.error_from_token(
                        &attr.token,
                        format!(
                            "'{}' is not supported on '<{}>' (line {}, column {}). It belongs on a plain HTML element (the ignored subtree) or on a component tag (the ignored component range).",
                            META_ATTR_IGNORE, tag_name, line, col
                        ),
                    ));
                }
            }
            // parse_html_attribute rejects every other `#c-*` name, so
            // reaching here with one is a parser bug, not user error.
            other => {
                return Err(context.error_from_token(
                    &attr.token,
                    format!(
                        "Internal error: unexpected '#c-*' attribute '{}' reached placement validation.",
                        other
                    ),
                ));
            }
        }
    }
    Ok(())
}

/// Validate semantic attribute values whose contracts are narrower than the
/// grammar's general static/expression/template classification.
///
/// A dynamic attribute's value is an expression (or a nested template), so a
/// bare `c-foo`, an empty `c-foo=""`, or a whitespace-only `c-foo="   "` has
/// nothing to evaluate and is almost certainly a mistake: the user either
/// meant the static boolean attribute (`foo`) or forgot the value.
///
/// The exceptions are the control-flow shorthand attributes that take no
/// value by design (`c-else`, `c-empty`).
fn validate_attribute_values(node: &Node, context: &ParserContext) -> Result<(), ParseError> {
    let tag_name = node.tag_name();

    for attr in node.attrs() {
        let attr_name = attr.key.content.as_str();

        if is_dynamic_target_static_attr(tag_name, attr_name) {
            let has_nonempty_value = attr
                .inner_value
                .as_ref()
                .is_some_and(|value| !value.content.trim().is_empty());
            if !has_nonempty_value {
                return Err(context.error_from_token(
                    &attr.token,
                    format!(
                        "Tag '<{}>' static 'is' must have a non-empty value.",
                        tag_name
                    ),
                ));
            }
        }

        if matches!(tag_name, C_SLOT_TAG | C_FILL_TAG) && attr_name == "name" {
            let has_nonempty_value = attr
                .inner_value
                .as_ref()
                .is_some_and(|value| !value.content.trim().is_empty());
            if !has_nonempty_value {
                return Err(context.error_from_token(
                    &attr.token,
                    format!(
                        "Tag '<{}>' static 'name' must have a non-empty value.",
                        tag_name
                    ),
                ));
            }
        }

        if attr.kind == HtmlAttrKind::Template {
            let expression_only = attr_name == "c-bind"
                || is_dynamic_target_expr_attr(tag_name, attr_name)
                || (matches!(tag_name, C_SLOT_TAG | C_FILL_TAG) && attr_name == "c-name")
                || (tag_name == C_SLOT_TAG && attr_name == "c-required");
            if expression_only {
                let message = if attr_name == "c-bind" {
                    "'c-bind' must be an expression that resolves to a mapping; template values are not allowed."
                        .to_string()
                } else {
                    format!(
                        "'{}' on '<{}>' must be an expression; template values are not allowed.",
                        attr_name, tag_name
                    )
                };
                return Err(context.error_from_token(&attr.token, message));
            }
        }

        if attr.kind == HtmlAttrKind::Static {
            continue;
        }
        // `#c-*` attributes have their own value rules (`#c-key` requires an
        // expression, `#c-ignore` must be bare), enforced when the attribute
        // is parsed; the `c-*` message below would mislead for them.
        if attr.kind == HtmlAttrKind::Meta {
            continue;
        }
        if attr_name == C_ELSE_TAG || attr_name == C_EMPTY_TAG {
            continue;
        }

        let has_nonempty_value = attr
            .inner_value
            .as_ref()
            .is_some_and(|v| !v.content.trim().is_empty());
        if has_nonempty_value {
            continue;
        }

        // Control-flow attrs (c-if, c-elif, c-for) miss their condition or
        // iterable; suggesting a static attribute would mislead there.
        let message = if attr_name == "c-bind" || CONTROL_FLOW_TAGS.contains(attr_name) {
            format!("'{}' attribute must have a non-empty value.", attr_name)
        } else {
            format!(
                "Dynamic attribute '{}' must have a non-empty value. Write '{}' for a static boolean attribute, or give it an expression: {}=\"...\".",
                attr_name,
                &attr_name[2..],
                attr_name
            )
        };
        return Err(context.error_from_token(&attr.token, message));
    }
    Ok(())
}

/// Validate a Node against its parent template.
///
/// This runs after we popped the Node from the stack.
fn validate_node_against_parent(
    node: &Node,
    parent_template: &Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    validate_tag_grouping(node, parent_template, context)?;
    validate_fill_exclusivity(node, parent_template, context)?;

    Ok(())
}

/// Validate that a `<c-fill>` node is inside a valid component.
///
/// `<c-fill>` must be inside a component tag (either `<c-component>` or a custom component like `<c-MyComp>`).
/// It can be nested inside transparent tags (`<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`),
/// in which case we keep looking up the stack.
///
/// # Errors
/// - If `<c-fill>` is not inside any component (reached root)
/// - If `<c-fill>` is inside a regular HTML tag (doesn't start with `c-`)
/// - If `<c-fill>` is inside a reserved special tag
///
/// E.g. this is valid ✅:
/// ```html
/// <c-my-comp>
///   <c-fill name="footer"> </c-fill>
/// </c-my-comp>
/// ```
///
/// This is valid ✅:
/// ```html
/// <c-my-comp>
///   <c-for each="item in items">
///     <c-fill name="item"> </c-fill>
///   </c-for>
/// </c-my-comp>
/// ```
///
/// This is valid ✅:
/// ```html
/// <c-my-comp>
///   <c-if cond="is_visible">
///     <c-fill name="header"> </c-fill>
///   </c-if>
/// </c-my-comp>
/// ```
///
/// This is NOT valid (c-fill inside regular HTML tag) ❌:
/// ```html
/// <div>
///   <c-fill name="footer"> </c-fill>
/// </div>
/// ```
///
/// This is NOT valid (c-fill inside regular HTML tag) ❌:
/// ```html
/// <c-my-comp>
///   <div>
///     <c-fill name="footer"> </c-fill>
///   </div>
/// </c-my-comp>
/// ```
///
/// This is NOT valid (c-fill inside regular HTML tag) ❌:
/// ```html
/// <c-my-comp>
///   <c-if cond="is_visible">
///     <div>
///       <c-fill name="footer"> </c-fill>
///     </div>
///   </c-if>
/// </c-my-comp>
/// ```
fn validate_fill_placement(
    node: &Node,
    tag_stack: &[TagStackEntry],
    context: &ParserContext,
) -> Result<(), ParseError> {
    let tag_name = node.tag_name();

    // Only validate if this is a <c-fill> tag
    if tag_name != C_FILL_TAG {
        return Ok(());
    }

    // Get the start_tag token for error reporting
    let start_tag_token = &node.start_tag().token;

    // Walk up the tag stack, skipping transparent tags
    for stack_entry in tag_stack.iter().rev() {
        let parent_tag_name = stack_entry.start_tag.name.content.as_str();

        // If we find a transparent tag, continue looking up
        if CONTROL_FLOW_TAGS.contains(&parent_tag_name) {
            continue;
        }

        // If we find a reserved tag, raise error
        if is_reserved_citry_tag_identity(parent_tag_name) {
            return Err(context.error_from_token(
                start_tag_token,
                format!(
                    "Tag '<c-fill>' cannot be inside '<{}>'. It must be inside a component tag (e.g., '<c-component>' or '<c-MyComp>').",
                    parent_tag_name
                ),
            ));
        }

        // If the tag doesn't start with 'c-', it's a regular HTML tag (e.g. '<div>') - raise error
        // NOTE: Regular HTML tags can be INSIDE `<c-fill>`, but not the other way around,
        // as <c-fill> mark the start of a content block.
        if !has_citry_component_prefix(parent_tag_name) {
            return Err(context.error_from_token(
                start_tag_token,
                format!(
                    "Tag '<c-fill>' cannot be inside '<{}>'. It must be inside a component tag (e.g., '<c-component>' or '<c-MyComp>').",
                    parent_tag_name
                ),
            ));
        }

        // If we reach here, the tag starts with 'c-' and is not reserved or transparent,
        // so it must be a component - this is valid!
        return Ok(());
    }

    // If we've exhausted the stack, we're at the root - raise error
    Err(context.error_from_token(
        start_tag_token,
        "Tag '<c-fill>' must be inside a component tag (e.g., '<c-component>' or '<c-MyComp>')."
            .to_string(),
    ))
}

/// Validate that `<c-fill>` tags are not mixed with incompatible tags at the same level.
///
/// "Fill-compatible" tags are `<c-fill>` itself and control flow tags
/// (`c-if/c-elif/c-else/c-for/c-empty`). At a given sibling level, once a fill-compatible
/// tag appears, all subsequent siblings must also be fill-compatible (and vice versa).
///
/// When a control flow tag is a sibling of `<c-fill>`, its body must recursively contain
/// only `<c-fill>` and/or other control flow tags (no regular HTML, components, text, etc.).
///
/// # Valid examples
///
/// ```html
/// <c-my-comp>
///   <c-fill name="header">A</c-fill>
///   <c-fill name="footer">B</c-fill>
/// </c-my-comp>
/// ```
///
/// ```html
/// <c-my-comp>
///   <c-fill name="header">A</c-fill>
///   <c-if cond="x"><c-fill name="footer">B</c-fill></c-if>
/// </c-my-comp>
/// ```
///
/// # Invalid examples
///
/// ```html
/// <c-my-comp>
///   <c-fill name="header">A</c-fill>
///   <div>Hello</div>
/// </c-my-comp>
/// ```
///
/// ```html
/// <c-my-comp>
///   <c-fill name="header">A</c-fill>
///   <c-if cond="x"><div>Not a fill</div></c-if>
/// </c-my-comp>
/// ```
///
/// # Errors
/// - If a fill-compatible tag follows a non-fill-compatible sibling (or vice versa)
/// - If a control flow tag sibling of `<c-fill>` contains non-fill, non-control-flow content
fn validate_fill_exclusivity(
    node: &Node,
    template: &Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    let tag_name = node.tag_name();

    // Find the last Node in template.elements (skip Text and Expr)
    let last_node = template.elements.iter().rev().find_map(|elem| match elem {
        TemplateElement::Node(n) => Some(n),
        _ => None,
    });

    // If there's no previous node, there's nothing to validate
    let Some(prev_node) = last_node else {
        return Ok(());
    };

    let prev_tag_name = prev_node.tag_name();

    // Get the start_tag token for error reporting
    let start_tag_token = &node.start_tag().token;

    /// A tag is "fill-compatible" if it's `<c-fill>` or a control flow tag.
    /// At a sibling level that contains `<c-fill>`, only fill-compatible tags are allowed.
    fn is_fill_compatible(tag: &str) -> bool {
        tag == C_FILL_TAG || CONTROL_FLOW_TAGS.contains(tag)
    }

    let is_current_compat = is_fill_compatible(tag_name);
    let is_prev_compat = is_fill_compatible(prev_tag_name);

    // Determine if we're in a "fill context" - i.e. there is at least one actual <c-fill>
    // tag among the siblings (including the current node being added). Without a <c-fill>,
    // control flow tags can be siblings of anything normally.
    let is_current_fill = tag_name == C_FILL_TAG;
    let has_fill_in_siblings = is_current_fill
        || template
            .elements
            .iter()
            .any(|elem| matches!(elem, TemplateElement::Node(n) if n.tag_name() == C_FILL_TAG));

    // If we're NOT in a fill context, no fill-related validation needed
    if !has_fill_in_siblings {
        return Ok(());
    }

    // We ARE in a fill context. Only fill-compatible tags are allowed.

    // If current is fill-compatible and previous is NOT, raise error
    if is_current_compat && !is_prev_compat {
        return Err(context.error_from_token(
            start_tag_token,
            format!(
                "Tag '<{}>' cannot follow '<{}>' here. '<c-fill>' (and control flow) tags must be grouped together, not mixed with other tags.",
                tag_name, prev_tag_name
            ),
        ));
    }

    // If current is NOT fill-compatible and previous IS, raise error
    if !is_current_compat && is_prev_compat {
        return Err(context.error_from_token(
            start_tag_token,
            format!(
                "Tag '<{}>' cannot follow '<{}>' here. '<c-fill>' (and control flow) tags must be grouped together, not mixed with other tags.",
                tag_name, prev_tag_name
            ),
        ));
    }

    // Both are fill-compatible. If a control flow tag is present, validate that its body
    // only contains fills and/or other control flow tags.
    if is_current_compat && is_prev_compat {
        // Validate the CURRENT node's body when it's a control flow tag
        // (c-fill bodies are fine - they contain the slot content).
        if CONTROL_FLOW_TAGS.contains(tag_name) {
            if let Node::WithBody { body, .. } = node {
                if !_contains_only_fills_and_control_flow(body) {
                    return Err(context.error_from_token(
                        start_tag_token,
                        format!(
                            "Control flow tag '<{}>' is a sibling of '<c-fill>' but contains non-fill content. \
                            When mixed with '<c-fill>' tags, control flow tags must contain only '<c-fill>' or other control flow tags.",
                            tag_name
                        ),
                    ));
                }
            }
        }

        // Also validate the PREVIOUS node if it's a control flow tag.
        // This handles the case where the first sibling is a control flow tag and the second is <c-fill>.
        if CONTROL_FLOW_TAGS.contains(prev_tag_name) {
            if let Node::WithBody { body, .. } = prev_node {
                if !_contains_only_fills_and_control_flow(body) {
                    return Err(context.error_from_token(
                        &prev_node.start_tag().token,
                        format!(
                            "Control flow tag '<{}>' is a sibling of '<c-fill>' but contains non-fill content. \
                            When mixed with '<c-fill>' tags, control flow tags must contain only '<c-fill>' or other control flow tags.",
                            prev_tag_name
                        ),
                    ));
                }
            }
        }
    }

    Ok(())
}

/// Check if a template body contains only `<c-fill>` tags and/or control flow tags (recursively).
///
/// Returns `true` if the body is "fill-only": every node is either `<c-fill>` or a control flow
/// tag whose body also satisfies this constraint. Text/expression elements are allowed only if
/// they contain only whitespace.
///
/// This is used to validate that control flow siblings of `<c-fill>` don't smuggle in
/// non-fill content like `<div>` or components.
fn _contains_only_fills_and_control_flow(template: &Template) -> bool {
    for element in &template.elements {
        match element {
            TemplateElement::Text(text) => {
                // Whitespace-only text is allowed (formatting/indentation)
                if !text.token.content.trim().is_empty() {
                    return false;
                }
            }
            TemplateElement::Expr(_) => {
                // Expressions are not allowed in fill-only context
                return false;
            }
            TemplateElement::Node(node) => {
                let tag_name = node.tag_name();
                if tag_name == C_FILL_TAG {
                    // <c-fill> is always OK
                    continue;
                } else if CONTROL_FLOW_TAGS.contains(tag_name) {
                    // Control flow tag: recursively check its body
                    if let Node::WithBody { body, .. } = node {
                        if !_contains_only_fills_and_control_flow(body) {
                            return false;
                        }
                    }
                    // Self-closing control flow is fine (empty body)
                } else {
                    // Any other tag (HTML, component, etc.) is not allowed
                    return false;
                }
            }
        }
    }
    true
}

/// Validate that a component body holding `<c-fill>` tags contains nothing else.
///
/// When a component body contains `<c-fill>` tags, the body is a "fill group":
/// every element in it must be a `<c-fill>`, a control flow tag whose body
/// recursively satisfies the same rule, or whitespace-only text. The whitespace
/// is formatting only - the runtime neither captures it into a slot nor renders
/// it. Anything else (non-whitespace text, a `{{ expr }}`, a regular tag) must
/// live inside one of the fills.
///
/// This runs when the component node is closed, so it sees the full body. The
/// per-sibling [`validate_fill_exclusivity`] catches node-vs-node mixing earlier
/// (with errors pointing at the later sibling); this check is the authoritative
/// one and additionally covers text and expression elements, and non-fill
/// content inside a control flow tag at a level with no direct `<c-fill>`
/// sibling.
fn validate_fill_group_content(
    template: &Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    for element in &template.elements {
        match element {
            TemplateElement::Text(text) => {
                if !text.token.content.trim().is_empty() {
                    return Err(context.error_from_token(
                        &text.token,
                        "Text cannot appear next to '<c-fill>' tags. When a component body \
                        contains '<c-fill>' tags, all other content must be inside the fills \
                        (whitespace-only text is allowed for formatting)."
                            .to_string(),
                    ));
                }
            }
            TemplateElement::Expr(expr) => {
                return Err(context.error_from_token(
                    &expr.token,
                    "Expression cannot appear next to '<c-fill>' tags. When a component body \
                    contains '<c-fill>' tags, all other content must be inside the fills."
                        .to_string(),
                ));
            }
            TemplateElement::Node(node) => {
                let tag_name = node.tag_name();
                if tag_name == C_FILL_TAG {
                    // A fill's body IS the slot content - don't descend.
                    continue;
                } else if CONTROL_FLOW_TAGS.contains(tag_name) {
                    // Control flow may hold nested fills; its body must satisfy
                    // the same rule.
                    if let Node::WithBody { body, .. } = node {
                        validate_fill_group_content(body, context)?;
                    }
                } else {
                    return Err(context.error_from_token(
                        &node.start_tag().token,
                        format!(
                            "Tag '<{}>' cannot appear next to '<c-fill>' tags. When a component \
                            body contains '<c-fill>' tags, all other content must be inside the fills.",
                            tag_name
                        ),
                    ));
                }
            }
        }
    }
    Ok(())
}

/// Recompute a template's free-variable metadata from the completed tree.
///
/// Construction-time aggregation cannot distinguish a binding header from its
/// body. This pass applies the actual lexical scopes:
///
/// - explicit `c-for` and `c-fill` attributes resolve outside their bindings;
/// - their bodies resolve with the new names in scope;
/// - on a shorthand `c-for` host, control-flow attributes are outside the loop
///   while ordinary/meta/template attributes and the body are inside it.
fn recompute_template_used_variables(template: &mut Template) -> Vec<Token> {
    let mut used_variables = Vec::new();
    for element in &mut template.elements {
        match element {
            TemplateElement::Expr(expr) => used_variables.extend(expr.used_variables.clone()),
            TemplateElement::Node(node) => {
                used_variables.extend(recompute_node_used_variables(node));
            }
            TemplateElement::Text(_) => {}
        }
    }
    template.used_variables = used_variables.clone();
    used_variables
}

fn recompute_node_used_variables(node: &mut Node) -> Vec<Token> {
    match node {
        Node::WithBody {
            start_tag,
            body,
            used_variables,
            introduced_variables,
            ..
        } => {
            let body_variables = recompute_template_used_variables(body);
            let tag_name = start_tag.name.content.as_str();
            let is_shorthand_for = tag_name != C_FOR_TAG
                && tag_name != C_FILL_TAG
                && !introduced_variables.is_empty()
                && start_tag
                    .attrs
                    .iter()
                    .any(|attr| attr.key.content == C_FOR_TAG);

            let mut recomputed = filter_bound_variables(body_variables, introduced_variables);
            for attr in &start_tag.attrs {
                if is_shorthand_for && !is_control_flow_attribute(&attr.key.content) {
                    recomputed.extend(filter_bound_variables(
                        attr.used_variables.clone(),
                        introduced_variables,
                    ));
                } else {
                    recomputed.extend(attr.used_variables.clone());
                }
            }
            *used_variables = recomputed.clone();
            recomputed
        }
        Node::SelfClosing {
            start_tag,
            used_variables,
            introduced_variables,
            ..
        } => {
            let tag_name = start_tag.name.content.as_str();
            let is_shorthand_for = tag_name != C_FOR_TAG
                && tag_name != C_FILL_TAG
                && !introduced_variables.is_empty()
                && start_tag
                    .attrs
                    .iter()
                    .any(|attr| attr.key.content == C_FOR_TAG);

            let mut recomputed = Vec::new();
            for attr in &start_tag.attrs {
                if is_shorthand_for && !is_control_flow_attribute(&attr.key.content) {
                    recomputed.extend(filter_bound_variables(
                        attr.used_variables.clone(),
                        introduced_variables,
                    ));
                } else {
                    recomputed.extend(attr.used_variables.clone());
                }
            }
            *used_variables = recomputed.clone();
            recomputed
        }
    }
}

fn filter_bound_variables(used_variables: Vec<Token>, bindings: &[Token]) -> Vec<Token> {
    if bindings.is_empty() {
        return used_variables;
    }
    let binding_names: HashSet<String> = bindings
        .iter()
        .map(|binding| canonical_identifier(&binding.content))
        .collect();
    used_variables
        .into_iter()
        .filter(|token| !binding_names.contains(&canonical_identifier(&token.content)))
        .collect()
}

fn canonical_identifier(identifier: &str) -> String {
    identifier.nfkc().collect()
}

fn is_control_flow_attribute(attr_name: &str) -> bool {
    CONTROL_FLOW_GROUPS
        .iter()
        .any(|group| group.contains(&attr_name))
}

/// Collect all statically known loop/fill declarations in a template,
/// including declarations nested inside template-valued attributes.
fn collect_template_binding_tokens(template: &Template, context: &ParserContext) -> Vec<Token> {
    let mut bindings = Vec::new();
    for element in &template.elements {
        let TemplateElement::Node(node) = element else {
            continue;
        };
        bindings.extend(node.introduced_variables().clone());
        for attr in node.attrs() {
            bindings.extend(context.nested_template_bindings(&attr.token));
        }
        if let Node::WithBody { body, .. } = node {
            bindings.extend(collect_template_binding_tokens(body, context));
        }
    }
    bindings
}

/// Validate loop/fill declarations against the complete lexical context.
fn validate_template_variable_shadowing(
    template: &Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    let root_free_names: HashSet<String> = template
        .used_variables
        .iter()
        .map(|token| canonical_identifier(&token.content))
        .collect();
    validate_template_bindings(template, &root_free_names, &[], context)
}

fn validate_template_bindings(
    template: &Template,
    root_free_names: &HashSet<String>,
    active_bindings: &[String],
    context: &ParserContext,
) -> Result<(), ParseError> {
    for element in &template.elements {
        let TemplateElement::Node(node) = element else {
            continue;
        };

        let tag_name = node.tag_name();
        let bindings = node.introduced_variables();
        validate_binding_site(
            bindings,
            root_free_names,
            active_bindings,
            &format!("tag '<{}>'", tag_name),
            context,
        )?;

        let is_shorthand_for = tag_name != C_FOR_TAG
            && tag_name != C_FILL_TAG
            && !bindings.is_empty()
            && node
                .attrs()
                .iter()
                .any(|attr| attr.key.content == C_FOR_TAG);
        let mut body_bindings = active_bindings.to_vec();
        body_bindings.extend(
            bindings
                .iter()
                .map(|token| canonical_identifier(&token.content)),
        );

        for attr in node.attrs() {
            let nested_bindings = context.nested_template_bindings(&attr.token);
            let nested_active = if is_shorthand_for && !is_control_flow_attribute(&attr.key.content)
            {
                body_bindings.as_slice()
            } else {
                active_bindings
            };
            validate_bindings_against_outer_scope(
                &nested_bindings,
                root_free_names,
                nested_active,
                "nested template attribute",
                context,
            )?;
        }

        if let Node::WithBody { body, .. } = node {
            validate_template_bindings(body, root_free_names, &body_bindings, context)?;
        }
    }
    Ok(())
}

/// Nested templates validate their own lexical structure while they are parsed.
/// This outer pass only needs to reject their declarations when they collide
/// with names visible in the writer's surrounding scope. The collected tokens
/// are intentionally flat, so repeated names may represent legal sibling scopes.
fn validate_bindings_against_outer_scope(
    bindings: &[Token],
    root_free_names: &HashSet<String>,
    active_bindings: &[String],
    site: &str,
    context: &ParserContext,
) -> Result<(), ParseError> {
    for binding in bindings {
        let name = canonical_identifier(&binding.content);
        if root_free_names.contains(&name) || active_bindings.iter().any(|active| active == &name) {
            return Err(context.error_from_token(
                binding,
                format!(
                    "Cannot define variable '{}' in {} - variable name is already taken. Variable shadowing is not allowed, use a different name.",
                    binding.content, site
                ),
            ));
        }
    }
    Ok(())
}

fn validate_binding_site(
    bindings: &[Token],
    root_free_names: &HashSet<String>,
    active_bindings: &[String],
    site: &str,
    context: &ParserContext,
) -> Result<(), ParseError> {
    let mut local_names = HashSet::new();
    for binding in bindings {
        let name = canonical_identifier(&binding.content);
        if !local_names.insert(name.clone()) {
            return Err(context.error_from_token(
                binding,
                format!(
                    "Cannot define variable '{}' more than once in {}. Use a distinct name for each binding.",
                    binding.content, site
                ),
            ));
        }
        if root_free_names.contains(&name) || active_bindings.iter().any(|active| active == &name) {
            return Err(context.error_from_token(
                binding,
                format!(
                    "Cannot define variable '{}' in {} - variable name is already taken. Variable shadowing is not allowed, use a different name.",
                    binding.content, site
                ),
            ));
        }
    }
    Ok(())
}

/// Enrich a tag's control-flow attributes and compute the variables it
/// introduces into its body scope, in a single pass.
///
/// The parser keeps the AST 1:1 with the source (it does NOT rewrite
/// `<div c-if="x">` into `<c-if cond="x">`; that expansion happens in the
/// compiler). But the attribute variable metadata is corrected in place so the
/// explicit-tag and shorthand authoring styles agree once the compiler expands
/// them:
///
/// - The explicit `cond` (on `<c-if>`/`<c-elif>`) and `each` (on `<c-for>`)
///   attributes are not `c-` prefixed, so attribute parsing classifies them as
///   `Static` and skips variable tracking. They are upgraded to `Expression`
///   with their used variables populated.
/// - The shorthand `c-for` attribute (on any element) is parsed as a generic
///   expression, so its used variables wrongly include the loop targets (e.g.
///   `c-for="x in xs"` reports both `x` and `xs`). They are recomputed as the
///   loop's free variables (`xs`), matching the explicit `each` form.
///
/// The returned vector is the node's introduced variables: the loop targets for
/// a `c-for` (explicit or shorthand) and the data/fallback variables for a
/// `<c-fill>`. For a for-loop clause both the used and introduced variables come
/// from one [`extract_forloop_variables`] call, so the clause is analysed once.
///
/// The `c-if`/`c-elif` shorthand attributes already track their variables
/// correctly (a plain expression, no targets), so they need no change.
fn process_control_flow_metadata(
    tag_name: &str,
    tag_token: &Token,
    attrs: &mut [HtmlAttr],
    context: &ParserContext,
) -> Result<Vec<Token>, ParseError> {
    // A spread on a physical structural tag is accepted by the broad grammar,
    // but none of these runtime nodes resolves spread attributes. Reject it
    // before the explicit `<c-for>` path reports only the secondary missing
    // `each` error. A shorthand host has a different physical tag name and
    // keeps its ordinary element/component spread behavior.
    if matches!(
        tag_name,
        C_IF_TAG | C_ELIF_TAG | C_ELSE_TAG | C_FOR_TAG | C_EMPTY_TAG | C_RAW_TAG
    ) {
        if let Some(attr) = attrs.iter().find(|attr| attr.key.content == "c-bind") {
            return Err(context.error_from_token(
                &attr.token,
                format!(
                    "'c-bind' is not supported directly on '<{}>'. Put the spread on an element or component inside it, or write control flow on the spread host (for example, '<div c-if=\"...\" c-bind=\"...\">').",
                    tag_name
                ),
            ));
        }
    }

    // `<c-fill>` introduces statically known data/fallback variables. A later
    // c-bind may replace either name, so only direct attributes after the last
    // spread are certain to be in scope. Keep their authored order for stable
    // AST/compiler metadata.
    if tag_name == C_FILL_TAG {
        let mut data: Option<(usize, Vec<Token>)> = None;
        let mut fallback: Option<(usize, Vec<Token>)> = None;
        for (index, attr) in attrs.iter_mut().enumerate() {
            match attr.key.content.as_str() {
                "c-bind" => {
                    data = None;
                    fallback = None;
                }
                "data" => {
                    if let Some(inner_value) = &attr.inner_value {
                        let pattern = parse_fill_data_pattern(inner_value, context)?;
                        let introduced = if let Some(whole) = &pattern.whole {
                            vec![whole.clone()]
                        } else {
                            pattern
                                .fields
                                .iter()
                                .map(|field| field.target.clone())
                                .chain(pattern.rest.iter().cloned())
                                .collect()
                        };
                        attr.fill_data_pattern = Some(pattern);
                        data = Some((index, introduced));
                    }
                }
                "fallback" => {
                    if let Some(inner_value) = &attr.inner_value {
                        fallback = Some((index, vec![inner_value.clone()]));
                    }
                }
                _ => {}
            }
        }
        let mut introduced: Vec<(usize, Vec<Token>)> = data.into_iter().chain(fallback).collect();
        introduced.sort_by_key(|(index, _)| *index);
        return Ok(introduced
            .into_iter()
            .flat_map(|(_, tokens)| tokens)
            .collect());
    }

    // Explicit `<c-for each="...">`: the `each` attribute is required and must
    // have a value. Its clause yields both the used and introduced variables.
    if tag_name == C_FOR_TAG {
        let each_attr = attrs
            .iter_mut()
            .find(|attr| attr.key.content == "each")
            .ok_or_else(|| {
                context.error_from_token(
                    tag_token,
                    "Tag '<c-for>' must have an 'each' attribute.".to_string(),
                )
            })?;
        let each_value = each_attr.inner_value.clone().ok_or_else(|| {
            context.error_from_token(
                &each_attr.token,
                "Tag '<c-for>' attribute 'each' must have a value.".to_string(),
            )
        })?;
        let vars = extract_forloop_variables(&each_value, context)?;
        each_attr.kind = HtmlAttrKind::Expression;
        each_attr.used_variables = vars.used;
        return Ok(vars.introduced);
    }

    // Otherwise: enrich a `cond` expression (on `<c-if>`/`<c-elif>`) and/or a
    // shorthand `c-for` attribute (on any element). Only the shorthand `c-for`
    // introduces variables.
    let mut introduced = Vec::new();
    for attr in attrs.iter_mut() {
        let is_for_shorthand = attr.key.content == C_FOR_TAG;
        let is_cond = matches!(tag_name, C_IF_TAG | C_ELIF_TAG) && attr.key.content == "cond";
        if !is_for_shorthand && !is_cond {
            continue;
        }

        let Some(inner_value) = attr.inner_value.clone() else {
            // Boolean / valueless attribute: leave for the attribute-presence
            // validator to report (`cond` requires a value).
            continue;
        };
        if inner_value.content.trim().is_empty() {
            // `cond=""` carries no expression; an empty value is the boolean form
            // (the compiler normalizes it to `True`), so there is nothing to
            // track. Leave it as-is.
            continue;
        }

        if is_for_shorthand {
            let vars = extract_forloop_variables(&inner_value, context)?;
            attr.used_variables = vars.used;
            introduced = vars.introduced;
        } else {
            let (used_variables, comments) = process_expression(&inner_value, None, context)?;
            attr.used_variables = used_variables;
            attr.comments.extend(comments);
        }
        attr.kind = HtmlAttrKind::Expression;
    }

    Ok(introduced)
}

/// Parse the small binding language used by a direct `<c-fill data="...">`.
fn parse_fill_data_pattern(
    value: &Token,
    context: &ParserContext,
) -> Result<FillDataPattern, ParseError> {
    let mut parsed = GrammarParser::parse(Rule::fill_data_pattern, &value.content).map_err(|_| {
        context.error_from_token(
            value,
            "Invalid <c-fill> data binding. Use a variable name or one-level destructuring such as '{ root_attrs, table_attrs as inner_table_attrs, **rest }'."
                .to_string(),
        )
    })?;
    let pattern_pair = parsed
        .next()
        .expect("a successful fill_data_pattern parse has one pair");
    let form = pattern_pair
        .into_inner()
        .find(|pair| {
            matches!(
                pair.as_rule(),
                Rule::fill_data_identifier | Rule::fill_data_destructure
            )
        })
        .expect("fill_data_pattern contains one binding form");

    if form.as_rule() == Rule::fill_data_identifier {
        let whole = fill_data_token(&form, value);
        validate_fill_data_identifier(&whole, context)?;
        return Ok(FillDataPattern {
            token: value.clone(),
            whole: Some(whole),
            fields: Vec::new(),
            rest: None,
        });
    }

    let items: Vec<_> = form
        .into_inner()
        .filter(|pair| pair.as_rule() == Rule::fill_data_item)
        .collect();
    let mut fields = Vec::new();
    let mut rest = None;
    let mut sources = HashSet::new();
    let mut targets = HashSet::new();

    for (index, item) in items.iter().enumerate() {
        let item_kind = item
            .clone()
            .into_inner()
            .next()
            .expect("fill_data_item contains a field or rest binding");
        match item_kind.as_rule() {
            Rule::fill_data_field => {
                let mut identifiers = item_kind
                    .into_inner()
                    .filter(|pair| pair.as_rule() == Rule::fill_data_identifier);
                let source = fill_data_token(
                    &identifiers
                        .next()
                        .expect("fill_data_field contains a source identifier"),
                    value,
                );
                let target = identifiers
                    .next()
                    .map_or_else(|| source.clone(), |pair| fill_data_token(&pair, value));
                validate_fill_data_identifier(&source, context)?;
                validate_fill_data_identifier(&target, context)?;
                if !sources.insert(source.content.clone()) {
                    return Err(context.error_from_token(
                        &source,
                        format!(
                            "Cannot read slot-data field '{}' more than once in a <c-fill> data binding.",
                            source.content
                        ),
                    ));
                }
                if !targets.insert(canonical_identifier(&target.content)) {
                    return Err(context.error_from_token(
                        &target,
                        format!(
                            "Cannot define variable '{}' more than once in a <c-fill> data binding.",
                            target.content
                        ),
                    ));
                }
                fields.push(FillDataField { source, target });
            }
            Rule::fill_data_rest => {
                let identifier = item_kind
                    .into_inner()
                    .find(|pair| pair.as_rule() == Rule::fill_data_identifier)
                    .expect("fill_data_rest contains a target identifier");
                let target = fill_data_token(&identifier, value);
                validate_fill_data_identifier(&target, context)?;
                if index + 1 != items.len() {
                    return Err(context.error_from_token(
                        &target,
                        "The '**rest' binding must be the last item in a <c-fill> data binding."
                            .to_string(),
                    ));
                }
                if rest.is_some() {
                    return Err(context.error_from_token(
                        &target,
                        "A <c-fill> data binding may contain only one '**rest' item.".to_string(),
                    ));
                }
                if !targets.insert(canonical_identifier(&target.content)) {
                    return Err(context.error_from_token(
                        &target,
                        format!(
                            "Cannot define variable '{}' more than once in a <c-fill> data binding.",
                            target.content
                        ),
                    ));
                }
                rest = Some(target);
            }
            _ => unreachable!("fill_data_item grammar has only field and rest variants"),
        }
    }

    Ok(FillDataPattern {
        token: value.clone(),
        whole: None,
        fields,
        rest,
    })
}

fn fill_data_token(pair: &pest::iterators::Pair<'_, Rule>, value: &Token) -> Token {
    Token::from_pair(pair).offset(
        value.start_index,
        value.line_col.0.saturating_sub(1),
        value.line_col.1.saturating_sub(1),
    )
}

fn validate_fill_data_identifier(token: &Token, context: &ParserContext) -> Result<(), ParseError> {
    let parsed = PYTHON_LANG.parse_expression(&token.content).map_err(|_| {
        context.error_from_token(
            token,
            format!(
                "<c-fill> data bindings require valid Python identifiers, got {:?}.",
                token.content
            ),
        )
    })?;
    let is_one_name = parsed.assigned_vars.is_empty()
        && parsed.comments.is_empty()
        && parsed.used_vars.len() == 1
        && parsed.used_vars[0].content == token.content
        && parsed.used_vars[0].start_index == 0
        && parsed.used_vars[0].end_index == token.content.len();
    if !is_one_name {
        return Err(context.error_from_token(
            token,
            format!(
                "<c-fill> data bindings require valid Python identifiers, got {:?}.",
                token.content
            ),
        ));
    }
    Ok(())
}

/// Analyse a `<c-for>` clause and return its introduced (loop target) and used
/// (free) variables, with token positions adjusted into the template's
/// coordinate space.
///
/// Both halves come from one [`LangImpl::parse_forloop_variables`] call, so the
/// clause is parsed once and the two variable sets are guaranteed consistent.
fn extract_forloop_variables(
    each_value: &Token,
    context: &ParserContext,
) -> Result<ForLoopVars, ParseError> {
    let vars = context
        .lang
        .parse_forloop_variables(&each_value.content)
        .map_err(|e| {
            context.error_from_token(
                each_value,
                format!("Failed to parse 'each' attribute: {}", e),
            )
        })?;

    let index_offset = each_value.start_index;
    let (value_line, value_col) = each_value.line_col;
    let line_offset = value_line - 1;
    let col_offset = value_col - 1;
    let adjust = |tokens: Vec<Token>| -> Vec<Token> {
        tokens
            .into_iter()
            .map(|token| token.offset(index_offset, line_offset, col_offset))
            .collect()
    };

    let introduced = adjust(vars.introduced);
    let mut seen_names = HashSet::new();
    for token in &introduced {
        if !seen_names.insert(canonical_identifier(&token.content)) {
            return Err(context.error_from_token(
                token,
                format!(
                    "Cannot define variable '{}' more than once in a '<c-for>' clause. Use a distinct name for each loop target.",
                    token.content
                ),
            ));
        }
    }

    Ok(ForLoopVars {
        introduced,
        used: adjust(vars.used),
    })
}

/// Validate that special tags and user-defined components have the correct attributes.
///
/// Checks if the attributes on the given Node are allowed/required.
///
/// The rules come from 2 sources:
/// 1. Internal `TAG_ATTR_RULES` (hard-codedd),
/// 2. User-defined rules. This allows us to raise error messages for user-defined tags.
fn validate_attributes_present(node: &Node, context: &ParserContext) -> Result<(), ParseError> {
    let tag_name = node.tag_name();
    let attrs = node.attrs();

    // Get the start_tag token for error reporting
    let start_tag_token = &node.start_tag().token;
    let is_component_boundary = is_component_boundary_tag(tag_name);

    // Extract attribute names, excluding `c-bind` which always bypasses
    // allowed/required attrs checks (it spreads a dict at runtime, so it
    // could provide any attributes dynamically). `#c-*` attributes are also
    // excluded: they are framework metadata about the node, never one of the
    // tag's inputs, so a tag's allowed/required attribute rules do not apply
    // to them (their placement rules live in validate_meta_attr_placement).
    // The client props directive is likewise a component-boundary instruction,
    // not a declared Python kwarg.
    let attr_names: Vec<&str> = attrs
        .iter()
        .filter(|attr| attr.kind != HtmlAttrKind::Meta)
        .map(|attr| attr.key.content.as_str())
        .filter(|&name| {
            name != "c-bind"
                && !is_client_props_attr(name)
                && !(is_component_boundary && is_component_boundary_handler_attr(name))
        })
        .collect();
    let has_c_bind = attrs.iter().any(|attr| attr.key.content == "c-bind");

    // Check if this tag has validation rules - first check built-in rules, then user-provided rules.
    // User rules are keyed by lowercase tag name: component tags match case-insensitively
    // everywhere else (the compiler lowercases component names), so `<c-MyCard>` and
    // `<c-mycard>` validate against the same rules.
    let tag_name_lower = tag_name.to_ascii_lowercase();
    let builtin_tag_name = if citry_component_tag_eq(tag_name, C_COMPONENT_TAG) {
        C_COMPONENT_TAG
    } else if citry_component_tag_eq(tag_name, C_ELEMENT_TAG) {
        C_ELEMENT_TAG
    } else {
        tag_name
    };
    let (allowed_attrs, required_attrs) =
        if let Some(builtin_rules) = TAG_ATTR_RULES.get(builtin_tag_name) {
            // Use built-in rules directly
            (&builtin_rules.allowed_attrs, &builtin_rules.required_attrs)
        } else if let Some(user_rules) = context.user_rules.get(tag_name_lower.as_str()) {
            // Use user-provided rules
            (&user_rules.allowed_attrs, &user_rules.required_attrs)
        } else {
            // No rules defined for this tag - allow any attributes (may be set dynamically with c-bind)
            return Ok(());
        };

    // Validate allowed attributes
    // - If `allowed_attrs` is `None`, any attributes are allowed.
    // - If `allowed_attrs` is `Some([])`, no attributes are allowed.
    // - If `allowed_attrs` is `Some([["c-name", "name"], ["data"]])`, either "c-name" OR "name" may be present (but not both),
    //   and "data" may be present as well.
    match allowed_attrs {
        // Any attributes allowed (only required_attrs are checked)
        // No further validation needed
        None => {}
        // Allowed attributes are set explicitly - validate against them.
        Some(allowed_groups) => {
            // Build a set of all allowed attribute names (flatten all groups)
            let allowed_set: HashSet<&str> = allowed_groups
                .iter()
                .flat_map(|group| group.iter().map(|s| s.as_str()))
                .collect();

            // Check that all attributes on the tag are in the allowed set
            let invalid_attrs: Vec<&str> = attr_names
                .iter()
                .filter(|&&name| !allowed_set.contains(name))
                .copied()
                .collect();

            // Raise error if any attributes are invalid.
            // The allowed names are listed in definition order (from the rule
            // groups), NOT by iterating the HashSet - set iteration order varies
            // between runs and error messages must be reproducible.
            if !invalid_attrs.is_empty() {
                let allowed_str = allowed_groups
                    .iter()
                    .flat_map(|group| group.iter().map(|s| s.as_str()))
                    .collect::<Vec<&str>>()
                    .join("', '");
                return Err(context.error_from_token(
                    start_tag_token,
                    format!(
                        "Tag '<{}>' can only have the following attributes: '{}'. Found invalid attributes: {}.",
                        tag_name,
                        allowed_str,
                        invalid_attrs.join(", ")
                    ),
                ));
            }

            // When we get here, we know that all attributes are contained in the allowed set.
            // Next we check that for each allowed group, there's at most only one attribute present.
            for allowed_group in allowed_groups {
                let mut found_in_group: Vec<&str> = Vec::new();
                for attr_name in attr_names.iter() {
                    if allowed_group
                        .iter()
                        .any(|allowed| allowed.as_str() == *attr_name)
                    {
                        found_in_group.push(*attr_name);
                    }
                }

                // Raise error if more than one attribute is found in the group
                if found_in_group.len() > 1 {
                    return Err(context.error_from_token(
                        start_tag_token,
                        format!(
                            "Tag '<{}>' must have only one of the attributes: {}, but found multiple: {}.",
                            tag_name,
                            allowed_group.join(", "),
                            found_in_group.join(", ")
                        ),
                    ));
                }
            }
        }
    }

    // Validate required attributes
    // Each inner list in required_attrs means "one of" (at least one must be present).
    //
    // If `c-bind` is present, we skip the required attrs check entirely, because
    // `c-bind` spreads a dictionary into attributes at runtime, so the required
    // attributes may be provided dynamically.
    // E.g. `<c-my-comp c-bind="my_dict">` could resolve to `<c-my-comp id="1" class="foo">`
    if !has_c_bind {
        for required_group in required_attrs {
            // Check if the tag contains at least one of the attributes from the required group
            let has_any_required = required_group.iter().any(|required_attr_name: &String| {
                attr_names.iter().any(|attr_name| {
                    if citry_component_tag_eq(tag_name, C_ELEMENT_TAG) {
                        match required_attr_name.as_str() {
                            "is" => is_dynamic_target_static_attr(tag_name, attr_name),
                            "c-is" => is_dynamic_target_expr_attr(tag_name, attr_name),
                            _ => required_attr_name == attr_name,
                        }
                    } else {
                        required_attr_name == attr_name
                    }
                })
            });

            // If none matched, report error.
            if !has_any_required {
                if required_group.len() == 1 {
                    return Err(context.error_from_token(
                        start_tag_token,
                        format!(
                            "Tag '<{}>' must have a '{}' attribute.",
                            tag_name, required_group[0]
                        ),
                    ));
                } else {
                    let options = required_group.join("', '");
                    return Err(context.error_from_token(
                        start_tag_token,
                        format!(
                            "Tag '<{}>' must have one of the following attributes: '{}'.",
                            tag_name, options
                        ),
                    ));
                }
            }
        }
    }

    Ok(())
}

/// Validate that a tag does not have duplicate or conflicting attributes.
///
/// A static and dynamic spelling of one logical attribute (`id` + `c-id`) is
/// an explicit duplicate and therefore an error. Plain HTML elements and
/// `<c-element>` keep the accumulating `class`/`c-class` and
/// `style`/`c-style` exceptions. Dynamic `c-bind` contributions are not known
/// until render and remain repeatable/interlaceable.
///
/// **Case 1: Duplicate attributes**
///
/// A tag cannot have multiple attributes with the same name, except `c-bind`.
/// E.g., `<div class="x" class="y">` is invalid, but `<div c-bind="..." c-bind="...">` is allowed.
///
/// **Case 2: Control flow attribute conflicts**
///
/// A tag cannot have multiple attributes from the same control flow group:
/// - `[c-if, c-elif, c-else]` - only one allowed
/// - `[c-for, c-empty]` - only one allowed
///
/// However, attributes from different groups can coexist (e.g., `c-if` and `c-for` together is allowed).
///
/// **Case 3: Control flow priorities conflicts**
///
/// If a single tag uses attributes from several control flow group (e.g. IF and FOR),
/// then only the group with the highest priority can be non-first.
///
/// E.g. IF has higher priority over FOR, so for IF we can use also `c-elif`, `c-else`,
/// while from the FOR group we MUST use only `c-for`.
/// - ✅ <div c-if="x" c-for="y">
/// - ✅ <div c-elif="x" c-for="y">
/// - ✅ <div c-else="x" c-for="y">
///
/// - ❌ <div c-if="x" c-empty="y">
/// - ❌ <div c-elif="x" c-empty="y">
/// - ❌ <div c-else="x" c-empty="y">
///
/// **Errors**
///
/// - If duplicate attribute names are found (except c-bind)
/// - If multiple control flow attributes from the same group are found
fn validate_attribute_conflicts(node: &Node, context: &ParserContext) -> Result<(), ParseError> {
    let attrs = node.attrs();
    let tag_name = node.tag_name();
    let accumulates_html_attrs =
        citry_component_tag_eq(tag_name, C_ELEMENT_TAG) || !has_citry_component_prefix(tag_name);
    let component_boundary = is_component_boundary_tag(tag_name);

    // Track full attribute names for duplicate detection (except c-bind)
    let mut seen_full_names = HashSet::new();
    // Track the rendered/input key after removing exactly one dynamic `c-`
    // prefix. This catches two explicit spellings of one logical input while
    // keeping directives and spreads out of the ordinary attribute namespace.
    let mut seen_logical_names: HashMap<String, String> = HashMap::new();

    // Track control flow attributes - Group name -> (group_index, attr_name, is_first_item, token)
    let mut seen_control_flow_groups: HashMap<String, (usize, String, bool, Token)> =
        HashMap::new();

    for attr in attrs {
        let attr_name = &attr.key.content;

        // c-bind is a dynamic spread, so it is both repeatable and excluded
        // from explicit logical-key conflicts.
        if attr_name == "c-bind" {
            continue;
        }

        // Case 1: Check for duplicate attribute names
        // E.g. `<div class="x" class="y">` is invalid.
        let full_name_identity = if accumulates_html_attrs {
            attr_name.to_ascii_lowercase()
        } else {
            attr_name.clone()
        };
        if !seen_full_names.insert(full_name_identity) {
            return Err(context.error_from_token(
                &attr.token,
                format!(
                    "Duplicate attribute '{}' found. Each attribute name can only appear once (except 'c-bind').",
                    attr_name
                ),
            ));
        }

        // Structural directives do not render an ordinary attribute, so for
        // example HTML `for` and Citry `c-for` are different inputs.
        let is_control_flow_directive = CONTROL_FLOW_GROUPS
            .iter()
            .any(|group| group.contains(&attr_name.as_str()));
        if attr.kind != HtmlAttrKind::Meta && !is_control_flow_directive {
            let authored_logical_name = attr_name.strip_prefix("c-").unwrap_or(attr_name);
            let logical_name = if accumulates_html_attrs {
                authored_logical_name.to_ascii_lowercase()
            } else {
                authored_logical_name.to_string()
            };
            let is_accumulator =
                accumulates_html_attrs && matches!(logical_name.as_str(), "class" | "style");
            if !is_accumulator {
                if let Some(previous_name) = seen_logical_names.get(&logical_name) {
                    let source_ordered_client_binding = component_boundary
                        && is_component_tag_client_binding_attr(previous_name)
                        && is_component_tag_client_binding_attr(attr_name);
                    if previous_name != attr_name && !source_ordered_client_binding {
                        return Err(context.error_from_token(
                            &attr.token,
                            format!(
                                "Attributes '{}' and '{}' provide the same logical attribute '{}'. Choose one explicit spelling; use 'c-bind' for values supplied dynamically.",
                                previous_name, attr_name, logical_name
                            ),
                        ));
                    }
                } else {
                    seen_logical_names.insert(logical_name, attr_name.clone());
                }
            }
        }

        // Case 2: Check for control flow attribute conflicts
        //
        // Multiple attrs from same group is invalid:
        // - ❌ <div c-if="x" c-elif="y">
        // - ❌ <div c-if="x" c-else>
        // - ❌ <div c-elif="x" c-else>
        // - ❌ <div c-for="x" c-empty>
        //
        // Multiple attrs from different groups is valid:
        // - ✅ <div c-if="x" c-for="y">
        for (group_index, group) in CONTROL_FLOW_GROUPS.iter().enumerate() {
            if !group.contains(&attr_name.as_str()) {
                continue;
            }

            // Each kind of control flow (IF, FOR) is defined as a group of tags that belong to the same group.
            // We use the first item from the group's list as group names (e.g. "c-if", "c-for").
            let group_name = group[0].to_string();

            // Check if we've already seen another attribute from this group.
            // E.g. `<div c-if="x" c-elif="y">` is invalid.
            if seen_control_flow_groups.contains_key(&group_name) {
                // We've already seen an attribute from this group.
                let (_, prev_attr, _, _) = seen_control_flow_groups.get(&group_name).unwrap();
                return Err(context.error_from_token(
                    &attr.token,
                    format!(
                        "Cannot have both '{}' and '{}' attributes on the same tag. Only one control flow attribute from the group [{}] is allowed.",
                        prev_attr,
                        attr_name,
                        group.join(", ")
                    ),
                ));
            }

            let is_first_item = attr_name == group[0];
            seen_control_flow_groups.insert(
                group_name,
                (
                    group_index,
                    attr_name.clone(),
                    is_first_item,
                    attr.token.clone(),
                ),
            );

            // Found the group that matches current attribute, no need to check
            // other groups.
            break;
        }
    }

    // Case 3: Check for control flow priorities conflicts
    //
    // If a single tag uses attributes from several control flow group (e.g. IF and FOR),
    // then only the group with the highest priority can be non-first.
    //
    // E.g. IF has higher priority over FOR, so for IF we can use also `c-elif`, `c-else`,
    // while from the FOR group we MUST use only `c-for`.
    // - ✅ <div c-if="x" c-for="y">
    // - ✅ <div c-elif="x" c-for="y">
    // - ✅ <div c-else="x" c-for="y">
    //
    // - ❌ <div c-if="x" c-empty="y">
    // - ❌ <div c-elif="x" c-empty="y">
    // - ❌ <div c-else="x" c-empty="y">
    //
    // We can't mix IF with EMPTY, because `<c-empty>` would be nested
    // inside <c-if>/<c-elif>/<c-else>, and so would no longer have access to its <c-for>
    // (which is expected to come before <c-empty>).
    //
    // Only check if we have multiple control flow groups
    if seen_control_flow_groups.len() > 1 {
        // Sort by group_index (priority) from 0 (highest) to up
        let mut sorted_groups: Vec<(usize, String, bool, Token)> =
            seen_control_flow_groups.into_values().collect();
        sorted_groups.sort_by_key(|(group_index, _, _, _)| *group_index);

        // Take the first entry (highest priority group)
        let (_, first_attr, _, _) = &sorted_groups[0];

        // Check the remainder - all lower priority groups must use first items
        // At this point we know where is multiple attributes from multiple groups.
        // We also know that there CAN'T be multiple attributes from the SAME group.
        // So all items in `sorted_groups[1..]` will have different group_index. And this group_index
        // will be go higher, because we've already sorted the list by group_index.
        for (_, attr_name, is_first_item, attr_token) in &sorted_groups[1..] {
            if !is_first_item {
                return Err(context.error_from_token(
                    attr_token,
                    format!(
                        "Cannot have '{}' together with '{}'. '{}' has higher priority and will wrap the content before '{}'.",
                        first_attr, attr_name, first_attr, attr_name,
                    ),
                ));
            }
        }
    }

    Ok(())
}

/// Validate statically known `<c-fill>` names within a component node.
///
/// Only an effective static `name` participates in parse-time equality. A
/// `c-name` or `c-bind` expression is evaluated separately for every fill, so
/// identical authored expressions may still resolve to different names.
///
/// This validation applies only to component Nodes with body (e.g. `<c-component>` or `<c-MyComp>`).
///
/// `<c-fill>` tags may be nested inside control flow nodes (e.g. `<c-if>/<c-elif>/<c-else>` and `<c-for>/<c-empty>`),
/// so first we need to extract them all recursively from the body.
///
/// **Slot Validation:**
/// - If no `<c-fill>` nodes are found but body has meaningful content, it's treated as the "default" slot
/// - Validates against slot rules (allowed_slots and required_slots)
///
/// **Errors**
///
/// - If duplicate `name` values are found
/// - If slot name is not allowed (only when name value came from `name` attr, not dynamic `c-name`)
/// - If required slots are missing (only when no `<c-fill>` tags with `c-name` or `c-bind` attrs are present)
/// - If default slot is used but "default" slot name is not allowed
fn validate_fill_names(
    node: &Node,
    fill_nodes: &[FillNodeInfo],
    context: &ParserContext,
) -> Result<(), ParseError> {
    // Only validate component nodes with body
    let tag_name = node.tag_name();
    let is_component =
        has_citry_component_prefix(tag_name) && !is_reserved_citry_tag_identity(tag_name);

    if !is_component {
        return Ok(());
    }

    // Get slot rules for this tag (if any).
    // Even without rules, we still validate duplicates - that's always an error.
    // User rules are keyed by lowercase tag name (same rule as the attribute
    // validation: component tags match case-insensitively).
    let no_required: Vec<String> = vec![];
    let no_slot_data_fields: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let tag_name_lower = tag_name.to_ascii_lowercase();
    let builtin_tag_name = if citry_component_tag_eq(tag_name, C_COMPONENT_TAG) {
        C_COMPONENT_TAG
    } else if citry_component_tag_eq(tag_name, C_ELEMENT_TAG) {
        C_ELEMENT_TAG
    } else {
        tag_name
    };
    let (allowed_slots, required_slots, slot_data_fields) =
        if let Some(builtin_rules) = TAG_ATTR_RULES.get(builtin_tag_name) {
            // Built-in rules for built-in tags
            (
                &builtin_rules.allowed_slots,
                &builtin_rules.required_slots,
                &builtin_rules.slot_data_fields,
            )
        } else if let Some(user_rules) = context.user_rules.get(tag_name_lower.as_str()) {
            // User-defined rules for user-defined tags
            (
                &user_rules.allowed_slots,
                &user_rules.required_slots,
                &user_rules.slot_data_fields,
            )
        } else {
            // No slot rules defined for this tag - allow any slots, require none,
            // but still check for duplicates below.
            (&None, &no_required, &no_slot_data_fields)
        };

    let has_meaningful_content = match node {
        Node::WithBody { body, .. } => _has_fill_meaningful_content(body),
        Node::SelfClosing { .. } => false,
    };

    let format_error = |node: &Node, message: String| -> Result<(), ParseError> {
        let start_tag_token = &node.start_tag().token;
        Err(context.error_from_token(start_tag_token, message))
    };

    // Collect slot names from explicit <c-fill> tags
    let mut found_slots: HashSet<String> = HashSet::new();
    // Track the maximum possible number of unique fills at runtime.
    // Static `name` fills always count as 1. Dynamic fills (`c-name`/`c-bind`)
    // count as 1 unless inside a `<c-for>`, where they could provide unbounded fills.
    //
    // Examples:
    //   `<c-fill name="header">` => counts as 1 (static)
    //   `<c-fill c-name="slot_var">` => counts as 1 (dynamic, not in for loop)
    //   `<c-for each="s in slots"><c-fill c-name="s">` => unbounded (dynamic in for loop)
    //   `<c-for each="s in slots"><c-fill name="header">` => counts as 1 (static, even in for loop)
    //   `<c-empty><c-fill c-name="slot_var">` => counts as 1 (c-empty renders at most once)
    let mut max_possible_fills: usize = 0;
    let mut has_unbounded_dynamic_fill = false;
    // Whether any fill has a dynamic name (c-name or c-bind). When true,
    // the per-name required slot check is skipped since we can't know which
    // names the dynamic fills will resolve to at runtime.
    //
    // E.g. with `required_slots: ["default", "footer"]`:
    //   `<c-fill c-name="a"> <c-fill c-name="b">` => per-name check skipped
    //     (a and b could resolve to "default" and "footer" at runtime)
    //   `<c-fill name="default"> <c-fill name="footer">` => per-name check runs
    //     (both names are known statically)
    let mut has_any_dynamic_fill = false;

    if fill_nodes.is_empty() {
        // No explicit <c-fill> tags found
        // Check if body has meaningful content (treat as "default" slot)
        if has_meaningful_content {
            // Body has content - treat as implicit "default" slot
            found_slots.insert("default".to_string());
            max_possible_fills = 1;

            // Validate that implicit "default" slot is allowed
            if let Some(allowed_slots_list) = allowed_slots {
                if !allowed_slots_list.contains(&"default".to_string()) {
                    return format_error(
                        node,
                        format!(
                            "Tag '<{}>' does not allow a 'default' slot, but body content was provided.",
                            tag_name
                        ),
                    );
                }
            }
        }
    } else {
        // Explicit <c-fill> tags found - the body is a fill group, so nothing
        // outside the fills is allowed (whitespace-only text is formatting).
        if let Node::WithBody { body, .. } = node {
            validate_fill_group_content(body, context)?;
        }

        // Validate the fills themselves. Only final static identities can be
        // compared without evaluating user expressions.
        let mut seen_static_names: HashMap<String, &Node> = HashMap::new();

        // For overflow detection: count unique dynamic fills NOT inside any control flow tag.
        // These are fills whose identity is resolved at runtime (c-name or c-bind) and are
        // at the "top level" of the component body (not inside c-if/c-for/etc).
        let mut dynamic_fills_outside_control_flow: usize = 0;
        // Track static fill names that matched allowed_slots (for overflow remaining count)
        let mut static_fills_in_allowed: HashSet<String> = HashSet::new();

        for fill_info in fill_nodes {
            let fill_node = fill_info.node;
            let identity = _extract_fill_identity(fill_node);

            let is_dynamic = identity.is_dynamic();
            if is_dynamic {
                has_any_dynamic_fill = true;
            }

            // Validate identity and check for duplicates
            match &identity {
                FillIdentity::StaticName(name_value) => {
                    // Validate that this slot name is allowed.
                    // We can only validate static `name` attrs, not dynamic `c-name`.
                    // We skip if `allowed_slots` == None (any slot name allowed)
                    if let Some(allowed_slots_list) = allowed_slots {
                        if !allowed_slots_list.contains(name_value) {
                            return format_error(
                                fill_node,
                                format!(
                                    "Tag '<{}>' does not allow a slot named '{}'.",
                                    tag_name, name_value
                                ),
                            );
                        }
                        // Track this static fill for overflow detection
                        static_fills_in_allowed.insert(name_value.clone());
                    }

                    validate_fill_data_sources(
                        fill_node,
                        tag_name,
                        name_value,
                        slot_data_fields,
                        context,
                    )?;

                    // Check for duplicate static name values.
                    //
                    // Duplicate detection only covers fills OUTSIDE control flow:
                    // the same name in mutually exclusive branches (c-if/c-else)
                    // is valid, since at most one branch materializes at runtime.
                    // Duplicates that DO materialize together are caught at
                    // runtime, during fill collection.
                    //
                    // NOTE: A future improvement could analyze branches to catch
                    // guaranteed duplicates (e.g. two same-name fills in ONE
                    // branch) statically, but this is not implemented yet.
                    if !fill_info.inside_control_flow {
                        if seen_static_names.contains_key(name_value) {
                            return format_error(
                                fill_node,
                                format!(
                                    "Duplicate <c-fill> with name='{}' found. Each fill name can only appear once.",
                                    name_value
                                ),
                            );
                        }
                        seen_static_names.insert(name_value.clone(), fill_node);
                    }
                    found_slots.insert(name_value.clone());
                }
                FillIdentity::Dynamic => {
                    // Dynamic identities are resolved independently at runtime,
                    // where duplicate resolved names are validated.
                    if !fill_info.inside_control_flow {
                        // Track dynamic fills not inside control flow for overflow detection
                        dynamic_fills_outside_control_flow += 1;
                    }
                }
                FillIdentity::None => {
                    // No identity attrs - skip duplicate check.
                    // Missing attrs are validated elsewhere (validate_attributes_present).
                }
            }

            // Count towards max possible fills:
            // - Static `name` fills always count as 1 (even inside for loop, the name doesn't change)
            //   E.g. `<c-for each="x in xs"><c-fill name="header">` => 1 (loop repeats same name)
            // - Dynamic fills (`c-name`/`c-bind`) inside `<c-for>` are unbounded
            //   E.g. `<c-for each="s in slots"><c-fill c-name="s">` => unbounded
            // - Dynamic fills NOT inside `<c-for>` count as 1
            //   E.g. `<c-fill c-name="slot_var">` => 1
            if is_dynamic && fill_info.inside_for_loop {
                has_unbounded_dynamic_fill = true;
            } else {
                max_possible_fills += 1;
            }
        }

        // Overflow check: if all allowed slots are statically filled and there are extra
        // dynamic fills outside of control flow, it's guaranteed to fail at runtime.
        //
        // The dynamic fill will either:
        //   - resolve to an already-filled slot name => duplicate error at runtime
        //   - resolve to a non-allowed slot name => not-allowed error at runtime
        //
        // This check explicitly excludes fills inside ANY control flow tag
        // (c-if/c-elif/c-else/c-for/c-empty) because conditional/loop branches make
        // it too complex to reason about statically.
        //
        // NOTE: A future improvement could analyze control flow branches to verify
        // that each branch doesn't exceed the allowed slot count, but this is not
        // implemented yet.
        //
        // Examples (with `allowed_slots=["h", "f"]`):
        //   `<c-fill name="h"> <c-fill name="f"> <c-fill c-name="x">` => error (0 remaining, 1 dynamic)
        //   `<c-fill name="h"> <c-fill c-name="x">` => ok (1 remaining, 1 dynamic)
        //   `<c-fill name="h"> <c-fill name="f"> <c-if ..><c-fill c-name="x"></c-if>` => ok (inside control flow)
        if let Some(allowed_slots_list) = allowed_slots {
            if dynamic_fills_outside_control_flow > 0 {
                let remaining = allowed_slots_list
                    .len()
                    .saturating_sub(static_fills_in_allowed.len());
                if dynamic_fills_outside_control_flow > remaining {
                    return format_error(
                        node,
                        format!(
                            "Tag '<{}>' allows {} slot(s), but {} are statically filled and there are {} additional dynamic fill(s) outside control flow. \
                            The dynamic fill(s) will either duplicate an existing slot or use a non-allowed name.",
                            tag_name,
                            allowed_slots_list.len(),
                            static_fills_in_allowed.len(),
                            dynamic_fills_outside_control_flow,
                        ),
                    );
                }
            }
        }
    }

    // Validate required slots
    if !required_slots.is_empty() && !has_unbounded_dynamic_fill {
        // Count check: even with dynamic fills, if the total number of possible
        // unique fills is fewer than required slots, we know it can't work.
        //
        // E.g. with `required_slots: ["default", "footer"]`:
        //   `<c-fill c-name="x">` => 1 fill < 2 required => error
        //   `<c-fill c-name="x"> <c-fill c-name="y">` => 2 fills >= 2 required => ok
        if max_possible_fills < required_slots.len() {
            return format_error(
                node,
                format!(
                    "Tag '<{}>' requires {} slot(s), but only {} <c-fill> tag(s) were provided.",
                    tag_name,
                    required_slots.len(),
                    max_possible_fills,
                ),
            );
        }

        // Per-name check: verify each required slot is present.
        // This only applies when ALL fills are static, because dynamic fills
        // (c-name/c-bind) could resolve to any name at runtime.
        //
        // E.g. with `required_slots: ["default", "footer"]`:
        //   `<c-fill name="default"> <c-fill name="header">` => "footer" missing => error
        //   `<c-fill name="default"> <c-fill c-name="x">` => skipped (x could be "footer")
        if !has_any_dynamic_fill {
            for required_slot in required_slots {
                if !found_slots.contains(required_slot.as_str()) {
                    return format_error(
                        node,
                        format!(
                            "Tag '<{}>' must have a slot named '{}'.",
                            tag_name, required_slot
                        ),
                    );
                }
            }
        }
    }

    Ok(())
}

/// Check if a template body has content beyond formatting whitespace.
fn _has_fill_meaningful_content(body: &Template) -> bool {
    body.elements.iter().any(|element| match element {
        TemplateElement::Text(text) => !text.token.content.trim().is_empty(),
        TemplateElement::Expr(_) | TemplateElement::Node(_) => true,
    })
}

/// Info about a `<c-fill>` node found during extraction, including whether it's
/// nested inside a `<c-for>` loop or any control flow tag.
struct FillNodeInfo<'a> {
    node: &'a Node,
    /// Whether this fill is nested inside a `<c-for>` tag (directly or via other
    /// control flow tags). This matters for required slots validation: a dynamic
    /// fill inside a for loop could provide any number of fills at runtime.
    /// Note: `<c-empty>` does NOT count, as it renders at most once.
    ///
    /// Examples:
    /// - `<c-for each="s in slots"><c-fill c-name="s"></c-fill></c-for>` => true
    /// - `<c-if cond="x"><c-for each="s in slots"><c-fill c-name="s"></c-fill></c-for></c-if>` => true
    /// - `<c-empty><c-fill c-name="s"></c-fill></c-empty>` => false
    /// - `<c-fill c-name="s"></c-fill>` => false
    inside_for_loop: bool,
    /// Whether this fill is nested inside ANY control flow tag
    /// (`c-if/c-elif/c-else/c-for/c-empty`). Used for the overflow check:
    /// fills inside control flow are excluded from the "dynamic fills exceed
    /// remaining allowed slots" validation, because conditional/loop branches
    /// make it too complex to reason about statically.
    ///
    /// NOTE: A future improvement could analyze branches to verify that all
    /// branches provide at least the same fills, but this is not implemented yet.
    ///
    /// Examples:
    /// - `<c-if cond="x"><c-fill c-name="s"></c-fill></c-if>` => true
    /// - `<c-for each="s in slots"><c-fill c-name="s"></c-fill></c-for>` => true
    /// - `<c-fill c-name="s"></c-fill>` => false
    inside_control_flow: bool,
}

/// Recursively collect all `<c-fill>` nodes from a template body.
///
/// This searches through all elements, including those nested inside control flow nodes
/// (`<c-if>/<c-elif>/<c-else>` and `<c-for>/<c-empty>`).
///
/// Tracks two flags per fill:
/// - `inside_for_loop`: true only when inside a `<c-for>` ancestor (not `<c-empty>`)
/// - `inside_control_flow`: true when inside ANY control flow tag
///
/// Example: given this template body for `<c-my-comp>`:
/// ```html
/// <c-fill name="header">...</c-fill>
/// <c-for each="s in slots">
///   <c-fill c-name="s">...</c-fill>
/// </c-for>
/// <c-empty>
///   <c-fill name="fallback">...</c-fill>
/// </c-empty>
/// ```
/// Returns 3 FillNodeInfo entries:
/// - `name="header"` with `inside_for_loop: false, inside_control_flow: false`
/// - `c-name="s"` with `inside_for_loop: true, inside_control_flow: true`
/// - `name="fallback"` with `inside_for_loop: false, inside_control_flow: true`
fn extract_fill_nodes(
    template: &Template,
    inside_for_loop: bool,
    inside_control_flow: bool,
) -> Vec<FillNodeInfo<'_>> {
    let mut fill_nodes = Vec::new();

    for element in &template.elements {
        match element {
            TemplateElement::Node(node) => {
                let tag_name = node.tag_name();
                if tag_name == C_FILL_TAG {
                    fill_nodes.push(FillNodeInfo {
                        node,
                        inside_for_loop,
                        inside_control_flow,
                    });
                } else if CONTROL_FLOW_TAGS.contains(&tag_name) {
                    // Recursively search inside control flow nodes.
                    // Only `<c-for>` sets inside_for_loop to true.
                    // `<c-empty>` does NOT - it renders at most once.
                    // ALL control flow tags set inside_control_flow to true.
                    if let Node::WithBody { body, .. } = node {
                        let nested_inside_for = inside_for_loop || tag_name == C_FOR_TAG;
                        fill_nodes.extend(extract_fill_nodes(body, nested_inside_for, true));
                    }
                } else {
                    // NOTE: When we come across nested components or regular HTML tags,
                    // we stop the search and don't go deeper, as these are already part of the content itself,
                    // not content delimiters. So when we see a nested component or regular HTML tag,
                    // we can assume that what's inside the component is an implicit "default" slot.
                    //
                    // Of course, it could happen that there'd be both content-like tags and <c-fill> tags, e.g.
                    // ```html
                    // <c-my-comp>
                    //   <div>Hello</div>
                    //   <c-fill name="footer"> </c-fill>
                    // </c-my-comp>
                    // ```
                    // This would be invalid, and we check for it in `validate_fill_exclusivity()`.
                }
            }
            _ => {
                // Text and Expr don't contain nodes
            }
        }
    }

    fill_nodes
}

/// The effective identity category of a `<c-fill>` node.
///
/// Determined by walking the node's attributes right-to-left and finding the
/// rightmost `name`, `c-name`, or `c-bind` attribute.
///
/// - If rightmost is `name` -> `StaticName(value)`
/// - If rightmost is `c-name` or `c-bind` -> `Dynamic`
/// - If none found -> `None`
///
/// Examples:
/// - `<c-fill c-bind="b" name="a">` -> rightmost=`name` -> `StaticName("a")`
/// - `<c-fill name="a" c-bind="b">` -> rightmost=`c-bind` -> `Dynamic`
///
/// Explicit `name` and `c-name` cannot coexist; `c-bind` may interlace with
/// either explicit provider because its keys are known only at render time.
#[derive(Debug, Clone, PartialEq, Eq)]
enum FillIdentity {
    /// Rightmost identity attr is `name="..."` -> static slot name
    StaticName(String),
    /// Rightmost identity attr is `c-name="..."` or `c-bind="..."`.
    Dynamic,
    /// No identity attrs at all (no name, c-name, or c-bind)
    None,
}

impl FillIdentity {
    /// Returns true if this identity is dynamic (resolved at runtime).
    fn is_dynamic(&self) -> bool {
        matches!(self, FillIdentity::Dynamic)
    }
}

/// Extract the identity of a `<c-fill>` node by walking its attributes right-to-left.
///
/// See [`FillIdentity`] for the full identity resolution rules.
fn _extract_fill_identity(node: &Node) -> FillIdentity {
    node.attrs()
        .iter()
        .rev()
        .find_map(|attr| match attr.key.content.as_str() {
            "name" => Some(FillIdentity::StaticName(
                attr.inner_value
                    .as_ref()
                    .map(|value| value.content.clone())
                    .unwrap_or_default(),
            )),
            "c-name" | "c-bind" => Some(FillIdentity::Dynamic),
            _ => None,
        })
        .unwrap_or(FillIdentity::None)
}

/// Validate explicit source fields in the effective direct `data` binding.
///
/// Both the slot identity and the data provider use rightmost-provider
/// semantics. The caller invokes this helper only for a statically named fill;
/// if a rightmost `c-bind` can provide `data`, the data shape remains a runtime
/// concern. Whole-data bindings and `**rest` select no explicit source fields.
fn validate_fill_data_sources(
    fill_node: &Node,
    component_tag_name: &str,
    slot_name: &str,
    slot_data_fields: &BTreeMap<String, Vec<String>>,
    context: &ParserContext,
) -> Result<(), ParseError> {
    let Some(allowed_fields) = slot_data_fields.get(slot_name) else {
        return Ok(());
    };
    let Some(pattern) = _extract_effective_fill_data_pattern(fill_node) else {
        return Ok(());
    };

    for field in &pattern.fields {
        if allowed_fields.contains(&field.source.content) {
            continue;
        }
        let available = if allowed_fields.is_empty() {
            "This slot's declared data shape has no fields.".to_string()
        } else {
            format!("Available fields: {}.", allowed_fields.join(", "))
        };
        return Err(context.error_from_token(
            &field.source,
            format!(
                "Slot '{}' on tag '<{}>' does not expose a slot-data field named '{}'. {}",
                slot_name, component_tag_name, field.source.content, available
            ),
        ));
    }
    Ok(())
}

/// Return the effective direct data pattern, or `None` for no data provider or
/// a rightmost dynamic `c-bind` provider.
fn _extract_effective_fill_data_pattern(node: &Node) -> Option<&FillDataPattern> {
    node.attrs()
        .iter()
        .rev()
        .find_map(|attr| match attr.key.content.as_str() {
            "data" => Some(attr.fill_data_pattern.as_ref()),
            "c-bind" => Some(None),
            _ => None,
        })?
}

/// Extract slot information from a `<c-slot>` node.
///
/// Returns `Some(StaticNamedSlot)` if:
/// - The node is a `<c-slot>` tag
/// - Its effective name is statically known: the rightmost name provider is a
///   static `name` attribute, or there is no name provider (`name`, `c-name`,
///   or `c-bind`), in which case the slot is named `"default"`. The synthesized
///   default-name token carries the start-tag token's position.
///
/// Returns `None` when the rightmost name provider is dynamic (`c-name`, or
/// `c-bind` which may supply a name at runtime).
///
/// The rightmost requiredness provider determines `required` independently:
/// static `required` gives `Some(true)`, `c-required` or `c-bind` gives `None`,
/// and no provider gives `Some(false)`.
fn extract_slot_from_node(node: &Node) -> Option<StaticNamedSlot> {
    let tag_name = node.tag_name();
    if tag_name != C_SLOT_TAG {
        return None;
    }

    let attrs = node.attrs();

    // Runtime attributes resolve left to right. The rightmost name provider
    // therefore decides whether this slot can be declared statically.
    let name_token = match attrs
        .iter()
        .rev()
        .find(|attr| matches!(attr.key.content.as_str(), "name" | "c-name" | "c-bind"))
    {
        Some(attr) if attr.key.content == "name" => attr.inner_value.clone()?,
        Some(_) => return None,
        None => {
            // No name provider means the default slot. Anchor the synthesized
            // token at the start tag because there is no source value.
            let tag_token = &node.start_tag().token;
            Token {
                content: "default".to_string(),
                start_index: tag_token.start_index,
                end_index: tag_token.end_index,
                line_col: tag_token.line_col,
            }
        }
    };

    // The same rightmost-provider rule applies independently to requiredness.
    let required = match attrs.iter().rev().find(|attr| {
        matches!(
            attr.key.content.as_str(),
            "required" | "c-required" | "c-bind"
        )
    }) {
        Some(attr) if attr.key.content == "required" => Some(true),
        Some(_) => None,
        None => Some(false),
    };

    Some(StaticNamedSlot {
        token: name_token,
        required,
    })
}

/// Validate that a node can follow the previous nodes in the template.
///
/// This checks tag ordering rules (e.g., `<c-elif>` can only follow `<c-if>`).
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
///
/// So the validation needs to check for both the tag name and the attributes.
///
/// # Errors
/// - If the tag requires a previous tag but `template.elements` is empty
/// - If the tag requires a previous tag but `template.elements` contains no Nodes
/// - If the effective outer control-flow tag of the previous Node is not in the
///   allowed set.
fn effective_control_flow_tag(node: &Node) -> &str {
    let physical_tag = node.tag_name();
    if CONTROL_FLOW_TAGS.contains(physical_tag) {
        return physical_tag;
    }

    // Match the compiler's lowering precedence exactly. A node carrying both
    // `c-if` and `c-for` becomes an if whose body is a for, so a following
    // `c-empty` must not attach to that inner loop across the outer if.
    for group in CONTROL_FLOW_GROUPS {
        for control_tag in *group {
            if node
                .attrs()
                .iter()
                .any(|attr| attr.key.content == *control_tag)
            {
                return control_tag;
            }
        }
    }

    physical_tag
}

fn validate_tag_grouping(
    node: &Node,
    template: &Template,
    context: &ParserContext,
) -> Result<(), ParseError> {
    let tag_name = effective_control_flow_tag(node);

    // If this tag has no ordering constraints, it's valid
    let Some(allowed_previous_tags) = TAG_ORDERING_RULES.get(tag_name) else {
        return Ok(());
    };

    // Get the start_tag token for error reporting
    let start_tag_token = &node.start_tag().token;

    // Format allowed tags for error message
    let allowed_tags_str = || -> String {
        allowed_previous_tags
            .iter()
            .map(|tag| format!("<{}>", tag))
            .collect::<Vec<String>>()
            .join(", ")
    };

    // Find the previous element sibling in the parent's template.elements.
    // We are constructing the template as we go, so the last Node in the template will be the last FINISHED Node.
    // The Node that is being validated is NOT YET FINISHED, so it's not part of the template.
    // See: https://developer.mozilla.org/en-US/docs/Web/API/Element/previousElementSibling
    //
    // Whitespace-only text between the branches of one group is formatting,
    // not content (the compiler drops it when grouping the branches), so it is
    // skipped here. Anything else in between (text, an HTML comment, which
    // parses as a Text element, or a `{{ ... }}` expression) breaks the group:
    // the branches must act as a single node, and content between them would
    // have nowhere to render. That is rejected here, at parse time, instead of
    // compiling the orphaned branch tag into an unknown component.
    let mut previous_node: Option<&Node> = None;
    for elem in template.elements.iter().rev() {
        match elem {
            TemplateElement::Node(n) => {
                previous_node = Some(n);
                break;
            }
            TemplateElement::Text(text) if text.token.content.trim().is_empty() => continue,
            TemplateElement::Text(_) | TemplateElement::Expr(_) => {
                return Err(context.error_from_token(
                    start_tag_token,
                    format!(
                        "Tag '<{}>' must follow one of: {}. Found other content in between.",
                        tag_name,
                        allowed_tags_str()
                    ),
                ));
            }
        }
    }
    let previous_node = previous_node.ok_or_else(|| {
        // No previous node found
        context.error_from_token(
            start_tag_token,
            format!(
                "Tag '<{}>' must follow one of: {}. No previous tag found.",
                tag_name,
                allowed_tags_str()
            ),
        )
    })?;

    // We've found the previous node. Now check if it's allowed
    let prev_tag_name = effective_control_flow_tag(previous_node);

    if !allowed_previous_tags.contains(prev_tag_name) {
        return Err(context.error_from_token(
            start_tag_token,
            format!(
                "Tag '<{}>' must follow one of: {}. Found '<{}>' instead.",
                tag_name,
                allowed_tags_str(),
                prev_tag_name
            ),
        ));
    }

    Ok(())
}
