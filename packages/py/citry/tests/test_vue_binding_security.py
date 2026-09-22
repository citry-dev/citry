from __future__ import annotations

import re
import warnings

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared
from citry.extension import Extension

_HANDLER_ONLY_DETAIL = "this control has a browser handler but no native navigation or submission fallback"
_SELECTED_EVENTS_DETAIL = "selected event, poll, or State control bindings require the Citry Events runtime"
_OMIT_MARKER_RE = re.compile(r"data-citry-omit-handler-[0-9a-f]+", re.IGNORECASE)


def _registry(**options):
    return Citry(
        secret="vue-binding-security-test-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
        **options,
    )


def _capture_runtime_warnings(call):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        result = call()
    return result, tuple(item for item in caught if item.category is RuntimeWarning)


def _handler_only_warnings(records):
    return tuple(record for record in records if _HANDLER_ONLY_DETAIL in str(record.message))


def _marker_from(html: str) -> str:
    match = _OMIT_MARKER_RE.search(html)
    assert match is not None
    return match.group(0)


def test_omit_warns_for_selected_event_handler_and_removes_private_marker() -> None:
    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    html, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert len(_handler_only_warnings(warnings_seen)) == 1
    assert "Save" in html
    assert "data-cev-" not in html
    assert "data-citry-omit-handler" not in html.lower()


def test_control_binding_does_not_get_handler_only_omit_warning() -> None:
    from citry._vue.serialization import analyze_vue_serialization

    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<input :c-query="save">'

        class State:
            query: str = ""

        class Events:
            def save(self, state):
                return None

    rendered = render_prepared(Page())
    analysis = analyze_vue_serialization(rendered)
    html, warnings_seen = _capture_runtime_warnings(
        lambda: rendered.serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert "events" in analysis.active_policy_requirements
    assert not _handler_only_warnings(warnings_seen)
    assert "data-citry-omit-handler" not in html.lower()


def test_omit_marker_cleanup_handles_quoted_case_duplicates_utf8_csp_and_integrity() -> None:
    class DuplicateQuotedMarker(Extension):
        name = "duplicate_quoted_omit_marker"

        def on_serialize(self, ctx):
            marker = _marker_from(ctx.html)
            return ctx.html.replace(marker, f'{marker.upper()}="first" {marker}="second"', 1)

    registry = _registry(
        extensions=[DuplicateQuotedMarker],
        security_csp="strict",
        security_javascript="omit",
        security_script_integrity="citry",
    )

    class Page(Component):
        citry = registry
        template = '<p>Žluťoučký</p><button id="kept" type="button" @c-click="save">Save</button>'
        js = "globalThis.managed = true;"
        css = "button { color: purple; }"

        class Events:
            def save(self):
                return None

    result, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize_result(deps_strategy="simple", csp_nonce="requestNonce")
    )

    assert len(_handler_only_warnings(warnings_seen)) == 1
    assert "Žluťoučký" in result.html
    assert result.html.count('id="kept"') == 1
    assert "data-citry-omit-handler" not in result.html.lower()
    assert "purple" in result.html
    assert re.search(r'<style\b[^>]*\bnonce="requestNonce"', result.html)
    assert "globalThis.managed" not in result.html
    assert result.security.scripts == ()
    assert result.security.csp_script_hashes == ()


def test_omit_marker_cleanup_preserves_separator_before_adjacent_first_attribute() -> None:
    class MoveMarkerFirst(Extension):
        name = "move_omit_marker_first"

        def on_serialize(self, ctx):
            marker = _marker_from(ctx.html)
            without_original = re.sub(rf"\s{re.escape(marker)}(?=[\s/>])", "", ctx.html, count=1)
            return re.sub(
                r"<button\b",
                f'<button {marker.upper()}=""id="kept"',
                without_original,
                count=1,
                flags=re.IGNORECASE,
            )

    registry = _registry(extensions=[MoveMarkerFirst])

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    html, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert len(_handler_only_warnings(warnings_seen)) == 1
    assert re.search(r'<button id="kept" type="button"[^>]*>', html)
    assert "data-citry-omit-handler" not in html.lower()


