"""
Row HTML for public ``simple="vue"`` leaves.

Evaluating an admitted ``simple="vue"`` occurrence only records its values.
When serialize writes output that contains the row, a function generated
once per template (the row HTML writer) writes the row's finished HTML from
those records, cut where the component's root marker attributes go.
Serialize then joins those pieces with the markers, so it does not rebuild
the row through the general per-row path or scan it again. These tests pin
that the result is byte-identical to the ordinary component path and to the
per-row serialize path used when no row HTML exists, that serialize really
skips the per-row work, and that full client-mounted or hydrated documents
never write it.
"""

from __future__ import annotations

import itertools
import re
from typing import Any

import pytest

import citry.serialize as serializer
from citry import Citry, Component
from citry._vue import leaf_program
from citry.citry_render import CitryRender, SimpleVueRecord

# One row exercising the supported shapes: a c-bind spread on the root next
# to an authored attribute, Python text and attribute values, c-if/c-else
# and c-for inside the row, a raw-text element, and Vue-only bindings.
ROW_TEMPLATE = """
<article c-bind="row_attrs" data-fixed="source">
<h3 class="title">{{ row['title'] }}</h3>
<span
  c-data-count="row['count']"
  c-data-ratio="row['ratio']"
  c-data-label="row['label']"
  c-hidden="row['hidden']"
>{{ row['count'] }}</span>
<button type="button" @click="open = !open" :aria-expanded="open">toggle</button>
<ul v-show="open">
<c-if cond="row['items']">
<li c-for="item in row['items']" c-data-item="item['id']">{{ item['label'] }}</li>
</c-if>
<c-else>
<li>none</li>
</c-else>
</ul>
<textarea>{{ row['note'] }}</textarea>
<p>{{ row['blank'] }}</p>
</article>
"""

GROUP_TEMPLATE = """
<section c-data-group="group['id']">
<c-Row c-for="row in group['rows']" #c-key="row['id']" c-row="row" />
</section>
"""

PAGE_BODY = """<main><c-Group c-for="group in groups" #c-key="group['id']" c-group="group" /></main>"""

PAGE_DOCUMENT = """
<!doctype html>
<html>
<head><title>Rows</title></head>
<body>
<main><c-Group c-for="group in groups" #c-key="group['id']" c-group="group" /></main>
</body>
</html>
"""


def _rows(count: int, group: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(count):
        row_id = f"g{group}-r{index}"
        rows.append(
            {
                "id": row_id,
                # HTML-significant characters, quotes, and non-ASCII text.
                "title": f"<b>Row {index}</b> & \"quoted\" 'single' ✓ café",
                "count": index,
                "ratio": index / 4,
                "label": 'a<b>&"c"' if index % 2 else "",
                "hidden": index % 3 == 0,
                "items": [{"id": f"{row_id}-i{item}", "label": f"item <{item}> & more"} for item in range(index % 3)],
                "note": "</textarea><b>not markup</b>",
                # Python-produced whitespace-only text must survive.
                "blank": "   " if index % 2 else "",
                "selected": index == 1,
                "source_id": None if index % 2 else f"src-{index}",
            }
        )
    return rows


def _groups(rows_per_group: int) -> list[dict[str, Any]]:
    return [{"id": f"g{group}", "rows": _rows(rows_per_group, group)} for group in range(2)]


def _row_attrs(row: dict[str, Any]) -> dict[str, object]:
    attrs: dict[str, object] = {
        "id": f"row-{row['id']}",
        "class": "row selected" if row["selected"] else "row",
        "title": row["title"],
        "data-selected": "true" if row["selected"] else "false",
        "aria-busy": row["selected"],
        "data-index": row["count"],
    }
    if row["source_id"] is not None:
        attrs["data-source-id"] = row["source_id"]
    return attrs


def _build(
    *,
    simple: object,
    document: bool = False,
    row_template: str = ROW_TEMPLATE,
    security_javascript: str = "allow",
    css_tone: bool = False,
    ssr_element_threshold: int | None = None,
) -> type[Component]:
    """Build a Page -> Group loop -> Row tree on a fresh engine with fixed render IDs."""
    counter = itertools.count()
    # None keeps the engine's default hydration threshold.
    threshold: dict[str, Any] = (
        {} if ssr_element_threshold is None else {"ssr_element_threshold": ssr_element_threshold}
    )
    app = Citry(
        autodiscover=False,
        id_generator=lambda: f"r{next(counter)}",
        security_javascript=security_javascript,  # type: ignore[arg-type]
        **threshold,
    )
    # Fragment serialization references assets by URL, so it needs a prefix.
    app.set_mounted_prefix("/citry")
    simple_mode = simple
    page_template = PAGE_DOCUMENT if document else PAGE_BODY

    class Row(Component):
        citry = app
        simple = simple_mode
        template = row_template
        js = """
            $component({data(){return {open: true};}});
        """

        class Kwargs:
            row: dict

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"row": kwargs.row, "row_attrs": _row_attrs(kwargs.row)}

        # CSS variables give every row root a second marker attribute.
        if css_tone:
            css = """
                article { color: var(--tone); }
            """

            @staticmethod
            def css_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
                return {"tone": "red" if kwargs.row["selected"] else "blue"}

    class Group(Component):
        citry = app
        template = GROUP_TEMPLATE
        js = """
            $component({data(){return {open: true};}});
        """

        class Kwargs:
            group: dict

    class Page(Component):
        citry = app
        template = page_template

    return Page


