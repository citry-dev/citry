r"""
Check that a page rendered by the previous citry release keeps working when its requests reach the candidate.

During a rolling deploy some workers still run the old release while others
already run the new one, so a page one release rendered sends its requests to
the other. This script stages exactly that:

1. It installs the previous published citry release in one virtual
   environment and the candidate in another.
2. One release renders pages with State and Events, and a cached component,
   into a store both processes share (`scenario.py render`).
3. The other release answers the pages' event calls and serves their runtime
   and definition files, and renders the cached component again
   (`scenario.py serve`).
4. Each answer must be a success or the documented `stale_state` error,
   which the page reports as out of date so the app can tell the visitor.
   Any other error fails the check. A success must also mean the right
   thing: the counter's `bump` handler ran once on the State the page sent,
   so the render it returns shows the count 1.
5. For each counter whose first call succeeded, the page's next click is
   sent to the same serving release with the State the first answer
   returned (`scenario.py answer`), and its render must show 2. With signed
   State this proves the new token carries the new count. With server-stored
   State the answer returns a new pointer, so this proves the serving
   release wrote the new count to the shared store and reads it back. After
   a `stale_state` answer the page has no State to send, so the second call
   is skipped and reported as skipped, not failed.

Steps 2 to 5 run twice: an old page sent to the new release, then a new page
sent to the old release.

Only deploys between two releases of the same major version, 1 or later, are
promised to work (see the Versioning section of
packages/protocol/events/v1/spec.md). For any other pair, such as 0.9.0 to
1.0.0, the script runs every check and reports the results, and neither a
failed check nor a stage that could not run fails the run. It decides this
from the two version numbers alone. Finding the previous release on PyPI
comes before that decision, so a failure there always fails the run.

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
from dataclasses import dataclass, field, replace
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
# The Content-Type Citry's browser code sends with every Vue Events call.
EVENTS_CONTENT_TYPE = "application/citry-events+json"
# The text scenario.py's counters show, `count_label()` there; the number is
# the count the render shows.
COUNT_LABEL = re.compile(r"rolling-count-(\d+)")


@dataclass
class Outcome:
    """One check's result: `ok`, `stale` (the documented stale_state), `skip`, or `fail`."""

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


