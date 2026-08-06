"""
Tests for the events manifest emission and runtime injection (WP10): the
``data-citry-events`` tag (docs/design/events.md 4.4), the runtime script and
bootstrap stub, the fixed-name ``data-cid`` marker (5.5), and the two
lifecycle emission additions for the dependency manager
(docs/design/dependencies.md 8.4).

Exact-output assertions are authored observe-then-lock: the emission ran on
representative pages, the real output was read, and that output is locked
here. Volatile parts are pinned the way the sibling suites do it: render ids
via the conftest counter, and the token clock via the ``tokens._now``
indirection, so the minted tokens are byte-stable within a test.
"""

import base64
import json
import re

import pytest

from citry import Citry, Component
from citry.ext.dependencies.routes import script_url
from citry.ext.events import event
from citry.ext.events.tokens import mint_state_token, verify_state_token

SIGNING_KEY = "test-secret-key"
FIXED_NOW = 1_700_000_000.0

_EVENTS_TAG_RE = re.compile(r'<script type="application/json" data-citry-events>(.*?)</script>', re.DOTALL)
_DEPS_TAG_RE = re.compile(r'<script type="application/json" data-citry>(.*?)</script>', re.DOTALL)


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch):
    """Pin the token mint clock, so tokens are stable and lockable."""
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def _events_manifest(html):
    match = _EVENTS_TAG_RE.search(html)
    assert match is not None, "no events manifest in output"
    return json.loads(match.group(1))


def _deps_manifest(html):
    match = _DEPS_TAG_RE.search(html)
    assert match is not None, "no data-citry manifest in output"
    return json.loads(match.group(1))


def _unb64(value):
    return base64.b64decode(value).decode()


def _fetch_descriptor(entry):
    encoded = entry[0] if isinstance(entry, list) else entry
    return json.loads(_unb64(encoded))


def _instances(manifest):
    return manifest["componentInstances"]


def _classes(manifest):
    return {entry["componentClassId"]: entry for entry in manifest["componentClasses"]}


def _search(c):
    """An Events component exercising State, ``_public``, and the descriptor hints."""

    class SearchState:
        query: str = ""
        limit: int = 10
        internal_note: str = "server-only"
        _public = ("query", "limit")

    class Search(Component):
        citry = c
        State = SearchState

        class Events:
            _debounce = 200

            def save(self, state):
                return None

            @event(name="find", methods=("GET",), debounce=300)
            def filter_items(self, state):
                return None

        template = """
            <div>search</div>
        """

    return Search


def _mounted_citry():
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")
    return c


