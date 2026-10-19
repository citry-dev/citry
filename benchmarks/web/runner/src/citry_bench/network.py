"""Collect passive HTTP evidence; unsupported byte definitions stay explicit."""

import math
import re
from urllib.parse import urlsplit

from playwright.sync_api import Error, Page, Request

from citry_bench.sockets import collect_sockets


def server_timing_duration(entries: list[dict], metric: str) -> tuple[float | None, str, str | None]:
    """Read one named duration from each response or correlated socket record."""
    values = []
    for entry in entries:
        matches = re.findall(rf"(?:^|,)\s*{re.escape(metric)}\s*;\s*dur=([^;,\s]+)", entry.get("header") or "")
        if len(matches) > 1:
            return None, "invalid", f"duplicate {metric} timing in one response"
        direct = entry.get(metric + "_ms")
        candidates = [*matches, *([] if direct is None else [direct])]
        for candidate in candidates:
            try:
                value = float(candidate)
            except (TypeError, ValueError):
                return None, "invalid", f"{metric} timing is not numeric"
            if not math.isfinite(value) or value < 0:
                return None, "invalid", f"{metric} timing must be finite and nonnegative"
            values.append(value)
    if not values:
        return None, "missing", f"{metric} timing is missing"
    return sum(values), "measured", None


def server_prepare_duration(
    entries: list[dict], errors: list[str] | None = None
) -> tuple[float | None, str, str | None]:
    if errors:
        return None, "invalid", "; ".join(errors)
    return server_timing_duration(entries, "prepare")


def _unavailable_phase(ready: dict, kind: str, reason: str) -> dict:
    elapsed = ready.get("end", 0) - ready.get("start", 0)
    return {
        "kind": kind,
        "status": "unavailable",
        "reason": reason,
        "segments": [{"key": "unclassified", "ms": elapsed}],
    }


def _phase(kind: str, ready: dict, values: list[tuple[str, float]]) -> dict:
    elapsed = ready.get("end", 0) - ready.get("start", 0)
    if not math.isfinite(elapsed) or elapsed < 0:
        return _unavailable_phase(ready, kind, "the browser interval is invalid")
    if any(not math.isfinite(value) or value < 0 for _, value in values):
        return _unavailable_phase(ready, kind, "phase boundaries overlap or are invalid")
    if not math.isclose(sum(value for _, value in values), elapsed, abs_tol=1e-6):
        return _unavailable_phase(ready, kind, "phase durations do not compose the browser interval")
    return {
        "kind": kind,
        "status": "measured",
        "reason": None,
        "segments": [{"key": key, "ms": value} for key, value in values],
    }


def latency_phase(
    operation: str,
    ready: dict,
    records: list[dict],
    resource_entries: list[tuple[dict, dict]],
    socket_result: dict | None,
) -> dict:
    """Compose only browser-clock intervals and explicit server durations."""
    if operation == "initial":
        documents = [(record, entry) for record, entry in resource_entries if record["resource_type"] == "document"]
        if len(documents) != 1:
            return _unavailable_phase(ready, "initial-http", "the main document exchange is missing or ambiguous")
        document, entry = documents[0]
        application, status, reason = server_timing_duration(
            [{"header": document.get("server_timing", "")}], "application"
        )
        if status != "measured":
            return _unavailable_phase(ready, "initial-http", reason or "main document server timing is unavailable")
        try:
            start = float(ready["start"])
            end = float(ready["end"])
            request_start = float(entry["requestStart"])
            response_start = float(entry["responseStart"])
            response_end = float(entry["responseEnd"])
        except (KeyError, TypeError, ValueError):
            return _unavailable_phase(ready, "initial-http", "main document Resource Timing is incomplete")
        return _phase(
            "initial-http",
            ready,
            [
                ("browser_before", request_start - start),
                ("server", application),
                ("exchange_residual", response_start - request_start - application),
                ("response_receive", response_end - response_start),
                ("browser_after", end - response_end),
            ],
        )

    kind = "action-websocket" if socket_result is not None else "action-http"
    try:
        start = float(ready["start"])
        end = float(ready["end"])
    except (KeyError, TypeError, ValueError):
        return _unavailable_phase(ready, kind, "the browser interval is incomplete")
    if socket_result is not None:
        if records:
            return _unavailable_phase(ready, kind, "the action used both HTTP and WebSocket exchanges")
        outgoing = [entry for entry in socket_result["messages"] if entry["direction"] == "sent"]
        incoming = [entry for entry in socket_result["messages"] if entry["direction"] == "received"]
        if len(outgoing) != 1 or len(incoming) != 1:
            return _unavailable_phase(ready, kind, "the WebSocket exchange is not a single request and response")
        application, status, reason = server_timing_duration(incoming, "server")
        if status != "measured":
            return _unavailable_phase(ready, kind, reason or "server application timing is unavailable")
        sent = outgoing[0]["at"]
        received = incoming[0]["at"]
        return _phase(
            kind,
            ready,
            [
                ("browser_before", sent - start),
                ("server", application),
                ("exchange_residual", received - sent - application),
                ("browser_after", end - received),
            ],
        )

    if len(resource_entries) != 1:
        return _unavailable_phase(ready, kind, "the HTTP exchange is missing or is not a single request")
    record, entry = resource_entries[0]
    application, status, reason = server_timing_duration([{"header": record.get("server_timing", "")}], "application")
    if status != "measured":
        return _unavailable_phase(ready, kind, reason or "server application timing is unavailable")
    try:
        request_start = float(entry["requestStart"])
        response_start = float(entry["responseStart"])
        response_end = float(entry["responseEnd"])
    except (KeyError, TypeError, ValueError):
        return _unavailable_phase(ready, kind, "action Resource Timing is incomplete")
    return _phase(
        kind,
        ready,
        [
            ("browser_before", request_start - start),
            ("server", application),
            ("exchange_residual", response_start - request_start - application),
            ("response_receive", response_end - response_start),
            ("browser_after", end - response_end),
        ],
    )


