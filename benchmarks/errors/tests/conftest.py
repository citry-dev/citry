"""A small benchmark of one made-up framework, run end to end without installing anything or opening a browser."""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from citry_errors import cli, report, work
from citry_errors.config import load_catalogue, load_frameworks, load_ports
from citry_errors.runtime import Observation

if TYPE_CHECKING:
    from pathlib import Path

    from citry_errors.config import Framework

# The check stage fails, naming the file, when the app text holds BAD. It
# sleeps a random moment first, so cases run on several workers finish in a
# different order from the one they started in. It also leaves a file in the
# working copy, as a build does, which the browser check must not see.
_CHECK = (
    "import random, sys, time\n"
    "time.sleep(random.random() * 0.05)\n"
    "open('tool-output.txt', 'w').write('built')\n"
    "text = open('app.txt').read()\n"
    "if 'BAD' in text:\n"
    "    print('app.txt: BAD found'); sys.exit(1)\n"
)

# The editor stage warns, at the changed line, when the app text holds MEH.
# Its braces are doubled in the definition, because the runner fills in
# placeholders such as {work} in every argument.
_WARN = (
    "import json\n"
    "text = open('app.txt').read()\n"
    "messages = [{'line': 1, 'severity': 1, 'ruleId': 'meh', 'message': 'meh'}] if 'MEH' in text else []\n"
    "print(json.dumps([{'filePath': 'app.txt', 'messages': messages}]))\n"
)

FRAMEWORK = f"""\
key = "toy"
name = "Toy"

[setup]
manifests = ["app.txt"]
command = ["true"]

[[stages]]
stage = "editor"
label = "toy editor"
argv = [{json.dumps(sys.executable)}, "-c", {json.dumps(_WARN.replace("{", "{{").replace("}", "}}"))}]
parser = "eslint-json"

[[stages]]
stage = "check"
label = "toy check"
argv = [{json.dumps(sys.executable)}, "-c", {json.dumps(_CHECK)}]
parser = "exit"

[runtime]
argv = ["unused: the tests replace the browser check"]
page_path = "/"

[[runtime.journeys.default]]
action = "click"
selector = "button"
"""

# Each mistake's new text: BAD is reported by the check, MEH gets a warning
# in the editor and shows on the page, CHANGED only shows on the page, and
# SAME changes nothing anyone can see.
MISTAKES = {
    "m01-bad": "BAD",
    "m02-changed": "CHANGED",
    "m03-bad-again": "BAD again",
    "m04-same": "SAME",
    "m05-changed-again": "CHANGED again",
    "m06-bad-third": "BAD third",
    "m07-meh": "MEH",
}


@dataclass
class Toy:
    root: Path
    cache: Path
    observed: list[str] = field(default_factory=list)
    # Working copies whose development server the fake browser check treats as never answering.
    silent_servers: set[str] = field(default_factory=set)
    # Working copies whose default journey the fake browser check treats as stopping early.
    stopped_journeys: set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def run(self, **options: object) -> Path:
        args = argparse.Namespace(
            framework=None, mistake=None, skip_runtime=False, jobs=4, static_jobs=2, no_cache=False
        )
        for name, value in options.items():
            setattr(args, name, value)
        return cli.run(args)

    def records(self, run_dir: Path) -> list[dict]:
        return [json.loads(line) for line in (run_dir / "results.jsonl").read_text().splitlines()]


def _fake_observe(toy: Toy):  # noqa: ANN202 - returns the replacement for runtime.observe
    def observe(_framework: Framework, _env: Path, path: Path, log_path: Path) -> Observation:
        # A random pause makes the cases finish out of order.
        time.sleep(random.random() * 0.05)  # noqa: S311
        text = (path / "app.txt").read_text()
        # The development server starts from a fresh copy, whether or not the tools ran in this run.
        if (path / "tool-output.txt").exists():
            raise AssertionError("the browser check saw what the tools wrote")
        with toy.lock:
            toy.observed.append(path.name)
        if path.name in toy.silent_servers:
            log_path.write_text("")
            return Observation(started=False, failure="the development server did not answer")
        log_path.write_text("GET / 200\n")
        # The page shows the app text, so a case that changes it reads as a different page.
        snapshot = {"elements": [], "text": text.replace("SAME", "Hello")}
        failure = "TimeoutError: locator.click: Timeout 5000ms exceeded." if path.name in toy.stopped_journeys else ""
        return Observation(snapshot_loaded=snapshot, snapshot=snapshot, snapshot_reloaded=snapshot, failure=failure)

    return observe


@pytest.fixture
def toy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Toy:
    root = tmp_path / "bench"
    framework = root / "frameworks" / "toy"
    (framework / "baseline").mkdir(parents=True)
    (framework / "framework.toml").write_text(FRAMEWORK)
    (framework / "baseline" / "app.txt").write_text("Hello\n")
    catalogue = ["# Toy mistakes.\n"]
    for mistake, new in MISTAKES.items():
        catalogue.append(
            f'[[mistake]]\nid = "{mistake}"\ntitle = "{mistake}"\ncategory = "naming"\norigin = "neutral"\n'
            'description = "d"\ncorrect = "c"\n\n'
        )
        case = root / "cases" / mistake / "toy"
        case.mkdir(parents=True)
        (case / "port.toml").write_text(
            f'status = "ported"\nmistake = {{ file = "app.txt", contains = "{new}" }}\n\n'
            f'[[edits]]\nfile = "app.txt"\nold = "Hello"\nnew = "{new}"\n'
        )
    (root / "catalogue.toml").write_text("".join(catalogue))
    cache = tmp_path / "cache"
    found = Toy(root, cache)
    monkeypatch.setattr(cli, "CACHE", cache)
    monkeypatch.setattr(work, "CACHE", cache)
    monkeypatch.setattr(cli, "load_frameworks", lambda: load_frameworks(root / "frameworks"))
    monkeypatch.setattr(cli, "load_ports", lambda: load_ports(root / "cases"))
    monkeypatch.setattr(cli, "load_catalogue", lambda: load_catalogue(root / "catalogue.toml"))
    # The report reads the definitions too, to name the frameworks and mistakes.
    monkeypatch.setattr(report, "load_frameworks", lambda: load_frameworks(root / "frameworks"))
    monkeypatch.setattr(report, "load_catalogue", lambda: load_catalogue(root / "catalogue.toml"))
    monkeypatch.setattr(cli, "observe", _fake_observe(found))
    return found