@pytest.mark.parametrize("form", ["boolean", "unquoted"])
def test_omit_marker_cleanup_handles_boolean_and_unquoted_attributes(form: str) -> None:
    class RewriteMarker(Extension):
        name = "rewrite_omit_marker_form"

        def on_serialize(self, ctx):
            marker = _marker_from(ctx.html)
            replacement = marker.upper() if form == "boolean" else f"{marker.upper()}=private"
            return ctx.html.replace(marker, replacement, 1)

    registry = _registry(extensions=[RewriteMarker])

    class Page(Component):
        citry = registry
        template = '<button id="kept" type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    html, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert len(_handler_only_warnings(warnings_seen)) == 1
    assert 'id="kept"' in html
    assert "data-citry-omit-handler" not in html.lower()


def test_omit_marker_leak_into_text_fails_closed() -> None:
    leaked_html = ""

    class LeakMarker(Extension):
        name = "leak_omit_marker"

        def on_serialize(self, ctx):
            nonlocal leaked_html
            marker = _marker_from(ctx.html)
            without_attribute = re.sub(rf"\s{re.escape(marker)}(?=[\s/>])", "", ctx.html, count=1)
            leaked_html = f"{without_attribute}{marker}"
            return leaked_html

    registry = _registry(extensions=[LeakMarker])

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    with pytest.raises(ValueError, match="omission handler metadata escaped settled HTML cleanup"):
        render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")

    assert leaked_html.endswith(_marker_from(leaked_html))


@pytest.mark.parametrize(
    ("template", "values", "has_selected_action"),
    [
        ('<c-if cond="shown"><button type="button" @c-click="save">Action</button></c-if>', {"shown": False}, False),
        ('<c-if cond="shown"><button type="button" @c-click="save">Action</button></c-if>', {"shown": True}, True),
        (
            '<c-for each="item in items"><button type="button" @c-click="save">Action {{ item }}</button></c-for>',
            {"items": []},
            False,
        ),
        (
            '<c-for each="item in items"><button type="button" @c-click="save">Action {{ item }}</button></c-for>',
            {"items": ["one"]},
            True,
        ),
    ],
)
def test_omit_handler_warning_tracks_selected_if_and_loop_occurrences(
    template: str, values: dict[str, object], has_selected_action: bool
) -> None:
    registry = _registry()
    component_template = template

    class Page(Component):
        citry = registry
        template = component_template

        class Events:
            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return values

    html, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert bool(_handler_only_warnings(warnings_seen)) is has_selected_action
    assert ("Action" in html) is has_selected_action
    assert "data-citry-omit-handler" not in html.lower()


def test_event_and_poll_on_same_element_create_one_fallback_warning() -> None:
    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save" @c-poll.10s="refresh">Action</button>'

        class Events:
            def save(self):
                return None

            def refresh(self):
                return None

    html, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert len(_handler_only_warnings(warnings_seen)) == 1
    assert "data-cev-" not in html
    assert "data-citry-omit-handler" not in html.lower()


def test_forbid_uses_selected_typed_event_even_after_hook_removes_markup() -> None:
    hook_calls = 0

    class StripMarkup(Extension):
        name = "strip_selected_event_markup"

        def on_serialize(self, ctx):
            nonlocal hook_calls
            hook_calls += 1
            assert "data-cev-" not in ctx.html
            return "<p>plain hook result</p>"

    registry = _registry(extensions=[StripMarkup])

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    with pytest.raises(ValueError, match="selected event, poll, or State control bindings"):
        render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="forbid")

    assert hook_calls == 1


def test_forbid_uses_selected_js_data_even_after_hook_removes_markup() -> None:
    hook_calls = 0

    class StripMarkup(Extension):
        name = "strip_selected_js_data_markup"

        def on_serialize(self, ctx):
            nonlocal hook_calls
            hook_calls += 1
            return "<p>plain hook result</p>"

    registry = _registry(extensions=[StripMarkup])

    class Page(Component):
        citry = registry
        template = "<p>Static fallback</p>"

        def js_data(self, kwargs, slots):
            return {"enabled": True}

    with pytest.raises(ValueError, match="selected component js_data requires the Vue runtime"):
        render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="forbid")

    assert hook_calls == 1


