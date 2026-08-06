use citry_template_formatter::{
    EmbeddedFormatResult, EmbeddedLanguage, EmbeddedRegionKind, finish_embedded_format,
    prepare_embedded_format,
};

#[test]
fn plans_and_composes_expression_free_script_and_style_bodies() {
    let source = include_str!("fixtures/v1/embedded/script-style.input.citry-html");
    let expected = include_str!("fixtures/v1/embedded/script-style.expected.citry-html");
    let plan = prepare_embedded_format(source).expect("prepare embedded formatting");

    assert_eq!(plan.requests().len(), 2);
    assert_eq!(plan.requests()[0].language(), EmbeddedLanguage::JavaScript);
    assert_eq!(plan.requests()[0].kind(), EmbeddedRegionKind::ScriptBody);
    assert_eq!(plan.requests()[1].language(), EmbeddedLanguage::Css);
    assert_eq!(plan.requests()[1].kind(), EmbeddedRegionKind::StyleBody);

    let results = [
        EmbeddedFormatResult::formatted(
            plan.id(),
            plan.requests()[0].id(),
            "const answer = 41 + 1;\n",
            Some("fake-javascript@1"),
        ),
        EmbeddedFormatResult::formatted(
            plan.id(),
            plan.requests()[1].id(),
            ".card {\n  color: red;\n}\n",
            Some("fake-css@1"),
        ),
    ];
    let outcome = finish_embedded_format(&plan, &results).expect("compose embedded formatting");

    assert_eq!(outcome.source(), expected);
    assert_eq!(outcome.providers(), &["fake-css@1", "fake-javascript@1"]);
    assert!(outcome.notices().is_empty());
}

#[test]
fn unsupported_and_protected_bodies_are_not_offered_to_providers() {
    let source = include_str!("fixtures/v1/preservation/unavailable.input.citry-html");
    let plan = prepare_embedded_format(source).expect("prepare embedded formatting");

    assert!(plan.requests().is_empty());
    let codes = plan
        .notices()
        .iter()
        .map(|notice| notice.code())
        .collect::<Vec<_>>();
    assert_eq!(
        codes,
        [
            "citry.format.embedded-interpolation-unsupported",
            "citry.format.embedded-language-unsupported",
            "citry.format.embedded-suppressed",
        ]
    );

    let outcome = finish_embedded_format(&plan, &[]).expect("finish notice-only plan");
    assert_eq!(outcome.source(), plan.formatted_source());
}

#[test]
fn result_identity_and_cardinality_are_validated_atomically() {
    let plan = prepare_embedded_format("<script>let  value=1</script>").unwrap();
    let request = &plan.requests()[0];

    let cases = [
        vec![],
        vec![EmbeddedFormatResult::unchanged("wrong-plan", request.id())],
        vec![EmbeddedFormatResult::unchanged(plan.id(), "wrong-region")],
        vec![
            EmbeddedFormatResult::unchanged(plan.id(), request.id()),
            EmbeddedFormatResult::unchanged(plan.id(), request.id()),
        ],
    ];
    for results in cases {
        let error = finish_embedded_format(&plan, &results).expect_err("invalid results accepted");
        assert_eq!(error.code(), "citry.format.provider-invalid");
    }
}

#[test]
fn provider_delimiter_conflicts_and_errors_reject_the_complete_plan() {
    let plan = prepare_embedded_format("<script>let  value=1</script>").unwrap();
    let request = &plan.requests()[0];
    let conflict = [EmbeddedFormatResult::formatted(
        plan.id(),
        request.id(),
        "const value = '</script>';\n",
        Some("fake@1"),
    )];
    assert_eq!(
        finish_embedded_format(&plan, &conflict).unwrap_err().code(),
        "citry.format.provider-invalid"
    );

    for text in ["if (x) {{ foo }}", "if (x) {# fmt: off #}"] {
        let result = [EmbeddedFormatResult::formatted(
            plan.id(),
            request.id(),
            text,
            Some("fake@1"),
        )];
        assert_eq!(
            finish_embedded_format(&plan, &result).unwrap_err().code(),
            "citry.format.provider-invalid"
        );
    }

    let css_plan = prepare_embedded_format("<style>a{color:red}</style>").unwrap();
    for text in ["a{{ color: red }}", "a{# fmt: off #}"] {
        let result = [EmbeddedFormatResult::formatted(
            css_plan.id(),
            css_plan.requests()[0].id(),
            text,
            Some("fake@1"),
        )];
        assert_eq!(
            finish_embedded_format(&css_plan, &result)
                .unwrap_err()
                .code(),
            "citry.format.provider-invalid"
        );
    }

    let failed = [EmbeddedFormatResult::error(
        plan.id(),
        request.id(),
        "provider crashed",
    )];
    assert_eq!(
        finish_embedded_format(&plan, &failed).unwrap_err().code(),
        "citry.format.provider-invalid"
    );
}

