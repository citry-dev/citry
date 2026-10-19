import json
from types import SimpleNamespace

from citry_bench import memory


class Process:
    def __init__(
        self, pid, *, created=None, rss=0, uss=0, children=(), denied_uss=False, denied_rss=False, disappear=False
    ):
        self.pid = pid
        self.created = float(pid) if created is None else created
        self._rss, self._uss = rss, uss
        self._children = list(children)
        self._denied_uss, self._disappear = denied_uss, disappear
        self._denied_rss = denied_rss

    def create_time(self):
        if self._disappear:
            raise memory.psutil.NoSuchProcess(self.pid)
        return self.created

    def name(self):
        return f"p{self.pid}"

    def children(self, recursive=False):
        assert recursive
        return self._children

    def memory_info(self):
        if self._denied_rss:
            raise memory.psutil.AccessDenied(self.pid)
        return SimpleNamespace(rss=self._rss)

    def memory_full_info(self):
        if self._denied_uss:
            raise memory.psutil.AccessDenied(self.pid)
        return SimpleNamespace(uss=self._uss)


def test_pinned_root_rejects_pid_reuse(monkeypatch):
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: Process(1, created=2.0))
    value = memory.endpoint_process_memory(memory.ProcessIdentity(1, 1.0))
    assert value["rss"]["status"] == "unavailable"
    assert value["process_notes"] == [{"pid": 1, "reason": "pid-reused"}]


def test_disappearing_child_makes_rss_partial(monkeypatch):
    child = Process(2, disappear=True)
    root = Process(1, rss=100, uss=60, children=[child])
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: root)
    value = memory.endpoint_process_memory(memory.ProcessIdentity(1, 1.0))
    assert value["rss"] == {"status": "partial", "value": 100, "missing": [{"pid": 2, "reason": "NoSuchProcess"}]}


def test_endpoint_retains_partial_uss_without_reporting_complete(monkeypatch):
    child = Process(2, rss=20, denied_uss=True)
    root = Process(1, rss=100, uss=60, children=[child])
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: root)
    value = memory.endpoint_process_memory(memory.ProcessIdentity(1, 1.0))
    assert value["rss"]["status"] == "measured"
    assert value["uss"] == {"status": "partial", "value": 60, "missing": [{"pid": 2, "reason": "AccessDenied"}]}
    assert value["uss_bytes"] is None


def test_rss_failure_does_not_become_zero_or_suppress_uss(monkeypatch):
    child = Process(2, uss=8, denied_rss=True)
    root = Process(1, rss=100, uss=60, children=[child])
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: root)
    value = memory.endpoint_process_memory(memory.ProcessIdentity(1, 1.0))
    assert value["rss"] == {
        "status": "partial",
        "value": 100,
        "missing": [{"pid": 2, "reason": "AccessDenied"}],
    }
    assert value["rss_bytes"] is None
    assert value["rss_partial_bytes"] == 100
    assert value["uss"]["status"] == "measured"
    assert value["uss_bytes"] == 68


def test_sampler_uses_cheap_rss_and_includes_endpoints(monkeypatch):
    readings = iter((100, 80))
    monkeypatch.setattr(
        memory,
        "_rss_snapshot",
        lambda _root: {"status": "measured", "value": next(readings), "monotonic_ns": memory.time.monotonic_ns()},
    )
    monkeypatch.setattr(memory, "endpoint_process_memory", lambda _root: {"rss_bytes": 80})
    sampler = memory.ServerSampler(memory.ProcessIdentity(1, 1.0))
    sampler.start()
    sampler._stop.set()
    observed = sampler.stop()
    assert observed["server_samples"] == 2
    assert observed["server_sampled_peak_rss_bytes"] == 100


def test_stuck_sampler_is_incomplete_and_does_not_take_final_sample(monkeypatch):
    sampler = memory.ServerSampler(memory.ProcessIdentity(1, 1.0))
    sampler.samples = [{"status": "measured", "value": 10, "monotonic_ns": 1}]
    sampler._thread = SimpleNamespace(join=lambda timeout=None: None, is_alive=lambda: True)  # noqa: ARG005
    monkeypatch.setattr(memory, "endpoint_process_memory", lambda _root: {"rss_bytes": 10})
    observed = sampler.stop()
    assert observed["server_sampler_status"] == "incomplete"
    assert observed["server_sampled_peak_rss_bytes"] is None
    assert len(sampler.samples) == 1


class Session:
    def __init__(self, values, *, detach_error=False):
        self.values, self.detach_error = values, detach_error

    def send(self, command):
        value = self.values[command]
        if isinstance(value, BaseException):
            raise value
        return value

    def detach(self):
        if self.detach_error:
            raise RuntimeError("detach failed")


