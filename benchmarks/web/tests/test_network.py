"""Reject byte accounting that would hide missing or late responses."""

from citry_bench.network import Network, latency_phase, server_prepare_duration, server_timing_duration


class Response:
    status = 200

    def all_headers(self):
        return {"x-bench-operation": "op", "x-bench-revision": "1"}

    def body(self):
        return "héllo".encode()


class Request:
    url = "http://localhost/event"
    method = "POST"
    resource_type = "fetch"
    post_data_buffer = "é".encode()
    timing = {}

    def response(self):
        return Response()

    def sizes(self):
        return {"requestBodySize": 2, "responseBodySize": 6}


def collector():
    network = Network.__new__(Network)
    request = Request()
    network.origin = "localhost"
    network.transport = "http"
    network.requests = [{"request": request, "operation": "op"}]
    network.finished = {request}
    network.failed = {}
    network.raw = [
        {
            "event": "responseReceived",
            "operation": "op",
            "value": {
                "requestId": "request-1",
                "response": {"url": Request.url, "protocol": "http/1.1"},
            },
        },
        {
            "event": "responseReceivedExtraInfo",
            "operation": "op",
            "value": {
                "requestId": "request-1",
                "statusCode": 200,
            },
        },
    ]
    network.sockets = []
    return network


def test_unicode_body_sizes_are_bytes():
    network = collector()
    result = network.collect(
        "op", {"end": 100, "revision": 1}, {"resources": [{"name": Request.url, "responseEnd": 90}], "navigation": []}
    )
    assert result["errors"] == []
    assert result["request_body_bytes"] == 2
    assert result["decoded_response_bytes"] == 6
    assert result["wire_bytes"] is None
    assert result["latency_phase"]["status"] == "unavailable"
    assert result["server_prepare_status"] == "missing"


def test_late_response_is_rejected_even_if_finished_before_collection():
    network = collector()
    result = network.collect(
        "op", {"end": 100, "revision": 1}, {"resources": [{"name": Request.url, "responseEnd": 110}], "navigation": []}
    )
    assert result["encoded_response_body_bytes"] is None
    assert "within the operation" in str(result["errors"])


def test_wrong_acknowledged_revision_is_rejected():
    result = collector().collect(
        "op", {"end": 100, "revision": 2}, {"resources": [{"name": Request.url, "responseEnd": 90}], "navigation": []}
    )
    assert "differs from ready revision" in str(result["errors"])


def test_previous_same_url_entry_cannot_complete_current_request():
    network = collector()
    previous = Request()
    network.requests.insert(0, {"request": previous, "operation": "old"})
    network.finished.add(previous)
    result = network.collect(
        "op",
        {"start": 50, "end": 75, "revision": 1},
        {
            "resources": [{"name": Request.url, "startTime": 1, "responseEnd": 5}],
            "navigation": [],
        },
    )
    assert "Missing Resource Timing occurrence" in str(result["errors"])
    assert result["decoded_response_bytes"] is None


def test_resource_from_before_click_cannot_complete_action():
    result = collector().collect(
        "op",
        {"start": 50, "end": 75, "revision": 1},
        {
            "resources": [{"name": Request.url, "startTime": 1, "responseEnd": 5}],
            "navigation": [],
        },
    )
    assert "within the operation" in str(result["errors"])


def test_missing_protocol_evidence_cannot_prove_identity_transfer():
    network = collector()
    network.raw = []
    result = network.collect(
        "op",
        {"end": 100, "revision": 1},
        {
            "resources": [{"name": Request.url, "responseEnd": 90}],
            "navigation": [],
        },
    )
    assert "CDP response evidence" in str(result["errors"])
    assert result["encoded_response_body_bytes"] is None


def test_initial_and_action_phases_sum_to_the_browser_endpoint():
    initial = latency_phase(
        "initial",
        {"start": 0, "end": 100},
        [],
        [
            (
                {"resource_type": "document", "server_timing": "application;dur=20"},
                {"requestStart": 10, "responseStart": 40, "responseEnd": 50},
            )
        ],
        None,
    )
    assert initial == {
        "kind": "initial-http",
        "status": "measured",
        "reason": None,
        "segments": [
            {"key": "browser_before", "ms": 10},
            {"key": "server", "ms": 20},
            {"key": "exchange_residual", "ms": 10},
            {"key": "response_receive", "ms": 10},
            {"key": "browser_after", "ms": 50},
        ],
    }
    action = latency_phase(
        "op",
        {"start": 10, "end": 50},
        [],
        [
            (
                {"server_timing": "application;dur=5"},
                {"requestStart": 15, "responseStart": 30, "responseEnd": 35},
            )
        ],
        None,
    )
    assert sum(segment["ms"] for segment in action["segments"]) == 40
    assert action["segments"] == [
        {"key": "browser_before", "ms": 5},
        {"key": "server", "ms": 5},
        {"key": "exchange_residual", "ms": 10},
        {"key": "response_receive", "ms": 5},
        {"key": "browser_after", "ms": 15},
    ]


def test_websocket_phase_has_no_invented_response_receipt():
    socket = {
        "messages": [
            {"direction": "sent", "at": 15},
            {"direction": "received", "at": 35, "server_ms": 8},
        ]
    }
    phase = latency_phase("op", {"start": 10, "end": 50}, [], [], socket)
    assert phase["status"] == "measured"
    assert phase["segments"] == [
        {"key": "browser_before", "ms": 5},
        {"key": "server", "ms": 8},
        {"key": "exchange_residual", "ms": 12},
        {"key": "browser_after", "ms": 15},
    ]


def test_ambiguous_or_inconsistent_phase_is_wholly_unclassified():
    ready = {"start": 10, "end": 50}
    ambiguous = latency_phase(
        "op",
        ready,
        [],
        [
            (
                {"server_timing": "application;dur=5"},
                {"requestStart": 15, "responseStart": 30, "responseEnd": 35},
            )
        ]
        * 2,
        None,
    )
    assert ambiguous["status"] == "unavailable"
    assert ambiguous["segments"] == [{"key": "unclassified", "ms": 40}]
    overlapping = latency_phase(
        "op",
        ready,
        [],
        [
            (
                {"server_timing": "application;dur=5"},
                {"requestStart": 15, "responseStart": 18, "responseEnd": 35},
            )
        ],
        None,
    )
    assert overlapping["status"] == "unavailable"
    assert "overlap" in overlapping["reason"]


def test_prepare_metric_sums_outputs_and_rejects_invalid_values_without_zero_fill():
    assert server_timing_duration(
        [{"header": "application;dur=9, prepare;dur=1.25"}, {"prepare_ms": 2.75}], "prepare"
    ) == (4, "measured", None)
    missing = server_timing_duration([{"header": "application;dur=9"}], "prepare")
    assert missing[0] is None
    assert missing[1] == "missing"
    invalid = server_timing_duration([{"header": "prepare;dur=-1"}], "prepare")
    assert invalid[0] is None
    assert invalid[1] == "invalid"
    incomplete = server_prepare_duration([{"prepare_ms": 2}], ["missing serializer span"])
    assert incomplete == (None, "invalid", "missing serializer span")
