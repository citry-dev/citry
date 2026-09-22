"""Run the behavioral checks for the executable Events migration snippets."""

from __future__ import annotations

import json
from types import SimpleNamespace

from citry.ext.events import EventError, actions
from citry.ext.events.results import coerce_result
from docs_site.snippets import migrate_component_view as component_view
from docs_site.snippets import migrate_livecomponents as livecomponents
from docs_site.snippets import migrate_tetra as tetra
from docs_site.snippets import migrate_unicorn as unicorn


def _events_info(comp_cls):
    extension = comp_cls.citry.extensions.get_extension("events")
    return extension.resolve(comp_cls)


def _serialized_html(element):
    return element.render().serialize(deps_strategy="simple")


def _marker_names(component):
    return [marker["name"] for marker in _prepared_manifest(component)["markers"]]


def _event_context(component):
    [occurrence] = _prepared_manifest(component)["occurrences"]
    return occurrence["eventContext"]


def _prepared_manifest(component):
    source = component.render().serialize()
    prefix = "CitryStable.startPrepared("
    start = source.index(prefix) + len(prefix)
    prepared, _consumed = json.JSONDecoder().raw_decode(source[start:])
    return prepared["manifest"]


def _verify_component_view() -> None:
    rendered = _serialized_html(component_view.ContactForm())
    assert f"/citry/ext/events/e/{component_view.ContactForm.class_id}" in rendered
    assert '<form method="post"' in rendered
    assert "CitryStable.startPrepared" not in rendered

    verb_cls = _events_info(component_view.ContactForm).events_cls
    [action] = coerce_result(verb_cls.post(object(), SimpleNamespace(name="Ada")), handler="post")
    assert isinstance(action, actions.Render)
    assert action.target is None
    assert action.swap == "morph"
    assert "Thank you, Ada!" in _serialized_html(action.element)

    named = component_view.NamedContactForm().render().serialize()
    assert f"/citry/ext/events/e/{component_view.NamedContactForm.class_id}/submit" in named
    assert "CitryStable.startPrepared" in named
    assert _marker_names(component_view.NamedContactForm()) == ["result"]

    named_action = _events_info(component_view.NamedContactForm).events_cls.submit(
        object(), SimpleNamespace(name="Ada")
    )
    assert isinstance(named_action, actions.Render)
    assert named_action.target == "mark:result"
    assert named_action.swap == "morph"
    assert "Thank you, Ada!" in _serialized_html(named_action.element)

    loader_info = _events_info(component_view.FragmentLoader)
    assert loader_info.handlers["preview"].methods == ("GET",)
    assert loader_info.handlers["details"].methods == ("GET",)
    assert _marker_names(component_view.FragmentLoader()) == ["fragment-target"]
    for name in ("preview", "details"):
        action = getattr(loader_info.events_cls(), name)()
        assert isinstance(action, actions.Render)
        assert action.target == "mark:fragment-target"
        assert action.swap == "morph"
        assert f"Loaded {name}" in _serialized_html(action.element)


def _verify_unicorn() -> None:
    state = unicorn.LiveSearch.State(query="shoe")
    result = _events_info(unicorn.LiveSearch).events_cls().refresh(state)
    assert "shoe shoes" in _serialized_html(result)

    rating = _events_info(unicorn.Rating).events_cls().rate(SimpleNamespace(stars=5))
    assert ">5</output>" in _serialized_html(rating)

    submit = _events_info(unicorn.ContactForm).events_cls().submit
    caught_error = None
    try:
        submit(SimpleNamespace(email="invalid"))
    except EventError as error:
        caught_error = error
    assert caught_error is not None
    assert caught_error.fields == {"email": "Enter a valid email address."}

    dispatch = _events_info(unicorn.Preferences).events_cls().save()
    assert dispatch == actions.Dispatch(
        "Preferences:saved",
        {"message": "Preferences saved"},
    )


def _verify_tetra() -> None:
    info = _events_info(tetra.Counter)
    assert info.handlers["increment"].debounce == 200

    state = tetra.Counter.State(count=1)
    element, data = info.events_cls().increment(SimpleNamespace(amount=2), state)
    assert "Count: 3" in _serialized_html(element)
    assert data == actions.Data({"count": 3})

    initial_html = _serialized_html(tetra.TaskEditor())
    assert "Task 42: pending" in initial_html
    result = _events_info(tetra.TaskEditor).events_cls().complete(SimpleNamespace(task_id=42))
    assert [type(item) for item in result] == [actions.Dispatch, actions.Render]
    assert result[0].name == "TaskEditor:completed"
    assert result[1].target is None
    completed_html = _serialized_html(result[1].element)
    assert "Task 42: complete" in completed_html
    assert "Task 42: pending" not in completed_html
    next_result = _events_info(tetra.TaskEditor).events_cls().complete(SimpleNamespace(task_id=42))
    assert next_result[1].target == result[1].target
    assert "Task 42: complete" in _serialized_html(next_result[1].element)


def _verify_livecomponents() -> None:
    server_info = _events_info(livecomponents.ServerCounter)
    signed_info = _events_info(livecomponents.SignedCounter)
    assert server_info.state_meta.storage == "server"
    assert server_info.state_meta.public == ("count",)
    assert signed_info.state_meta.storage == "signed"

    server_context = _event_context(livecomponents.ServerCounter())
    signed_context = _event_context(livecomponents.SignedCounter())
    assert server_context["stateToken"].startswith("ces1.")
    assert signed_context["stateToken"].startswith("cev1.")

    state = livecomponents.ServerCounter.State(count=4)
    result = server_info.events_cls().increment(state)
    assert "Count: 5" in _serialized_html(result)

    initial_html = _serialized_html(livecomponents.TaskEditor())
    assert 'id="task-summary"' in initial_html
    assert "Task 42 not saved" in initial_html
    assert _marker_names(livecomponents.TaskEditor()) == ["task-summary"]
    actions_result = _events_info(livecomponents.TaskEditor).events_cls().save(SimpleNamespace(task_id=42))
    assert [type(item) for item in actions_result] == [actions.Render, actions.Dispatch]
    assert actions_result[0].target == "mark:task-summary"
    assert actions_result[0].swap == "morph"
    summary_html = _serialized_html(actions_result[0].element)
    assert 'id="task-summary"' in summary_html
    assert "Task 42 saved" in summary_html
    assert actions_result[1].name == "TaskEditor:saved"
    assert actions_result[1].detail == {"taskId": 42}
    next_result = _events_info(livecomponents.TaskEditor).events_cls().save(SimpleNamespace(task_id=42))
    assert next_result[0].target == actions_result[0].target
    assert "Task 42 saved" in _serialized_html(next_result[0].element)
    assert next_result[1] == actions_result[1]


def main() -> None:
    """Execute every snippet contract in an isolated Python process."""
    _verify_component_view()
    _verify_unicorn()
    _verify_tetra()
    _verify_livecomponents()


if __name__ == "__main__":
    main()