class TestEventsManifestDocument:
    def test_two_instance_page_locks_the_manifest(self):
        c = _mounted_citry()
        search = _search(c)
        template = '<html><head></head><body><c-search query="shoes" /><c-search query="hats" /></body></html>'
        page = type("Page", (Component,), {"citry": c, "template": template})

        manifest = _events_manifest(str(page()))

        # The tokens the page minted are exactly what the public mint API
        # produces for the same state under the same pinned clock.
        expected_tokens = [
            mint_state_token(
                search.State(query=query),
                class_id=search.class_id,
                secret=SIGNING_KEY,
                max_age=None,
                max_bytes=8192,
            )
            for query in ("shoes", "hats")
        ]
        assert manifest["protocol"] == "citry-events/1"
        assert re.fullmatch(r"[0-9a-f]{64}", manifest["clientGraphRevision"])
        # Named records follow render order and expose only public State.
        assert _instances(manifest) == [
            {
                "renderId": "c2",
                "componentClassId": search.class_id,
                "stateToken": expected_tokens[0],
                "publicState": {"limit": 10, "query": "shoes"},
            },
            {
                "renderId": "c3",
                "componentClassId": search.class_id,
                "stateToken": expected_tokens[1],
                "publicState": {"limit": 10, "query": "hats"},
            },
        ]

    def test_values_map_respects_public_but_the_token_carries_all_fields(self):
        c = _mounted_citry()
        search = _search(c)

        html = str(search(query="shoes"))
        manifest = _events_manifest(html)
        [instance] = _instances(manifest)
        token = instance["stateToken"]

        # The non-public field appears nowhere in plain sight...
        assert instance["publicState"] == {"limit": 10, "query": "shoes"}
        assert "server-only" not in html
        # ...but rides inside the opaque token (7.1: signed, not hidden from
        # the server's own round-trip).
        verified = verify_state_token(token, cls=search, secrets=[SIGNING_KEY])
        assert verified.state_kwargs == {"query": "shoes", "limit": 10, "internal_note": "server-only"}

    def test_public_state_cannot_close_the_manifest_script(self):
        c = _mounted_citry()
        search = _search(c)

        html = str(search(query="</script><script>alert(1)</script>"))
        match = _EVENTS_TAG_RE.search(html)
        assert match is not None
        assert "</script" not in match.group(1).lower()
        [instance] = json.loads(match.group(1))["componentInstances"]
        assert instance["publicState"]["query"] == "</script><script>alert(1)</script>"

    def test_class_descriptor_locks_hints_and_name_override(self):
        c = _mounted_citry()
        search = _search(c)

        manifest = _events_manifest(str(search(query="q")))
        # One descriptor per class: the wire names (the @event(name=...)
        # override, not the method name), the primary HTTP method, and the
        # resolved timing hints (@event beats the component _debounce).
        assert _classes(manifest) == {
            search.class_id: {
                "componentClassId": search.class_id,
                "eventHandlers": {
                    "find": {
                        "httpMethod": "GET",
                        "usesState": True,
                        "debounceMilliseconds": 300,
                    },
                    "save": {
                        "httpMethod": "POST",
                        "usesState": True,
                        "debounceMilliseconds": 200,
                    },
                },
            },
        }

    @pytest.mark.parametrize(
        ("model", "expected_model"),
        [
            (("query",), ["query"]),
            ((), []),
        ],
    )
    def test_class_descriptor_carries_a_narrowed_or_empty_model(self, model, expected_model):
        c = _mounted_citry()

        class SearchState:
            query: str = ""
            limit: int = 10
            _public = ("query", "limit")
            _model = model

        class Search(Component):
            citry = c
            State = SearchState

            class Events:
                def save(self, state):
                    return None

            template = "<div>search</div>"

        manifest = _events_manifest(str(Search()))

        assert _classes(manifest) == {
            Search.class_id: {
                "componentClassId": Search.class_id,
                "eventHandlers": {"save": {"httpMethod": "POST", "usesState": True}},
                "writableStateFields": expected_model,
            },
        }

    def test_class_descriptor_carries_queue_knobs_only_when_non_default(self):
        c = _mounted_citry()

        class Widget(Component):
            citry = c

            class Events:
                def refresh(self):
                    return None

                @event(latest_wins=True, bundle=False)
                def autosave(self):
                    return None

                @event(latest_wins=True)
                def poll(self):
                    return None

                @event(latest_wins=False, bundle=True)
                def plain(self):
                    return None

            template = """
                <div>widget</div>
            """

        manifest = _events_manifest(str(Widget()))
        # The queue knobs ride the descriptor only at non-default values
        # (design 4.4): the knobbed handlers carry them, while the bare
        # handler and the handler decorated with the default values carry
        # neither field.
        assert _classes(manifest) == {
            Widget.class_id: {
                "componentClassId": Widget.class_id,
                "eventHandlers": {
                    "autosave": {
                        "httpMethod": "POST",
                        "latestCallWins": True,
                        "allowBatching": False,
                    },
                    "plain": {"httpMethod": "POST"},
                    "poll": {"httpMethod": "POST", "latestCallWins": True},
                    "refresh": {"httpMethod": "POST"},
                },
            },
        }

    def test_no_events_tag_without_events_components(self):
        c = _mounted_citry()

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """

        assert "data-citry-events" not in str(Card())

    def test_events_manifest_is_emitted_before_the_data_citry_tag(self):
        c = _mounted_citry()
        search = _search(c)

        html = str(search(query="q"))
        events_at = html.index("data-citry-events")
        deps_at = html.index("data-citry>")
        # The boot-order rule (events.md 5.2): whenever a component call can
        # fire, the events manifest must already be parsed.
        assert events_at < deps_at

    def test_runtime_script_url_is_emitted_before_the_route_exists(self):
        c = _mounted_citry()
        search = _search(c)

        # The path is fixed by design (events.md 3.8), so the tag is asserted
        # before any route serves it.
        assert '<script src="/citry/ext/events/runtime.js"></script>' in str(search(query="q"))

    def test_bootstrap_stub_is_emitted_inline(self):
        c = _mounted_citry()
        search = _search(c)

        html = str(search(query="q"))
        stub_at = html.index("Citry events bootstrap stub")
        runtime_at = html.index('src="/citry/ext/events/runtime.js"')
        assert stub_at < runtime_at  # the stub is in place before the runtime evaluates

    def test_stateless_events_component_registers_with_empty_token_and_values(self):
        c = _mounted_citry()

        class Clicker(Component):
            citry = c

            class Events:
                def go(self):
                    return None

            template = """
                <button>go</button>
            """

        manifest = _events_manifest(str(Clicker()))
        assert _instances(manifest) == [
            {
                "renderId": "c1",
                "componentClassId": Clicker.class_id,
                "stateToken": None,
                "publicState": {},
            }
        ]

    def test_unmounted_document_inlines_the_owned_alpine_runtime(self):
        # No web integration mounted: the manifest and stub still ride, and
        # A3 inlines the same pinned bundle so graph-linked callbacks and
        # Alpine markup work in the zero-configuration document flow.
        c = Citry(secret=SIGNING_KEY)

        class Solo(Component):
            citry = c

            class Events:
                def hi(self):
                    return None

            template = """
                <em>solo</em>
            """

        html = str(Solo())
        assert "data-citry-events" in html
        assert "Citry events bootstrap stub" in html
        assert '<script src="/citry/ext/events/runtime.js"' not in html
        assert "Citry events client runtime. GENERATED FILE" in html


class TestDataCidMarker:
    def test_instance_root_carries_the_fixed_name_marker(self):
        c = _mounted_citry()
        search = _search(c)

        html = str(search(query="q"))
        # Alongside the per-instance data-cid-<id> marker: a CSS selector
        # cannot wildcard attribute names, so closest() needs the fixed name
        # (events.md 5.5).
        assert '<div data-cid-c1="" data-citry-root="" data-cid="c1">search</div>' in html

    def test_shared_root_merges_ids_innermost_last(self):
        c = _mounted_citry()

        class Inner(Component):
            citry = c

            class Events:
                def ping(self):
                    return None

            template = """
                <span>inner</span>
            """

        class Outer(Component):
            citry = c

            class Events:
                def poke(self):
                    return None

            template = "<c-inner />"

        html = str(Outer())
        # One element roots both instances: both per-instance markers, and one
        # merged fixed-name marker with the innermost instance id last.
        assert '<span data-cid-c2="" data-citry-root="" data-cid-c1="" data-cid="c1 c2">inner</span>' in html

    def test_non_events_component_gets_no_fixed_name_marker(self):
        c = _mounted_citry()

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """

        assert 'data-cid="' not in str(Card())

    def test_client_active_non_events_component_gets_the_general_root_marker(self):
        c = _mounted_citry()

        class Card(Component):
            citry = c
            js = "$component(() => {})"
            template = '<p x-text="1">card</p>'

        html = str(Card())
        assert 'data-citry-root=""' in html
        assert 'data-cid="c1"' in html
        assert '<script src="/citry/ext/events/runtime.js"></script>' in html
        assert "data-citry-events" not in html

    def test_unrelated_static_branch_stays_out_of_the_client_registry(self):
        c = _mounted_citry()

        class Active(Component):
            citry = c
            js = "$component(() => {})"
            template = '<p class="active">active</p>'

        class Static(Component):
            citry = c
            template = '<p class="static">static</p>'

        class Page(Component):
            citry = c
            template = "<main><c-active /><c-static /></main>"

        html = str(Page())
        active = re.search(r'<p class="active"[^>]*>', html)
        static = re.search(r'<p class="static"[^>]*>', html)
        assert active is not None
        assert static is not None
        assert 'data-citry-root=""' in active.group()
        assert 'data-citry-root=""' not in static.group()
        assert 'data-cid="' not in static.group()


