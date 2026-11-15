r"""
Check that a page rendered by the previous citry release keeps working when its requests reach the candidate.

During a rolling deploy some workers still run the old release while others
already run the new one, so a page one release rendered sends its requests to
the other. This script stages exactly that:

1. It installs the previous published citry release in one virtual
   environment and the candidate in another.
2. The old release renders pages with State and Events, and a cached
   component, into a store both processes share (`scenario.py render`).
3. The new release answers the old pages' event calls, the old page's runtime
   and definition files, and renders the cached component again
   (`scenario.py serve`).
4. Each answer must be a success or the documented reload, a `stale_state`
   error that makes the page offer the visitor a reload. Any other error fails
   the check.

Only deploys between two 1.x releases are promised to work (see the Versioning
section of packages/protocol/events/v1/spec.md). When the previous release is
0.x, or the two releases have different major versions, the script runs every
check and reports the results, but a failed check does not fail the run. It
decides this from the two version numbers alone.

Run it from the repository root:

    python scripts/rolling_deploy/check.py --previous 0.9.0

In release qualification it gets the built wheel, and the citry-core wheel
when citry-core ships in the same release:

    python scripts/rolling_deploy/check.py \\
        --candidate dist/citry-1.0.0-py3-none-any.whl \\
        --core-wheel core-dist/citry_core-2.0.1-....whl
"""

from __future__ import annotations

import argparse
import html.parser
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO = Path(__file__).resolve().with_name("scenario.py")
CITRY_PROJECT = REPO_ROOT / "packages" / "py" / "citry"
PYPI_JSON = "https://pypi.org/pypi/citry/json"
PREFIX = "/citry"
# What an application needs on top of citry to run scenario.py.
SCENARIO_REQUIREMENTS = ("diskcache>=5.6",)
# The headers Citry's browser code sends with every Vue Events call.
EVENTS_CONTENT_TYPE = "application/citry-events+json"


@dataclass
class Outcome:
    """One check's result: `ok`, `reload` (the documented stale_state), or `fail`."""

    name: str
    status: str
    detail: str


@dataclass
class Report:
    previous: str
    candidate: str
    promised: bool
    outcomes: list[Outcome] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str) -> None:
        self.outcomes.append(Outcome(name, status, detail))

    @property
    def failed(self) -> list[Outcome]:
        return [outcome for outcome in self.outcomes if outcome.status == "fail"]


def version_tuple(version: str) -> tuple[int, ...] | None:
    """Read a final release number such as 1.2.3; anything else (a pre-release) is None."""
    if re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        return None
    return tuple(int(part) for part in version.split("."))


def candidate_version(candidate: Path) -> str:
    """Read the candidate's version from its wheel name or its pyproject.toml."""
    if candidate.suffix == ".whl":
        # A wheel name is `{name}-{version}-{tags}.whl`, and the version holds no dash.
        return candidate.name.split("-")[1]
    project = tomllib.loads((candidate / "pyproject.toml").read_text(encoding="utf-8"))
    return str(project["project"]["version"])


def newest_release_before(candidate: str) -> str:
    """Return the newest final citry release on PyPI that is older than the candidate."""
    with urllib.request.urlopen(PYPI_JSON, timeout=30) as response:  # noqa: S310 - a fixed https URL
        return pick_previous(json.load(response)["releases"], candidate)


def pick_previous(releases: dict[str, list[dict[str, Any]]], candidate: str) -> str:
    """Pick the newest final release older than the candidate from PyPI's `releases` map, skipping yanked ones."""
    limit = version_tuple(candidate)
    if limit is None:
        msg = f"the candidate version {candidate!r} is not a final release number"
        raise SystemExit(msg)
    usable = [
        version
        for version, files in releases.items()
        if (number := version_tuple(version)) is not None
        and number < limit
        and files
        and not all(item.get("yanked") for item in files)
    ]
    if not usable:
        msg = f"PyPI lists no citry release older than {candidate}"
        raise SystemExit(msg)
    return max(usable, key=lambda version: version_tuple(version) or ())