def test_page_memory_keeps_cdp_metrics_independent(monkeypatch):
    page_session = Session(
        {
            "Runtime.getHeapUsage": RuntimeError("heap off"),
            "Memory.getDOMCounters": {"documents": 2, "nodes": 8, "jsEventListeners": 3},
        }
    )
    browser_session = Session({"SystemInfo.getProcessInfo": RuntimeError("system off")}, detach_error=True)
    page = SimpleNamespace(context=SimpleNamespace(new_cdp_session=lambda _page: page_session))
    browser = SimpleNamespace(new_browser_cdp_session=lambda: browser_session)
    observed = memory.page_memory(page, browser)
    assert observed["status"] == "partial"
    assert observed["browser_processes"]["status"] == "unavailable"
    assert observed["heap"]["status"] == "unavailable"
    assert observed["dom"]["status"] == "measured"
    assert observed["documents"] == 2
    assert observed["browser_session_detach"]["status"] == "unavailable"


def test_page_session_creation_failure_keeps_browser_rss(monkeypatch):
    root = Process(1, rss=100)
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: root)
    browser_session = Session(
        {
            "SystemInfo.getProcessInfo": {"processInfo": [{"id": 1, "type": "browser"}]},
            "Browser.getVersion": {"product": "Chrome/151", "protocolVersion": "1.3"},
        }
    )
    page = SimpleNamespace(
        context=SimpleNamespace(new_cdp_session=lambda _page: (_ for _ in ()).throw(RuntimeError("page off")))
    )
    observed = memory.page_memory(page, SimpleNamespace(new_browser_cdp_session=lambda: browser_session))
    assert observed["status"] == "partial"
    assert observed["browser_rss_bytes"] == 100
    assert observed["heap"]["status"] == "unavailable"


def test_browser_root_comes_from_unique_cdp_browser_record(monkeypatch):
    child = Process(2, rss=20)
    root = Process(1, rss=100, children=[child])
    monkeypatch.setattr(memory.psutil, "Process", lambda pid: root if pid == 1 else child)
    page_session = Session(
        {
            "Runtime.getHeapUsage": {"usedSize": 10, "totalSize": 20},
            "Memory.getDOMCounters": {"documents": 2, "nodes": 8, "jsEventListeners": 3},
        }
    )
    browser_session = Session(
        {
            "SystemInfo.getProcessInfo": {
                "processInfo": [{"id": 1, "type": "browser"}, {"id": 2, "type": "renderer"}]
            },
            "Browser.getVersion": {"product": "Chrome/151", "protocolVersion": "1.3"},
        }
    )
    page = SimpleNamespace(context=SimpleNamespace(new_cdp_session=lambda _page: page_session))
    observed = memory.page_memory(page, SimpleNamespace(new_browser_cdp_session=lambda: browser_session))
    assert observed["browser_processes"]["root"]["pid"] == 1
    assert observed["browser_rss_bytes"] == 120


def test_browser_root_replacement_is_unavailable(monkeypatch):
    replacement = Process(1, created=2.0, rss=100)
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: replacement)
    page_session = Session(
        {
            "Runtime.getHeapUsage": {"usedSize": 10, "totalSize": 20},
            "Memory.getDOMCounters": {"documents": 2, "nodes": 8, "jsEventListeners": 3},
        }
    )
    browser_session = Session(
        {
            "SystemInfo.getProcessInfo": {"processInfo": [{"id": 1, "type": "browser"}]},
            "Browser.getVersion": {"product": "Chrome/151", "protocolVersion": "1.3"},
        }
    )
    page = SimpleNamespace(context=SimpleNamespace(new_cdp_session=lambda _page: page_session))
    observed = memory.page_memory(
        page,
        SimpleNamespace(new_browser_cdp_session=lambda: browser_session),
        memory.ProcessIdentity(1, 1.0),
    )
    assert observed["status"] == "partial"
    assert observed["browser_processes"]["status"] == "unavailable"
    assert "identity changed" in observed["browser_processes"]["reason"]


def test_browser_version_drift_does_not_discard_rss(monkeypatch):
    root = Process(1, rss=100)
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: root)
    page_session = Session(
        {
            "Runtime.getHeapUsage": {"usedSize": 10, "totalSize": 20},
            "Memory.getDOMCounters": {"documents": 2, "nodes": 8, "jsEventListeners": 3},
        }
    )
    browser_session = Session(
        {
            "SystemInfo.getProcessInfo": {"processInfo": [{"id": 1, "type": "browser"}]},
            "Browser.getVersion": {"product": "Chrome/152", "protocolVersion": "1.4"},
        }
    )
    page = SimpleNamespace(context=SimpleNamespace(new_cdp_session=lambda _page: page_session))
    observed = memory.page_memory(
        page,
        SimpleNamespace(new_browser_cdp_session=lambda: browser_session),
        memory.ProcessIdentity(1, 1.0),
        ("Chrome/151", "1.3"),
    )
    assert observed["browser_rss_bytes"] == 100
    assert observed["browser_version"]["status"] == "unavailable"


