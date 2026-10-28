//! `mark_html` must put a component's root marker on exactly the elements
//! the browser makes the component's top-level elements. Each input here is
//! marked, the result is parsed with html5ever (a parser that follows the
//! browser's rules) as the content of a `<div>`, and every top-level element
//! must carry the marker while no nested element or text does.
//!
//! One shape is left out on purpose: a stray `</p>` makes the browser create
//! an empty `<p>` that has no tag in the source, so no scanner can mark it.

use citry_html_transform::mark_html;
use html5ever::tendril::TendrilSink;
use html5ever::{namespace_url, ns, parse_fragment, LocalName, ParseOpts, QualName};
use markup5ever_rcdom::{Handle, NodeData, RcDom};

/// Describe every element or text node whose marker disagrees with where the
/// browser placed it.
fn misplaced_markers(node: &Handle, top_level: bool, problems: &mut Vec<String>) {
    for child in node.children.borrow().iter() {
        match &child.data {
            NodeData::Element { name, attrs, .. } => {
                let marked = attrs
                    .borrow()
                    .iter()
                    .any(|attr| attr.name.local.as_ref() == "data-m");
                if top_level && !marked {
                    problems.push(format!("top-level <{}> has no marker", name.local));
                }
                if !top_level && marked {
                    problems.push(format!("nested <{}> has a marker", name.local));
                }
                misplaced_markers(child, false, problems);
            }
            NodeData::Text { contents } if contents.borrow().contains("data-m") => {
                problems.push("a marker is in text".to_owned());
            }
            _ => {}
        }
    }
}

fn problems_for(html: &str) -> Vec<String> {
    let marked = mark_html(html, &["data-m".to_owned()], "c-render-id");
    let mut joined = marked.segments[0].clone();
    for (placeholder, segment) in marked.placeholders.iter().zip(&marked.segments[1..]) {
        joined.push_str(&placeholder.html);
        joined.push_str(segment);
    }
    let dom = parse_fragment(
        RcDom::default(),
        ParseOpts::default(),
        QualName::new(None, ns!(html), LocalName::from("div")),
        Vec::new(),
    )
    .one(joined.as_str());
    // A fragment parse puts one `html` element under the document, holding
    // the parsed nodes.
    let root = dom.document.children.borrow()[0].clone();
    let mut problems = Vec::new();
    misplaced_markers(&root, true, &mut problems);
    problems
}

