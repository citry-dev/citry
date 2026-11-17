"""
With a key, nobody can confirm a guessed `css_data()` value by requesting its URL, and no `js_data()` script is served.

These tests go through the routes only, so they show the same behaviour
on any release that has these routes. The keys behind the names are
tested in `test_css_data_stylesheet_keys.py`.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import re

import pytest

from citry import Citry, Component, InMemoryCache
from citry._vue.events import hold_page_assets
from citry.contrib.wsgi import wsgi_app
from citry.ext.dependencies.routes import script_url

SECRET = "css-data-name-secret-0123456789abcdef"  # noqa: S105 - a test value
OLD_SECRET = "css-data-old-secret-0123456789abcdef"  # noqa: S105 - a test value


def _get(app: Citry, path: str) -> tuple[str, bytes]:
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "SCRIPT_NAME": "",
        "QUERY_STRING": "",
        "wsgi.input": io.BytesIO(b""),
    }
    statuses: list[str] = []
    body = b"".join(wsgi_app(app)(environ, lambda status, _headers: statuses.append(status)))
    return statuses[0], body


def _widget(app: Citry) -> type[Component]:
    class Widget(Component):
        citry = app
        template = """
            <span class="w">w</span>
        """
        css = """
            .w { width: var(--pct); }
        """

        def css_data(self, kwargs, slots):
            return {"pct": f"{kwargs['pct']}%"}

    return Widget


def _plain_name(data: dict[str, str]) -> str:
    # What an outsider can compute from a guessed value: the canonical JSON's sha256.
    source = json.dumps(data, separators=(",", ":"))
    return hashlib.sha256(source.encode()).hexdigest()[:32]


def _rendered_name(widget: type[Component], rendered: object) -> str:
    dependencies = rendered.context.extra["dependencies"]  # type: ignore[attr-defined]
    return next(item for item in dependencies if item.class_id == widget.class_id).css_vars_hash


@pytest.mark.parametrize(
    "settings",
    [
        pytest.param({"secret": SECRET}, id="secret_and_this_process_store"),
        pytest.param({"secret": SECRET, "cache": InMemoryCache()}, id="secret_and_configured_cache"),
        pytest.param({}, id="no_secret_and_this_process_store"),
    ],
)
def test_a_guessed_value_cannot_be_confirmed_through_the_stylesheet_url(settings: dict[str, object]) -> None:
    app = Citry(**settings)
    app.set_mounted_prefix("/citry")
    widget = _widget(app)
    rendered = widget(pct=37).render()
    with hold_page_assets(app, rendered):
        name = _rendered_name(widget, rendered)
        # The page's own URL works.
        status, body = _get(app, f"/cache/{widget.class_id}.{name}.css")
        assert status.startswith("200")
        assert b"--pct: 37%;" in body
        # The name an outsider computes from the right guess is not that URL.
        guessed = _plain_name({"pct": "37%"})
        assert name != guessed
        status, _body = _get(app, f"/cache/{widget.class_id}.{guessed}.css")
        assert status.startswith("404")


def test_the_vue_stylesheet_url_cannot_be_computed_from_a_guessed_value() -> None:
    # On an interactive page the same stylesheet is also served at a URL named
    # by the sha256 of its bytes, and those bytes hold the stylesheet's name.
    app = Citry(secret=SECRET)
    app.set_mounted_prefix("/citry")

    class Bar(Component):
        citry = app
        template = """
            <div class="bar" @click="n += 1">bar</div>
        """
        js = """
            $component({ data() { return { n: 0 }; } });
        """
        css = """
            .bar { width: var(--pct); }
        """

        def css_data(self, kwargs, slots):
            return {"pct": "42%"}

    html = Bar().render().serialize()
    assert "/ext/events/assets/" in html
    guessed = f"/* {Bar.class_id} */\n[data-ccss-{_plain_name({'pct': '42%'})}] {{\n  --pct: 42%;\n}}"
    digest = hashlib.sha256(guessed.encode()).hexdigest()
    status, _body = _get(app, f"/ext/events/assets/{digest}.css")
    assert status.startswith("404")


def _bar(app: Citry) -> type[Component]:
    class Bar(Component):
        citry = app
        template = """
            <div class="bar" @click="n += 1">bar</div>
        """
        js = """
            $component({ data() { return { n: 0 }; } });
        """
        css = """
            .bar { width: var(--pct); }
        """

        def css_data(self, kwargs, slots):
            return {"pct": kwargs.get("pct", "42%")}

    return Bar


def test_a_vue_stylesheet_left_in_a_shared_cache_under_a_name_without_a_key_is_not_served() -> None:
    # A shared cache can still hold the file an earlier release published
    # for this stylesheet, named by the sha256 of bytes anyone can compute.
    cache = InMemoryCache()
    app = Citry(secret=SECRET, cache=cache)
    app.set_mounted_prefix("/citry")
    bar = _bar(app)
    leftover = f"/* {bar.class_id} */\n[data-ccss-{_plain_name({'pct': '42%'})}] {{\n  --pct: 42%;\n}}"
    digest = hashlib.sha256(leftover.encode()).hexdigest()
    cache.set(f"citry:vue-style:{digest}", leftover)
    status, body = _get(app, f"/ext/events/assets/{digest}.css")
    assert status.startswith("404")
    assert b"42%" not in body


def test_a_vue_stylesheet_another_worker_published_is_served() -> None:
    # Two engines share one cache and one secret, as two workers do.
    cache = InMemoryCache()
    first = Citry(secret=SECRET, cache=cache)
    second = Citry(secret=SECRET, cache=cache)
    for app in (first, second):
        app.set_mounted_prefix("/citry")
    _bar(second)
    html = _bar(first)(pct="17%").render().serialize()
    digests = re.findall(r"/ext/events/assets/([0-9a-f]{64})\.css", html)
    bodies = [_get(second, f"/ext/events/assets/{digest}.css") for digest in digests]
    assert all(status.startswith("200") for status, _body in bodies)
    assert any(b"--pct: 17%;" in body for _status, body in bodies)


def test_a_stylesheet_named_before_a_secret_rotation_still_resolves() -> None:
    # Three engines share one cache, as deploys around a secret rotation do.
    cache = InMemoryCache()
    before = Citry(secret=OLD_SECRET, cache=cache)
    during = Citry(secret=[SECRET, OLD_SECRET], cache=cache)
    after = Citry(secret=SECRET, cache=cache)
    for app in (before, during, after):
        app.set_mounted_prefix("/citry")
    widgets = [_widget(app) for app in (before, during, after)]
    rendered = widgets[0](pct=37).render()
    rendered.serialize()
    url = f"/cache/{widgets[0].class_id}.{_rendered_name(widgets[0], rendered)}.css"
    # While the old secret stays listed, a page rendered before the rotation keeps its stylesheet.
    assert _get(during, url)[0].startswith("200")
    # Once it is removed, the old name means nothing.
    assert _get(after, url)[0].startswith("404")


def test_a_configured_cache_without_a_secret_warns_once(caplog: pytest.LogCaptureFixture) -> None:
    # Workers sharing the cache must compute the same name, and with no secret
    # they share no key, so the name stays a plain hash and the log says so.
    app = Citry(cache=InMemoryCache())
    app.set_mounted_prefix("/citry")
    widget = _widget(app)
    with caplog.at_level(logging.WARNING, logger="citry"):
        for pct in (1, 2, 3):
            widget(pct=pct).render().serialize()
    warnings = [record for record in caplog.records if "no secret" in record.getMessage()]
    assert len(warnings) == 1
    assert "css_data()" in warnings[0].getMessage()
    # The documented gap: a guessed value can be confirmed in this setup.
    status, _body = _get(app, f"/cache/{widget.class_id}.{_plain_name({'pct': '2%'})}.css")
    assert status.startswith("200")


@pytest.mark.parametrize(
    "settings",
    [
        pytest.param({"secret": SECRET, "cache": InMemoryCache()}, id="secret_and_configured_cache"),
        pytest.param({}, id="no_secret_and_this_process_store"),
    ],
)
def test_an_engine_with_a_key_does_not_warn(settings: dict[str, object], caplog: pytest.LogCaptureFixture) -> None:
    app = Citry(**settings)
    app.set_mounted_prefix("/citry")
    with caplog.at_level(logging.WARNING, logger="citry"):
        _widget(app)(pct=1).render().serialize()
    assert not [record for record in caplog.records if "no secret" in record.getMessage()]


def _old_js_data_entry(class_id: str, data: dict[str, str], *, short_name: bool) -> tuple[str, str]:
    # What citry 0.3.0 to 0.5.1 stored for one js_data() result, with no
    # expiry. Citry 0.1.0 and 0.2.0 stored the same script under a name of
    # six hex characters.
    source = json.dumps(data, allow_nan=False, separators=(",", ":"))
    if short_name:
        name = hashlib.md5(source.encode(), usedforsecurity=False).hexdigest()[:6]
    else:
        name = hashlib.sha256(source.encode()).hexdigest()[:32]
    encoded = base64.b64encode(source.encode()).decode()
    content = f'Citry.manager.registerComponentData("{class_id}", "{name}", atob("{encoded}"));'
    script = {"kind": "variables", "url": None, "content": content, "attrs": {}, "wrap": True}
    return name, json.dumps({**script, "origin_class_id": class_id})


def _account(app: Citry) -> type[Component]:
    class Account(Component):
        citry = app
        template = """
            <div class="account">account</div>
        """
        js = """
            console.log("account");
        """

        def js_data(self, kwargs, slots):
            return {"pin": "4711"}

    return Account


@pytest.mark.parametrize(
    "short_name",
    [pytest.param(False, id="written_by_0_3_0_to_0_5_1"), pytest.param(True, id="written_by_0_1_0_or_0_2_0")],
)
def test_a_js_data_script_left_in_a_shared_cache_by_an_older_release_is_not_served(short_name: bool) -> None:
    cache = InMemoryCache()
    app = Citry(secret=SECRET, cache=cache)
    app.set_mounted_prefix("/citry")
    account = _account(app)
    name, entry = _old_js_data_entry(account.class_id, {"pin": "4711"}, short_name=short_name)
    cache.set(f"citry:{account.class_id}:js:{name}", entry)
    status, body = _get(app, f"/cache/{account.class_id}.{name}.js")
    assert status.startswith("404")
    assert b"4711" not in body
    assert b"atob" not in body


def test_an_unreadable_leftover_stylesheet_entry_is_a_miss() -> None:
    # An entry of another shape counts as missing instead of answering 500.
    cache = InMemoryCache()
    app = Citry(secret=SECRET, cache=cache)
    app.set_mounted_prefix("/citry")
    widget = _widget(app)
    name = "0" * 32
    cache.set(f"citry:{widget.class_id}:css:{name}", "not json")
    assert _get(app, f"/cache/{widget.class_id}.{name}.css")[0].startswith("404")


def test_the_class_javascript_is_still_served_at_its_hashed_url() -> None:
    app = Citry(secret=SECRET, cache=InMemoryCache())
    app.set_mounted_prefix("/citry")
    account = _account(app)
    url = script_url(account, "js")
    assert url.startswith(f"/citry/cache/{account.class_id}.")
    status, body = _get(app, url.removeprefix("/citry"))
    assert status.startswith("200")
    assert b'console.log("account")' in body


class CountingCache(InMemoryCache):
    """A shared cache that records every read and delete, the round trips a remote backend would make."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def get(self, key: str) -> str | None:
        self.calls.append("get")
        return super().get(key)

    def delete(self, key: str) -> None:
        self.calls.append("delete")
        super().delete(key)

    def has(self, key: str) -> bool:
        self.calls.append("has")
        return super().has(key)

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self.calls.append("set")
        super().set(key, value, ttl)

    def take_calls(self) -> int:
        # A remote backend answers each call in one round trip, so the
        # number of calls is what the response time follows.
        calls, self.calls = len(self.calls), []
        return calls


