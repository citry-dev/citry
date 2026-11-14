"""
Composition between Cache and i18n.

Cache variation by i18n context data comes first. The rest checks that a cache
hit gives the page a definition for every `$c-tr` binding ID its HTML names,
including IDs from a component outside the cached output, and that export and
replay refuse a stored entry whose binding IDs cannot be trusted.
"""

from __future__ import annotations

import itertools
import json
import re
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component, InMemoryCache
from citry._vue.capture import render_prepared_direct
from citry._vue.events import default_events_producer
from citry.ext.cache.errors import CacheArtifactError
from citry.ext.i18n.bindings import BINDING_HELPER, is_binding_id, split_binding_id
from citry.ext.i18n.extension import _bindings_from_wire
from citry.ext.i18n.usage import AMBIENT_CLIENT_OWNER, CLIENT_CONTEXT_KEY, EXTRA_KEY

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_element import CitryElement


class RecordingCache(InMemoryCache):
    def __init__(self) -> None:
        super().__init__()
        self.gets = 0
        self.sets = 0

    def get(self, key: str) -> str | None:
        self.gets += 1
        return super().get(key)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.sets += 1
        super().set(key, value, ttl)


def configured_app(backend: RecordingCache) -> Citry:
    return Citry(
        cache=backend,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
            }
        },
    )


