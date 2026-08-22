//! Orchestrates one formatting run and proves the result before returning it.
//!
//! Formatting proper lives in `format_once`; everything in `verify_candidate`
//! exists so this crate never hands back text it cannot vouch for. The checks
//! compare the template against itself before and after, so they catch a
//! printer that moved bytes it should not have. They cannot catch a wrong
//! judgment in `html.rs` about where whitespace matters, because both sides
//! would then be wrong the same way.

use citry_template_parser::{ParseOptions, Template, parse_template, parse_template_with_options};

use crate::error::FormatError;
use crate::printer::EditPlan;
use crate::projection::{ProjectionCapability, verify_contract_projection_with_options};
use crate::source::SourceModel;

/// Format `source`, then refuse to return the result unless it verifies.
pub(crate) fn format(source: &str) -> Result<String, FormatError> {
    format_with_options(source, &ParseOptions::default())
}

pub(crate) fn format_with_options(
    source: &str,
    options: &ParseOptions,
) -> Result<String, FormatError> {
    let options = options
        .localized_for_source(source)
        .map_err(|error| FormatError::from_parse(&error))?;
    let (candidate, before_model, candidate_options) = format_once_with_options(source, &options)?;
    verify_candidate_with_options(
        source,
        &options,
        &candidate,
        &candidate_options,
        &before_model,
    )?;
    Ok(candidate)
}

/// Check the six properties a formatted template has to have.
///
/// Every failure here is an `Invariant` error rather than a formatting result:
/// the formatter got something wrong, and returning the text anyway would hand
/// the caller a corrupted template.
#[cfg(test)]
fn verify_candidate(
    source: &str,
    candidate: &str,
    before_model: &SourceModel,
) -> Result<(), FormatError> {
    verify_candidate_with_options(
        source,
        &ParseOptions::default(),
        candidate,
        &ParseOptions::default(),
        before_model,
    )
}

fn verify_candidate_with_options(
    source: &str,
    source_options: &ParseOptions,
    candidate: &str,
    candidate_options: &ParseOptions,
    before_model: &SourceModel,
) -> Result<(), FormatError> {
    // 1. The edit plan is a pure function of the input. Re-deriving it from the
    // original source must land on the same bytes, which is what rules out a
    // printer that depends on iteration order or leftover state.
    let (planned_candidate, _, planned_options) = format_once_with_options(source, source_options)
        .map_err(|error| {
            FormatError::invariant(format!(
                "formatter could not reproduce its edit plan during verification: {error}"
            ))
        })?;
    if planned_candidate != candidate || planned_options != *candidate_options {
        return Err(FormatError::invariant(
            "formatted template does not match the deterministic structural edit plan",
        ));
    }

    // 2. Re-laying out markup must not change what the markup means. The
    // projection keeps only the parts a reader's browser reacts to, so two
    // templates with the same projection render the same however differently
    // they are indented.
    verify_contract_projection_with_options(
        source,
        source_options,
        candidate,
        candidate_options,
        ProjectionCapability::PythonExpressions,
    )
    .map_err(|error| {
        FormatError::invariant(format!(
            "formatted template changed the structural layout contract: {error}"
        ))
    })?;

    // 3. Output that no longer parses is always a bug, never a result. The
    // model rebuilt here is also what the remaining fingerprint checks read.
    let parsed_candidate = parse_with_options(candidate, candidate_options).map_err(|error| {
        FormatError::invariant(format!("formatted template did not reparse: {error}"))
    })?;
    let after_model =
        SourceModel::build_with_options(candidate, &parsed_candidate, candidate_options)?;
    // 4. Comments carry author intent and several of them are directives, so
    // losing, duplicating, or reordering one is never an acceptable trade for
    // nicer layout.
    if before_model.markup_comment_fingerprint() != after_model.markup_comment_fingerprint() {
        return Err(FormatError::invariant(
            "formatted template changed the canonical markup comment inventory",
        ));
    }
    // 5. Two kinds of bytes the author put off limits: ranges behind a
    // suppression directive, and verbatim bodies such as `<c-raw>`. Both are
    // compared as fingerprints rather than spans because the surrounding text
    // may legitimately have moved.
    if before_model.protected_fingerprint(source)?
        != after_model.protected_fingerprint(candidate)?
    {
        return Err(FormatError::invariant(
            "formatted template changed protected suppression bytes",
        ));
    }
    if before_model.verbatim_fingerprint() != after_model.verbatim_fingerprint() {
        return Err(FormatError::invariant(
            "formatted template changed a verbatim body",
        ));
    }

    // 6. Formatting an already formatted template must be a no-op. Without
    // this, formatting on every save could walk a file a little further each
    // time and show up as endless diff noise.
    let (second_pass, _, second_pass_options) =
        format_once_with_options(candidate, candidate_options).map_err(|error| {
            FormatError::invariant(format!(
                "formatted template failed its second pass: {error}"
            ))
        })?;
    if second_pass != candidate || second_pass_options != *candidate_options {
        return Err(FormatError::invariant(
            "formatted template was not byte-idempotent",
        ));
    }
    Ok(())
}