def _plant_leftover(cache: InMemoryCache, class_id: str, pct: str) -> tuple[str, str, str]:
    # What citry 1.0.0 leaves in a shared cache for one css_data() result:
    # the stored values under a name made without a key, and the Vue copy.
    source = json.dumps({"pct": pct}, separators=(",", ":"))
    name = _plain_name({"pct": pct})
    text = f"/* {class_id} */\n[data-ccss-{name}] {{\n  --pct: {pct};\n}}"
    style = {"kind": "variables", "url": None, "content": text, "attrs": {}, "origin_class_id": class_id}
    entry_key = f"citry:{class_id}:css:{name}"
    copy_key = f"citry:vue-style:{hashlib.sha256(text.encode()).hexdigest()}"
    cache.set(entry_key, json.dumps({**style, "source": source}))
    cache.set(copy_key, text)
    return name, entry_key, copy_key


def _copy_digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _published_copy(cache: CountingCache, bar: type[Component], pct: str) -> tuple[str, str]:
    # A worker renders an interactive page and publishes its css_data()
    # stylesheet's Vue copy.
    html = bar(pct=pct).render().serialize()
    for digest in dict.fromkeys(re.findall(r"/ext/events/assets/([0-9a-f]{64})\.css", html)):
        text = InMemoryCache.get(cache, f"citry:vue-style:{digest}") or ""
        if f"--pct: {pct}" in text:
            return digest, text
    raise AssertionError("no css_data() copy published")