def test_component_explicitly_varies_by_plain_i18n_context_identity() -> None:
    backend = RecordingCache()
    app = configured_app(backend)
    renders: list[str] = []

    class LocaleCard(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return self.component.i18n.context.identity

        def template_data(self, kwargs, slots):
            locale = self.i18n.context.locale
            renders.append(locale)
            return {"locale": locale}

        template = "{{ locale }}"
        messages = "unused-message = present"

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(LocaleCard().render(provides=english)) == "en-US"
    assert str(LocaleCard().render(provides=english)) == "en-US"
    assert str(LocaleCard().render(provides=czech)) == "cs-CZ"
    assert str(LocaleCard().render(provides=czech)) == "cs-CZ"

    assert renders == ["en-US", "cs-CZ"]
    assert backend.sets == 2


def test_omitting_i18n_context_follows_the_normal_cache_rule_and_shares() -> None:
    backend = RecordingCache()
    app = configured_app(backend)
    renders = 0

    class Brand(Component):
        citry = app

        class Cache:
            enabled = True

        class Slots:
            pass

        def template_data(self, kwargs, slots):
            nonlocal renders
            renders += 1
            return super().template_data(kwargs, slots)

        template = "Citry"
        messages = "unused-message = present"

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(Brand().render(provides=english)) == "Citry"
    assert str(Brand().render(provides=czech)) == "Citry"

    assert renders == 1
    assert backend.sets == 1


def test_fragment_accepts_the_same_plain_context_identity_in_vary() -> None:
    backend = RecordingCache()
    app = configured_app(backend)

    class Page(Component):
        citry = app

        class Kwargs:
            locale: str

        def template_data(self, kwargs, slots):
            return {
                "locale": kwargs.locale,
                "locale_context": self.i18n.context,
            }

        template = """\
<c-cache key="copy" c-vary="locale_context.identity">{{ locale }}</c-cache>\
"""
        messages = "unused-message = present"

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(Page(locale="English").render(provides=english)) == "English"
    assert str(Page(locale="English").render(provides=english)) == "English"
    assert str(Page(locale="Czech").render(provides=czech)) == "Czech"
    assert str(Page(locale="Czech").render(provides=czech)) == "Czech"

    assert backend.sets == 2


def test_cache_vary_signature_stays_extension_neutral() -> None:
    backend = RecordingCache()
    app = configured_app(backend)
    calls = 0

    class Card(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return self.component.i18n.context.identity

        class Slots:
            pass

        template = "card"
        messages = "unused-message = present"

    assert str(Card()) == "card"
    assert str(Card()) == "card"
    assert calls == 2


class StoringCache(InMemoryCache):
    """A cache that keeps every value it was given, so a test can edit a stored entry."""

    def __init__(self) -> None:
        super().__init__()
        self.written: dict[str, str] = {}

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.written[key] = value
        super().set(key, value, ttl)


def i18n_app(backend: InMemoryCache | None = None) -> Citry:
    return Citry(
        autodiscover=False,
        cache=backend if backend is not None else InMemoryCache(),
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ")}},
    )


def render_with_binding_ids(
    component: CitryElement, *, provides: Mapping[str, Any] | None = None
) -> tuple[str, list[str], list[str]]:
    """Render the way the Vue page does; return the HTML, its marker IDs, and the IDs the page defines."""
    app = component.comp_cls.citry
    rendered = render_prepared_direct(component, provides=provides)
    manifest = default_events_producer(app).prepare_from_render(
        rendered, citry=app, app_id="i18n-cache-unit", revision=0
    )
    payload = manifest["extensions"]["i18n"]["payload"]
    html = rendered.serialize(deps_strategy="ignore")
    marked = [part for value in re.findall(r'data-citry-i18n-binding="([^"]*)"', html) for part in value.split()]
    defined = [binding["id"] for requirement in payload["requirements"] for binding in requirement["bindings"]]
    return html, marked, defined


def assert_every_marker_is_defined_once(html_markers: list[str], defined: list[str], *, count: int) -> None:
    """The page must send exactly the definitions its markers name, because the browser throws on a missing one."""
    assert len(html_markers) == count
    assert sorted(html_markers) == sorted(defined)
    assert len(set(html_markers)) == count


def test_fragment_cache_replays_bindings_allocated_outside_it_with_fresh_ids() -> None:
    app = i18n_app()
    stamps = itertools.count(1)

    class Page(Component):
        citry = app
        messages = """
        loading = Loading
        save = Save
        """

        def template_data(self, kwargs, slots):
            return {"stamp": next(stamps)}

        # Page's template contains every `$c-tr` element, so Page allocates all
        # four IDs, although two of the elements sit inside the cached part.
        template = """
        <c-i18n c-client="True" tag="main">
          <output $c-tr:loading>{{ tr("loading") }}</output>
          <c-cache key="fragment">
            <b>{{ stamp }}</b>
            <button
              c-aria-label="tr('save')"
              $c-tr:save[aria-label]
              $c-tr:save
            >{{ tr("save") }}</button>
          </c-cache>
          <output $c-tr:loading>{{ tr("loading") }}</output>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=4)
        # The cached part is replayed, not rendered again: it keeps the stamp
        # from the first render, while Page makes a new binding ID on each render.
        assert re.findall(r"<b>(\d+)</b>", html) == ["1"]
        seen.extend(marked)
    # A replay must not reuse an ID that an earlier render sent to the browser.
    assert len(set(seen)) == len(seen) == 12


def test_component_cache_replays_bindings_of_a_fill_allocated_outside_it() -> None:
    app = i18n_app()
    renders: list[int] = []

    class Card(Component):
        citry = app

        class Cache:
            enabled = True

            # Slot content cannot be part of an automatic cache key, so a fixed
            # key is how this card gets cached with the caller's content inside.
            def vary(self, kwargs, slots):
                return "stable"

        def template_data(self, kwargs, slots):
            renders.append(1)
            return {}

        template = "<section><c-slot /></section>"

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        template = """
        <c-i18n c-client="True" tag="main">
          <c-card><output $c-tr:loading>{{ tr("loading") }}</output></c-card>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=1)
        seen.extend(marked)
    assert renders == [1]
    assert len(set(seen)) == 3


def test_fragment_cache_at_the_root_of_a_child_template_replays_the_childs_bindings() -> None:
    app = i18n_app()

    class Panel(Component):
        citry = app
        template = """
        <c-cache key="panel">
          <i $c-tr:loading>{{ tr("loading") }}</i>
        </c-cache>
        """

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        # The second panel replays what the first one saved, in the same render.
        template = """
        <c-i18n c-client="True" tag="main">
          <c-panel />
          <c-panel />
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=2)
        seen.extend(marked)
    assert len(set(seen)) == 6


def test_fragment_cache_replays_a_binding_inside_a_provider_it_contains() -> None:
    app = i18n_app()

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        # The provider is part of the cached output, and Page's template
        # contains the element inside it, so Page allocates the binding.
        template = """
        <c-cache key="provider-inside">
          <c-i18n c-client="True" tag="main">
            <i $c-tr:loading>{{ tr("loading") }}</i>
          </c-i18n>
        </c-cache>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=1)
        seen.extend(marked)
    assert len(set(seen)) == 3


