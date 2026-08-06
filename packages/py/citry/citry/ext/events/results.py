"""
The return channel of the ``events`` extension: from a handler's return value
to the wire actions of the result envelope.

Two steps, in dispatch order (design ``docs/design/events.md`` 3.4, 4.3, 6.2):

- :func:`extract_download_result` recognizes the response-level download
  shape before resolvers or recursive action coercion can change its meaning.
- :func:`coerce_result` turns every ordinary handler return into a list of
  action values (the ``actions`` module's constructors). The built-in
  conversions run first (``None`` acknowledges, an element renders, a dict is
  data, a list is ordered actions), then the engine's result resolvers
  (``CitrySettings.event_result_resolvers``) get a chance to claim the value,
  and anything still unclaimed is a pointed error. Built-ins running first
  means a resolver can teach the channel new types but never change what a
  dict or an element means.
- :func:`encode_actions` turns those action values into the JSON-ready wire
  shapes, in the exact order returned: a render action renders its element
  and serializes it as a fragment (whose manifests carry the fresh state),
  targets serialize as CSS selectors or the ``render:<render id>`` form, and
  the timing fields ride along when set. Two ``data`` actions in one result
  are an encode-time error; actions trailing a redirect (and a render
  coexisting with one) are debug-logged but never reordered or dropped.

The module also owns the debug-mode tracking of constructed-but-unreturned
return values: :func:`track_constructed_actions` records every action or
download constructed while a handler runs on the per-call events instance,
and :func:`warn_unreturned_actions` names the ones the handler dropped. "Debug
mode" here means the ``"citry"`` logger has DEBUG enabled (the engine has no
separate debug flag), so production calls pay nothing for the tracking.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from citry._protocol.events import (
    build_data_action,
    build_event_action,
    build_redirect_action,
    build_render_action,
    build_url_action,
)
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender
from citry.ext.events.actions import (
    _CONSTRUCTED_ACTIONS,
    Action,
    Data,
    Dispatch,
    Download,
    PushUrl,
    Redirect,
    Render,
    ReplaceUrl,
)
from citry.util.logger import logger

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

# The attribute on the per-call events instance that holds the constructed
# actions while debug tracking is active.
_TRACKED_ATTR = "_constructed_actions"


################################################
# RETURN-VALUE COERCION
################################################


def coerce_result(
    value: Any,
    *,
    resolvers: Sequence[Any] = (),
    events: Any = None,
    handler: str,
) -> list[Action]:
    """
    Turn an event handler's return value into its list of actions.

    The rules, per returned item (design ``events.md`` 3.4): ``None``
    acknowledges (no actions); an action passes through; a component element
    or a ``CitryRender`` becomes a render of the calling instance; a ``dict``
    becomes a data action; a ``list`` / ``tuple`` coerces each element by
    these same rules, in order. Anything else is offered to the result
    resolvers in order (the first to return actions wins), and if none
    claims it, raises the pointed error naming ``actions.Data(...)`` as the
    wrap and result resolvers as the way to teach the channel the type.

    Args:
        value: The handler's return value.
        resolvers: The engine's result resolvers
            (``CitrySettings.event_result_resolvers``); each is asked as
            ``resolver.resolve(value, events)`` and answers a list of actions
            or ``None`` to decline.
        events: The per-call events instance, passed through to resolvers.
        handler: The handler's wire name, for error messages.

    Returns:
        The actions, in return order. Empty means acknowledged.

    Raises:
        ValueError: When a value cannot become an action, or a resolver
            answers something other than a list of actions or ``None``.

    """
    if value is None:
        return []
    if isinstance(value, Action):
        return [value]
    if isinstance(value, (CitryElement, CitryRender)):
        return [Render(value)]
    if isinstance(value, dict):
        return [Data(value)]
    if isinstance(value, (list, tuple)):
        coerced: list[Action] = []
        for item in value:
            coerced.extend(coerce_result(item, resolvers=resolvers, events=events, handler=handler))
        return coerced

    for resolver in resolvers:
        resolved = resolver.resolve(value, events)
        if resolved is None:
            continue
        if not isinstance(resolved, (list, tuple)) or not all(isinstance(item, Action) for item in resolved):
            msg = (
                f"Result resolver {type(resolver).__name__} answered {resolved!r} for event handler"
                f" {handler!r}; a resolver answers a list of actions (e.g. [actions.Data(...)]),"
                f" or None to decline."
            )
            raise ValueError(msg)
        return list(resolved)

    if isinstance(value, str):
        msg = (
            f"Event handler {handler!r} returned a string; a bare string is never guessed (is it"
            f" HTML or JSON?). Return actions.Data(...) to answer the caller with a JSON value;"
            f" HTML comes from rendering a component (return the element, or actions.Render(element))."
        )
        # ValueError, not TypeError: one exception type for the whole
        # return-channel error matrix.
        raise ValueError(msg)  # noqa: TRY004
    msg = (
        f"Event handler {handler!r} returned {type(value).__name__!r}, which cannot become an"
        f" action. Return None, an action (actions.Data(...), actions.Render(...),"
        f" actions.Dispatch(...), actions.Redirect(...), actions.PushUrl(...),"
        f" actions.ReplaceUrl(...)), a component element, a dict, or a list"
        f" of these; wrap the value in actions.Data(...), or register a result resolver for"
        f" {type(value).__name__} (CitrySettings.event_result_resolvers) to return it bare."
    )
    raise ValueError(msg)


def extract_download_result(value: Any, *, handler: str) -> Download | None:
    """
    Extract the one response-level download shape before action coercion.

    A download is valid bare or as the only literal top-level list or tuple
    item. It cannot be combined with envelope actions, nested in another
    collection, or supplied by a result resolver.
    """
    if isinstance(value, Download):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 1 and isinstance(value[0], Download):
        return value[0]
    if _contains_download(value):
        msg = (
            f"Event handler {handler!r} returned actions.Download with other values, or nested it"
            " inside another collection. A download bypasses the result envelope, so return it"
            " bare or as the only top-level list or tuple item."
        )
        raise ValueError(msg)
    return None


def _contains_download(value: Any) -> bool:
    """Whether nested list, tuple, or dictionary values contain a download result."""
    if isinstance(value, Download):
        return True
    if isinstance(value, (list, tuple)):
        return any(_contains_download(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_download(item) for item in value.values())
    return False


################################################
# WIRE ENCODING
################################################


def encode_actions(
    actions: Sequence[Action],
    *,
    instance_id: str | None,
    handler: str,
) -> list[dict[str, Any]]:
    """
    Encode a handler's actions into the wire shapes of the result envelope.

    Order is faithful: the encoded list is the given list, never reordered,
    never filtered (design ``events.md`` 4.3). A render action renders its
    element here and serializes it with ``deps_strategy="fragment"``, so the
    HTML carries its own dependency and events manifests (fresh state tokens
    included). A render or dispatch without an explicit target is
    self-addressed to the calling instance as ``render:<render id>``.

    Args:
        actions: The coerced actions, in return order.
        instance_id: The calling instance's id (the call envelope's
            ``callerRenderId``), or ``None`` for an instance-less call. With
            ``None``, a dispatch targets ``document`` (no ``target`` field)
            and a render must carry an explicit ``target``.
        handler: The handler's wire name, for errors and debug warnings.

    Returns:
        One JSON-ready object per action, in order.

    Raises:
        ValueError: When the result holds two data actions (which promise
            value would win?), a render has neither a target nor a calling
            instance, or an action is not one of the v1 kinds.

    """
    data_count = sum(isinstance(action, Data) for action in actions)
    if data_count > 1:
        msg = (
            f"Event handler {handler!r} returned {data_count} 'data' actions in one result; at"
            f" most one is allowed (each call resolves one client promise, so which value would"
            f" win?). Merge them into a single actions.Data(...)."
        )
        raise ValueError(msg)

    # The unreliable-but-legal shapes get a debug note and nothing else:
    # actions are never reordered or dropped (design events.md 4.3).
    redirect_at = next((i for i, action in enumerate(actions) if isinstance(action, Redirect)), None)
    if redirect_at is not None and redirect_at < len(actions) - 1:
        logger.debug(
            f"Event handler {handler!r} returned {len(actions) - 1 - redirect_at} action(s) after"
            f" a redirect; they race the navigation and may never apply. Actions are never"
            f" reordered or dropped, so move them before the redirect if they must apply."
        )
    if redirect_at is not None and any(isinstance(action, Render) for action in actions):
        logger.debug(
            f"Event handler {handler!r} returned a render together with a redirect; the browser"
            f" navigates away, so the rendered content is never seen."
        )

    selector_render_at = next(
        (
            i
            for i, action in enumerate(actions)
            if isinstance(action, Render) and action.target is not None and not action.target.startswith("render:")
        ),
        None,
    )
    if selector_render_at is not None and instance_id is not None:
        later_self_addressed = sum(
            isinstance(action, Dispatch) or (isinstance(action, Render) and action.target is None)
            for action in actions[selector_render_at + 1 :]
        )
        if later_self_addressed:
            logger.debug(
                f"Event handler {handler!r} returned {later_self_addressed} self-addressed action(s) after"
                f" a selector-targeted render; that render can retire or replace the calling instance"
                f" before the later action resolves its render target. Reorder the actions or target the"
                f" later action explicitly if it must address the rendered region."
            )

    return [_encode_action(action, instance_id=instance_id, handler=handler) for action in actions]


def _encode_action(action: Action, *, instance_id: str | None, handler: str) -> dict[str, Any]:
    """One action's wire object, field order matching the design's envelope examples."""
    encoded: dict[str, Any]
    if isinstance(action, Render):
        if action.target is not None:
            target = action.target
        elif instance_id is not None:
            target = f"render:{instance_id}"
        else:
            msg = (
                f"actions.Render from event handler {handler!r} has no target: the call carries no"
                f" component instance to default to. Pass target=... (a CSS selector string)."
            )
            raise ValueError(msg)
        rendered = action.element.render() if isinstance(action.element, CitryElement) else action.element
        encoded = build_render_action(
            target,
            action.swap,
            rendered.serialize(deps_strategy="fragment"),
            delay=action.delay,
            wait=action.wait,
        )
    elif isinstance(action, Data):
        encoded = build_data_action(action.value, delay=action.delay)
    elif isinstance(action, Dispatch):
        # Self-addressed at encode time; an instance-less call dispatches on
        # document, which the wire spells as "no target" (design events.md 4.3).
        encoded = build_event_action(
            action.name,
            detail=action.detail,
            include_detail=action.detail is not None,
            target=f"render:{instance_id}" if instance_id is not None else None,
            delay=action.delay,
            wait=action.wait,
        )
    elif isinstance(action, Redirect):
        encoded = build_redirect_action(action.url, delay=action.delay, wait=action.wait)
    elif isinstance(action, PushUrl):
        encoded = build_url_action(action.url, "push", delay=action.delay, wait=action.wait)
    elif isinstance(action, ReplaceUrl):
        encoded = build_url_action(action.url, "replace", delay=action.delay, wait=action.wait)
    else:
        msg = (
            f"Cannot encode {type(action).__name__} from event handler {handler!r}: the action"
            f" set is closed (render, data, event, redirect, url). Custom client behavior goes through"
            f" actions.Dispatch(...) and a listener on the page."
        )
        # ValueError, not TypeError: one exception type for the whole
        # return-channel error matrix.
        raise ValueError(msg)  # noqa: TRY004

    return encoded


################################################
# DEBUG TRACKING OF CONSTRUCTED ACTIONS
################################################


@contextmanager
def track_constructed_actions(events: Any) -> Iterator[None]:
    """
    Record every action or download constructed inside the block, in debug mode.

    A constructed action does nothing by itself; it must be returned. This
    context manager (wrapped around the handler call and the coercion of its
    return value) registers each constructed action on the per-call events
    instance, so :func:`warn_unreturned_actions` can name the ones the
    handler dropped. Active only when the ``"citry"`` logger has DEBUG
    enabled; otherwise the block runs untouched and nothing is recorded.

    Args:
        events: The per-call events instance the constructed actions are
            recorded on; ``None`` disables tracking (nothing to record on).

    """
    if events is None or not logger.isEnabledFor(logging.DEBUG):
        yield
        return
    constructed: list[Any] = []
    setattr(events, _TRACKED_ATTR, constructed)
    token = _CONSTRUCTED_ACTIONS.set(constructed)
    try:
        yield
    finally:
        _CONSTRUCTED_ACTIONS.reset(token)


def warn_unreturned_actions(events: Any, returned: Sequence[Any], handler: str) -> None:
    """
    Log a warning for return values constructed during the call but never returned.

    Compares (by identity) what :func:`track_constructed_actions` recorded on
    the per-call events instance against the actions the handler's return
    value coerced to. Does nothing when tracking was inactive or every
    constructed action was returned.

    Args:
        events: The per-call events instance the call was tracked on.
        returned: The coerced actions of the handler's return value.
        handler: The handler's wire name, named in the warning.

    """
    constructed: list[Any] | None = getattr(events, _TRACKED_ATTR, None) if events is not None else None
    if not constructed:
        return
    unreturned = [action for action in constructed if not any(action is kept for kept in returned)]
    if not unreturned:
        return
    names = ", ".join(type(action).__name__ for action in unreturned)
    logger.warning(
        f"Event handler {handler!r} constructed {len(unreturned)} return value(s) that were never"
        f" returned: {names}. Construction does nothing by itself; return the value for it to"
        f" apply."
    )