#[test]
fn citry_comments_inside_embedded_bodies_are_not_delegated() {
    for source in [
        "<script>{# note #}const x=1;</script>",
        "<style>{# note #}a{color:red}</style>",
    ] {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty(), "{source}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-interpolation-unsupported"
        );
        assert_eq!(finish_embedded_format(&plan, &[]).unwrap().source(), source);
    }
}

#[test]
fn unavailable_results_preserve_the_region_and_report_it() {
    let plan = prepare_embedded_format("<style>.a{color:red}</style>").unwrap();
    let request = &plan.requests()[0];
    let results = [EmbeddedFormatResult::unavailable(
        plan.id(),
        request.id(),
        "no CSS provider",
    )];
    let outcome = finish_embedded_format(&plan, &results).unwrap();

    assert_eq!(outcome.source(), plan.formatted_source());
    assert_eq!(outcome.notices().len(), 1);
    assert_eq!(
        outcome.notices()[0].code(),
        "citry.format.provider-unavailable"
    );
}

#[test]
fn composition_preserves_crlf_unicode_and_missing_final_newline() {
    let source = "<main>\r\n<script>const  label='Žluťoučký 🦀'</script>\r\n</main>";
    let plan = prepare_embedded_format(source).unwrap();
    let request = &plan.requests()[0];
    let results = [EmbeddedFormatResult::formatted(
        plan.id(),
        request.id(),
        "const label = 'Žluťoučký 🦀';\n",
        Some("fake@1"),
    )];
    let outcome = finish_embedded_format(&plan, &results).unwrap();

    assert!(!outcome.source().contains("\n") || outcome.source().contains("\r\n"));
    assert!(!outcome.source().ends_with(['\r', '\n']));
    assert!(outcome.source().contains("Žluťoučký 🦀"));
}

#[test]
fn css_identifier_whitespace_is_never_treated_as_provider_framing() {
    for identifier in ['\u{00a0}', '\u{2003}', '\u{0085}'] {
        let source = format!("<style>\n{identifier}\n.a{{color:red}}\n</style>");
        let plan = prepare_embedded_format(&source).unwrap();
        let request = &plan.requests()[0];

        assert!(request.virtual_source().starts_with(identifier));
        let formatted = format!("{identifier}\n.a {{\n  color: red;\n}}\n");
        let results = [EmbeddedFormatResult::formatted(
            plan.id(),
            request.id(),
            formatted,
            Some("fake-css@1"),
        )];
        let outcome = finish_embedded_format(&plan, &results).unwrap();

        assert!(outcome.source().contains(identifier));
    }
}

#[test]
fn css_escapes_cannot_hide_multiline_strings() {
    for source in [
        "<style>a{--x:foo\\\"bar;content:\"a\\\nb\"}</style>",
        "<style>a{--x:foo\\'bar;content:'a\\\nb'}</style>",
    ] {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty(), "{source}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported"
        );
        assert_eq!(finish_embedded_format(&plan, &[]).unwrap().source(), source);
    }

    let plan = prepare_embedded_format("<style>a{color:red}</style>").unwrap();
    let result = [EmbeddedFormatResult::formatted(
        plan.id(),
        plan.requests()[0].id(),
        "a{--x:foo\\\"bar;content:\"a\\\nb\"}",
        Some("fake@1"),
    )];
    assert_eq!(
        finish_embedded_format(&plan, &result).unwrap_err().code(),
        "citry.format.provider-invalid"
    );
}

#[test]
fn multiline_language_literals_are_preserved_without_provider_reindentation() {
    let sources = [
        "<script>\n    const x = `\n      hello\n    `;\n    console.log(x);\n</script>",
        "<script>\n    const x = \"hello\\\n      world\";\n</script>",
        "<style>\n    .a::before { content: \"hello\\\n      world\"; }\n</style>",
    ];
    for source in sources {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty());
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported"
        );
        assert!(
            plan.notices()[0]
                .message()
                .contains("multiline whitespace-sensitive token")
        );
        let outcome = finish_embedded_format(&plan, &[]).unwrap();
        assert_eq!(outcome.source(), source);
    }
}

