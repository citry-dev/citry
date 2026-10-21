"""Running cases side by side must give the same records as running them one by one."""

from __future__ import annotations

import json
import signal
import socket
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from citry_errors import cli, parallel, report, runtime
from citry_errors.config import ConfigError, Framework, Runtime, Step, load_framework
from conftest import MISTAKES

if TYPE_CHECKING:
    from pathlib import Path

    from conftest import Toy


def test_results_come_back_in_task_order_whatever_order_the_tasks_finish_in() -> None:
    # The first task finishes last, so completion order is the reverse of task order.
    def work(number: int) -> int:
        time.sleep(0.02 * (5 - number))
        return number * 10

    results = parallel.run_all(range(5), work, jobs=5, stop=threading.Event())
    assert results == [0, 10, 20, 30, 40]


def test_a_failing_task_stops_new_tasks_and_is_raised_after_the_running_ones_finish() -> None:
    finished: list[int] = []
    second_started = threading.Event()

    def work(number: int) -> int:
        if number == 0:
            # Fail only once the second worker is busy, so it has a case to finish.
            second_started.wait(timeout=5)
            raise ValueError("case 0 broke")
        second_started.set()
        time.sleep(0.05)
        finished.append(number)
        return number

    with pytest.raises(ValueError, match="case 0 broke"):
        parallel.run_all(range(20), work, jobs=2, stop=threading.Event())
    # The task that was running beside the failing one finished; the rest never started.
    assert finished == [1]


def test_ctrl_c_stops_new_tasks_sets_stop_and_waits_for_running_ones() -> None:
    stop = threading.Event()
    both_running = threading.Barrier(2)
    started: list[int] = []
    gave_up: list[int] = []

    def work(number: int) -> int:
        started.append(number)
        # Ctrl-C comes only once both workers are on a case.
        both_running.wait(timeout=5)
        if number == 0:
            # Ctrl-C reaches the main thread, which is waiting for the workers.
            signal.pthread_kill(threading.main_thread().ident, signal.SIGINT)
        # A running case notices `stop` at its next step and gives up its case.
        for _ in range(500):
            if stop.is_set():
                time.sleep(0.05)
                gave_up.append(number)
                raise parallel.Stopped
            time.sleep(0.01)
        return number

    with pytest.raises(KeyboardInterrupt):
        parallel.run_all(range(10), work, jobs=2, stop=stop)
    assert stop.is_set()
    assert sorted(started) == [0, 1]
    # Both workers had given up their case before run_all returned, so it waited for them.
    assert sorted(gave_up) == [0, 1]


def test_zero_jobs_is_rejected_rather_than_running_nothing() -> None:
    with pytest.raises(ValueError, match="must be 1 or more"):
        parallel.run_all(range(3), lambda n: n, jobs=0, stop=threading.Event())


def test_concurrent_workers_never_share_a_port_and_a_finished_one_frees_it() -> None:
    barrier = threading.Barrier(8)

    def hold() -> int:
        with runtime.reserve_port() as port:
            # Every worker holds its port until all eight have one.
            barrier.wait(timeout=5)
            return port

    with ThreadPoolExecutor(max_workers=8) as pool:
        ports = list(pool.map(lambda _: hold(), range(8)))
    assert len(set(ports)) == 8
    assert all(port in runtime._PORTS for port in ports)
    assert not runtime._reserved_ports


def test_a_port_another_program_listens_on_is_never_handed_out(monkeypatch: pytest.MonkeyPatch) -> None:
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        taken = busy.getsockname()[1]
        # With the taken port as the only one in the range, there is nothing to hand out.
        monkeypatch.setattr(runtime, "_PORTS", range(taken, taken + 1))
        with pytest.raises(RuntimeError, match="no free port"), runtime.reserve_port():
            pass


def test_a_server_whose_port_was_taken_is_started_again_on_another_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ports: list[int] = []

    def observe_on(framework, settings, env, work, log_path, port, backend_port):
        ports.append(port)
        if len(ports) == 1:
            log_path.write_text("OSError: [Errno 48] Address already in use\n")
            return runtime.Observation(started=False, failure="the development server did not answer")
        log_path.write_text("serving\n")
        return runtime.Observation(server_log=["serving"])

    monkeypatch.setattr(runtime, "_observe_on", observe_on)
    framework = Framework("toy", "Toy", (), (), (), Runtime(("x",), "/", 5, {"default": ()}), "", tmp_path)
    observation = runtime.observe(framework, tmp_path, tmp_path, tmp_path / "server.log")
    assert observation.started
    assert len(ports) == 2


