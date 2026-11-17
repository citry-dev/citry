"""The keys that name `css_data()` stylesheets: how Citry makes them from `secret`, and when it has none."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from citry import Citry, Component, InMemoryCache
from citry.ext.cache.errors import CacheArtifactError
from citry.ext.dependencies.extension import _capture_from_wire, _capture_to_wire
from citry.ext.dependencies.scripts import _CSS_DATA_KEY_LABEL, _css_data_hash, _css_data_keys, _css_vars_capture
from citry.ext.events.tokens import _STATE_TOKEN_KEY_LABEL, _state_token_key

SECRET = "css-data-name-secret-0123456789abcdef"  # noqa: S105 - a test value
OLD_SECRET = "css-data-old-secret-0123456789abcdef"  # noqa: S105 - a test value


def test_the_key_is_made_like_the_state_token_key_with_its_own_label() -> None:
    # The label is the HMAC key and the secret is the message, as for State tokens.
    key = _css_data_keys(Citry(secret=SECRET))[0]
    assert key == hmac.new(_CSS_DATA_KEY_LABEL, SECRET.encode(), hashlib.sha256).digest()
    assert _CSS_DATA_KEY_LABEL != _STATE_TOKEN_KEY_LABEL
    assert key != _state_token_key(SECRET)


def test_app_code_that_signs_the_label_with_the_raw_secret_does_not_hand_out_the_key() -> None:
    # Apps often sign text a visitor chooses with the same secret, such as an
    # unsubscribe link built as HMAC(SECRET_KEY, email). A visitor who asks
    # such code to sign the label must not get the key.
    signed_label = hmac.new(SECRET.encode(), _CSS_DATA_KEY_LABEL, hashlib.sha256).digest()
    assert signed_label not in _css_data_keys(Citry(secret=SECRET))


def test_each_secret_entry_gives_its_own_key_the_first_for_new_names() -> None:
    keys = _css_data_keys(Citry(secret=[SECRET, OLD_SECRET]))
    assert keys == (_css_data_keys(Citry(secret=SECRET))[0], _css_data_keys(Citry(secret=OLD_SECRET))[0])
    assert keys[0] != keys[1]


def test_a_render_cache_entry_named_before_a_secret_rotation_is_kept_until_the_old_secret_goes() -> None:
    cache = InMemoryCache()
    before = Citry(secret=OLD_SECRET, cache=cache)
    after = Citry(secret=[SECRET, OLD_SECRET], cache=cache)
    source = json.dumps({"pct": "37%"}, separators=(",", ":"))
    assert _css_data_hash(_css_data_keys(before)[0], source) != _css_data_hash(_css_data_keys(after)[0], source)
    capture = _css_vars_capture("w", source, _css_data_keys(before)[0])
    assert _capture_from_wire(_capture_to_wire(capture), path="a.css", class_id="w", citry=after) == capture
    # Once the old secret is removed, the entry is refused and rendered again.
    with pytest.raises(CacheArtifactError):
        _capture_from_wire(_capture_to_wire(capture), path="a.css", class_id="w", citry=Citry(secret=SECRET))


def test_a_render_cache_entry_whose_name_is_not_ascii_is_refused() -> None:
    app = Citry(secret=SECRET, cache=InMemoryCache())
    source = json.dumps({"pct": "37%"}, separators=(",", ":"))
    capture = _css_vars_capture("w", source, _css_data_keys(app)[0])
    wire = {**_capture_to_wire(capture), "hash": "\u00e9" * 32}
    with pytest.raises(CacheArtifactError):
        _capture_from_wire(wire, path="a.css", class_id="w", citry=app)


def test_without_a_secret_this_process_store_uses_a_random_process_key() -> None:
    # Without a configured cache, a stylesheet never leaves this process, so a
    # random key made once per process is enough, and engines in one process
    # agree on it.
    first, second = Citry(), Citry()
    assert _css_data_keys(first) == _css_data_keys(second)
    assert _css_data_keys(first)[0] is not None


def test_a_configured_cache_without_a_secret_names_stylesheets_without_a_key() -> None:
    assert _css_data_keys(Citry(cache=InMemoryCache())) == (None,)


def test_rendered_names_follow_the_first_secret() -> None:
    app = Citry(secret=[SECRET, OLD_SECRET], cache=InMemoryCache())
    app.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = app
        template = """
            <span class="w">w</span>
        """
        css = """
            .w { width: var(--pct); }
        """

        def css_data(self, kwargs, slots):
            return {"pct": "5%"}

    rendered = Widget().render()
    rendered.serialize(deps_strategy="fragment")
    dependencies = rendered.context.extra["dependencies"]
    name = next(item for item in dependencies if item.class_id == Widget.class_id).css_vars_hash
    source = json.dumps({"pct": "5%"}, separators=(",", ":"))
    assert name == _css_data_hash(_css_data_keys(Citry(secret=SECRET))[0], source)