def test_nested_fragment_caches_replay_bindings_allocated_outside_both() -> None:
    app = i18n_app()
    stamps = itertools.count(1)

    class Page(Component):
        citry = app
        messages = "loading = Loading"

        class Kwargs:
            outer: str

        def template_data(self, kwargs, slots):
            return {"outer": kwargs.outer, "stamp": next(stamps)}

        template = """
        <c-i18n c-client="True" tag="main">
          <c-cache key="outer" c-vary="outer">
            <b>{{ stamp }}</b>
            <c-cache key="inner">
              <i $c-tr:loading>{{ tr("loading") }}</i>
            </c-cache>
          </c-cache>
        </c-i18n>
        """

    seen: list[str] = []
    outer_stamps: list[str] = []
    # The second `a` hits the outer part. The first `b` misses it but finds the
    # inner part cached, and must store the outer part with the inner one's
    # binding inside it. The second `b` and the last `a` then hit the outer part.
    for outer in ("a", "a", "b", "b", "a"):
        html, marked, defined = render_with_binding_ids(Page(outer=outer))
        assert_every_marker_is_defined_once(marked, defined, count=1)
        seen.extend(marked)
        outer_stamps.extend(re.findall(r"<b>(\d+)</b>", html))
    # A hit shows the stamp of the render that stored the part. The second
    # `b` shows 3 only if the first `b` stored its outer part.
    assert outer_stamps == ["1", "1", "3", "3", "1"]
    assert len(set(seen)) == 5


def test_one_fragment_used_twice_in_a_page_gives_each_use_its_own_binding_id() -> None:
    app = i18n_app()

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        template = """
        <c-i18n c-client="True" tag="main">
          <c-cache key="same">
            <i $c-tr:loading>{{ tr("loading") }}</i>
          </c-cache>
          <c-cache key="same">
            <i $c-tr:loading>{{ tr("loading") }}</i>
          </c-cache>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=2)
        seen.extend(marked)
    assert len(set(seen)) == 6


def test_cached_component_replays_its_own_binding_and_the_one_in_a_caller_fill() -> None:
    app = i18n_app()

    class Card(Component):
        citry = app
        messages = "title = Title"

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        # Card allocates the heading's binding and Page allocates the fill's,
        # so the boundary's record must hold both after a replay.
        template = """
        <section>
          <h2 $c-tr:title>{{ tr("title") }}</h2>
          <c-slot />
        </section>
        """

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        template = """
        <c-i18n c-client="True" tag="main">
          <c-card><output $c-tr:loading>{{ tr("loading") }}</output></c-card>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=2)
        seen.extend(marked)
    assert len(set(seen)) == 6