def test_observer_sampling_failure_does_not_fail_scenario(tmp_path, monkeypatch):
    observer = memory.SessionMemoryObserver(
        tmp_path / "memory.jsonl", {"app": "x"}, memory.ProcessIdentity(1, 1.0), {}, object()
    )
    monkeypatch.setattr(observer, "establish_blank_browser", lambda _page: None)
    monkeypatch.setattr(memory, "_rss_snapshot", lambda _root: (_ for _ in ()).throw(RuntimeError("rss off")))
    observer.begin("initial", object(), "initial", warmup=False, cycle=None)
    observer.finish("initial", "ok", None)
    row = json.loads((tmp_path / "memory.jsonl").read_text())
    assert row["status"] == "ok"
    assert row["server_sampler_status"] == "incomplete"


def test_incomplete_sampler_does_not_invalidate_correct_scenario(tmp_path):
    observer = memory.SessionMemoryObserver(
        tmp_path / "memory.jsonl",
        {"app": "x", "cycle": 2, "page_load": 1, "session": "s"},
        memory.ProcessIdentity(1, 1.0),
        {},
        object(),
    )
    observer.pending = {
        **observer.info,
        "operation": "initial",
        "server": {"rss_bytes": 10},
        "server_sampler_status": "incomplete",
    }
    observer.finish("initial", "ok", None)
    row = json.loads((tmp_path / "memory.jsonl").read_text())
    assert row["status"] == "ok"
    assert row["scenario_status"] == "ok"
    assert (row["cycle"], row["page_load"], row["session"]) == (2, 1, "s")


class RecordingSession(Session):
    def __init__(self, values):
        super().__init__(values)
        self.commands = []

    def send(self, command):
        self.commands.append(command)
        # The heap shrinks once garbage is collected, as it does in V8.
        if command == "Runtime.getHeapUsage" and "HeapProfiler.collectGarbage" in self.commands:
            return {"usedSize": 4, "totalSize": 8}
        return super().send(command)


def test_observer_reads_heap_after_gc_only_after_the_existing_readings(tmp_path, monkeypatch):
    page, browser, page_session = _gc_fixture(monkeypatch)
    observer = memory.SessionMemoryObserver(tmp_path / "memory.jsonl", {"app": "x"}, None, {}, browser)
    observer.begin("initial", page, "initial", warmup=False, cycle=0)
    observer.at_layout("initial", page, {"state": {"revision": 1}})
    # The layout reading alone never collects garbage; the caller asks for
    # the after-GC heap separately once network accounting is done.
    assert "HeapProfiler.collectGarbage" not in page_session.commands
    observer.read_heap_after_gc("initial", page)
    observer.finish("initial", "ok", None)
    assert page_session.commands[-3:] == [
        "HeapProfiler.collectGarbage",
        "HeapProfiler.collectGarbage",
        "Runtime.getHeapUsage",
    ]
    row = json.loads((tmp_path / "memory.jsonl").read_text().splitlines()[-1])
    # The existing reading is taken before collection and keeps its value.
    assert row["browser"]["heap_used_bytes"] == 10
    assert row["browser"]["heap_after_gc"]["status"] == "measured"
    assert row["browser"]["heap_after_gc_used_bytes"] == 4
    assert row["browser"]["heap_after_gc_allocated_bytes"] == 8
    assert row["browser"]["status"] == "measured"


def test_failed_gc_leaves_other_readings_and_overall_status_unchanged(tmp_path, monkeypatch):
    page, browser, page_session = _gc_fixture(monkeypatch)
    page_session.values["HeapProfiler.collectGarbage"] = RuntimeError("gc off")
    observer = memory.SessionMemoryObserver(tmp_path / "memory.jsonl", {"app": "x"}, None, {}, browser)
    observer.begin("initial", page, "initial", warmup=False, cycle=0)
    observer.at_layout("initial", page, {"state": {"revision": 1}})
    observer.read_heap_after_gc("initial", page)
    observer.finish("initial", "ok", None)
    row = json.loads((tmp_path / "memory.jsonl").read_text().splitlines()[-1])
    assert row["browser"]["status"] == "measured"
    assert row["browser"]["heap_used_bytes"] == 10
    assert row["browser"]["heap_after_gc"] == {
        "status": "unavailable",
        "value": None,
        "reason": "RuntimeError: gc off",
    }
    assert row["browser"]["heap_after_gc_used_bytes"] is None


