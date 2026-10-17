from __future__ import annotations

from citry._vue.capture import _normalize_control_bindings, _normalize_event_bindings


def test_prepared_event_accepts_combined_debounce_and_throttle() -> None:
    [binding] = _normalize_event_bindings(
        (
            {
                "id": "citryEvent01",
                "event": "click",
                "handler": "save",
                "args": None,
                "prevent": False,
                "stop": False,
                "self": False,
                "once": False,
                "key": None,
                "debounce": 20,
                "throttle": 50,
            },
        )
    )
    assert (binding["debounce"], binding["throttle"]) == (20, 50)


def test_prepared_control_accepts_combined_debounce_and_throttle() -> None:
    [binding] = _normalize_control_bindings(
        (
            {
                "id": "citryControl01",
                "field": "query",
                "binding_mode": "two-way",
                "handler": "search",
                "lazy": False,
                "on": None,
                "key": None,
                "debounce": 50,
                "throttle": 20,
            },
        )
    )
    assert (binding["debounce"], binding["throttle"]) == (50, 20)