#[test]
fn position_sensitive_language_sentinels_are_not_reframed() {
    for source in [
        "<script>#!/usr/bin/env node\nconsole.log('ok');</script>",
        "<script>\u{feff}#!/usr/bin/env node\nconsole.log('ok');</script>",
        "<style>@charset \"UTF-8\";\n.a{color:red}</style>",
        "<style>\u{feff}.a{color:red}</style>",
    ] {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty());
        assert!(plan.notices()[0].message().contains("position-sensitive"));
        assert_eq!(finish_embedded_format(&plan, &[]).unwrap().source(), source);
    }
}

#[test]
fn javascript_regex_literals_do_not_look_like_multiline_strings() {
    let source = "<script>\n  const quote = /\"/;\n  const tick = /`/;\n  const slash = /a\\/b/;\n  const classed = /[\"`/]/;\n</script>";
    let plan = prepare_embedded_format(source).unwrap();

    assert_eq!(plan.requests().len(), 1);
    assert!(plan.notices().is_empty());
}

#[test]
fn ambiguous_statement_position_regex_literals_are_conservatively_preserved() {
    for source in [
        "<script>\n  if (ok) /\"/.test(value);\n  const x=1;\n</script>",
        "<script>\n  while (ok) /`/.test(value);\n  const x=1;\n</script>",
        "<script>if(ok) /\"/.test(x);const s=\"a\\\nb\";</script>",
        "<script>if(ok) /`/.test(x);const s=`a\nb`;</script>",
        "<script>value < /\"/.test(x);const s=\"a\\\nb\";</script>",
    ] {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty(), "{source}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported"
        );
    }

    let plan = prepare_embedded_format("<script>const x = 1;</script>").unwrap();
    for output in [
        "if(ok) /\"/.test(x);const s=\"a\\\nb\";",
        "if(ok) /`/.test(x);const s=`a\nb`;",
    ] {
        let result = [EmbeddedFormatResult::formatted(
            plan.id(),
            plan.requests()[0].id(),
            output,
            Some("fake@1"),
        )];
        assert_eq!(
            finish_embedded_format(&plan, &result).unwrap_err().code(),
            "citry.format.provider-invalid"
        );
    }
}

#[test]
fn multiline_comments_and_javascript_line_separators_are_preserved() {
    for source in [
        "<script>\n  /* keep\n      comment indent */\n  const x = 1;\n</script>",
        "<style>\n  /* keep\n      comment indent */\n  .a{}\n</style>",
        "<script>// comment\u{2028}const value = `\n  raw\n`;</script>",
    ] {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty());
        assert!(
            plan.notices()[0]
                .message()
                .contains("multiline whitespace-sensitive token")
        );
        assert_eq!(finish_embedded_format(&plan, &[]).unwrap().source(), source);
    }
}

#[test]
fn unsafe_provider_output_is_rejected_before_reindentation() {
    let plan = prepare_embedded_format("<script>const value=1;</script>").unwrap();
    let result = [EmbeddedFormatResult::formatted(
        plan.id(),
        plan.requests()[0].id(),
        "const value = `\n  raw\n`;\n",
        Some("fake@1"),
    )];

    let error = finish_embedded_format(&plan, &result).unwrap_err();
    assert_eq!(error.code(), "citry.format.provider-invalid");
    assert!(error.to_string().contains("cannot be reframed safely"));
}

#[test]
fn postfix_operators_cannot_hide_multiline_literals_after_division() {
    for operator in ["++", "--"] {
        for literal in ["`foo\n  bar`", "\"foo\\\n  bar\""] {
            let body = format!("x{operator} / {literal}");
            let source = format!("<script>{body}</script>");
            let plan = prepare_embedded_format(&source).unwrap();

            assert!(plan.requests().is_empty(), "{body}");
            assert_eq!(
                plan.notices()[0].code(),
                "citry.format.embedded-language-unsupported"
            );
        }
    }

    let plan = prepare_embedded_format("<script>x++ / value</script>").unwrap();
    let result = [EmbeddedFormatResult::formatted(
        plan.id(),
        plan.requests()[0].id(),
        "x++ / `foo\n  bar`",
        Some("fake@1"),
    )];
    assert_eq!(
        finish_embedded_format(&plan, &result).unwrap_err().code(),
        "citry.format.provider-invalid"
    );
}

