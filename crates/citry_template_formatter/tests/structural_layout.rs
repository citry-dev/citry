use citry_template_formatter::format_template;

#[test]
fn structural_layout_formats_complete_block_trees() {
    let source = "<main><section><h2>{{title}}</h2></section><footer></footer></main>";
    let expected = concat!(
        "<main>\n",
        "  <section>\n",
        "    <h2>{{ title }}</h2>\n",
        "  </section>\n",
        "  <footer></footer>\n",
        "</main>",
    );

    assert_eq!(format_template(source).unwrap(), expected);
    assert_eq!(format_template(expected).unwrap(), expected);
}

#[test]
fn root_processing_instructions_and_comment_stacks_follow_structure() {
    let directive = "<?xml version=\"1.0\"?><html><body></body></html>";
    let directive_expected = concat!(
        "<?xml version=\"1.0\"?>\n",
        "<html>\n",
        "  <body></body>\n",
        "</html>",
    );
    assert_eq!(format_template(directive).unwrap(), directive_expected);

    let comments = "<main><section></section>{# one #}{# two #}<footer></footer></main>";
    let comments_expected = concat!(
        "<main>\n",
        "  <section></section>\n",
        "  {# one #}\n",
        "  {# two #}\n",
        "  <footer></footer>\n",
        "</main>",
    );
    assert_eq!(format_template(comments).unwrap(), comments_expected);
}

#[test]
fn nested_template_comments_are_formatted_once() {
    let source = "<c-card c-body=\"<main>{# note #}<section></section></main>\" />";
    let expected = concat!(
        "<c-card\n",
        "  c-body=\"<main>\n",
        "    {# note #}\n",
        "    <section></section>\n",
        "  </main>\"\n",
        "/>",
    );

    assert_eq!(format_template(source).unwrap(), expected);
}

#[test]
fn mixed_inline_unknown_and_component_boundaries_remain_exact() {
    for source in [
        "<main>text<section></section></main>",
        "<div><span>A</span><span>B</span></div>",
        "<main><x-panel></x-panel><section></section></main>",
        "<main><c-CButton></c-CButton><section></section></main>",
    ] {
        assert_eq!(format_template(source).unwrap(), source);
    }

    let title = "x".repeat(100);
    let source = format!("<main><div title=\"{title}\"></div><span>A</span></main>");
    let expected =
        format!("<main><div\n        title=\"{title}\"\n      ></div><span>A</span></main>",);
    assert_eq!(format_template(&source).unwrap(), expected);
}

#[test]
fn root_margins_newlines_and_missing_final_newlines_are_preserved() {
    let source = "\r\n<main><section></section></main>\r\n";
    let expected = "\r\n<main>\r\n  <section></section>\r\n</main>\r\n";
    assert_eq!(format_template(source).unwrap(), expected);

    let without_final_newline = "<main><section></section></main>";
    assert!(
        !format_template(without_final_newline)
            .unwrap()
            .ends_with('\n')
    );
}

#[test]
fn verbatim_bodies_disable_all_descendant_formatting() {
    for source in [
        "<pre><div  class = \"x\" >{{  value }}</div></pre>",
        "<textarea><div  class = \"x\" ></div></textarea>",
        "<script><div  class = \"x\" ></div></script>",
        "<style><div  class = \"x\" ></div></style>",
        "<c-raw><div  class = \"x\" >{{  value }}</div></c-raw>",
    ] {
        assert_eq!(format_template(source).unwrap(), source);
    }
}

#[test]
fn structural_layout_resumes_around_protected_nodes() {
    let source = concat!(
        "<main>{# fmt: off #}<section  class = \"x\" ></section>",
        "{# fmt: on #}<footer  id = \"y\" ></footer></main>",
    );
    let expected = concat!(
        "<main>\n",
        "  {# fmt: off #}<section  class = \"x\" ></section>{# fmt: on #}\n",
        "  <footer id=\"y\"></footer>\n",
        "</main>",
    );

    assert_eq!(format_template(source).unwrap(), expected);
}

#[test]
fn fully_protected_children_still_layout_their_outer_container() {
    let source = concat!(
        "<main>{# fmt: off #}<section> <div></div> </section>{# fmt: on #}",
        "{# fmt: skip #}<footer> <div></div> </footer></main>",
    );
    let expected = concat!(
        "<main>\n",
        "  {# fmt: off #}<section> <div></div> </section>{# fmt: on #}\n",
        "  {# fmt: skip #}<footer> <div></div> </footer>\n",
        "</main>",
    );

    assert_eq!(format_template(source).unwrap(), expected);
    assert_eq!(format_template(expected).unwrap(), expected);
}

#[test]
fn expression_trivia_has_a_deterministic_width_boundary() {
    let fitting_value = "x".repeat(94);
    let fitting = format!("{{{{  {fitting_value}  }}}}");
    assert_eq!(
        format_template(&fitting).unwrap(),
        format!("{{{{ {fitting_value} }}}}"),
    );

    let long_value = "x".repeat(95);
    let long = format!("{{{{  {long_value}  }}}}");
    assert_eq!(
        format_template(&long).unwrap(),
        format!("{{{{ {long_value} }}}}"),
    );
}

#[test]
fn generated_boundary_combinations_converge() {
    let parents = ["main", "div", "select", "c-Card"];
    let children = [
        "<section></section>",
        "<span>A</span>",
        "<x-panel></x-panel>",
        "<!-- note -->",
    ];

    for parent in parents {
        for left in children {
            for right in children {
                let source = format!("<{parent}>{left}{right}</{parent}>");
                let formatted = format_template(&source)
                    .unwrap_or_else(|error| panic!("failed for {source:?}: {error}"));
                assert_eq!(
                    format_template(&formatted).unwrap(),
                    formatted,
                    "input: {source:?}",
                );
            }
        }
    }
}

#[test]
fn generated_boundaries_lock_structural_and_sensitive_classification() {
    for parent in ["main", "div"] {
        let blocks = format!("<{parent}><section></section><footer></footer></{parent}>");
        let blocks_expected =
            format!("<{parent}>\n  <section></section>\n  <footer></footer>\n</{parent}>",);
        assert_eq!(format_template(&blocks).unwrap(), blocks_expected);

        for sensitive in ["<span>A</span>", "<x-panel>A</x-panel>", "text"] {
            let mixed = format!("<{parent}>{sensitive}<section></section></{parent}>");
            assert_eq!(format_template(&mixed).unwrap(), mixed);
        }
    }
}