def _simple_records(render: CitryRender) -> list[SimpleVueRecord]:
    """Collect every simple='vue' record in a rendered tree."""
    records: list[SimpleVueRecord] = []
    pending: list[CitryRender] = [render]
    while pending:
        current = pending.pop()
        for part in current.parts:
            if type(part) is SimpleVueRecord:
                records.append(part)
            elif isinstance(part, CitryRender):
                pending.append(part)
    return records


@pytest.mark.parametrize("ssr", [True, False])
@pytest.mark.parametrize("deps_strategy", ["document", "fragment", "simple", "ignore"])
@pytest.mark.parametrize("document", [False, True], ids=["body", "physical-document"])
@pytest.mark.parametrize("security_javascript", ["allow", "omit"])
# Omitting JavaScript reports the dropped Vue behavior; that report is expected here.
@pytest.mark.filterwarnings("ignore:security_javascript='omit' found:RuntimeWarning")
def test_row_html_matches_ordinary_and_per_row_serialize(
    monkeypatch: pytest.MonkeyPatch, ssr: bool, deps_strategy: str, document: bool, security_javascript: str
) -> None:
    groups = _groups(4)
    options: dict[str, Any] = {"document": document, "security_javascript": security_javascript}

    ordinary_render = _build(simple=False, **options)(groups=groups).render()
    ordinary_html = ordinary_render.serialize(ssr=ssr, deps_strategy=deps_strategy)
    simple_render = _build(simple="vue", **options)(groups=groups).render()
    records = _simple_records(simple_render)
    assert len(records) == 8
    # The row HTML writer can write every row.
    assert all(record.leaf.row_html_segments is not None for record in records)
    simple_html = simple_render.serialize(ssr=ssr, deps_strategy=deps_strategy)

    # With row HTML switched off, serialize rebuilds and scans each row
    # itself, which is the reference output.
    monkeypatch.setattr(leaf_program, "_default_row_formatting", lambda: False)
    per_row_render = _build(simple="vue", **options)(groups=groups).render()
    assert all(record.leaf.row_html_segments is None for record in _simple_records(per_row_render))
    per_row_html = per_row_render.serialize(ssr=ssr, deps_strategy=deps_strategy)

    assert simple_html == ordinary_html
    assert simple_html == per_row_html
    # A client-mounted page (ssr=False or a fragment) carries no row HTML.
    # A document with SSR on hydrates and writes its rows from Vue's render,
    # which formats values the way Vue sets them, so only the static outputs
    # prove Citry's escaping and attribute cases byte for byte.
    static_output = deps_strategy in {"simple", "ignore"} or security_javascript == "omit"
    hydrated = ssr and deps_strategy == "document" and not static_output
    assert ('"hydrate":true' in simple_html) is hydrated
    assert ('data-fixed="source"' in simple_html) is (static_output or hydrated)
    if static_output:
        assert "&lt;b&gt;Row 1&lt;/b&gt; &amp; &#34;quoted&#34; &#39;single&#39;" in simple_html
        assert 'title="&lt;b&gt;Row 0&lt;/b&gt;' in simple_html
        assert 'data-source-id="src-0"' in simple_html
        assert 'data-label="a&lt;b&gt;&amp;&#34;c&#34;"' in simple_html
        assert "&lt;/textarea&gt;&lt;b&gt;not markup" in simple_html
        assert "<p>   </p>" in simple_html
        assert simple_html.count("data-cid-r") >= 8