def _strings(value: Any) -> Any:
    """Yield every string inside a JSON value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def shown_counts(actions: Any) -> set[int]:
    """
    Read the counts a call's render shows.

    scenario.py writes the count as one text value, so it appears as a
    string in the render whatever form the release returns: inside HTML, or
    as a value in a Vue render's data. Looking for that text, and not for a
    field name the release's browser code chose, keeps this working across
    releases.
    """
    return {int(match) for text in _strings(actions) for match in COUNT_LABEL.findall(text)}


def follow_up_page(page: Page, actions: Any) -> Page | None:
    """
    Return the page as the browser holds it after applying an answer, or None.

    The browser takes the State token and render ID from the Events record
    for the same component class in the answer's render (field names the
    Events protocol defines), and the app revision from the render of the
    same app. None means the answer holds no new State for this component.
    """
    record = next(
        (
            item
            for item in _walk(actions)
            if item.get("componentClassId") == page.component_class_id and isinstance(item.get("stateToken"), str)
        ),
        None,
    )
    if record is None:
        return None
    revision = next(
        (
            item["revision"]
            for item in _walk(actions)
            if item.get("appId") == page.app_id and isinstance(item.get("revision"), int)
        ),
        page.revision,
    )
    render_id = record.get("serverRenderId") or record.get("renderId") or page.render_id
    return replace(page, state_token=record["stateToken"], render_id=str(render_id), revision=revision)


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
class Page:
    """What the check needs from a page one release rendered."""

    script_urls: list[str]
    # Each definition file the page loads, with the SHA-256 the page expects.
    definitions: list[tuple[str, str]]
    helper_contracts: set[str]
    app_id: str
    revision: int
    occurrence_id: str
    component_class_id: str
    render_id: str
    state_token: str


def read_page(page: str) -> Page:
    """
    Find the Events records a rendered page holds.

    The field names the Events protocol defines (`componentClassId`,
    `stateToken`) cannot change during 1.x. The surrounding Vue app data
    belongs to the browser code of the release that rendered the page, so it
    is read loosely: any record holding a State token, inside an occurrence
    with an `id`, inside a manifest with an `appId`. If a later release moves
    these, this function stops with a message instead of guessing.
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
                        return Page(
                            script_urls=[url for url in parser.script_urls if url.startswith(PREFIX + "/")],
                            definitions=[
                                (item["url"], str(item.get("sha256", "")))
                                for item in definitions
                                if isinstance(item.get("url"), str)
                            ],
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
    msg = "found no Events record with a State token in the page; update read_page() for its format"
    raise SystemExit(msg)


def event_call(page: Page, request_id: str, *, send_sequence: int = 1) -> dict[str, Any]:
    """Build the request the page's browser code sends when the button is clicked."""
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
                "sendSequence": send_sequence,
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
    report: Report,
    name: str,
    page: Page,
    request_id: str,
    answer: dict[str, Any],
    *,
    page_reports_out_of_date: bool,
    expected_count: int = 1,
    send_sequence: int = 1,
) -> str:
    """Classify the other release's answer to a page's event call, and return the status it added."""
    try:
        body = json.loads(answer["body"])
        result = body["results"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        report.add(
            name,
            "fail",
            f"HTTP {answer.get('status')} with a body that is not an Events result: {answer.get('body', '')[:300]}",
        )
        return "fail"
    if body.get("protocol") != "citry-events/1" or body.get("requestId") != request_id:
        report.add(name, "fail", f"the answer is not a citry-events/1 result for this call: {answer['body'][:300]}")
        return "fail"
    if result.get("ok") is not True:
        code = (result.get("error") or {}).get("code")
        if code == "stale_state":
            report.add(name, "stale", f"HTTP {answer['status']} stale_state: the page reports that it is out of date")
            return "stale"
        report.add(name, "fail", f"HTTP {answer['status']} error {code!r}: {answer['body'][:300]}")
        return "fail"
    if answer["status"] != 200 or result.get("sendSequence") != send_sequence:
        report.add(
            name, "fail", f"a success with HTTP {answer['status']} and sendSequence {result.get('sendSequence')!r}"
        )
        return "fail"
    # A success must mean the handler ran once on the State the page sent:
    # the render shows exactly the next count, and no other.
    counts = shown_counts(result.get("actions", []))
    if counts != {expected_count}:
        shown = ", ".join(str(count) for count in sorted(counts)) or "no count"
        report.add(name, "fail", f"the call succeeded, but its render shows {shown}, not {expected_count}")
        return "fail"
    # A Vue render carries the helper contract it was compiled for. The page
    # refuses another contract, and reports it as out of date only when the
    # release that rendered it has that behaviour. Other changes to the render
    # format are not checked here.
    new_contracts = {
        record["helperContract"]
        for record in _walk(result.get("actions", []))
        if isinstance(record.get("helperContract"), str)
    }
    if not new_contracts - page.helper_contracts:
        report.add(
            name, "ok", f"the call succeeded, its render shows {expected_count}, and it uses the page's render helpers"
        )
        return "ok"
    if page_reports_out_of_date:
        report.add(name, "stale", "the render uses other render helpers: the page reports that it is out of date")
        return "stale"
    report.add(name, "fail", "the render uses other render helpers, and the page reports nothing for that")
    return "fail"


def judge_file(report: Report, name: str, answer: dict[str, Any], expected_sha256: str) -> None:
    """A file the page links must be served, byte for byte, by a worker on the other release."""
    if answer.get("status") != 200:
        report.add(name, "fail", f"HTTP {answer.get('status')}")
    elif answer.get("sha256") != expected_sha256:
        report.add(name, "fail", f"served, but its SHA-256 is {answer.get('sha256')}, not {expected_sha256}")
    else:
        report.add(name, "ok", "served with the SHA-256 the page expects")


def same_markup(first: str, second: str) -> bool:
    """Compare two renders, ignoring the render IDs Citry makes up anew for each render."""
    pattern = re.compile(r"data-cid-[a-z0-9_]+")
    return pattern.sub("data-cid-ID", first) == pattern.sub("data-cid-ID", second)


def runtime_digest(url: str) -> str:
    """Read the SHA-256 a hashed runtime URL such as `/citry/citry.<sha256>.js` names, or "" if none."""
    match = re.search(r"\.([0-9a-f]{64})\.js$", url)
    return match.group(1) if match else ""


def check_direction(
    report: Report, label: str, render_python: Path, serve_python: Path, work: Path, *, page_reports_out_of_date: bool
) -> None:
    """Render pages with one release and send their requests to the other, then judge the answers."""
    work.mkdir(parents=True, exist_ok=True)
    store = work / "store"
    run_scenario(render_python, "render", "--store", str(store), "--out", str(work / "pages.json"), cwd=work)
    rendered = json.loads((work / "pages.json").read_text(encoding="utf-8"))
    pages = {name: read_page(rendered[name]) for name in ("signed", "stored")}
    requests: dict[str, dict[str, Any]] = {}
    for name, page in pages.items():
        requests[f"event:{name}"] = event_call(page, f"rolling_{name}")
    signed = pages["signed"]
    for url in signed.script_urls:
        requests[f"runtime:{url}"] = {"method": "GET", "path": url}
    for url, _digest in signed.definitions:
        requests[f"definition:{url}"] = {"method": "GET", "path": url}
    (work / "requests.json").write_text(json.dumps(requests), encoding="utf-8")
    run_scenario(
        serve_python,
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
    answers = served["answers"]
    first_status = {
        name: judge_event_answer(
            report,
            f"{label}: event call, {name} State",
            page,
            f"rolling_{name}",
            answers[f"event:{name}"],
            page_reports_out_of_date=page_reports_out_of_date,
        )
        for name, page in pages.items()
    }
    check_second_calls(
        report,
        label,
        serve_python,
        work,
        pages,
        answers,
        first_status,
        page_reports_out_of_date=page_reports_out_of_date,
    )
    # A page that names no runtime or no definition file would make these
    # checks pass without testing anything.
    if not signed.script_urls:
        report.add(f"{label}: runtime", "fail", "the page links no runtime under the Citry prefix")
    for url in signed.script_urls:
        judge_file(report, f"{label}: runtime {url}", answers[f"runtime:{url}"], runtime_digest(url))
    if not signed.definitions:
        report.add(f"{label}: definitions", "fail", "the page names no definition file")
    for url, digest in signed.definitions:
        judge_file(report, f"{label}: definition {url}", answers[f"definition:{url}"], digest)
    cached = served["cached"]
    # Reusing the other release's entry and rendering again are both correct,
    # as long as the output is what a render without that entry gives.
    how = "reused the entry" if cached["reused"] else "rendered again"
    if same_markup(cached["shared"], cached["fresh"]):
        report.add(f"{label}: cached render", "ok", f"{how}; the output matches a render without the entry")
    else:
        report.add(f"{label}: cached render", "fail", f"{how}; {cached['shared']!r} != {cached['fresh']!r}")


def plan_second_calls(
    report: Report,
    label: str,
    pages: dict[str, Page],
    answers: dict[str, Any],
    first_status: dict[str, str],
) -> tuple[dict[str, Page], dict[str, dict[str, Any]]]:
    """
    Build the page's next click for each counter whose first call succeeded.

    A counter whose first call did not succeed is reported as skipped: after
    `stale_state` the page has no State to send, and after a failure the
    failure is already reported.
    """
    next_pages: dict[str, Page] = {}
    requests: dict[str, dict[str, Any]] = {}
    for name, page in pages.items():
        check_name = f"{label}: second event call, {name} State"
        if first_status[name] != "ok":
            reason = "stale_state" if first_status[name] == "stale" else "a failure"
            report.add(check_name, "skip", f"the first call ended with {reason}, so the page sends no second call")
            continue
        actions = json.loads(answers[f"event:{name}"]["body"])["results"][0].get("actions", [])
        next_page = follow_up_page(page, actions)
        if next_page is None:
            report.add(check_name, "fail", "the first answer holds no new State token for this component")
            continue
        next_pages[name] = next_page
        requests[f"event:{name}"] = event_call(next_page, f"rolling_{name}_2", send_sequence=2)
    return next_pages, requests


def check_second_calls(
    report: Report,
    label: str,
    serve_python: Path,
    work: Path,
    pages: dict[str, Page],
    answers: dict[str, Any],
    first_status: dict[str, str],
    *,
    page_reports_out_of_date: bool,
) -> None:
    """Send each counter's second click, with the State the first answer returned, to the same release."""
    next_pages, requests = plan_second_calls(report, label, pages, answers, first_status)
    if not requests:
        return
    (work / "requests-2.json").write_text(json.dumps(requests), encoding="utf-8")
    run_scenario(
        serve_python,
        "answer",
        "--store",
        str(work / "store"),
        "--requests",
        str(work / "requests-2.json"),
        "--out",
        str(work / "answered-2.json"),
        cwd=work,
    )
    second = json.loads((work / "answered-2.json").read_text(encoding="utf-8"))["answers"]
    for name, next_page in next_pages.items():
        judge_event_answer(
            report,
            f"{label}: second event call, {name} State",
            next_page,
            f"rolling_{name}_2",
            second[f"event:{name}"],
            page_reports_out_of_date=page_reports_out_of_date,
            expected_count=2,
            send_sequence=2,
        )


def check(previous: str, candidate: Path, core_wheel: Path | None, work: Path, report: Report) -> None:
    """Install both releases and check the deploy in both directions."""
    old_python = make_environment(work / "old-env", [f"citry=={previous}", *SCENARIO_REQUIREMENTS])
    new_requirements = [str(candidate), *SCENARIO_REQUIREMENTS]
    if core_wheel is not None:
        new_requirements.append(str(core_wheel))
    new_python = make_environment(work / "new-env", new_requirements)
    # Reporting a render the page cannot read as an out-of-date page ships
    # in 1.0.0, so a page from 0.x reports nothing. A run that starts from 0.x is never promised, so
    # this only changes what such a run reports.
    old_reports_out_of_date = (version_tuple(previous) or (0,)) >= (1, 0, 0)
    check_direction(
        report,
        "old page, new server",
        old_python,
        new_python,
        work / "old-to-new",
        page_reports_out_of_date=old_reports_out_of_date,
    )
    # During a deploy a page the new release rendered can also reach a worker
    # that still runs the old release.
    check_direction(
        report, "new page, old server", new_python, old_python, work / "new-to-old", page_reports_out_of_date=True
    )


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
    new_version = candidate_version(candidate)
    previous = args.previous or newest_release_before(new_version)
    report = Report(previous=previous, candidate=new_version, promised=deploy_is_promised(previous, new_version))
    started = time.monotonic()
    # Each environment takes 0.1 GB to 0.3 GB, so a temporary work directory
    # is deleted afterwards.
    work = args.keep.resolve() if args.keep is not None else Path(tempfile.mkdtemp(prefix="citry-rolling-deploy-"))
    work.mkdir(parents=True, exist_ok=True)
    try:
        check(previous, candidate, args.core_wheel, work, report)
    except (SystemExit, Exception) as error:  # noqa: BLE001 - every stage's failure is reported the same way
        # A deploy that is not promised may break the script itself, for
        # example when the candidate renames an API scenario.py uses. That is
        # reported like a failed check, so only a promised deploy fails the run.
        report.add("run", "fail", f"the check could not finish: {error}")
    finally:
        if args.keep is None:
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
