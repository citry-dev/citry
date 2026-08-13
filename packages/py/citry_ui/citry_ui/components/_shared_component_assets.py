"""Private helpers for sharing one component runtime and style asset."""

from __future__ import annotations

from dataclasses import dataclass

from citry.ext.dependencies import Script, Style


@dataclass(frozen=True, slots=True)
class SharedComponentAssets:
    """Hold one shared runtime dependency and its class-bound adapter."""

    runtime: Script
    style: Style
    component_js: str


def build_shared_component_assets(
    *,
    component_name: str,
    runtime_key: str,
    generation: int,
    component_source: str,
    style_source: str,
) -> SharedComponentAssets:
    """Extract one ``$component`` definition into a deduplicated dependency."""
    marker = "$component("
    marker_index = component_source.find(marker)
    if marker_index < 0:
        msg = f"{component_name} shared runtime source must contain one $component call."
        raise ValueError(msg)
    if component_source.find(marker, marker_index + len(marker)) >= 0:
        msg = f"{component_name} shared runtime source must contain exactly one $component call."
        raise ValueError(msg)

    source_without_trailing_space = component_source.rstrip()
    if not source_without_trailing_space.endswith(");"):
        msg = f"{component_name} shared runtime source must end with its $component call."
        raise ValueError(msg)

    prelude = component_source[:marker_index]
    definition = source_without_trailing_space[marker_index + len(marker) : -2]
    runtime_source = (
        prelude
        + f"""\n      (() => {{
        const runtimeKey = Symbol.for({runtime_key!r});
        const installed = globalThis[runtimeKey];
        if (installed !== undefined) {{
          if (installed.generation !== {generation}) {{
            throw new Error(
              "[citry-ui] cannot replace an incompatible {component_name} runtime; "
                + "a full page reload is required.",
            );
          }}
          return;
        }}
        const definition = {definition};
        globalThis[runtimeKey] = {{
          generation: {generation},
          definition,
          mount: definition.init,
          helpers: definition.helpers ?? {{}},
        }};
      }})();
"""
    )
    component_js = f"""
      const runtime = globalThis[Symbol.for({runtime_key!r})];
      if (runtime?.generation !== {generation}) {{
        throw new Error("[citry-ui] {component_name} runtime dependency did not load.");
      }}
      $component(runtime.definition);
    """
    return SharedComponentAssets(
        runtime=Script(content=runtime_source),
        style=Style(content=style_source),
        component_js=component_js,
    )


__all__: list[str] = []
