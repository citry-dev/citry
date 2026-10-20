"""Running cases side by side must give the same records as running them one by one."""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from citry_errors import parallel, runtime
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

    results = parallel.run_all(range(5), work, jobs=5, group=lambda _: "all", limits={}, stop=threading.Event())
    assert results == [0, 10, 20, 30, 40]


def test_a_framework_limit_caps_its_cases_and_lets_other_frameworks_go_first() -> None:
    running: Counter[str] = Counter()
    highest: Counter[str] = Counter()
    lock = threading.Lock()
    started: list[str] = []

    def work(task: str) -> str:
        with lock:
            running[task[0]] += 1
            highest[task[0]] = max(highest[task[0]], running[task[0]])
            started.append(task)
        time.sleep(0.03)
        with lock:
            running[task[0]] -= 1
        return task

    tasks = ["n1", "n2", "n3", "j1", "j2", "j3"]
    results = parallel.run_all(
        tasks, work, jobs=4, group=lambda task: task[0], limits={"n": 1}, stop=threading.Event()
    )
    assert results == tasks
    assert highest["n"] == 1
    # While n2 and n3 wait for n1, the j tasks behind them start.
    assert started.index("j1") < started.index("n2")
    assert highest["j"] > 1


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
        parallel.run_all(range(20), work, jobs=2, group=lambda _: "all", limits={}, stop=threading.Event())
    # The task that was running beside the failing one finished; the rest never started.
    assert finished == [1]


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

    def observe_on(framework, settings, env, work, log_path, port):
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


def test_a_server_that_fails_for_another_reason_is_not_started_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []

    def observe_on(framework, settings, env, work, log_path, port):
        calls.append(port)
        log_path.write_text("SyntaxError: invalid syntax\n")
        return runtime.Observation(started=False, failure="the development server did not answer")

    monkeypatch.setattr(runtime, "_observe_on", observe_on)
    framework = Framework("toy", "Toy", (), (), (), Runtime(("x",), "/", 5, {"default": ()}), "", tmp_path)
    assert not runtime.observe(framework, tmp_path, tmp_path, tmp_path / "server.log").started
    assert len(calls) == 1


@pytest.mark.parametrize(("value", "accepted"), [("2", True), ("0", False), ("true", False), ('"2"', False)])
def test_max_jobs_must_be_a_whole_number_of_cases(tmp_path: Path, value: str, accepted: bool) -> None:
    root = tmp_path / "toy"
    root.mkdir()
    (root / "framework.toml").write_text(
        f'key = "toy"\nname = "Toy"\nstages = []\nmax_jobs = {value}\n[setup]\nmanifests = []\ncommand = ["true"]\n'
    )
    if accepted:
        assert load_framework(root).max_jobs == int(value)
    else:
        with pytest.raises(ConfigError, match="max_jobs"):
            load_framework(root)


def test_a_run_on_several_workers_writes_the_same_records_as_one_worker(toy: Toy) -> None:
    one = toy.records(toy.run(jobs=1))
    several = toy.records(toy.run(jobs=4))
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
    }


def test_observe_runs_on_several_threads_at_once_with_a_real_browser(tmp_path: Path) -> None:
    """Each worker starts its own Playwright, so browser checks on several threads must not disturb each other."""
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
            f"<p>Site {number}</p><button onclick=\"this.textContent='done'\">go</button>"
        )
        sites.append(site)
    settings = Runtime(
        argv=(sys.executable, "-m", "http.server", "{port}", "--bind", "127.0.0.1"),
        page_path="/",
        ready_timeout=30,
        journeys={"default": (Step("click", selector="button"),)},
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