def deploy_is_promised(previous: str, candidate: str) -> bool:
    """Only deploys between two releases of the same major version, 1 or later, are promised."""
    old, new = version_tuple(previous), version_tuple(candidate)
    return old is not None and new is not None and old[0] >= 1 and old[0] == new[0]


def run(command: list[str], *, cwd: Path | None = None) -> None:
    """Run a command and stop with its output when it fails."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        msg = f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        raise SystemExit(msg)


def make_environment(path: Path, requirements: list[str]) -> Path:
    """Create a virtual environment with uv and install the requirements; return its Python."""
    run(["uv", "venv", "--quiet", "--python", sys.executable, str(path)])
    python = path / "bin" / "python"
    # `--no-sources` makes uv resolve citry-core from PyPI (or a wheel given
    # here) instead of the workspace member it would build from source.
    run(["uv", "pip", "install", "--quiet", "--no-sources", "--python", str(python), *requirements])
    return python


def run_scenario(python: Path, *args: str, cwd: Path) -> None:
    """Run scenario.py in an isolated interpreter, so the checkout's files cannot shadow the installed citry."""
    run([str(python), "-I", str(SCENARIO), *args], cwd=cwd)


class _PageParser(html.parser.HTMLParser):
    """Collect the runtime script URLs and the JSON data blocks of a rendered page."""

    def __init__(self) -> None:
        super().__init__()
        self.script_urls: list[str] = []
        self.json_blocks: list[str] = []
        self._in_json = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.script_urls.append(values["src"] or "")
        self._in_json = tag == "script" and values.get("type") == "application/json"

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_json = False

    def handle_data(self, data: str) -> None:
        if self._in_json:
            self.json_blocks.append(data)


def _walk(value: Any) -> Any:
    """Yield every dict inside a JSON value."""
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


@dataclass
class OldPage:
    """What the check needs from a page the old release rendered."""

    script_urls: list[str]
    definition_urls: list[str]
    helper_contracts: set[str]
    app_id: str
    revision: int
    occurrence_id: str
    component_class_id: str
    render_id: str
    state_token: str


def read_old_page(page: str) -> OldPage:
    """
    Find the Events records an old page holds.

    The field names the Events protocol defines (`componentClassId`,
    `stateToken`) cannot change during 1.x. The surrounding Vue app data
    belongs to the old release's browser code, so it is read loosely: any
    record holding a State token, inside an occurrence with an `id`, inside a
    manifest with an `appId`. If a later release moves these, this function
    stops with a message instead of guessing.
    """
    parser = _PageParser()
    parser.feed(page)
    for block in parser.json_blocks:
        data = json.loads(block)
        for manifest in _walk(data):
            if not isinstance(manifest.get("appId"), str) or not isinstance(manifest.get("occurrences"), list):
                continue
            for occurrence in manifest["occurrences"]:
                for record in _walk(occurrence):
                    if isinstance(record.get("stateToken"), str) and isinstance(record.get("componentClassId"), str):
                        definitions = [item for item in manifest.get("definitions", []) if isinstance(item, dict)]
                        return OldPage(
                            script_urls=[url for url in parser.script_urls if url.startswith(PREFIX + "/")],
                            definition_urls=[item["url"] for item in definitions if isinstance(item.get("url"), str)],
                            helper_contracts={
                                item["helperContract"]
                                for item in definitions
                                if isinstance(item.get("helperContract"), str)
                            },
                            app_id=manifest["appId"],
                            revision=int(manifest.get("revision", 0)),
                            occurrence_id=str(occurrence["id"]),
                            component_class_id=record["componentClassId"],
                            render_id=str(record.get("serverRenderId") or record.get("renderId")),
                            state_token=record["stateToken"],
                        )
    msg = "found no Events record with a State token in the old page; update read_old_page() for its format"
    raise SystemExit(msg)