def external_client_provides(app: Citry) -> dict[str, Any]:
    """Build `provides` values that stand for a client i18n provider outside the page being rendered."""

    class Provider(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"></c-i18n>'

    rendered = Provider().render()
    (record,) = [item for item in rendered.context.extra[EXTRA_KEY].values() if item.provider is not None]
    return {"citry_i18n": record.provider.context, CLIENT_CONTEXT_KEY: record.render_id}


def test_entry_made_under_an_outside_client_provider_is_skipped_on_a_render_without_one() -> None:
    app = i18n_app()
    renders: list[int] = []

    class Card(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        def template_data(self, kwargs, slots):
            renders.append(1)
            return {}

        template = "<section><c-slot /></section>"

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        template = """
        <c-card><output $c-tr:loading>{{ tr("loading") }}</output></c-card>
        """

    provides = external_client_provides(app)
    render_with_binding_ids(Page(), provides=provides)
    _html, marked, defined = render_with_binding_ids(Page(), provides=provides)
    assert renders == [1]
    assert_every_marker_is_defined_once(marked, defined, count=1)
    # The stored binding belongs to a provider that this render does not have,
    # so a hit could not define it and would fail the request. The card
    # renders again instead, as plain text with no binding.
    html, marked, defined = render_with_binding_ids(Page())
    assert renders == [1, 1]
    assert (marked, defined) == ([], [])
    assert "Loading" in html


def test_fragment_cache_inside_a_fill_passed_to_another_component_replays_its_bindings() -> None:
    app = i18n_app()

    class Card(Component):
        citry = app
        template = "<section><c-slot /></section>"

    class Page(Component):
        citry = app
        messages = "loading = Loading"
        # Card renders the fill, but Page's template contains the element, so
        # Page allocates the binding and Card is not the one to look for it in.
        template = """
        <c-i18n c-client="True" tag="main">
          <c-card>
            <c-cache key="in-fill">
              <output $c-tr:loading>{{ tr("loading") }}</output>
            </c-cache>
          </c-card>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=1)
        seen.extend(marked)
    assert len(set(seen)) == 3


def test_fragment_cache_in_a_loop_replays_a_binding_for_every_item() -> None:
    app = i18n_app()

    class Page(Component):
        citry = app
        messages = "loading = Loading"

        def template_data(self, kwargs, slots):
            # The repeated "a" is a hit within the first render.
            return {"items": ["a", "b", "a"]}

        template = """
        <c-i18n c-client="True" tag="main">
          <c-for each="item in items">
            <c-cache key="item" c-vary="item">
              <output $c-tr:loading>{{ tr("loading") }}</output>
              <b>{{ item }}</b>
            </c-cache>
          </c-for>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=3)
        seen.extend(marked)
    assert len(set(seen)) == 9


def test_fragment_cache_inside_a_component_cache_keeps_its_binding_ids_valid() -> None:
    app = i18n_app()

    class Page(Component):
        citry = app
        messages = "loading = Loading"

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "stable"

        # Page is the cached component here, so the component whose template
        # contains the binding is inside the cached output and its own record
        # holds the binding.
        template = """
        <c-i18n c-client="True" tag="main">
          <c-cache key="inner">
            <i $c-tr:loading>{{ tr("loading") }}</i>
          </c-cache>
        </c-i18n>
        """

    seen: list[str] = []
    for _ in range(3):
        _html, marked, defined = render_with_binding_ids(Page())
        assert_every_marker_is_defined_once(marked, defined, count=1)
        seen.extend(marked)
    assert len(set(seen)) == 3


_FORGED_BINDING_IDS = (
    "forged",
    "c1~i18n-",
    "C1~i18n-1",
    "c1~i18n-1x",
    "c1 c2~i18n-1",
)


@pytest.mark.parametrize("forged", _FORGED_BINDING_IDS)
def test_replay_skips_an_entry_whose_binding_id_is_not_one_the_collector_writes(forged: str) -> None:
    backend = StoringCache()
    app = i18n_app(backend)
    stamps = itertools.count(1)

    class Page(Component):
        citry = app
        messages = "loading = Loading"

        def template_data(self, kwargs, slots):
            return {"stamp": next(stamps)}

        template = """
        <c-i18n c-client="True" tag="main">
          <c-cache key="fragment">
            <b>{{ stamp }}</b>
            <i $c-tr:loading>{{ tr("loading") }}</i>
            <i $c-tr:loading>{{ tr("loading") }}</i>
          </c-cache>
        </c-i18n>
        """

    render_with_binding_ids(Page())
    stored = {key: value for key, value in backend.written.items() if "binding_markers" in value}
    assert len(stored) == 1
    ((key, value),) = stored.items()
    old_ids: list[str] = []

    def find_bindings(node: Any) -> None:
        if isinstance(node, dict):
            if "bindings" in node and "binding_markers" in node:
                old_ids.extend(binding["id"] for binding in node["bindings"])
            for child in node.values():
                find_bindings(child)
        elif isinstance(node, list):
            for child in node:
                find_bindings(child)

    find_bindings(json.loads(value))
    assert len(old_ids) == 2
    # The new name goes into the record, its marker, and the stored parts, so
    # the entry agrees with itself and only the shape check can refuse it.
    backend.set(key, value.replace(old_ids[1], forged))

    # The edited entry is skipped like any unusable one, so the cached part is
    # rendered again (a new stamp) and the page still defines every marker.
    html, marked, defined = render_with_binding_ids(Page())
    assert re.findall(r"<b>(\d+)</b>", html) == ["2"]
    assert_every_marker_is_defined_once(marked, defined, count=2)


def wire_binding(binding_id: object) -> dict[str, Any]:
    return {
        "id": binding_id,
        "message": "loading",
        "output": None,
        "owner": "ambient",
        "target": {"kind": "text"},
        "values": {},
        "values_expression": None,
    }


def stage_bindings(
    *binding_ids: object, markers: list[dict[str, Any]], ambient_owner: str = "outside-provider"
) -> Any:
    return _bindings_from_wire(
        [wire_binding(binding_id) for binding_id in binding_ids],
        markers,
        path="record",
        render_id="fresh",
        instance_ids=("fresh",),
        parent_ids=(),
        ambient_owner=ambient_owner,
    )


def test_stored_bindings_from_two_components_get_fresh_ids_from_the_replayed_boundary() -> None:
    records, markers, _replacements = stage_bindings(
        "c1~i18n-0",
        "c2~i18n-0",
        markers=[{"ids": [0, 1], "value": "c1~i18n-0 c2~i18n-0"}],
    )
    assert [record.id for record in records.records] == ["fresh~i18n-0", "fresh~i18n-1"]
    assert markers == [("fresh~i18n-0", "fresh~i18n-1")]


def test_stored_binding_owned_by_an_outside_provider_needs_the_render_to_have_one() -> None:
    stage_bindings("c1~i18n-0", markers=[])
    with pytest.raises(
        CacheArtifactError, match=r"bindings\[0\]\.owner is a client provider that this render does not"
    ):
        # With no provider in the render, the stored "ambient" owner resolves to the placeholder.
        stage_bindings("c1~i18n-0", markers=[], ambient_owner=AMBIENT_CLIENT_OWNER)


def test_stored_binding_id_that_repeats_in_one_record_is_refused() -> None:
    with pytest.raises(CacheArtifactError, match=r"bindings\[1\]\.id repeats an earlier binding ID"):
        stage_bindings("c1~i18n-0", "c1~i18n-0", markers=[])


@pytest.mark.parametrize("forged", [*_FORGED_BINDING_IDS, "c1~i18n-" + "9" * 5000, 5])
def test_stored_binding_id_must_be_shaped_like_one_the_collector_writes(forged: object) -> None:
    with pytest.raises(CacheArtifactError, match=r"bindings\[0\]\.id must look like"):
        stage_bindings(forged, markers=[])


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("c1~i18n-0", ("c1", 0)),
        ("a-b_c9~i18n-12", ("a-b_c9", 12)),
        ("", None),
        ("c1", None),
        ("c1~i18n-", None),
        ("~i18n-1", None),
        ("C1~i18n-1", None),
        ("c1~i18n-1.5", None),
        # An Arabic-Indic digit is a decimal digit, but the collector never writes one.
        ("c1~i18n-\u0661", None),
        # A number this long cannot be a counter, and converting it would raise.
        ("c1~i18n-" + "9" * 5000, None),
        (None, None),
    ],
)
def test_binding_id_shape(value: object, expected: tuple[str, int] | None) -> None:
    assert split_binding_id(value) == expected
    assert is_binding_id(value) is (expected is not None)