@pytest.mark.parametrize(("argv", "named"), [(("x", "{port}", "{backend_port}"), True), (("x", "{port}"), False)])
def test_a_server_that_names_a_backend_port_gets_a_second_reserved_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, argv: tuple[str, ...], named: bool
) -> None:
    seen: list[tuple[int, int, set[int]]] = []

    def observe_on(framework, settings, env, work, log_path, port, backend_port):
        # Both ports must stay reserved while the server runs, so no other worker gets either.
        seen.append((port, backend_port, set(runtime._reserved_ports)))
        log_path.write_text("serving\n")
        return runtime.Observation(server_log=["serving"])

    monkeypatch.setattr(runtime, "_observe_on", observe_on)
    framework = Framework("toy", "Toy", (), (), (), Runtime(argv, "/", 5, {"default": ()}), "", tmp_path)
    runtime.observe(framework, tmp_path, tmp_path, tmp_path / "server.log")
    [(port, backend_port, reserved)] = seen
    if named:
        assert backend_port in runtime._PORTS
        assert backend_port != port
        assert reserved == {port, backend_port}
    else:
        assert backend_port == 0
        assert reserved == {port}
    assert not runtime._reserved_ports


@pytest.mark.parametrize(
    "line",
    [
        "OSError: [Errno 48] Address already in use",
        "Error: listen EADDRINUSE: address already in use 127.0.0.1:20001",
        "Error: That port is already in use.",
        "Error: Frontend port: 20001 is already in use.",
    ],
)
def test_each_servers_port_clash_message_is_recognised(line: str) -> None:
    assert runtime._PORT_IN_USE.search(line)


def test_a_server_that_fails_for_another_reason_is_not_started_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []

    def observe_on(framework, settings, env, work, log_path, port, backend_port):
        calls.append(port)
        log_path.write_text("SyntaxError: invalid syntax\n")
        return runtime.Observation(started=False, failure="the development server did not answer")

    monkeypatch.setattr(runtime, "_observe_on", observe_on)
    framework = Framework("toy", "Toy", (), (), (), Runtime(("x",), "/", 5, {"default": ()}), "", tmp_path)
    assert not runtime.observe(framework, tmp_path, tmp_path, tmp_path / "server.log").started
    assert len(calls) == 1


@pytest.mark.parametrize(("value", "accepted"), [("2", True), ("0", False), ("true", False), ('"2"', False)])
def test_max_servers_must_be_a_whole_number_of_servers(tmp_path: Path, value: str, accepted: bool) -> None:
    root = tmp_path / "toy"
    root.mkdir()
    (root / "framework.toml").write_text(
        f'key = "toy"\nname = "Toy"\nstages = []\nmax_servers = {value}\n[setup]\nmanifests = []\ncommand = ["true"]\n'
    )
    if accepted:
        assert load_framework(root).max_servers == int(value)
    else:
        with pytest.raises(ConfigError, match="max_servers"):
            load_framework(root)


def _count_at_once(monkeypatch: pytest.MonkeyPatch) -> Counter[str]:
    """Wrap the tools and the browser check so the returned counter holds the most of each that ran together."""
    lock = threading.Lock()
    running = Counter[str]()
    most = Counter[str]()

    # Wraps either of two functions with different signatures.
    def counting(kind: str, real):
        def wrapped(*args: object) -> object:
            with lock:
                running[kind] += 1
                most[kind] = max(most[kind], running[kind])
            try:
                # Long enough that, without a limit, several workers would be here together.
                time.sleep(0.05)
                return real(*args)
            finally:
                with lock:
                    running[kind] -= 1

        return wrapped

    monkeypatch.setattr(cli, "run_stages", counting("tools", cli.run_stages))
    monkeypatch.setattr(cli, "observe", counting("browser", cli.observe))
    return most