def test_every_refused_vue_stylesheet_url_does_the_same_cache_work_as_a_miss() -> None:
    # The response time of a 404 must not tell whether the cache holds a
    # copy for the guessed URL, whatever kind of copy it is.
    cache = CountingCache()
    app = Citry(secret=OLD_SECRET, cache=cache)
    newer = Citry(secret=[SECRET, OLD_SECRET], cache=cache)
    for engine in (app, newer):
        engine.set_mounted_prefix("/citry")
    bar = _bar(app)
    _name, entry_key, leftover_key = _plant_leftover(cache, bar.class_id, "37%")
    rotation_digest, _text = _published_copy(cache, _bar(newer), "17%")
    # A copy with this worker's own name but other bytes, as a release that
    # writes the stylesheet text differently leaves.
    _digest, own_text = _published_copy(cache, bar, "9%")
    other_bytes = own_text + "\n"
    cache.set(f"citry:vue-style:{_copy_digest(other_bytes)}", other_bytes)
    unknown = f"/* NotAClass_0123ab */\n[data-ccss-{'0' * 32}] {{\n  --pct: 37%;\n}}"
    unknown_key = f"citry:vue-style:{_copy_digest(unknown)}"
    cache.set(unknown_key, unknown)
    missing_entry = f"/* {bar.class_id} */\n[data-ccss-{'1' * 32}] {{\n  --pct: 5%;\n}}"
    missing_key = f"citry:vue-style:{_copy_digest(missing_entry)}"
    cache.set(missing_key, missing_entry)
    urls = {
        "leftover": f"/ext/events/assets/{leftover_key.rsplit(':', 1)[1]}.css",
        "leftover_again": f"/ext/events/assets/{leftover_key.rsplit(':', 1)[1]}.css",
        "absent": f"/ext/events/assets/{'2' * 64}.css",
        "unknown_class": f"/ext/events/assets/{_copy_digest(unknown)}.css",
        "missing_entry": f"/ext/events/assets/{_copy_digest(missing_entry)}.css",
        "secret_not_held": f"/ext/events/assets/{rotation_digest}.css",
        "other_bytes": f"/ext/events/assets/{_copy_digest(other_bytes)}.css",
    }
    work = {}
    cache.take_calls()
    for label, url in urls.items():
        assert _get(app, url)[0].startswith("404"), label
        work[label] = cache.take_calls()
    assert all(calls == work["absent"] for calls in work.values()), work
    # A leftover and a copy with no stored values left are deleted, so the
    # next guess finds nothing.
    for key in (entry_key, leftover_key, missing_key):
        assert InMemoryCache.get(cache, key) is None
    # A copy of a class this worker does not know, or one named under a
    # secret it does not hold yet, may be linked by another worker, so it stays.
    assert InMemoryCache.get(cache, unknown_key) == unknown
    assert InMemoryCache.get(cache, f"citry:vue-style:{rotation_digest}") is not None
    assert _get(newer, urls["secret_not_held"])[0].startswith("200")