def test_serialize_skips_per_row_work_for_admitted_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """The per-row materialization and marker scan run a fixed number of times, not once per row."""
    counts = {"row_static_leaf_parts": 0, "mark_html": 0}
    row_leaves: set[int] = set()
    original_static_leaf_parts = leaf_program.static_leaf_parts
    original_mark_html = serializer.mark_html

    def counting_static_leaf_parts(value: Any, **kwargs: Any) -> list[str]:
        if id(value) in row_leaves:
            counts["row_static_leaf_parts"] += 1
        return original_static_leaf_parts(value, **kwargs)

    def counting_mark_html(*args: Any) -> Any:
        counts["mark_html"] += 1
        return original_mark_html(*args)

    monkeypatch.setattr(leaf_program, "static_leaf_parts", counting_static_leaf_parts)
    monkeypatch.setattr(serializer, "mark_html", counting_mark_html)

    def serialize_counts(rows_per_group: int, deps_strategy: str) -> dict[str, int]:
        rendered = _build(simple="vue")(groups=_groups(rows_per_group)).render()
        row_leaves.clear()
        row_leaves.update(id(record.leaf) for record in _simple_records(rendered))
        for key in counts:
            counts[key] = 0
        rendered.serialize(ssr=False, deps_strategy=deps_strategy)
        return dict(counts)

    # A client-mounted body page and a static page both build the row HTML.
    for deps_strategy in ("document", "simple"):
        few = serialize_counts(2, deps_strategy)
        many = serialize_counts(12, deps_strategy)
        assert many["row_static_leaf_parts"] == 0
        assert few == many

        # The per-row path, forced on, pays both costs once per row (24 rows).
        with monkeypatch.context() as forced:
            forced.setattr(leaf_program, "_default_row_formatting", lambda: False)
            per_row = serialize_counts(12, deps_strategy)
        assert per_row["row_static_leaf_parts"] == 24
        assert per_row["mark_html"] == many["mark_html"] + 24


def test_client_mounted_document_skips_row_html(monkeypatch: pytest.MonkeyPatch) -> None:
    """A client-mounted physical document never builds the HTML of its simple='vue' rows."""
    built: list[str | None] = []
    original_build_frame = serializer._build_frame

    def observe_build_frame(render: CitryRender, *args: Any, **kwargs: Any) -> str:
        built.append(render.frame.class_name)
        return original_build_frame(render, *args, **kwargs)

    monkeypatch.setattr(serializer, "_build_frame", observe_build_frame)
    groups = _groups(3)
    ordinary_html = _build(simple=False, document=True)(groups=groups).render().serialize(ssr=False)
    ordinary_frames = list(built)
    built.clear()
    simple_html = _build(simple="vue", document=True)(groups=groups).render().serialize(ssr=False)

    assert simple_html == ordinary_html
    # Only the Page frame is built; the Group frames that hold the rows are
    # skipped exactly as they are for ordinary rows.
    assert built == ordinary_frames == ["Page"]


def test_row_html_is_written_only_for_outputs_that_contain_the_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Render never writes row HTML, and documents skip it; only outputs with the rows' HTML write it."""
    writes = {"count": 0}
    original_default_row_formatting = leaf_program._default_row_formatting

    # The row HTML writer checks the formatting functions first on every call,
    # so this counts one call per row whose HTML serialize asked for.
    def counting_default_row_formatting() -> bool:
        writes["count"] += 1
        return original_default_row_formatting()

    monkeypatch.setattr(leaf_program, "_default_row_formatting", counting_default_row_formatting)
    groups = _groups(3)

    def count_writes(*, threshold: int | None, **options: Any) -> tuple[int, int, str]:
        rendered = _build(simple="vue", document=True, ssr_element_threshold=threshold)(groups=groups).render()
        after_render = writes["count"]
        writes["count"] = 0
        html = rendered.serialize(**options)
        written = writes["count"]
        writes["count"] = 0
        return after_render, written, html

    # A hydrated document writes rows from the server render programs, and a
    # client-mounted one skips the frames that hold them.
    after_render, written, hydrated = count_writes(threshold=0)
    assert '"hydrate":true' in hydrated
    assert (after_render, written) == (0, 0)
    after_render, written, client = count_writes(threshold=None, ssr=False)
    assert '"hydrate":true' not in client
    assert (after_render, written) == (0, 0)
    # Static output contains every row, so each of the six rows is written once.
    after_render, written, static_html = count_writes(threshold=None, deps_strategy="simple")
    assert (after_render, written) == (0, 6)
    assert static_html == (
        _build(simple=False, document=True)(groups=groups).render().serialize(deps_strategy="simple")
    )


