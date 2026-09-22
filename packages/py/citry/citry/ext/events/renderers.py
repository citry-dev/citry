"""Private per-engine selection of the Events Render encoding backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

from citry._protocol.events import RENDERERS, build_prepared_render_action
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender
from citry.ext.events.dispatcher import EventsDispatcher
from citry.ext.events.results import HTML_RENDER_ENCODER

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from citry.citry import Citry
    from citry.ext.events.actions import Render
    from citry.ext.events.results import RenderEncoder, RenderEncodingContext


@dataclass(slots=True)
class _RenderConfiguration:
    encoders: tuple[RenderEncoder, ...]
    preferred: str
    dispatcher: EventsDispatcher | None = None


@dataclass(frozen=True, slots=True)
class _VueMarkerTarget:
    """Private caller-relative marker metadata for one prepared render."""

    caller_render_id: str
    name: str


_CONFIGURATIONS: WeakKeyDictionary[Citry, _RenderConfiguration] = WeakKeyDictionary()


def uses_prepared_renderer(citry: Citry) -> bool:
    """Whether normal renders for this engine must retain direct Vue relationships."""
    config = _CONFIGURATIONS.get(citry)
    if config is None:
        return False
    return config.preferred == "vue-prepared/1"


class VuePreparedRenderEncoder:
    """Adapt one direct prepared producer to the generic Events render port."""

    renderer = "vue-prepared/1"

    def __init__(
        self,
        prepare: Callable[[CitryElement | CitryRender, RenderEncodingContext], Mapping[str, object]],
        prepare_marker: Callable[
            [CitryElement | CitryRender, RenderEncodingContext, _VueMarkerTarget], Mapping[str, object]
        ]
        | None = None,
    ) -> None:
        self._prepare = prepare
        self._prepare_marker = prepare_marker

    def encode(self, action: Render, target: str, context: RenderEncodingContext) -> dict[str, object]:
        if not isinstance(action.element, (CitryElement, CitryRender)):
            raise TypeError("vue-prepared/1 requires a CitryElement or a typed prepared CitryRender.")
        wire_target = target
        if target.startswith("mark:"):
            if context.caller_render_id is None:
                raise ValueError("a caller-relative marker target requires a calling component")
            if self._prepare_marker is None:
                raise ValueError("the selected prepared renderer does not support marker targets")
            marker = _VueMarkerTarget(context.caller_render_id, target[5:])
            prepared = self._prepare_marker(action.element, context, marker)
            wire_target = f"mark:{marker.caller_render_id}:{marker.name}"
        else:
            prepared = self._prepare(action.element, context)
        if type(prepared) is not dict:
            prepared = dict(prepared)
        return build_prepared_render_action(
            wire_target,
            action.swap,
            self.renderer,
            prepared,
            delay=action.delay,
            wait=action.wait,
        )


def configure_render_encoder(
    citry: Citry,
    encoder: RenderEncoder,
    *,
    preferred_renderer: str,
) -> None:
    """
    Configure one private renderer once, before the engine's routes are bound.

    Encoders receive the engine through ``RenderEncodingContext`` and must not
    retain it; keeping the weak-key registry collectible depends on that rule.
    """
    if preferred_renderer not in RENDERERS or encoder.renderer != preferred_renderer:
        raise ValueError("The configured preferred renderer must match a known encoder renderer.")
    current = _CONFIGURATIONS.get(citry)
    if current is not None:
        if current.dispatcher is not None:
            raise RuntimeError("Events render encoding must be configured before the engine's routes are bound.")
        raise RuntimeError("Events render encoding is already configured for this engine.")
    encoders = (encoder,) if encoder.renderer == HTML_RENDER_ENCODER.renderer else (encoder, HTML_RENDER_ENCODER)
    _CONFIGURATIONS[citry] = _RenderConfiguration(encoders, preferred_renderer)


def dispatcher_for(citry: Citry) -> EventsDispatcher:
    """Return the one route dispatcher frozen to this engine's configuration."""
    config = _CONFIGURATIONS.get(citry)
    if config is None:
        from citry._vue.events import default_events_producer  # noqa: PLC0415

        producer = default_events_producer(citry)
        vue = VuePreparedRenderEncoder(producer, producer.prepare_marker)
        config = _RenderConfiguration((vue, HTML_RENDER_ENCODER), vue.renderer)
        _CONFIGURATIONS[citry] = config
    if config.dispatcher is None:
        config.dispatcher = EventsDispatcher(
            render_encoders=config.encoders,
            preferred_renderer=config.preferred,
        )
    return config.dispatcher