def _gc_fixture(monkeypatch):
    root = Process(1, rss=100)
    monkeypatch.setattr(memory.psutil, "Process", lambda _pid: root)
    page_session = RecordingSession(
        {
            "Runtime.getHeapUsage": {"usedSize": 10, "totalSize": 20},
            "Memory.getDOMCounters": {"documents": 2, "nodes": 8, "jsEventListeners": 3},
            "HeapProfiler.collectGarbage": {},
        }
    )
    browser = SimpleNamespace(
        new_browser_cdp_session=lambda: Session(
            {
                "SystemInfo.getProcessInfo": {"processInfo": [{"id": 1, "type": "browser"}]},
                "Browser.getVersion": {"product": "Chrome/151", "protocolVersion": "1.3"},
            }
        )
    )
    page = SimpleNamespace(context=SimpleNamespace(new_cdp_session=lambda _page: page_session))
    return page, browser, page_session


def test_page_memory_never_collects_garbage(monkeypatch):
    page, browser, page_session = _gc_fixture(monkeypatch)
    observed = memory.page_memory(page, browser)
    assert "HeapProfiler.collectGarbage" not in page_session.commands
    assert "heap_after_gc" not in observed
    assert "heap_after_gc_used_bytes" not in observed


def test_observer_reads_heap_after_gc_only_when_asked(tmp_path, monkeypatch):
    page, browser, page_session = _gc_fixture(monkeypatch)
    observer = memory.SessionMemoryObserver(tmp_path / "memory.jsonl", {"app": "x"}, None, {}, browser)
    for operation, final in (("initial", False), ("select", False), ("probe", True)):
        observer.begin(operation, page, operation, warmup=False, cycle=0)
        observer.at_layout(operation, page, {"state": {"revision": 1}})
        if final:
            observer.read_heap_after_gc(operation, page)
        observer.finish(operation, "ok", None)
    rows = [json.loads(line) for line in (tmp_path / "memory.jsonl").read_text().splitlines()]
    # Earlier observations keep their ordinary heap reading and never trigger a collection.
    assert [row["browser"]["heap_used_bytes"] for row in rows] == [10, 10, 10]
    assert ["heap_after_gc" in row["browser"] for row in rows] == [False, False, True]
    assert rows[-1]["browser"]["heap_after_gc_used_bytes"] == 4
    assert page_session.commands.count("HeapProfiler.collectGarbage") == 2


def test_failure_before_the_after_gc_reading_records_a_reason(tmp_path, monkeypatch):
    page, browser, page_session = _gc_fixture(monkeypatch)
    observer = memory.SessionMemoryObserver(tmp_path / "memory.jsonl", {"app": "x"}, None, {}, browser)
    # The last observation reaches layout, then fails before the reading.
    observer.begin("probe", page, "probe", warmup=False, cycle=0, read_heap_after_gc=True)
    observer.at_layout("probe", page, {"state": {"revision": 1}})
    observer.finish("probe", "error", "Request failed")
    # A failure before layout still records the reason.
    observer.begin("again", page, "again", warmup=False, cycle=0, read_heap_after_gc=True)
    observer.finish("again", "timeout", "deadline")
    # An observation that never asked for the reading stays without the key.
    observer.begin("earlier", page, "earlier", warmup=False, cycle=0)
    observer.finish("earlier", "error", "Request failed")
    rows = [json.loads(line) for line in (tmp_path / "memory.jsonl").read_text().splitlines()]

    assert rows[0]["browser"]["heap_used_bytes"] == 10
    assert rows[0]["browser"]["heap_after_gc"] == {
        "status": "unavailable",
        "value": None,
        "reason": "observation ended with status 'error' before the after-GC reading",
    }
    assert rows[0]["browser"]["heap_after_gc_used_bytes"] is None
    assert rows[1]["browser"]["heap_after_gc"]["reason"] == (
        "observation ended with status 'timeout' before the after-GC reading"
    )
    assert "heap_after_gc" not in rows[2].get("browser", {})
    assert "HeapProfiler.collectGarbage" not in page_session.commands


def test_successful_after_gc_reading_is_not_replaced_by_a_reason(tmp_path, monkeypatch):
    page, browser, _page_session = _gc_fixture(monkeypatch)
    observer = memory.SessionMemoryObserver(tmp_path / "memory.jsonl", {"app": "x"}, None, {}, browser)
    observer.begin("probe", page, "probe", warmup=False, cycle=0, read_heap_after_gc=True)
    observer.at_layout("probe", page, {"state": {"revision": 1}})
    observer.read_heap_after_gc("probe", page)
    # An assertion after the reading can still fail the observation.
    observer.finish("probe", "error", "assertion")
    row = json.loads((tmp_path / "memory.jsonl").read_text())

    assert row["browser"]["heap_after_gc"]["status"] == "measured"
    assert row["browser"]["heap_after_gc_used_bytes"] == 4