def event_call(page: OldPage, request_id: str) -> dict[str, Any]:
    """Build the request the old page's browser code sends when the button is clicked."""
    envelope = {
        "protocol": "citry-events/1",
        "requestId": request_id,
        "capabilities": {
            "actions": ["render", "data", "state", "event", "redirect", "url"],
            "swaps": ["morph"],
            "renderers": ["vue-prepared/1"],
        },
        "calls": [
            {
                "componentClassId": page.component_class_id,
                "handlerName": "bump",
                "callerRenderId": page.render_id,
                "args": {},
                "stateToken": page.state_token,
                "sendSequence": 1,
            }
        ],
    }
    return {
        "method": "POST",
        "path": f"{PREFIX}/ext/events/call",
        "headers": {
            "Content-Type": EVENTS_CONTENT_TYPE,
            "X-Citry-Events": "1",
            "X-Citry-Vue-App": page.app_id,
            "X-Citry-Vue-Occurrence": page.occurrence_id,
            "X-Citry-Vue-Revision": str(page.revision),
        },
        "body": json.dumps(envelope),
    }


def judge_event_answer(
    report: Report, name: str, page: OldPage, request_id: str, answer: dict[str, Any], *, previous_offers_reload: bool
) -> None:
    """Classify the new release's answer to an old page's event call."""
    try:
        body = json.loads(answer["body"])
        result = body["results"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        report.add(
            name,
            "fail",
            f"HTTP {answer.get('status')} with a body that is not an Events result: {answer.get('body', '')[:300]}",
        )
        return
    if body.get("protocol") != "citry-events/1" or body.get("requestId") != request_id:
        report.add(name, "fail", f"the answer is not a citry-events/1 result for this call: {answer['body'][:300]}")
        return
    if result.get("ok") is not True:
        code = (result.get("error") or {}).get("code")
        if code == "stale_state":
            report.add(name, "reload", f"HTTP {answer['status']} stale_state: the old page offers a reload")
        else:
            report.add(name, "fail", f"HTTP {answer['status']} error {code!r}: {answer['body'][:300]}")
        return
    if answer["status"] != 200 or result.get("sendSequence") != 1:
        report.add(
            name, "fail", f"a success with HTTP {answer['status']} and sendSequence {result.get('sendSequence')!r}"
        )
        return
    # A Vue render from the new release carries the helper contract it was
    # compiled for. The old page refuses another contract, and offers a reload
    # only when the old release has that behaviour (1.0.0 and later).
    new_contracts = {
        record["helperContract"]
        for record in _walk(result.get("actions", []))
        if isinstance(record.get("helperContract"), str)
    }
    changed = new_contracts - page.helper_contracts
    if not changed:
        report.add(name, "ok", "the call succeeded and the old page can apply its render")
    elif previous_offers_reload:
        report.add(name, "reload", "the render uses other render helpers: the old page offers a reload")
    else:
        report.add(name, "fail", "the render uses other render helpers, and the old page offers no reload for that")


def judge_file(report: Report, name: str, answer: dict[str, Any]) -> None:
    """A file the old page links must still be served by a worker on the new release."""
    if answer.get("status") == 200:
        report.add(name, "ok", "served from the shared store")
    else:
        report.add(name, "fail", f"HTTP {answer.get('status')}")


def same_markup(first: str, second: str) -> bool:
    """Compare two renders, ignoring the render IDs Citry makes up anew for each render."""
    pattern = re.compile(r"data-cid-[a-z0-9_]+")
    return pattern.sub("data-cid-ID", first) == pattern.sub("data-cid-ID", second)


def check(previous: str, candidate: Path, core_wheel: Path | None, work: Path) -> Report:
    """Install both releases, run the scenario on each, and judge the answers."""
    new_version = candidate_version(candidate)
    report = Report(previous=previous, candidate=new_version, promised=deploy_is_promised(previous, new_version))
    store = work / "store"
    old_python = make_environment(work / "old-env", [f"citry=={previous}", *SCENARIO_REQUIREMENTS])
    new_requirements = [str(candidate), *SCENARIO_REQUIREMENTS]
    if core_wheel is not None:
        new_requirements.append(str(core_wheel))
    new_python = make_environment(work / "new-env", new_requirements)

    run_scenario(old_python, "render", "--store", str(store), "--out", str(work / "pages.json"), cwd=work)
    pages = json.loads((work / "pages.json").read_text(encoding="utf-8"))
    old_pages = {name: read_old_page(pages[name]) for name in ("signed", "stored")}
    requests: dict[str, dict[str, Any]] = {}
    for name, page in old_pages.items():
        requests[f"event:{name}"] = event_call(page, f"rolling_{name}")
    signed = old_pages["signed"]
    for url in signed.script_urls:
        requests[f"runtime:{url}"] = {"method": "GET", "path": url}
    for url in signed.definition_urls:
        requests[f"definition:{url}"] = {"method": "GET", "path": url}
    (work / "requests.json").write_text(json.dumps(requests), encoding="utf-8")

    run_scenario(
        new_python,
        "serve",
        "--store",
        str(store),
        "--requests",
        str(work / "requests.json"),
        "--out",
        str(work / "served.json"),
        cwd=work,
    )
    served = json.loads((work / "served.json").read_text(encoding="utf-8"))
    # The reload for a render the old page cannot read ships from 1.0.0 on.
    previous_offers_reload = (version_tuple(previous) or (0,)) >= (1, 0, 0)
    for name, page in old_pages.items():
        judge_event_answer(
            report,
            f"event call, {name} State",
            page,
            f"rolling_{name}",
            served["answers"][f"event:{name}"],
            previous_offers_reload=previous_offers_reload,
        )
    if not signed.script_urls:
        report.add("runtime URL", "fail", "the old page links no runtime under the Citry prefix")
    for url in signed.script_urls:
        judge_file(report, f"runtime {url}", served["answers"][f"runtime:{url}"])
    for url in signed.definition_urls:
        judge_file(report, f"definition {url}", served["answers"][f"definition:{url}"])
    cached = served["cached"]
    if same_markup(cached["shared"], cached["fresh"]):
        report.add("cached render", "ok", "the new release's output matches a render that did not read the old entry")
    else:
        report.add("cached render", "fail", f"shared {cached['shared']!r} != fresh {cached['fresh']!r}")
    return report


def format_report(report: Report, seconds: float) -> str:
    """Write the results as lines for the CI log, ending with whether a failure counts."""
    lines = [f"Rolling deploy from citry {report.previous} to {report.candidate} ({seconds:.0f} s)"]
    lines += [f"  {outcome.status.upper():7} {outcome.name}: {outcome.detail}" for outcome in report.outcomes]
    if report.promised:
        lines.append("Deploys between these releases are promised, so a failed check fails the run.")
    else:
        lines.append(
            "Only deploys between two releases of the same major version, 1 or later, are promised."
            " These results are reported only; a failed check does not fail the run."
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 2)[1].strip())
    parser.add_argument(
        "--previous",
        help="the citry release that rendered the open pages (default: the newest on PyPI older than the candidate)",
    )
    parser.add_argument(
        "--candidate", type=Path, default=CITRY_PROJECT, help="the candidate citry wheel or project directory"
    )
    parser.add_argument(
        "--core-wheel",
        type=Path,
        help="a citry-core wheel to install with the candidate, when PyPI does not have its pin yet",
    )
    parser.add_argument("--report", type=Path, help="also write the results to this JSON file")
    parser.add_argument("--keep", type=Path, help="work in this directory and keep it, instead of a temporary one")
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    previous = args.previous or newest_release_before(candidate_version(candidate))
    started = time.monotonic()
    if args.keep is not None:
        args.keep.mkdir(parents=True, exist_ok=True)
        report = check(previous, candidate, args.core_wheel, args.keep.resolve())
    else:
        # Each environment takes about 0.1 GB to 0.3 GB, so nothing is left behind.
        work = Path(tempfile.mkdtemp(prefix="citry-rolling-deploy-"))
        try:
            report = check(previous, candidate, args.core_wheel, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    seconds = time.monotonic() - started
    sys.stdout.write(format_report(report, seconds))
    if args.report is not None:
        args.report.write_text(
            json.dumps(
                {
                    "previous": report.previous,
                    "candidate": report.candidate,
                    "promised": report.promised,
                    "seconds": round(seconds, 1),
                    "outcomes": [outcome.__dict__ for outcome in report.outcomes],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return 1 if report.promised and report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