@pytest.mark.parametrize(
    ("jobs", "static_jobs", "max_servers", "browser", "tools"),
    [
        # `--static-jobs` limits the tools. Cases then reach their browser
        # checks one by one, so whether two of those overlap is down to timing
        # and is not checked.
        (4, 1, None, None, 1),
        # `--jobs` limits the browser checks, and the tools still run side by side.
        (1, 4, None, 1, "several"),
        # A framework's `max_servers` limits its browser checks below `--jobs`, not its tools.
        (4, 4, 1, 1, "several"),
    ],
)
def test_each_limit_caps_only_its_own_part_of_a_case(
    toy: Toy,
    monkeypatch: pytest.MonkeyPatch,
    jobs: int,
    static_jobs: int,
    max_servers: int | None,
    browser: int | str | None,
    tools: int | str,
) -> None:
    if max_servers is not None:
        definition = toy.root / "frameworks" / "toy" / "framework.toml"
        definition.write_text(
            definition.read_text().replace('name = "Toy"\n', f'name = "Toy"\nmax_servers = {max_servers}\n')
        )
    most = _count_at_once(monkeypatch)
    run_dir = toy.run(jobs=jobs, static_jobs=static_jobs, no_cache=True)
    if browser is not None:
        assert most["browser"] > 1 if browser == "several" else most["browser"] == browser
    assert most["tools"] > 1 if tools == "several" else most["tools"] == tools
    # The run records both limits, so a reader knows how it was run.
    run_info = json.loads((run_dir / "run.json").read_text())
    assert (run_info["jobs"], run_info["static_jobs"]) == (jobs, static_jobs)


def test_a_case_gives_up_before_starting_its_server_when_ctrl_c_came_while_it_waited_for_a_slot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    started: list[Path] = []
    monkeypatch.setattr(cli, "observe", lambda *args: started.append(args[2]))
    stop = threading.Event()
    stop.set()
    context = cli.Context(
        tmp_path,
        observe_runtime=True,
        reuse=False,
        environment="env",
        framework_digests={},
        stop=stop,
        tool_slots=threading.Semaphore(1),
        browser_slots=threading.Semaphore(1),
    )
    framework = Framework("toy", "Toy", (), (), (), None, "", tmp_path)
    with pytest.raises(parallel.Stopped):
        cli._observe(context, framework, None, tmp_path, tmp_path)
    assert started == []


def test_a_run_on_several_workers_writes_the_same_records_as_one_worker(toy: Toy) -> None:
    # Without the cache, so the second run runs every case again.
    one = toy.records(toy.run(jobs=1, no_cache=True))
    several = toy.records(toy.run(jobs=4, no_cache=True))
    assert one == several
    # Catalogue order, whatever order the workers finished in.
    assert [record["mistake"] for record in several] == list(MISTAKES)
    assert {record["mistake"]: record["strict"] for record in several} == {
        "m01-bad": "check",
        "m02-changed": "silent",
        "m03-bad-again": "check",
        "m04-same": "never",
        "m05-changed-again": "silent",
        "m06-bad-third": "check",
        "m07-meh": "silent",
    }


def test_observe_runs_on_several_threads_at_once_with_a_real_browser(tmp_path: Path) -> None:
    """
    Each worker starts its own Playwright, so browser checks on several threads must not disturb each other.

    Each check also runs two more journeys at once in their own browser
    contexts, and their console messages must still reach the record in
    the order the journeys are listed.
    """
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as playwright:
        try:
            playwright.chromium.launch().close()
        except playwright_api.Error as error:
            pytest.skip(f"Chromium is not installed: {error}")
    sites = []
    for number in range(3):
        site = tmp_path / f"site{number}"
        site.mkdir()
        (site / "index.html").write_text(
            f"<p>Site {number}</p>"
            f"<button id=d onclick=\"this.textContent='done'; console.error('d {number}')\">go</button>"
            + "".join(
                f"<button id={name} onclick=\"console.error('{name} {number}')\">{name}</button>" for name in "ab"
            )
        )
        sites.append(site)
    settings = Runtime(
        argv=(sys.executable, "-m", "http.server", "{port}", "--bind", "127.0.0.1"),
        page_path="/",
        ready_timeout=30,
        journeys={
            "default": (Step("click", selector="#d"),),
            # Clicks after `second` has, so its message comes last unless each
            # journey's messages are kept apart until the journeys end.
            "first": (Step("wait", ms=300), Step("click", selector="#b")),
            "second": (Step("click", selector="#a"),),
        },
        settle_ms=50,
    )
    framework = Framework("toy", "Toy", (), (), (), settings, "", tmp_path)
    with ThreadPoolExecutor(max_workers=3) as pool:
        observations = list(
            pool.map(lambda site: runtime.observe(framework, tmp_path, site, site.parent / f"{site.name}.log"), sites)
        )
    for number, observation in enumerate(observations):
        assert observation.started, observation.failure
        assert not observation.failure
        # Each thread saw its own server's page, after its own click.
        page = json.dumps(observation.snapshot)
        assert f"Site {number}" in page
        assert "done" in page
        assert all(f"Site {number}" in json.dumps(record.snapshot) for record in observation.journeys.values())
        assert observation.console_errors == [f"d {number}", f"b {number}", f"a {number}"]