class TestEventsManifestFragment:
    def test_fragment_carries_its_own_manifest_before_the_data_citry_tag(self):
        c = _mounted_citry()
        search = _search(c)

        html = search(query="frag").render().serialize(deps_strategy="fragment")
        manifest = _events_manifest(html)
        [instance] = _instances(manifest)
        assert instance["renderId"] == "c1"
        assert instance["componentClassId"] == search.class_id
        assert instance["stateToken"].startswith("cev1.")
        assert instance["publicState"] == {"limit": 10, "query": "frag"}
        # Self-contained and ordered: the events manifest precedes the
        # data-citry tag inside the fragment itself.
        assert html.index("data-citry-events") < html.index("data-citry>")

    def test_fragment_delivers_stub_and_runtime_through_the_manifest(self):
        c = _mounted_citry()
        search = _search(c)

        from citry.ext.events.emission import _EVENTS_BOOTSTRAP_STUB

        html = search(query="frag").render().serialize(deps_strategy="fragment")
        fetch_js = [_fetch_descriptor(item) for item in _deps_manifest(html)["fetch"]["js"]]
        # The stub is an inline descriptor (the manager runs those
        # synchronously while processing the manifest, events.md 5.2), the
        # runtime a URL descriptor the manager fetches once per page. The
        # stub body must reach the browser byte-for-byte (it is real JS the
        # manager executes), so it is compared against the constant itself;
        # the marker comment is what the document-strategy test greps for.
        assert fetch_js == [
            {"tag": "script", "attrs": {}, "content": _EVENTS_BOOTSTRAP_STUB},
            {"tag": "script", "attrs": {"src": "/citry/ext/events/runtime.js"}, "content": ""},
        ]
        assert _EVENTS_BOOTSTRAP_STUB.startswith("/* Citry events bootstrap stub:")

    def test_simple_strategy_emits_no_events_client(self):
        c = _mounted_citry()
        search = _search(c)

        html = search(query="q").render().serialize(deps_strategy="simple")
        # "simple" is the no-JS-runtime mode: no manager, so no events client
        # either. The data-cid markers still render (they are plain markup).
        assert "data-citry-events" not in html
        assert "runtime.js" not in html
        assert "bootstrap stub" not in html
        assert 'data-cid="c1"' in html