def test_forbid_treats_selected_state_control_as_active_policy() -> None:
    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<input :c-query="save">'

        class State:
            query: str = ""

        class Events:
            def save(self, state):
                return None

    with pytest.raises(ValueError, match="selected event, poll, or State control bindings"):
        render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="forbid")


def test_unused_events_declaration_is_not_active_policy_but_preserves_runtime_opt_in() -> None:
    registry = _registry()

    class Page(Component):
        citry = registry
        template = "<p>Static fallback</p>"

        class Events:
            def imperative(self):
                return None

    forbidden, warnings_seen = _capture_runtime_warnings(
        lambda: Page().render().serialize(security_javascript="forbid")
    )
    assert "Static fallback" in forbidden
    assert not any("selected event" in str(item.message) for item in warnings_seen)

    registry.set_mounted_prefix("/citry")
    allowed = Page().render().serialize(security_javascript="allow")
    assert "CitryStable.startPrepared" in allowed


def test_omit_marker_is_removed_on_cache_replay() -> None:
    template_data_calls = 0
    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">{{ label }}</button>'

        class Cache:
            enabled = True

        class State:
            value: int = 5
            _public = ("value",)
            _storage = "server"

        class Events:
            def save(self, state):
                return None

        def template_data(self, kwargs, slots):
            nonlocal template_data_calls
            template_data_calls += 1
            return {"label": "Save"}

    fresh = render_prepared(Page())
    replay = render_prepared(Page())
    assert template_data_calls == 1

    for rendered in (fresh, replay):
        html, warnings_seen = _capture_runtime_warnings(
            lambda rendered=rendered: rendered.serialize(deps_strategy="ignore", security_javascript="omit")
        )
        assert len(_handler_only_warnings(warnings_seen)) == 1
        assert "data-citry-omit-handler" not in html.lower()


def test_repeat_serialization_does_not_leak_omit_marker() -> None:
    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    rendered = render_prepared(Page())
    first, first_warnings = _capture_runtime_warnings(
        lambda: rendered.serialize(deps_strategy="ignore", security_javascript="omit")
    )
    second, second_warnings = _capture_runtime_warnings(
        lambda: rendered.serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert first == second
    assert len(_handler_only_warnings(first_warnings)) == 1
    assert len(_handler_only_warnings(second_warnings)) == 1
    assert "data-citry-omit-handler" not in first.lower()
    assert "data-citry-omit-handler" not in second.lower()


def test_omit_hook_removes_diagnostic_marker_before_fallback_scan() -> None:
    hook_calls = 0

    class RemoveManagedMarkup(Extension):
        name = "remove_omit_diagnostic_and_legacy_event_carriers"

        def on_serialize(self, ctx):
            nonlocal hook_calls
            hook_calls += 1
            assert _OMIT_MARKER_RE.search(ctx.html) is not None
            assert "data-cev-" not in ctx.html
            return _OMIT_MARKER_RE.sub("", ctx.html)

    registry = _registry(extensions=[RemoveManagedMarkup])

    class Page(Component):
        citry = registry
        template = '<button type="button" @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    html, warnings_seen = _capture_runtime_warnings(
        lambda: render_prepared(Page()).serialize(deps_strategy="ignore", security_javascript="omit")
    )

    assert hook_calls == 1
    assert "Save" in html
    assert "data-cev-" not in html
    assert "data-citry-omit-handler" not in html.lower()
    assert not _handler_only_warnings(warnings_seen)


def test_analysis_reads_selected_leaf_tables_without_materializing_them(monkeypatch) -> None:
    from citry._vue import leaf_program
    from citry._vue.leaf_program import PreparedLeafProgram
    from citry._vue.serialization import analyze_vue_serialization

    registry = _registry()

    class Page(Component):
        citry = registry
        template = '<c-for each="item in items"><button @c-click="save">{{ item }}</button></c-for>'

        class Events:
            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return {"items": ["one"]}

    rendered = render_prepared(Page())
    assert any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)

    def fail_materialization(_value):
        pytest.fail("serialization analysis materialized the selected leaf program")

    monkeypatch.setattr(leaf_program, "typed_leaf_parts", fail_materialization)
    analysis = analyze_vue_serialization(rendered)

    assert "events" in analysis.runtime_requirements
    assert "events" in analysis.active_policy_requirements