def test_hydrated_direct_root_writes_vue_html_and_static_output_reuses_row_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hydrated simple='vue' root writes Vue's HTML; static output still joins the row HTML."""
    row_parts_built: list[object] = []
    original_static_leaf_parts = leaf_program.static_leaf_parts

    def observe_static_leaf_parts(value: Any, **kwargs: Any) -> list[str]:
        row_parts_built.append(value)
        return original_static_leaf_parts(value, **kwargs)

    monkeypatch.setattr(leaf_program, "static_leaf_parts", observe_static_leaf_parts)

    def serialize_root(*, row_html: bool) -> tuple[str, str]:
        counter = itertools.count()
        app = Citry(autodiscover=False, id_generator=lambda: f"r{next(counter)}")

        class Root(Component):
            citry = app
            simple = "vue"
            template = '<main><p>{{ text }}</p><button type="button" @click="n = n + 1">go</button></main>'
            js = """
                $component({data(){return {n: 0};}});
            """

        rendered = Root(text="a & <b>").render()
        leaf = _simple_records(rendered)[0].leaf
        assert (leaf.row_html_segments is not None) is row_html
        row_parts_built.clear()
        static_html = rendered.serialize(deps_strategy="simple")
        # With row HTML, the static output joins the pieces the row HTML
        # writer produced and never rebuilds this row.
        assert (leaf not in row_parts_built) is row_html
        return rendered.serialize(ssr=True), static_html

    hydrated, static_html = serialize_root(row_html=True)

    # The host holds the HTML Vue renders: the listener is attached by Vue,
    # not written, and the host carries no render-id marker.
    assert '"hydrate":true' in hydrated
    assert re.search(
        r'<div id="citry-vue-[^"]+"><main><p>a &amp; &lt;b&gt;</p><button type="button">go</button></main></div>',
        hydrated,
    )
    assert "data-cid" not in hydrated.split("<script", 1)[0]
    assert static_html.split("<script", 1)[0].strip() == (
        '<main data-cid-r0=""><p>a &amp; &lt;b&gt;</p><button type="button" @click="n = n + 1">go</button></main>'
    )

    # The per-row serialize path produces the same bytes on both outputs.
    monkeypatch.setattr(leaf_program, "_default_row_formatting", lambda: False)
    assert serialize_root(row_html=False) == (hydrated, static_html)


@pytest.mark.parametrize(
    "row_template",
    [
        # Roots chosen per occurrence, so their marker positions are not fixed.
        """
        <c-if cond="row['hidden']"><p>{{ row['title'] }}</p></c-if>
        """,
        """
        <p c-for="item in row['items']" c-data-item="item['id']">{{ item['label'] }}</p>
        """,
    ],
    ids=["root-in-branch", "root-in-loop"],
)
@pytest.mark.parametrize("deps_strategy", ["document", "simple"])
def test_rows_without_fixed_roots_use_per_row_serialize(row_template: str, deps_strategy: str) -> None:
    groups = _groups(3)
    ordinary_html = (
        _build(simple=False, row_template=row_template)(groups=groups)
        .render()
        .serialize(ssr=False, deps_strategy=deps_strategy)
    )
    simple_render = _build(simple="vue", row_template=row_template)(groups=groups).render()
    records = _simple_records(simple_render)

    assert records
    assert all(record.leaf.row_html_segments is None for record in records)
    assert simple_render.serialize(ssr=False, deps_strategy=deps_strategy) == ordinary_html


def test_multiple_roots_each_get_their_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    row_template = """
        <article c-bind="row_attrs">{{ row['title'] }}</article>
        <br/>
        <aside c-data-count="row['count']">{{ row['count'] }}</aside>
    """
    groups = _groups(2)
    simple_render = _build(simple="vue", row_template=row_template)(groups=groups).render()
    records = _simple_records(simple_render)

    # One piece before, between, and after each of the three roots.
    assert all(len(record.leaf.row_html_segments or ()) == 4 for record in records)
    static_html = simple_render.serialize(ssr=False, deps_strategy="simple")
    assert static_html == _build(simple=False, row_template=row_template)(groups=groups).render().serialize(
        ssr=False, deps_strategy="simple"
    )
    assert static_html.count("<br data-cid-r") == 4
    client_html = simple_render.serialize(ssr=False)

    monkeypatch.setattr(leaf_program, "_default_row_formatting", lambda: False)
    per_row_render = _build(simple="vue", row_template=row_template)(groups=groups).render()
    assert per_row_render.serialize(ssr=False, deps_strategy="simple") == static_html
    assert per_row_render.serialize(ssr=False) == client_html