class TestCssLifecycleEmission:
    def test_component_css_sheet_carries_its_class_marker(self):
        c = _mounted_citry()

        class Card(Component):
            citry = c
            css = ".card { color: teal; }"
            template = """
                <p>card</p>
            """

        html = str(Card())
        # The class marker is how the client-side manager's cleanup finds the
        # sheet when the class's last instance leaves the page
        # (dependencies.md 8.4).
        assert f'<style data-citry-css-class="{Card.class_id}">.card {{ color: teal; }}</style>' in html

    def test_fragment_css_descriptor_carries_the_class_marker(self):
        c = _mounted_citry()

        class Card(Component):
            citry = c
            css = ".card { color: teal; }"
            template = """
                <p>card</p>
            """

        html = Card().render().serialize(deps_strategy="fragment")
        fetch_css = [_fetch_descriptor(item) for item in _deps_manifest(html)["fetch"]["css"]]
        assert fetch_css == [
            {
                "tag": "link",
                "attrs": {
                    "data-citry-css-class": Card.class_id,
                    "rel": "stylesheet",
                    "href": script_url(Card, "css"),
                },
                "content": "",
            },
        ]

    def test_css_only_instance_emits_its_presence_record(self):
        # A Component.css instance with no $component JS: nothing else
        # registers it with the client-side manager, so the manifest must
        # declare it present for the per-class CSS cleanup to count it
        # (dependencies.md 8.4).
        c = _mounted_citry()

        class Card(Component):
            citry = c
            css = ".card { color: teal; }"
            template = """
                <p>card</p>
            """

        manifest = _deps_manifest(str(Card()))
        assert manifest["calls"] == []
        assert [[_unb64(part) for part in entry] for entry in manifest["cssInstances"]] == [[Card.class_id, "c1"]]

    def test_oncomponent_instance_is_not_in_the_presence_record(self):
        # An instance whose class registers $component is already counted
        # live through its manifest call, so it must not appear twice.
        c = _mounted_citry()

        class Widget(Component):
            citry = c
            css = ".w { color: red; }"
            js = "$component(() => {});"
            template = """
                <span>w</span>
            """

        manifest = _deps_manifest(str(Widget()))
        assert manifest["cssInstances"] == []
        assert [_unb64(part) for part in manifest["calls"][0][:2]] == [Widget.class_id, "c1"]
