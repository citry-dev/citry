"""Run the behavioral checks for the executable Events migration snippets."""

from __future__ import annotations

from types import SimpleNamespace

from citry.ext.events import EventError, actions
from docs_site.snippets import migrate_component_view as component_view
from docs_site.snippets import migrate_livecomponents as livecomponents
from docs_site.snippets import migrate_tetra as tetra
from docs_site.snippets import migrate_unicorn as unicorn


def _events_info(comp_cls):
    extension = comp_cls.citry.extensions.get_extension("events")
    return extension.resolve(comp_cls)


def _verify_component_view() -> None:
    rendered = str(component_view.ContactForm())
    assert f"/citry/ext/events/e/{component_view.ContactForm.class_id}" in rendered

    verb_cls = _events_info(component_view.ContactForm).events_cls
    action = verb_cls.post(object(), SimpleNamespace(name="Ada"))
    assert isinstance(action, actions.Render)
    assert action.target == "#result"
    assert "Thank you, Ada!" in str(action.element)

    named = str(component_view.NamedContactForm())
    assert f"/citry/ext/events/e/{component_view.NamedContactForm.class_id}/submit" in named
    assert '@c-submit.prevent="submit"' not in named
    assert "data-cev-on" in named

    loader_info = _events_info(component_view.FragmentLoader)
    assert loader_info.handlers["preview"].methods == ("GET",)
    assert loader_info.handlers["details"].methods == ("GET",)


def _verify_unicorn() -> None:
    state = unicorn.LiveSearch.State(query="shoe")
    result = _events_info(unicorn.LiveSearch).events_cls().refresh(state)
    assert "shoe shoes" in str(result)

    rating = _events_info(unicorn.Rating).events_cls().rate(SimpleNamespace(stars=5))
    assert ">5</output>" in str(rating)

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
    rendered, data = info.events_cls().increment(SimpleNamespace(amount=2), state)
    assert "Count: 3" in str(rendered)
    assert data == actions.Data({"count": 3})

    assert 'id="task-summary"' in str(tetra.TaskEditor())
    result = _events_info(tetra.TaskEditor).events_cls().complete(SimpleNamespace(task_id=42))
    assert [type(item) for item in result] == [actions.Dispatch, actions.Render]
    assert result[0].name == "TaskEditor:completed"
    assert result[1].target == "#task-summary"
    assert 'id="task-summary"' in str(result[1].element)
    next_result = _events_info(tetra.TaskEditor).events_cls().complete(SimpleNamespace(task_id=42))
    assert next_result[1].target == result[1].target
    assert 'id="task-summary"' in str(next_result[1].element)


def _verify_livecomponents() -> None:
    server_info = _events_info(livecomponents.ServerCounter)
    signed_info = _events_info(livecomponents.SignedCounter)
    assert server_info.state_meta.storage == "server"
    assert server_info.state_meta.public == ("count",)
    assert signed_info.state_meta.storage == "signed"

    assert "data-citry-events" in str(livecomponents.ServerCounter())
    assert "data-citry-events" in str(livecomponents.SignedCounter())

    state = livecomponents.ServerCounter.State(count=4)
    result = server_info.events_cls().increment(state)
    assert "Count: 5" in str(result)

    assert 'id="task-summary"' in str(livecomponents.TaskEditor())
    actions_result = _events_info(livecomponents.TaskEditor).events_cls().save(SimpleNamespace(task_id=42))
    assert [type(item) for item in actions_result] == [actions.Render, actions.Dispatch]
    assert actions_result[0].target == "#task-summary"
    assert 'id="task-summary"' in str(actions_result[0].element)
    assert actions_result[1].name == "TaskEditor:saved"
    next_result = _events_info(livecomponents.TaskEditor).events_cls().save(SimpleNamespace(task_id=42))
    assert next_result[0].target == actions_result[0].target
    assert 'id="task-summary"' in str(next_result[0].element)


def main() -> None:
    """Execute every snippet contract in an isolated Python process."""
    _verify_component_view()
    _verify_unicorn()
    _verify_tetra()
    _verify_livecomponents()


if __name__ == "__main__":
    main()