@pytest.mark.parametrize("deps_strategy", ["document", "simple"])
def test_css_variable_marker_rows_match_ordinary(monkeypatch: pytest.MonkeyPatch, deps_strategy: str) -> None:
    built: list[str | None] = []
    original_build_frame = serializer._build_frame

    def observe_build_frame(render: CitryRender, *args: Any, **kwargs: Any) -> str:
        built.append(render.frame.class_name)
        return original_build_frame(render, *args, **kwargs)

    monkeypatch.setattr(serializer, "_build_frame", observe_build_frame)
    groups = _groups(3)
    ordinary_html = (
        _build(simple=False, document=True, css_tone=True)(groups=groups)
        .render()
        .serialize(ssr=False, deps_strategy=deps_strategy)
    )
    ordinary_frames = list(built)
    built.clear()
    simple_render = _build(simple="vue", document=True, css_tone=True)(groups=groups).render()
    records = _simple_records(simple_render)
    assert all(record.root_markers and record.leaf.row_html_segments is not None for record in records)

    assert simple_render.serialize(ssr=False, deps_strategy=deps_strategy) == ordinary_html
    # A row with its own marker keeps the Group frames built, as an ordinary
    # component with the same marker does. Simple rows join their Group's
    # frame instead of building one of their own.
    assert built == [name for name in ordinary_frames if name != "Row"]
    assert "Group" in built
    if deps_strategy == "simple":
        # Both markers follow the root's last attribute on all six rows.
        assert len(re.findall(r'<article [^>]* data-cid-r\d+="" data-ccss-[0-9a-f]+="">', ordinary_html)) == 6


# Shapes where the Python walk that places root markers must read the HTML
# exactly as the native marker scan does.
MARKER_SHAPES = {
    "root-comment-with-gt": """<!-- a > b --><div c-bind="row_attrs">{{ row['title'] }}</div>""",
    "uppercase-tags": """<DIV c-bind="row_attrs"><SPAN c-data-n="row['count']">x</SPAN></DIV>""",
    "quoted-gt-and-quotes": """<div title="a > b" data-q='say "hi"' c-bind="row_attrs">x</div>""",
    "unquoted-value": """<div data-u=plain c-data-n="row['count']">x</div>""",
    "void-roots": """<hr><img src="/a.png"/><div c-bind="row_attrs">x</div>""",
    "self-closing-non-void": """<div c-bind="row_attrs"><span c-data-n="row['count']" /></div>""",
    "raw-text-elements": """
        <div c-bind="row_attrs">
        <title>{{ row['title'] }}</title>
        <textarea c-data-n="row['count']">{{ row['note'] }}</textarea>
        </div>
    """,
    "plain-template-tag": """<div c-bind="row_attrs"><template><p>x</p></template></div>""",
    "text-only": """{{ row['title'] }}""",
    "spread-only-root": """<div c-bind="row_attrs"></div>""",
}


@pytest.mark.parametrize("row_template", list(MARKER_SHAPES.values()), ids=list(MARKER_SHAPES))
def test_marker_positions_match_native_scan(monkeypatch: pytest.MonkeyPatch, row_template: str) -> None:
    groups = _groups(3)
    ordinary_html = (
        _build(simple=False, row_template=row_template)(groups=groups)
        .render()
        .serialize(ssr=False, deps_strategy="simple")
    )
    simple_html = (
        _build(simple="vue", row_template=row_template)(groups=groups)
        .render()
        .serialize(ssr=False, deps_strategy="simple")
    )
    monkeypatch.setattr(leaf_program, "_default_row_formatting", lambda: False)
    per_row_html = (
        _build(simple="vue", row_template=row_template)(groups=groups)
        .render()
        .serialize(ssr=False, deps_strategy="simple")
    )

    assert simple_html == ordinary_html == per_row_html


def test_unprintable_int_attribute_still_fails_at_serialize() -> None:
    """A value the row HTML writer cannot format drops that row's HTML, and serialize raises as before."""
    row_template = """
        <div c-bind="row_attrs"><p c-data-x="row['count']">x</p></div>
    """
    groups = _groups(1)
    groups[0]["rows"][0]["count"] = 10**6000

    ordinary_render = _build(simple=False, row_template=row_template)(groups=groups).render()
    simple_render = _build(simple="vue", row_template=row_template)(groups=groups).render()
    records = _simple_records(simple_render)

    # Only the row holding the huge value lost its row HTML.
    assert [record.leaf.row_html_segments is None for record in records].count(True) == 1
    with pytest.raises(ValueError, match="integer string conversion") as ordinary_error:
        ordinary_render.serialize(ssr=False, deps_strategy="simple")
    with pytest.raises(ValueError, match="integer string conversion") as simple_error:
        simple_render.serialize(ssr=False, deps_strategy="simple")
    assert str(simple_error.value) == str(ordinary_error.value)