def export_stub(*, operands: set[str], records: dict[str, Any], boundary: str = "boundary") -> Any:
    """A minimal export context: the exporter reads only these fields."""
    return SimpleNamespace(
        root_context=SimpleNamespace(component=None, extra={EXTRA_KEY: records}),
        instances=(SimpleNamespace(render_id=boundary, index=0, class_id="class"),),
        selected_render_ids=frozenset({boundary}),
        browser_binding_operands={BINDING_HELPER: frozenset(operands)},
    )


def outside_record(*bindings: str, markers: tuple[tuple[str, ...], ...] = ()) -> Any:
    """The record of a component that is not part of the stored output."""
    records = [SimpleNamespace(id=value) for value in bindings]
    collector = SimpleNamespace(
        records=records,
        markers=list(markers),
        record_by_id={record.id: record for record in records},
        marker_by_id={binding_id: marker for marker in markers for binding_id in marker},
    )
    return SimpleNamespace(render_id="outer", bindings=collector)


def test_export_refuses_a_binding_id_that_no_render_record_holds() -> None:
    extension = i18n_app().extensions.get_extension("i18n")
    stub = export_stub(operands={"outer~i18n-0"}, records={"outer": outside_record()})
    # Storing the ID would replay a page the browser rejects, so the entry is not stored.
    with pytest.raises(CacheArtifactError, match=r"outer~i18n-0.*no component's i18n record holds"):
        extension.export_render_cache(stub)


def test_export_refuses_bindings_allocated_outside_when_the_cache_boundary_has_no_record() -> None:
    extension = i18n_app().extensions.get_extension("i18n")
    stub = export_stub(
        operands={"outer~i18n-0"},
        records={"outer": outside_record("outer~i18n-0", markers=(("outer~i18n-0",),))},
    )
    with pytest.raises(CacheArtifactError, match="no i18n record to hold the bindings that components outside"):
        extension.export_render_cache(stub)


def test_export_refuses_a_marker_that_lists_ids_both_used_and_not_used_by_the_stored_output() -> None:
    extension = i18n_app().extensions.get_extension("i18n")
    stub = export_stub(
        operands={"outer~i18n-0"},
        records={
            "outer": outside_record(
                "outer~i18n-0",
                "outer~i18n-1",
                markers=(("outer~i18n-0", "outer~i18n-1"),),
            )
        },
    )
    with pytest.raises(CacheArtifactError, match="lists IDs both used and not used by the stored output"):
        extension.export_render_cache(stub)
