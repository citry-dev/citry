"""
A pytest plugin that records every Vue page the test suite prepares.

The parity check (`check.py` beside this file) needs real inputs: the
compiled render functions a page uses and the manifest the browser receives
with them. The test suite already builds hundreds of such pages, so this
plugin listens while it runs instead of keeping a second, hand-written list
of templates.

Load it with `-p scripts.vue_render_parity.collect` and name an output
directory with `--vue-render-parity-corpus=DIR`. Without that option the
plugin does nothing. Each pytest process (each xdist worker too) writes its
own `corpus-<worker>.jsonl`, one page per line, skipping pages it has
already written. `scripts/check.py` loads it in its main pytest phase.

A recorded page holds exactly what the server's hydration renderer reads:
the manifest JSON, the component tag for each type key, and every compiled
definition the manifest names (its browser JavaScript, and the render code
the Rust program is read from).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any

import pytest

_OPTION = "--vue-render-parity-corpus"

# The compiled definition's browser JavaScript wraps the render code between
# the helper preamble and this registration line (see `_vue/compiler.py`).
_CODE_START = "\nfunction render("
_CODE_END = "\nwindow.__citryRuntimeDefinitions="


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        _OPTION,
        default=None,
        help="Record every prepared Vue page into this directory for the Vue render parity check.",
    )


@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    corpus = session.config.getoption(_OPTION)
    if corpus is None:
        return
    # pytest-cov starts measuring in its own `pytest_sessionstart` (in each
    # xdist worker too). Importing Citry any earlier would run its module
    # bodies unmeasured and lower the coverage total, so the recorder is
    # created here, after that hook.
    recorder = _Recorder(Path(corpus))
    recorder.install()
    _ACTIVE.append(recorder)
    session.config.add_cleanup(recorder.uninstall)
    session.config.add_cleanup(_ACTIVE.clear)


def render_code(javascript: str) -> str | None:
    """Return the `function render(...)` source inside a definition's browser JavaScript."""
    start = javascript.find(_CODE_START)
    end = javascript.rfind(_CODE_END)
    if start < 0 or end < start:
        return None
    return javascript[start + 1 : end]


class _Recorder:
    """Wraps two private serialization helpers to see each prepared page once."""

    def __init__(self, directory: Path) -> None:
        # Imported here, not at the top, for the coverage reason given in
        # `pytest_sessionstart`.
        from citry._vue import serialization  # noqa: PLC0415

        self.serialization = serialization
        directory.mkdir(parents=True, exist_ok=True)
        worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
        self.path = directory / f"corpus-{worker}.jsonl"
        self.seen: set[str] = set()
        # `prepare_vue_serialization` passes the compiled definitions it built
        # before delivery (`early_selected_tree`) to `_prepare_initial_result`,
        # and the tags come out of `_component_tags_for_manifest` a few lines
        # later; a per-thread slot holds the tree until the second call.
        self.pending = threading.local()
        self.original_prepare = serialization._prepare_initial_result
        self.original_tags = serialization._component_tags_for_manifest
        self.test_id = ""

    def install(self) -> None:
        recorder = self

        def prepare(*args: Any, **kwargs: Any) -> Any:
            recorder.pending.tree = kwargs.get("early_selected_tree")
            return recorder.original_prepare(*args, **kwargs)

        def tags(producer: Any, manifest: dict[str, Any], cached_tags: dict[str, str] | None) -> dict[str, str]:
            result = recorder.original_tags(producer, manifest, cached_tags)
            tree = getattr(recorder.pending, "tree", None)
            recorder.pending.tree = None
            recorder.record(manifest, result, tree)
            return result

        self.serialization._prepare_initial_result = prepare
        self.serialization._component_tags_for_manifest = tags

    def uninstall(self) -> None:
        self.serialization._prepare_initial_result = self.original_prepare
        self.serialization._component_tags_for_manifest = self.original_tags

    def record(self, manifest: dict[str, Any], tags: dict[str, str], tree: Any) -> None:
        # Some unit tests pass hand-made manifest fragments through the tag
        # helper; only a manifest with a root is a page the server renders.
        if "rootId" not in manifest:
            return
        # The same JSON the page embeds and the hydration renderer reads.
        manifest_json = self.serialization._script_json(manifest)
        compiled = getattr(tree, "compiled_by_definition", None) or {}
        by_id = {item.id: item for item in compiled.values()}
        definitions: dict[str, dict[str, Any]] = {}
        missing = []
        for occurrence in manifest.get("occurrences", ()):
            definition_id = occurrence.get("definitionId")
            if definition_id in definitions:
                continue
            item = by_id.get(definition_id)
            if item is None:
                missing.append(definition_id)
                continue
            definitions[definition_id] = {
                "javascript": item.javascript,
                "code": render_code(item.javascript),
                # The Rust reader maps `<component :is>` aliases to real tags.
                "dynamicElements": json.dumps(list(item.dynamic_elements), separators=(",", ":")),
            }
        page = {
            "manifest": manifest_json,
            "tags": dict(sorted(tags.items())),
            "definitions": definitions,
            "missingDefinitions": sorted(set(missing)),
        }
        # Many tests render the same page; one copy is enough to compare.
        digest = hashlib.sha256(json.dumps(page, sort_keys=True).encode()).hexdigest()
        if digest in self.seen:
            return
        self.seen.add(digest)
        page["digest"] = digest
        page["test"] = self.test_id
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(page) + "\n")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    # Name the first test that produced each page, so a mismatch can be
    # reproduced by running that one test.
    if _ACTIVE:
        _ACTIVE[0].test_id = item.nodeid


# The recorder of this process, when the option is given.
_ACTIVE: list[_Recorder] = []