/// Apply edit passes until the text stops changing.
///
/// Returns the formatted text together with the model built from the *original*
/// source, which is what the fingerprint checks above compare against.
#[cfg(test)]
fn format_once(source: &str) -> Result<(String, SourceModel), FormatError> {
    let (candidate, model, _) = format_once_with_options(source, &ParseOptions::default())?;
    Ok((candidate, model))
}

fn format_once_with_options(
    source: &str,
    options: &ParseOptions,
) -> Result<(String, SourceModel, ParseOptions), FormatError> {
    // Parsing first is what makes the rest safe: only spans the parse
    // identified are ever edited, so a `{# fmt: on #}` sitting inside an
    // attribute value or a `<c-raw>` body stays ordinary text.
    let template =
        parse_with_options(source, options).map_err(|error| FormatError::from_parse(&error))?;
    let mut model = SourceModel::build_with_options(source, &template, options)?;
    let before_model = model.clone();
    // Layout columns and one-line fit can change after an earlier structural,
    // tag, or expression edit. Those dependencies point forward in source
    // order, so one pass per editable item plus a fixed-point check is ample.
    let max_passes = model
        .tags
        .len()
        .saturating_add(model.body_gaps.len())
        .saturating_add(model.expressions.len())
        .saturating_add(2);
    let mut current = source.to_string();
    let mut current_options = options.clone();

    for _ in 0..max_passes {
        let plan = EditPlan::build(&current, &model)?;
        // Check the plan against the protected ranges before touching anything,
        // so an edit that would reach into suppressed bytes never runs.
        plan.validate_for_source(&current, &model.protected)?;
        let candidate = plan.apply(&current)?;
        let candidate_options = plan.rebase_options(&current_options)?;
        // A pass that changes nothing is the fixed point: everything that could
        // move has moved, and the columns it depended on have settled.
        if candidate == current {
            return Ok((candidate, before_model, candidate_options));
        }

        // Edits shift every offset after them, so the model is rebuilt from the
        // new text rather than patched. A failure here means the formatter
        // produced something it cannot read back, which is a bug in the plan.
        current = candidate;
        current_options = candidate_options;
        let template = parse_with_options(&current, &current_options).map_err(|error| {
            FormatError::invariant(format!(
                "an intermediate formatter pass did not reparse: {error}"
            ))
        })?;
        model = SourceModel::build_with_options(&current, &template, &current_options).map_err(
            |error| {
                FormatError::invariant(format!(
                    "an intermediate formatter pass failed source validation: {error}"
                ))
            },
        )?;
    }

    // Reaching here means two passes kept undoing each other. That is a
    // formatter bug, so stop rather than return whichever text the loop
    // happened to end on.
    Err(FormatError::invariant(format!(
        "formatter did not converge after {max_passes} passes"
    )))
}

fn parse_with_options(
    source: &str,
    options: &ParseOptions,
) -> Result<Template, Box<citry_template_parser::ParseError>> {
    if options == &ParseOptions::default() {
        parse_template(source, None, None)
    } else {
        parse_template_with_options(source, None, None, options)
    }
    .map_err(Box::new)
}

#[cfg(test)]
mod tests {
    use crate::error::FormatErrorKind;

    use super::{format, format_once, verify_candidate};

    #[test]
    fn structural_formatting_recurses_into_nested_template_values() {
        let source = r#"<c-card  c-body="<div  class = 'x' ></div>" ></c-card>"#;
        let expected = r#"<c-card c-body="<div class='x'></div>"></c-card>"#;

        assert_eq!(format(source).unwrap(), expected);
    }

    #[test]
    fn verification_rejects_semantic_and_source_preservation_mutations() {
        let source = "<c-card title='x' disabled>{{ user.name }}text{# note #}</c-card>";
        let (_, before_model) = format_once(source).unwrap();
        let mutations = [
            "<c-panel title='x' disabled>{{ user.name }}text{# note #}</c-panel>",
            "<c-card title='y' disabled>{{ user.name }}text{# note #}</c-card>",
            "<c-card title=\"x\" disabled>{{ user.name }}text{# note #}</c-card>",
            "<c-card disabled title='x'>{{ user.name }}text{# note #}</c-card>",
            "<c-card title='x' disabled>{{ user.id }}text{# note #}</c-card>",
            "<c-card title='x' disabled>{{ user.name }}copy{# note #}</c-card>",
            "<c-card title='x' disabled>{{ user.name }}text</c-card>",
            "<c-card title='x' disabled>{{ user.name }}text{# note #}</c-panel>",
        ];

        for mutation in mutations {
            let error = verify_candidate(source, mutation, &before_model).unwrap_err();
            assert_eq!(error.kind(), FormatErrorKind::Invariant, "{mutation}");
        }

        let structural_source = "<main><section></section></main>";
        let (_, structural_model) = format_once(structural_source).unwrap();
        let unplanned_layout = "<main>\n<section></section>\n</main>";
        let error = verify_candidate(structural_source, unplanned_layout, &structural_model)
            .expect_err("unplanned structural layout must be rejected");
        assert_eq!(error.kind(), FormatErrorKind::Invariant);
    }