class Network:
    def __init__(self, page: Page):
        self.page = page
        self.operation = "initial"
        self.origin = None
        self.transport = "http"
        self.requests: list[dict] = []
        self.finished: set[Request] = set()
        self.failed: dict[Request, str] = {}
        self.raw: list[dict] = []
        self.sockets: list[dict] = []
        page.on("request", self._request)
        page.on("requestfinished", lambda request: self.finished.add(request))
        page.on("requestfailed", lambda request: self.failed.update({request: request.failure}))
        self.cdp = page.context.new_cdp_session(page)
        self.cdp.send("Network.enable")
        for name in (
            "requestWillBeSent",
            "responseReceived",
            "responseReceivedExtraInfo",
            "dataReceived",
            "loadingFinished",
            "loadingFailed",
            "requestServedFromCache",
        ):
            self.cdp.on("Network." + name, self._raw_handler(name))
        for name in (
            "webSocketCreated",
            "webSocketWillSendHandshakeRequest",
            "webSocketHandshakeResponseReceived",
            "webSocketFrameSent",
            "webSocketFrameReceived",
            "webSocketClosed",
            "webSocketFrameError",
        ):
            self.cdp.on("Network." + name, self._socket_handler(name))

    def _request(self, request: Request) -> None:
        self.requests.append({"request": request, "operation": self.operation})

    def _raw_handler(self, name: str):
        def record(value: dict) -> None:
            self.raw.append({"event": name, "operation": self.operation, "value": value})

        return record

    def _socket_handler(self, name: str):
        def record(value: dict) -> None:
            self.sockets.append({"event": name, "operation": self.operation, "value": value})

        return record

    def collect(self, operation: str, ready: dict, snapshot: dict, audit: dict | None = None) -> dict:
        records = []
        resource_entries = []
        errors = []
        server = []
        occurrences = {}
        for entry in self.requests:
            url = entry["request"].url
            occurrence = occurrences.get(url, 0)
            occurrences[url] = occurrence + 1
            if entry["operation"] != operation:
                continue
            request = entry["request"]
            row = {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "url_occurrence": occurrence,
            }
            if self.origin and urlsplit(request.url).netloc != self.origin:
                errors.append(f"Unexpected external resource: {request.url}")
            if request in self.failed:
                row["failure"] = self.failed[request]
                errors.append(f"Request failed: {request.url}: {request.failure}")
            elif request not in self.finished:
                # Do not wait until a late required response masks an early mark.
                row["failure"] = "unfinished-at-readiness-observation"
                errors.append(f"Request unfinished at readiness observation: {request.url}")
            else:
                try:
                    response = request.response()
                    if response is None:
                        raise ValueError("Finished request has no response")
                    sizes = request.sizes()
                    headers = response.all_headers()
                    body = b"" if 300 <= response.status < 400 else response.body()
                    request_body = request.post_data_buffer
                    row.update(
                        {
                            "status": response.status,
                            "decoded_response_bytes": len(body),
                            "request_body_bytes": len(request_body or b""),
                            "playwright_sizes": sizes,
                            "content_encoding": headers.get("content-encoding", "identity"),
                            "server_timing": headers.get("server-timing"),
                            "response_operation": headers.get("x-bench-operation"),
                            "response_revision": headers.get("x-bench-revision"),
                            "timing": request.timing,
                        }
                    )
                    if row["content_encoding"] != "identity":
                        errors.append(f"Unexpected compression: {row['content_encoding']}")
                    if 300 <= response.status < 400:
                        errors.append(f"Redirects require separate qualification: {request.url}")
                    if response.status >= 400:
                        errors.append(f"HTTP {response.status}: {request.url}")
                    if sizes["requestBodySize"] != row["request_body_bytes"]:
                        errors.append(f"Request body accounting differs: {request.url}")
                    if headers.get("server-timing"):
                        server.append({"url": request.url, "operation": operation, "header": headers["server-timing"]})
                except (Error, ValueError) as error:
                    row["failure"] = str(error)
                    errors.append(f"Cannot account for {request.url}: {error}")
            records.append(row)
        raw = [r for r in self.raw if r["operation"] == operation]
        cached = any(
            r["event"] == "requestServedFromCache"
            or r["event"] == "responseReceived"
            and (r["value"]["response"].get("fromDiskCache") or r["value"]["response"].get("fromServiceWorker"))
            for r in raw
        )
        sockets = [r for r in self.sockets if r["operation"] == operation]
        if sockets and self.transport != "websocket":
            errors.append("Persistent transport requires a qualified socket adapter and encoded-message meter")
        if any(r["event"] == "responseReceivedExtraInfo" and r["value"].get("statusCode") == 304 for r in raw):
            errors.append("Unexpected cache revalidation in the identity profile")
        protocols = {r["value"]["response"].get("protocol") for r in raw if r["event"] == "responseReceived"}
        received = [r["value"] for r in raw if r["event"] == "responseReceived"]
        extras = {r["value"]["requestId"] for r in raw if r["event"] == "responseReceivedExtraInfo"}
        for url in {record["url"] for record in records}:
            responses = [value for value in received if value["response"].get("url") == url]
            expected_count = sum(record["url"] == url for record in records)
            if len(responses) != expected_count or any(value["requestId"] not in extras for value in responses):
                errors.append(f"Missing or ambiguous CDP response evidence: {url}")
        if (records and not protocols) or protocols - {"http/1.1"}:
            errors.append(f"Unqualified HTTP protocol: {protocols}")
        if cached:
            errors.append("Unexpected cached response in the initial identity profile")
        # Resource entries use the same document clock as the stored ready mark.
        # Checking their end time prevents later Python collection from masking
        # a response that was still arriving when readiness was declared.
        entries = snapshot["resources"] + snapshot["navigation"]
        for record in records:
            matches = sorted(
                (entry for entry in entries if entry["name"] == record["url"]),
                key=lambda entry: entry.get("startTime", 0),
            )
            occurrence = record["url_occurrence"]
            if occurrence >= len(matches):
                errors.append(f"Missing Resource Timing occurrence {occurrence}: {record['url']}")
                continue
            current = matches[occurrence]
            resource_entries.append((record, current))
            if current["responseEnd"] > ready["end"] or current.get("startTime", 0) < ready.get("start", 0):
                errors.append(f"Resource completion is not evidenced within the operation: {record['url']}")
        if operation != "initial" and self.transport == "http":
            acknowledgements = [r for r in records if r.get("response_operation") == operation]
            if not acknowledgements:
                errors.append("No response acknowledges the measured operation")
            elif not any(str(r.get("response_revision")) == str(ready["revision"]) for r in acknowledgements):
                errors.append("Acknowledged response revision differs from ready revision")
        complete = not errors
        # Identity-only, uncached HTTP makes decoded and transferred body bytes equal.
        decoded = sum(r.get("decoded_response_bytes", 0) for r in records)
        result = {
            "operation": operation,
            "requests": records,
            "request_count": len(records),
            "decoded_response_bytes": decoded if complete else None,
            "encoded_response_body_bytes": decoded if complete else None,
            "request_body_bytes": sum(r.get("request_body_bytes", 0) for r in records) if complete else None,
            "byte_method": "identity HTTP bodies, uncached; Playwright body retrieval after readiness",
            "wire_bytes": None,
            "errors": errors,
            "server_timings": server,
            "cdp": raw,
            "sockets": sockets,
        }

        if self.transport == "websocket":
            if audit is None:
                raise ValueError("Socket accounting requires server audit evidence")
            socket_result = collect_sockets(self.sockets, ready, snapshot, audit)
            result["socket_accounting"] = socket_result
            result["errors"].extend(socket_result["errors"])
            result["server_timings"].extend(socket_result["server_timings"])
            for key in ("request_body_bytes", "decoded_response_bytes", "encoded_response_body_bytes"):
                result[key] = result[key] + socket_result[key] if not result["errors"] else None
            result["server_exchange_count"] = socket_result["sent_messages"]
            result["byte_method"] += "; " + socket_result["byte_method"]
        else:
            socket_result = None
            result["server_exchange_count"] = result["request_count"]
        preparation_errors = socket_result["preparation_errors"] if socket_result is not None else None
        server_prepare = server_prepare_duration(result["server_timings"], preparation_errors)
        result["server_prepare_ms"], result["server_prepare_status"], result["server_prepare_reason"] = server_prepare
        result["latency_phase"] = latency_phase(
            operation,
            ready,
            records,
            resource_entries,
            socket_result,
        )
        return result