def test_what_a_server_prints_after_it_is_stopped_is_left_out_of_the_record(tmp_path: Path) -> None:
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as playwright:
        try:
            playwright.chromium.launch().close()
        except playwright_api.Error as error:
            pytest.skip(f"Chromium is not installed: {error}")
    (tmp_path / "index.html").write_text("<button>go</button>")
    # A server that, like `reflex run`, reports an error when the stop signal reaches it.
    (tmp_path / "server.py").write_text(
        "import http.server, signal, sys\n"
        "def stop(*_):\n"
        "    print('[ERROR] Unexpected exit from worker-1', flush=True)\n"
        "    sys.exit(0)\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        "print('serving', flush=True)\n"
        "handler = http.server.SimpleHTTPRequestHandler\n"
        "http.server.test(HandlerClass=handler, port=int(sys.argv[1]), bind='127.0.0.1')\n"
    )
    settings = Runtime(
        argv=(sys.executable, "-u", str(tmp_path / "server.py"), "{port}"),
        page_path="/",
        ready_timeout=30,
        journeys={"default": (Step("click", selector="button"),)},
        settle_ms=50,
    )
    framework = Framework("toy", "Toy", (), (), (), settings, "", tmp_path)
    log = tmp_path / "server.log"
    observation = runtime.observe(framework, tmp_path, tmp_path, log)
    assert "serving" in observation.server_log
    assert not any("ERROR" in line for line in observation.server_log)
    # The log file itself keeps the whole output.
    assert "[ERROR] Unexpected exit from worker-1" in log.read_text()


def test_a_static_error_skips_the_browser_check_and_a_warning_does_not(toy: Toy) -> None:
    records = {record["mistake"]: record for record in toy.records(toy.run(jobs=3))}
    caught = {"m01-bad", "m03-bad-again", "m06-bad-third"}
    # The clean app and every case no static stage reported as an error ran in the browser.
    assert sorted(toy.observed) == sorted(["baseline", *(set(MISTAKES) - caught)])
    for mistake in caught:
        assert records[mistake]["runtime"] is None
        assert records[mistake]["runtime_skipped"] == "caught by toy check"
        assert (records[mistake]["strict"], records[mistake]["lenient"]) == ("check", "check")
    # A warning decides only the lenient column, so the browser check still ran for the strict one.
    meh = records["m07-meh"]
    assert (meh["strict"], meh["lenient"], meh["runtime_skipped"]) == ("silent", "editor", "")
    assert meh["runtime"]["output_differs"]


def test_a_case_whose_browser_check_was_skipped_is_scored_as_a_static_error(toy: Toy, tmp_path: Path) -> None:
    run_dir = toy.run(jobs=2)
    report.write(run_dir, tmp_path / "report")
    summary = json.loads((tmp_path / "report" / "results.json").read_text())
    by_mistake = {row["mistake"]: row for row in summary["results"]}
    assert (by_mistake["m01-bad"]["bucket"], by_mistake["m01-bad"]["cell"]) == ("static-error", "C")
    assert by_mistake["m01-bad"]["runtime_skipped"] == "caught by toy check"
    matrix = (tmp_path / "report" / "matrix.md").read_text()
    # The run names its commit and the tree of the benchmark's inputs, in each report.
    source = json.loads((run_dir / "run.json").read_text())
    assert f"benchmark inputs tree `{source['inputs_tree']}`" in matrix
    assert summary["source"]["inputs_tree"] == source["inputs_tree"]
    assert f"benchmark inputs tree {source['inputs_tree'][:12]}" in (tmp_path / "report" / "report.html").read_text()
    # Only a run with the browser check turned off has unscored cases.
    assert "Not scored" not in matrix
    assert "Not scored" not in (tmp_path / "report" / "report.html").read_text()