    #[test]
    fn unquoted_provider_results_fall_back_per_region() {
        assert_eq!(
            format("<div c-title=x+1></div>").unwrap(),
            "<div c-title=x+1></div>"
        );
        assert_eq!(
            format("<c-Card>\n<c-fill name=item data={first,second}></c-fill>\n</c-Card>").unwrap(),
            "<c-Card>\n<c-fill name=item data={first,second}></c-fill>\n</c-Card>",
        );
    }

    #[test]
    fn embedded_python_suppression_comments_preserve_their_region() {
        let cases = [
            "<div c-title=\"foo(  1)  # fmt: skip\"></div>",
            "{{foo(  1)  # fmt: skip}}",
            "<c-for each=\"item  in items  # fmt: skip\">{{ item }}</c-for>",
        ];
        for source in cases {
            assert_eq!(format(source).unwrap(), source);
        }
    }

    #[test]
    fn long_fill_data_patterns_use_citry_owned_multiline_layout() {
        let fields = (0..12)
            .map(|index| format!("field_{index}_with_a_name"))
            .collect::<Vec<_>>()
            .join(",");
        let source =
            format!("<c-Card>\n<c-fill name=\"item\" data=\"{{{fields}}}\"></c-fill>\n</c-Card>");
        let formatted = format(&source).unwrap();
        assert!(formatted.contains("data=\"{\n"));
        assert!(formatted.contains("field_11_with_a_name,\n"));
        assert!(formatted.lines().all(|line| line.chars().count() <= 100));
        assert_eq!(format(&formatted).unwrap(), formatted);
    }

    #[test]
    fn python_comment_normalization_preserves_provider_owned_comments() {
        let cases = [
            (
                "<div c-title=\"foo( 1)  #comment\"></div>",
                "<div c-title=\"foo(1)  # comment\"></div>",
            ),
            (
                "<li c-for=\"item in items  #keep\">{{item}}</li>",
                "<li c-for=\"item in items  # keep\">{{ item }}</li>",
            ),
            (
                "<main>{{user.name  # person}}</main>",
                "<main>{{ user.name  # person }}</main>",
            ),
        ];
        for (source, expected) in cases {
            assert_eq!(format(source).unwrap(), expected);
        }
    }

    #[test]
    fn python_regions_follow_lone_cr_and_account_for_suffix_width() {
        let lone_cr = "<main>\r{{[first,  # keep\rsecond]}}\r</main>\r";
        let formatted_cr = format(lone_cr).unwrap();
        assert!(!formatted_cr.contains('\n'));
        assert_eq!(format(&formatted_cr).unwrap(), formatted_cr);

        let callable = "f".repeat(76);
        let source = format!("<main>{{{{ {callable}(first, second) }}}}</main>");
        let formatted = format(&source).unwrap();
        assert!(formatted.contains('\n'));
        assert!(formatted.lines().all(|line| line.chars().count() <= 100));
        assert_eq!(format(&formatted).unwrap(), formatted);
    }

    #[test]
    fn adjacent_interpolations_converge_across_the_width_boundary() {
        let expression = "{{foo( 1,bar= [1,2])}}";
        for count in 1..=12 {
            let source = format!("<main>{}</main>", expression.repeat(count));
            let formatted = format(&source).unwrap();
            assert_eq!(format(&formatted).unwrap(), formatted, "count={count}");
        }
    }

    #[test]
    fn deeply_nested_expression_respects_absolute_width() {
        let source = format!("<p>{}{{{{foo(first,second)}}}}</p>", "x".repeat(85));
        let formatted = format(&source).unwrap();
        assert!(formatted.lines().all(|line| line.chars().count() <= 100));
        assert!(formatted.contains("first,"));
        assert_eq!(format(&formatted).unwrap(), formatted);
    }

    #[test]
    fn leading_multiline_expression_uses_its_parent_tag_column() {
        let source = concat!(
            "<main><section>{{build_payload(",
            "first_argument,second_argument,third_argument,fourth_argument,",
            "fifth_argument,sixth_argument,seventh_argument",
            ")}}</section></main>",
        );
        let expected = concat!(
            "<main>\n",
            "  <section>{{\n",
            "    build_payload(\n",
            "      first_argument,\n",
            "      second_argument,\n",
            "      third_argument,\n",
            "      fourth_argument,\n",
            "      fifth_argument,\n",
            "      sixth_argument,\n",
            "      seventh_argument,\n",
            "    )\n",
            "  }}</section>\n",
            "</main>",
        );

        assert_eq!(format(source).unwrap(), expected);
        assert_eq!(format(expected).unwrap(), expected);
    }
}