#[test]
fn root_markers_land_on_the_elements_the_browser_makes_top_level() {
    let inputs = [
        "<xmp></div></xmp><p>x</p>",
        "<textarea/><p>x</p>",
        "<div/><p>x</p>",
        "<svg><title/><circle/></svg><p>x</p>",
        "<svg/><p>x</p>",
        "<math><mi/></math><p>x</p>",
        "<iframe></div></iframe><p>x</p>",
        "<noembed></div></noembed><p>x</p>",
        "<noframes></div></noframes><p>x</p>",
        "<plaintext></plaintext><p>x</p>",
        "<svg><foreignObject><textarea></foreignObject></textarea></foreignObject></svg><p>x</p>",
        "<my-tag/><p>x</p>",
        "<span/>a<b>c</b>",
        "<p>a</p><br/><img/><p>b</p>",
        "<svg><style><g/></style></svg><p>x</p>",
        "<TEXTAREA/><p>x</p>",
        "<title/><p>x</p>",
        "<script/><p>x</p>",
        "<style></div></style><p>x</p>",
        "<div><i class=\"icon\"/></div><p>x</p>",
        "<button><span/></button><p>x</p>",
        "<section><div/></section><p>x</p>",
        "<div><span/></div><b>x</b>",
        "<ul><li/><li/></ul><p>x</p>",
        "<li/><li/>",
        "<p/><p>x</p>",
        "<p/><div>x</div>",
        "</div><p>x</p>",
        "<p>a</span></p><p>b</p>",
        "<svg><title></div></title></svg><p>x</p>",
        "<svg><style></div></style></svg><p>x</p>",
        "<math><mi><mglyph/></mi></math><p>x</p>",
        "<svg><input></svg><p>x</p>",
        "<keygen/><p>x</p>",
        "<basefont/><p>x</p>",
        "<bgsound/><p>x</p>",
        "<frame/><p>x</p>",
        "<image/><p>x</p>",
        "<noscript><p>a</p></noscript><p>x</p>",
        "<div><p>a<p>b</div><p>c</p>",
        "<ul><li>a<li>b</ul><p>x</p>",
        "<dl><dt>a<dd>b<dt>c</dl><p>x</p>",
        "<select><option>a<option>b</select><p>x</p>",
        "<p>a<p>b",
        "<li>a<ul><li>b</ul></li><li>c</li>",
        "<div title=\"a/>b\">x</div><p>y</p>",
        "<div data-x='>'>x</div><p>y</p>",
        "<p>a</p><p",
        "<br><br/><hr/><p>x</p>",
        "<table><tr><td>a</td></tr></table><p>x</p>",
        "<div><svg><circle/><path/></svg></div><p>x</p>",
        "<svg><foreignObject><div/></foreignObject></svg><p>x</p>",
        "<svg><desc><b/></desc></svg><p>x</p>",
        "<math><mtext><div/></mtext></math><p>x</p>",
        "<template c-render-id=\"c1\"></template><p>x</p>",
        "<xmp><template c-render-id=\"c1\"></template></xmp><p>x</p>",
        "<div><template c-render-id=\"c1\"></template></div><p>x</p>",
        "<SCRIPT>a</SCRIPT><p>x</p>",
        "<script>a</scripty></script><p>x</p>",
        "<textarea>a</textarea><p>x</p>",
        "<b><i>x</b></i><p>y</p>",
        "<a><div>x</div></a><p>y</p>",
        "<span>a</span>b<span>c</span>",
        "<!-- <div> --><p>x</p>",
        "<![CDATA[<div>]]><p>x</p>",
        "<?x <div> ?><p>x</p>",
        "<p>a</P><p>b</p>",
        "<DIV/><P>x</P>",
        "<svg><a/></svg><p>x</p>",
        "<svg><svg/></svg><p>x</p>",
        "<math><math/></math><p>x</p>",
        "<button><button>a</button></button><p>x</p>",
        "<option>a<option>b",
        "<optgroup><option>a</optgroup><p>x</p>",
        "<h1>a<h2>b</h2></h1><p>x</p>",
        "<form><form>a</form></form><p>x</p>",
        "<iframe/><p>x</p>",
        "<noembed/><p>x</p>",
        "<em>a<p>b</p></em><p>c</p>",
        "<div><span></div><p>x</p>",
        "<div><b><i></div><p>x</p>",
        "<ul><li>a<div><li>b</div></ul><p>x</p>",
        "<p><button><p>a</button></p><p>b</p>",
        "<dl><dd><div><dt>a</div></dl><p>x</p>",
        "<table><caption><p>a</caption></table><p>x</p>",
        "<object><p>a</object><p>x</p>",
        "<svg><g></svg><p>x</p>",
        "<svg><g><foreignObject><p>a</p></foreignObject></g></svg><p>x</p>",
        "<math><mi><b>a</b></mi></math><p>x</p>",
        "<section><h1>a</h1><h2>b</h2></section><p>x</p>",
        "<h1>a</h2><p>x</p>",
        "<custom-el><div>a</custom-el></div><p>x</p>",
        "<span><div>a</span></div><p>x</p>",
        "<table><tr><td>a</tr></table><p>x</p>",
        "<table><tr><td>a</table><p>x</p>",
        "<table><tr><td>a<td>b</tr></table><p>x</p>",
        "<table><caption>c</table><p>x</p>",
        "<table><tr><th>a<th>b<tr><td>c</table><p>x</p>",
        "<table><thead><tr><th>a<tbody><tr><td>b</table><p>x</p>",
        "<table><tr><td><table><tr><td>a</table></td></tr></table><p>x</p>",
        "<a href=x>a</a><a>b</a>",
        "<li>a<li>b<p>c</p>",
        "<select><option>a<optgroup><option>b</select><p>x</p>",
        "<ruby>a<rt>b</ruby><p>x</p>",
    ];
    let disagreements: Vec<String> = inputs
        .iter()
        .filter_map(|input| {
            let problems = problems_for(input);
            (!problems.is_empty()).then(|| format!("{input}: {problems:?}"))
        })
        .collect();
    assert!(disagreements.is_empty(), "{disagreements:#?}");
}