#[test]
fn keyword_named_properties_cannot_hide_multiline_literals_after_division() {
    for property in ["return", "delete", "new"] {
        let body = format!("const x = obj.{property} / denom + `a\nb`;");
        let source = format!("<script>{body}</script>");
        let plan = prepare_embedded_format(&source).unwrap();

        assert!(plan.requests().is_empty(), "{body}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported"
        );
    }

    let plan = prepare_embedded_format("<script>const x = 1;</script>").unwrap();
    let result = [EmbeddedFormatResult::formatted(
        plan.id(),
        plan.requests()[0].id(),
        "const x = obj.return / denom + `a\nb`;",
        Some("fake@1"),
    )];
    assert_eq!(
        finish_embedded_format(&plan, &result).unwrap_err().code(),
        "citry.format.provider-invalid"
    );

    let private =
        "<script>class C { #return=2;m(){return this.#return / denom + `a\nb`;}}</script>";
    let plan = prepare_embedded_format(private).unwrap();
    assert!(plan.requests().is_empty());
    assert_eq!(
        plan.notices()[0].code(),
        "citry.format.embedded-language-unsupported"
    );

    for identifier in ["of", "await", "yield"] {
        let source =
            format!("<script>var {identifier}=2;const x={identifier} / denom + `a\nb`;</script>");
        let plan = prepare_embedded_format(&source).unwrap();
        assert!(plan.requests().is_empty(), "{identifier}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported"
        );
    }
}

#[test]
fn nested_javascript_templates_are_conservatively_preserved() {
    for source in [
        "<script>const x = `${`foo\n  bar`}`</script>",
        "<script>const x = `head${`foo\n  bar`}tail`</script>",
    ] {
        let plan = prepare_embedded_format(source).unwrap();

        assert!(plan.requests().is_empty(), "{source}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported"
        );
        assert_eq!(finish_embedded_format(&plan, &[]).unwrap().source(), source);
    }

    let plan = prepare_embedded_format("<script>const x = 1;</script>").unwrap();
    let result = [EmbeddedFormatResult::formatted(
        plan.id(),
        plan.requests()[0].id(),
        "const x = `${`foo\n  bar`}`",
        Some("fake@1"),
    )];
    assert_eq!(
        finish_embedded_format(&plan, &result).unwrap_err().code(),
        "citry.format.provider-invalid"
    );
}

#[test]
fn provider_output_cannot_hide_position_sentinels_behind_layout_whitespace() {
    let cases = [
        (
            "<script>const value=1;</script>",
            "\n#! /usr/bin/env node\nconst value=1;",
        ),
        (
            "<style>.a{color:red}</style>",
            " \n@charset \"UTF-8\";\n.a{color:red}",
        ),
        ("<style>.a{color:red}</style>", "\n\u{feff}.a{color:red}"),
    ];

    for (source, output) in cases {
        let plan = prepare_embedded_format(source).unwrap();
        let result = [EmbeddedFormatResult::formatted(
            plan.id(),
            plan.requests()[0].id(),
            output,
            Some("fake@1"),
        )];

        let error = finish_embedded_format(&plan, &result).unwrap_err();
        assert_eq!(error.code(), "citry.format.provider-invalid", "{output:?}");
        assert!(error.to_string().contains("cannot be reframed safely"));
    }
}

#[test]
fn script_type_classification_follows_html_javascript_values() {
    let supported = [
        "<script>let x=1</script>",
        "<script type>let x=1</script>",
        "<script type=\"\">let x=1</script>",
        "<script type=\"module\">let x=1</script>",
        "<script type=\"application/x-javascript\">let x=1</script>",
        "<script type=\"text/javascript1.5\">let x=1</script>",
        "<script type=\"text/livescript\">let x=1</script>",
        "<script type=\"\t text/javascript \n\">let x=1</script>",
        "<style type=\"\u{000C}text/css\r\">a{color:red}</style>",
    ];
    for source in supported {
        let plan = prepare_embedded_format(source).unwrap();
        assert_eq!(plan.requests().len(), 1, "{source}");
        assert!(plan.notices().is_empty(), "{source}");
    }

    let unsupported = [
        "<script type=\"importmap\">{}</script>",
        "<script type=\"speculationrules\">{}</script>",
        "<script type=\"application/json\">{}</script>",
        "<script type=\"text/javascript; charset=utf-8\">let x=1</script>",
        "<script type=\"\u{00A0}text/javascript\u{00A0}\">let x=1</script>",
        "<style type=\"\u{0085}text/css\u{0085}\">a{color:red}</style>",
    ];
    for source in unsupported {
        let plan = prepare_embedded_format(source).unwrap();
        assert!(plan.requests().is_empty(), "{source}");
        assert_eq!(
            plan.notices()[0].code(),
            "citry.format.embedded-language-unsupported",
            "{source}"
        );
    }
}
