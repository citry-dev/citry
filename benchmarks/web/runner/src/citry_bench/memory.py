"""Memory-only observations attached to the common layout opportunity endpoint."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

import psutil

from citry_bench.results import append


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    create_time: float


def pin_process(pid: int) -> ProcessIdentity | None:
    try:
        process = psutil.Process(pid)
        return ProcessIdentity(process.pid, process.create_time())
    except psutil.Error:
        return None


def _identity(process: psutil.Process) -> dict[str, object]:
    return {"pid": process.pid, "create_time": process.create_time(), "name": process.name()}


def _reason(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"


def _unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "reason": reason}


def process_tree(root: ProcessIdentity | None) -> tuple[list[psutil.Process], list[dict[str, object]]]:
    if root is None:
        return [], [{"pid": None, "reason": "root-identity-unavailable"}]
    notes: list[dict[str, object]] = []
    try:
        process = psutil.Process(root.pid)
        if process.create_time() != root.create_time:
            return [], [{"pid": root.pid, "reason": "pid-reused"}]
        members = [process, *process.children(recursive=True)]
    except psutil.Error as error:
        return [], [{"pid": root.pid, "reason": type(error).__name__}]
    live = []
    for member in members:
        try:
            _identity(member)
            live.append(member)
        except psutil.Error as error:
            notes.append({"pid": member.pid, "reason": type(error).__name__})
    return live, notes


def _rss_snapshot(root: ProcessIdentity | None) -> dict[str, object]:
    """Cheap sampler read: deliberately never requests USS."""
    members, notes = process_tree(root)
    total = 0
    identities = []
    for process in members:
        try:
            identity = _identity(process)
            total += process.memory_info().rss
            identities.append(identity)
        except psutil.Error as error:
            notes.append({"pid": process.pid, "reason": type(error).__name__})
    status = "measured" if identities and not notes else "partial" if identities else "unavailable"
    return {
        "status": status,
        "value": total if identities else None,
        "processes": identities,
        "notes": notes,
        "monotonic_ns": time.monotonic_ns(),
    }


def endpoint_process_memory(root: ProcessIdentity | None) -> dict[str, object]:
    """Read independent RSS and endpoint-only USS for a pinned tree."""
    members, notes = process_tree(root)
    rss = uss = 0
    identities: list[dict[str, object]] = []
    rss_read = uss_read = 0
    rss_missing: list[dict[str, object]] = []
    uss_missing: list[dict[str, object]] = []
    for process in members:
        try:
            identities.append(_identity(process))
        except psutil.Error as error:
            notes.append({"pid": process.pid, "reason": type(error).__name__})
            continue
        try:
            rss += process.memory_info().rss
            rss_read += 1
        except psutil.Error as error:
            rss_missing.append({"pid": process.pid, "reason": type(error).__name__})
        try:
            uss += process.memory_full_info().uss
            uss_read += 1
        except (AttributeError, psutil.Error) as error:
            uss_missing.append({"pid": process.pid, "reason": type(error).__name__})
    intended = len(identities)
    rss_status = (
        "measured" if intended and rss_read == intended and not notes else "partial" if rss_read else "unavailable"
    )
    uss_status = (
        "measured" if intended and uss_read == intended and not notes else "partial" if uss_read else "unavailable"
    )
    root_record = {"pid": root.pid, "create_time": root.create_time} if root else None
    return {
        "root": root_record,
        "rss": {"status": rss_status, "value": rss if rss_read else None, "missing": [*notes, *rss_missing]},
        "uss": {"status": uss_status, "value": uss if uss_read else None, "missing": [*notes, *uss_missing]},
        "rss_bytes": rss if rss_status == "measured" else None,
        "rss_partial_bytes": rss if rss_status == "partial" else None,
        "uss_bytes": uss if uss_status == "measured" else None,
        "uss_partial_bytes": uss if uss_status == "partial" else None,
        "uss_missing": uss_missing,
        "processes": identities,
        "process_notes": [*notes, *rss_missing],
        "observed_monotonic_ns": time.monotonic_ns(),
    }


@dataclass
class ServerSampler:
    root: ProcessIdentity | None
    interval_s: float = 0.05
    samples: list[dict[str, object]] = field(default_factory=list)
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None
    _error: BaseException | None = None

    def start(self) -> None:
        self._stop.clear()
        self._sample()
        self._thread = threading.Thread(target=self._run, name="citry-memory-sampler", daemon=True)
        self._thread.start()

    def _sample(self) -> None:
        self.samples.append(_rss_snapshot(self.root))

    def _run(self) -> None:
        try:
            while not self._stop.wait(self.interval_s):
                self._sample()
        except BaseException as error:
            self._error = error

    def stop(self) -> dict[str, object]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.interval_s * 4))
            if self._thread.is_alive():
                return {
                    "server": {
                        "root": ({"pid": self.root.pid, "create_time": self.root.create_time} if self.root else None),
                        "rss": _unavailable("sampling thread still running"),
                        "uss": _unavailable("sampling thread still running"),
                        "rss_bytes": None,
                        "uss_bytes": None,
                    },
                    "server_sampler_status": "incomplete",
                    "server_sampler_reason": "sampling thread did not stop before its deadline",
                    "server_sampled_peak_rss_bytes": None,
                    "server_samples": len(self.samples),
                }
        self._sample()
        endpoint = endpoint_process_memory(self.root)
        rss = [sample["value"] for sample in self.samples if isinstance(sample.get("value"), int)]
        times = [sample["monotonic_ns"] for sample in self.samples]
        gaps = [(right - left) / 1_000_000 for left, right in zip(times, times[1:], strict=False)]
        complete = self._error is None and all(sample["status"] == "measured" for sample in self.samples)
        return {
            "server": endpoint,
            "server_sampler_status": "complete" if complete else "incomplete",
            "server_sampler_reason": _reason(self._error) if self._error else None,
            "server_sampled_peak_rss_bytes": max(rss) if complete and rss else None,
            "server_sampled_partial_peak_rss_bytes": max(rss) if not complete and rss else None,
            "server_samples": len(self.samples),
            "server_sample_gap_ms_min": min(gaps) if gaps else None,
            "server_sample_gap_ms_max": max(gaps) if gaps else None,
            "server_sample_started_ns": times[0] if times else None,
            "server_sample_ended_ns": times[-1] if times else None,
            "server_sample_notes": [sample for sample in self.samples if sample["status"] != "measured"],
        }


def _safe_detach(session: Any) -> dict[str, object]:
    try:
        session.detach()
    except Exception as error:
        return _unavailable(_reason(error))
    return {"status": "measured"}


def _heap_after_gc(page_session: Any) -> dict[str, object]:
    """Force V8 garbage collection, then read the heap the page still retains.

    The second collection finishes work the first one leaves behind, such as
    objects freed by finalizers. Forcing collection changes the heap, browser
    memory and DOM counts any later reading would see, so it runs only after
    the page's last ordinary reading.
    """
    try:
        page_session.send("HeapProfiler.collectGarbage")
        page_session.send("HeapProfiler.collectGarbage")
        value = page_session.send("Runtime.getHeapUsage")
    except Exception as error:
        return _unavailable(_reason(error))
    return {
        "status": "measured",
        "used_bytes": value["usedSize"],
        "allocated_bytes": value["totalSize"],
        "collections": 2,
    }


def page_memory(
    page: Any,
    browser: Any,
    expected_browser_root: ProcessIdentity | None = None,
    expected_browser_version: tuple[str, str] | None = None,
) -> dict[str, object]:
    """Read browser RSS, heap and DOM counters with independent failures."""
    observed_ns = time.monotonic_ns()
    try:
        page_session = page.context.new_cdp_session(page)
    except Exception as error:
        page_session = None
        page_session_error = _reason(error)
    else:
        page_session_error = None
    try:
        browser_session = browser.new_browser_cdp_session()
    except Exception as error:
        browser_session = None
        browser_processes = _unavailable(_reason(error))
        browser_version = _unavailable(_reason(error))
        browser_detach = _unavailable("browser session was not created")
    else:
        root_identity = None
        try:
            records = browser_session.send("SystemInfo.getProcessInfo")["processInfo"]
            roots = [item for item in records if item.get("type") == "browser"]
            if len(roots) != 1:
                raise ValueError("CDP did not report exactly one browser process")
            root = psutil.Process(int(roots[0]["id"]))
            root_created = root.create_time()
            root_identity = {"pid": root.pid, "create_time": root_created, "name": root.name()}
            if expected_browser_root is not None and (
                root.pid != expected_browser_root.pid or root_created != expected_browser_root.create_time
            ):
                raise ValueError("CDP browser process identity changed after the blank baseline")
            descendants = {(item.pid, item.create_time()): item for item in root.children(recursive=True)}
            processes = []
            missing = []
            rss = 0
            for item in records:
                pid = int(item["id"])
                process = (
                    root
                    if pid == root.pid
                    else next((value for (candidate, _), value in descendants.items() if candidate == pid), None)
                )
                if process is None:
                    missing.append({"pid": pid, "reason": "not-browser-descendant"})
                    continue
                try:
                    identity = _identity(process)
                    rss += process.memory_info().rss
                    processes.append((process, identity))
                except psutil.Error as error:
                    missing.append({"pid": pid, "reason": type(error).__name__})
            status = "measured" if processes and not missing else "partial" if processes else "unavailable"
            browser_processes = {
                "status": status,
                "value": rss if processes else None,
                "rss_bytes": rss if status == "measured" else None,
                "rss_partial_bytes": rss if status == "partial" else None,
                "root": _identity(root),
                "processes": [identity for _, identity in processes],
                "missing": missing,
            }
            try:
                version = browser_session.send("Browser.getVersion")
                identity = (version.get("product"), version.get("protocolVersion"))
                if not all(isinstance(item, str) for item in identity):
                    raise ValueError("CDP browser version response is incomplete")
                if expected_browser_version is not None and identity != expected_browser_version:
                    raise ValueError("CDP browser or protocol version changed after the blank baseline")
                browser_version = {"status": "measured", "product": identity[0], "protocol_version": identity[1]}
            except Exception as error:
                browser_version = _unavailable(_reason(error))
        except Exception as error:
            browser_processes = _unavailable(_reason(error))
            if root_identity is not None:
                browser_processes["root"] = root_identity
            browser_version = _unavailable("browser process discovery failed before version query")
        finally:
            browser_detach = _safe_detach(browser_session)
    if page_session is None:
        heap = _unavailable(page_session_error or "page CDP session unavailable")
        dom = _unavailable(page_session_error or "page CDP session unavailable")
    else:
        try:
            value = page_session.send("Runtime.getHeapUsage")
            heap = {"status": "measured", "used_bytes": value["usedSize"], "allocated_bytes": value["totalSize"]}
        except Exception as error:
            heap = _unavailable(_reason(error))
        try:
            value = page_session.send("Memory.getDOMCounters")
            dom = {
                "status": "measured",
                "documents": value["documents"],
                "nodes": value["nodes"],
                "listeners": value["jsEventListeners"],
            }
        except Exception as error:
            dom = _unavailable(_reason(error))
        page_detach = _safe_detach(page_session)
    statuses = {browser_processes["status"], heap["status"], dom["status"]}
    return {
        "status": "measured" if statuses == {"measured"} else "partial" if "measured" in statuses else "unavailable",
        "browser_processes": browser_processes,
        "browser_version": browser_version,
        "browser_session_detach": browser_detach,
        "page_session_detach": page_detach
        if page_session is not None
        else _unavailable("page session was not created"),
        "heap": heap,
        "dom": dom,
        "browser_rss_bytes": browser_processes.get("rss_bytes"),
        "browser_rss_partial_bytes": browser_processes.get("rss_partial_bytes"),
        "heap_used_bytes": heap.get("used_bytes"),
        "heap_allocated_bytes": heap.get("allocated_bytes"),
        "documents": dom.get("documents"),
        "nodes": dom.get("nodes"),
        "listeners": dom.get("listeners"),
        "observed_monotonic_ns": observed_ns,
    }


def with_deltas(value: dict[str, object], baseline: dict[str, object], prefix: str) -> dict[str, object]:
    result = dict(value)
    for key in ("rss_bytes", "uss_bytes", "browser_rss_bytes", "heap_used_bytes", "heap_allocated_bytes"):
        current, origin = value.get(key), baseline.get(key)
        result[f"{key}_{prefix}_delta"] = (
            current - origin if isinstance(current, int) and isinstance(origin, int) else None
        )
    return result


class SessionMemoryObserver:
    def __init__(
        self,
        path: Any,
        info: dict[str, object],
        server: ProcessIdentity | None,
        idle_server: dict[str, object],
        browser: Any,
    ):
        self.path, self.info, self.server = path, info, server
        self.idle_server, self.browser = idle_server, browser
        self.blank_browser: dict[str, object] | None = None
        self.browser_root: ProcessIdentity | None = None
        self.browser_version: tuple[str, str] | None = None
        self.previous: dict[str, object] | None = None
        self.sampler: ServerSampler | None = None
        self.pending: dict[str, object] | None = None
        # Whether the pending observation is the page's last one, which alone
        # takes the after-GC heap reading.
        self.pending_reads_heap_after_gc = False

    def establish_blank_browser(self, page: Any) -> None:
        self.blank_browser = page_memory(page, self.browser)
        browser_processes = self.blank_browser.get("browser_processes", {})
        if isinstance(browser_processes, dict):
            root = browser_processes.get("root")
            if (
                isinstance(root, dict)
                and isinstance(root.get("pid"), int)
                and isinstance(root.get("create_time"), float)
            ):
                self.browser_root = ProcessIdentity(root["pid"], root["create_time"])
        version = self.blank_browser.get("browser_version", {})
        if isinstance(version, dict) and version.get("status") == "measured":
            self.browser_version = (version["product"], version["protocol_version"])

    def begin(
        self,
        operation: str,
        page: Any,
        action: str,
        warmup: bool,
        cycle: int | None,
        *,
        read_heap_after_gc: bool = False,
    ) -> None:
        """Start one observation.

        Pass ``read_heap_after_gc=True`` for the page's last observation, which
        the caller follows with ``read_heap_after_gc``. If that observation
        fails before the reading, ``finish`` records why it is missing.
        """
        self.pending_reads_heap_after_gc = read_heap_after_gc
        self.pending = {
            **self.info,
            "operation": operation,
            "action": action,
            "cycle": cycle,
            "warmup": warmup,
            "status": "invalid",
        }
        try:
            if self.blank_browser is None:
                self.establish_blank_browser(page)
            self.sampler = ServerSampler(self.server)
            self.sampler.start()
        except Exception as error:
            self.sampler = None
            self.pending["server_sampler_status"] = "incomplete"
            self.pending["server_sampler_reason"] = _reason(error)
            self.pending["server"] = {
                "rss": _unavailable(_reason(error)),
                "uss": _unavailable(_reason(error)),
                "rss_bytes": None,
                "uss_bytes": None,
            }

    def at_layout(self, operation: str, page: Any, ready: dict[str, object]) -> None:
        """Record memory at the layout endpoint.

        The heap after forced garbage collection is a separate step,
        ``read_heap_after_gc``, because the caller must first finish reading
        the observation's response bodies.
        """
        if self.pending is None:
            raise AssertionError("memory observation was not started")
        if self.sampler is not None:
            try:
                sample = self.sampler.stop()
            except Exception as error:
                sample = {
                    "server_sampler_status": "incomplete",
                    "server_sampler_reason": _reason(error),
                    "server": {
                        "rss": _unavailable(_reason(error)),
                        "uss": _unavailable(_reason(error)),
                        "rss_bytes": None,
                        "uss_bytes": None,
                    },
                }
            finally:
                self.sampler = None
            self.pending.update(sample)
        try:
            browser = page_memory(page, self.browser, self.browser_root, self.browser_version)
        except Exception as error:
            browser = {
                "status": "unavailable",
                "browser_processes": _unavailable(_reason(error)),
                "heap": _unavailable(_reason(error)),
                "dom": _unavailable(_reason(error)),
            }
        server = self.pending.get("server", {})
        assert isinstance(server, dict)
        self.pending["server"] = with_deltas(server, self.idle_server, "idle_server")
        if self.previous is not None:
            self.pending["server"] = with_deltas(self.pending["server"], self.previous["server"], "previous_action")
        self.pending["browser"] = with_deltas(browser, self.blank_browser or {}, "blank_browser")
        self.pending["revision"] = ready.get("state", {}).get("revision")
        self.pending["observed_monotonic_ns"] = time.monotonic_ns()

    def read_heap_after_gc(self, operation: str, page: Any) -> None:
        """Force V8 garbage collection on the page's last observation and read the heap again.

        Call it only after the observation's ordinary readings and its network
        accounting: collecting earlier would lower every later heap reading on
        the page, and Chromium drops some already-received script bodies when
        garbage is collected, so reading them afterwards fails.
        """
        if self.pending is None or "browser" not in self.pending:
            raise AssertionError("memory observation has no layout reading")
        try:
            session = page.context.new_cdp_session(page)
        except Exception as error:
            heap_after_gc = _unavailable(_reason(error))
        else:
            heap_after_gc = _heap_after_gc(session)
            _safe_detach(session)
        browser = self.pending["browser"]
        assert isinstance(browser, dict)
        # These keys appear only on an observation that asked for the reading,
        # so a report can tell "not requested" from "failed".
        browser.update(
            {
                "heap_after_gc": heap_after_gc,
                "heap_after_gc_used_bytes": heap_after_gc.get("used_bytes"),
                "heap_after_gc_allocated_bytes": heap_after_gc.get("allocated_bytes"),
            }
        )

    def finish(self, operation: str, status: str, error: str | None) -> None:
        if self.sampler is not None:
            try:
                stopped = self.sampler.stop()
            except Exception as sampling_error:
                stopped = {
                    "server_sampler_status": "incomplete",
                    "server_sampler_reason": _reason(sampling_error),
                    "server": {
                        "rss": _unavailable(_reason(sampling_error)),
                        "uss": _unavailable(_reason(sampling_error)),
                        "rss_bytes": None,
                        "uss_bytes": None,
                    },
                }
            self.sampler = None
            if self.pending is not None:
                self.pending.update(stopped)
        if self.pending is None:
            return
        browser = self.pending.get("browser")
        if self.pending_reads_heap_after_gc and not (isinstance(browser, dict) and "heap_after_gc" in browser):
            # The observation stopped before the after-GC reading, for example
            # when a response or assertion failed. Record why instead of
            # leaving the key out, which reads as "never requested".
            skipped = _unavailable(f"observation ended with status {status!r} before the after-GC reading")
            browser = browser if isinstance(browser, dict) else {}
            browser.update(
                {
                    "heap_after_gc": skipped,
                    "heap_after_gc_used_bytes": None,
                    "heap_after_gc_allocated_bytes": None,
                }
            )
            self.pending["browser"] = browser
        self.pending_reads_heap_after_gc = False
        self.pending["status"] = "ok" if status == "ok" else "invalid"
        self.pending["scenario_status"] = status
        if error:
            self.pending["error"] = error
        append(self.path, self.pending)
        if self.pending["status"] == "ok":
            self.previous = self.pending
        self.pending = None
