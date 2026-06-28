"""Tests for the Django contrib hot-reload piggyback (``enable_hot_reload``)."""

# ruff: noqa: ANN

import pytest

from citry import Citry, Component


def _loaded_template_component(tmp_path):
    """An engine + component whose template_file is loaded (so it is in the file index)."""
    file_path = tmp_path / "card.html"
    file_path.write_text("<p>v1</p>")
    engine = Citry(dirs=[tmp_path])

    class Card(Component):
        citry = engine
        template_file = "card.html"

    Card.get_template()
    return engine, Card, file_path


def test_invalid_mode_raises_without_django():
    # The mode check runs before Django is imported, so this needs no Django.
    from citry.contrib.django import enable_hot_reload

    with pytest.raises(ValueError, match="mode must be 'hot' or 'restart'"):
        enable_hot_reload(Citry(), mode="nope")  # type: ignore[arg-type]


def test_hot_mode_invalidates_and_suppresses_restart(tmp_path):
    pytest.importorskip("django")
    from django.utils.autoreload import file_changed

    from citry.contrib.django import enable_hot_reload

    engine, card, file_path = _loaded_template_component(tmp_path)
    file_path.write_text("<p>v2</p>")

    receiver = enable_hot_reload(engine, mode="hot")
    try:
        results = file_changed.send_robust(sender=None, file_path=file_path)
        ours = [value for recv, value in results if recv is receiver]
    finally:
        file_changed.disconnect(receiver)

    # hot mode returns True, which tells Django's autoreloader the change was
    # handled (no process restart), and the cache is refreshed in place.
    assert ours == [True]
    assert card.get_template().source == "<p>v2</p>"


def test_restart_mode_invalidates_but_lets_django_restart(tmp_path):
    pytest.importorskip("django")
    from django.utils.autoreload import file_changed

    from citry.contrib.django import enable_hot_reload

    engine, card, file_path = _loaded_template_component(tmp_path)
    file_path.write_text("<p>v2</p>")

    receiver = enable_hot_reload(engine, mode="restart")
    try:
        results = file_changed.send_robust(sender=None, file_path=file_path)
        ours = [value for recv, value in results if recv is receiver]
    finally:
        file_changed.disconnect(receiver)

    # restart mode returns None so Django falls through to its own restart, but
    # the caches are still cleared first.
    assert ours == [None]
    assert card.get_template().source == "<p>v2</p>"


def test_unknown_file_is_left_to_django(tmp_path):
    pytest.importorskip("django")
    from django.utils.autoreload import file_changed

    from citry.contrib.django import enable_hot_reload

    engine, _, _ = _loaded_template_component(tmp_path)

    receiver = enable_hot_reload(engine, mode="hot")
    try:
        results = file_changed.send_robust(sender=None, file_path=tmp_path / "unrelated.py")
        ours = [value for recv, value in results if recv is receiver]
    finally:
        file_changed.disconnect(receiver)

    # A file no component loaded returns None, so Django decides what to do.
    assert ours == [None]
