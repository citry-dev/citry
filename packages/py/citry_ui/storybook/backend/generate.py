"""Generate disposable Server and HTML stories from the Python catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from backend.catalog import CATALOG_SCHEMA_VERSION, SCENARIOS, StorybookScenario

_ROOT = Path(__file__).resolve().parents[1]
_GENERATED = _ROOT / "generated"
_GENERATOR_VERSION = 1


def _filename(scenario: StorybookScenario) -> str:
    return scenario.id.replace("/", "--")


def _title(scenario: StorybookScenario) -> str:
    return f"Citry UI/{scenario.group}/{scenario.title}"


def _parameters(scenario: StorybookScenario) -> dict[str, object]:
    citry_parameters: dict[str, object] = {
        "catalogSchemaVersion": CATALOG_SCHEMA_VERSION,
        "clientInteractive": scenario.client_interactive,
        "generatorVersion": _GENERATOR_VERSION,
        "scenarioId": scenario.id,
        "sourceDigest": _source_digest(scenario),
    }
    if scenario.ready_selector is not None:
        citry_parameters["readySelector"] = scenario.ready_selector
        citry_parameters["readyTimeoutMs"] = scenario.ready_timeout_ms
    return {
        "citry": citry_parameters,
        "docs": {
            "description": {
                "component": scenario.description,
            },
            "source": {
                "code": scenario.usage,
                "language": "python",
            },
        },
    }


def _source_digest(scenario: StorybookScenario) -> str:
    source = {
        "args": scenario.args,
        "argTypes": scenario.arg_types,
        "clientInteractive": scenario.client_interactive,
        "description": scenario.description,
        "group": scenario.group,
        "id": scenario.id,
        "readySelector": scenario.ready_selector,
        "readyTimeoutMs": scenario.ready_timeout_ms,
        "title": scenario.title,
        "usage": scenario.usage,
    }
    encoded = json.dumps(source, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _projection(scenario: StorybookScenario) -> dict[str, object]:
    return {
        "title": _title(scenario),
        "storyName": "Preview",
        "scenarioId": scenario.id,
        "args": scenario.args,
        "argTypes": scenario.arg_types,
        "parameters": _parameters(scenario),
        "tags": ["autodocs"],
    }


def _server_story(scenario: StorybookScenario) -> str:
    projection = _projection(scenario)
    value = {
        "title": projection["title"],
        "argTypes": projection["argTypes"],
        "parameters": projection["parameters"],
        "tags": projection["tags"],
        "stories": [
            {
                "name": projection["storyName"],
                "args": projection["args"],
                "parameters": {
                    "server": {
                        "id": projection["scenarioId"],
                    },
                },
            },
        ],
    }
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _html_story(scenario: StorybookScenario) -> str:
    projection = _projection(scenario)
    title = json.dumps(projection["title"], ensure_ascii=False)
    story_name = json.dumps(projection["storyName"], ensure_ascii=False)
    args = json.dumps(projection["args"], indent=2, ensure_ascii=False)
    arg_types = json.dumps(projection["argTypes"], indent=2, ensure_ascii=False)
    parameters = json.dumps(projection["parameters"], indent=2, ensure_ascii=False)
    tags = json.dumps(projection["tags"], ensure_ascii=False)
    return f"""import {{
  loadCitryScenario,
  renderCitryScenario,
}} from "../../src/html-adapter.js";

const meta = {{
  title: {title},
  argTypes: {arg_types},
  parameters: {parameters},
  tags: {tags},
}};

export default meta;

export const Preview = {{
  name: {story_name},
  args: {args},
  loaders: [loadCitryScenario],
  render: renderCitryScenario,
}};
"""


def generated_outputs() -> dict[Path, str]:
    """Return every deterministic generated path and its expected content."""
    outputs: dict[Path, str] = {}
    for scenario in SCENARIOS:
        stem = _filename(scenario)
        outputs[_GENERATED / "server" / f"{stem}.stories.json"] = _server_story(scenario)
        outputs[_GENERATED / "html" / f"{stem}.stories.js"] = _html_story(scenario)
    return outputs


def write_outputs(*, check: bool) -> bool:
    """Write projections, or return whether committed projections are current."""
    outputs = generated_outputs()
    expected_paths = set(outputs)
    existing_paths = {
        *(_GENERATED / "server").glob("*.stories.json"),
        *(_GENERATED / "html").glob("*.stories.js"),
    }
    stale_paths = existing_paths - expected_paths
    changed_paths = {path for path, content in outputs.items() if not path.exists() or path.read_text() != content}
    if check:
        return not stale_paths and not changed_paths

    for path in sorted(stale_paths):
        path.unlink()
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated stories are stale.")
    args = parser.parse_args()
    current = write_outputs(check=args.check)
    if not current:
        sys.stderr.write("Generated Storybook projections are stale. Run the generator.\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