def test_every_refused_stylesheet_name_does_the_same_cache_work_as_a_miss() -> None:
    cache = CountingCache()
    app = Citry(secret=OLD_SECRET, cache=cache)
    newer = Citry(secret=[SECRET, OLD_SECRET], cache=cache)
    for engine in (app, newer):
        engine.set_mounted_prefix("/citry")
    widget = _widget(app)
    newer_widget = _widget(newer)
    name, entry_key, _copy_key = _plant_leftover(cache, widget.class_id, "37%")
    rendered = newer_widget(pct=17).render()
    rendered.serialize()
    rotation_name = _rendered_name(newer_widget, rendered)
    cache.set(f"citry:{widget.class_id}:css:{'3' * 32}", "not json")
    names = {
        "leftover": name,
        "leftover_again": name,
        "absent": _plain_name({"pct": "38%"}),
        "not_json": "3" * 32,
        "secret_not_held": rotation_name,
    }
    # The first request for a class stores the class's own stylesheet in
    # this process, whatever name it asks for.
    _get(app, f"/cache/{widget.class_id}.{'4' * 32}.css")
    work = {}
    cache.take_calls()
    for label, value in names.items():
        assert _get(app, f"/cache/{widget.class_id}.{value}.css")[0].startswith("404"), label
        work[label] = cache.take_calls()
    assert all(calls == work["absent"] for calls in work.values()), work
    assert InMemoryCache.get(cache, entry_key) is None
    assert _get(newer, f"/cache/{widget.class_id}.{rotation_name}.css")[0].startswith("200")


class ReadOnlyCache(InMemoryCache):
    """A shared cache that refuses deletes, as a read-only replica does."""

    def delete(self, key: str) -> None:
        raise RuntimeError("this cache refuses writes")


def test_a_cache_that_refuses_deletes_still_answers_404() -> None:
    # A 404 for a name nobody stored writes nothing, and one for a leftover
    # that cannot be deleted stays a 404 instead of a server error.
    cache = ReadOnlyCache()
    app = Citry(secret=SECRET, cache=cache)
    app.set_mounted_prefix("/citry")
    bar = _bar(app)
    name, _entry_key, copy_key = _plant_leftover(cache, bar.class_id, "37%")
    for path in (
        f"/cache/{bar.class_id}.{_plain_name({'pct': '38%'})}.css",
        f"/ext/events/assets/{'2' * 64}.css",
        f"/cache/{bar.class_id}.{name}.css",
        f"/ext/events/assets/{copy_key.rsplit(':', 1)[1]}.css",
    ):
        assert _get(app, path)[0].startswith("404"), path
