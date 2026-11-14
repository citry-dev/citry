"""
Tests for the JSON depth check that runs before Citry parses request text.

Python's JSON parser uses one C call per nesting level. In a thread with a
small stack, CPython 3.12 and 3.13 can crash the whole process on deep text
instead of raising ``RecursionError``, so Citry checks the depth on the text
first. The thread tests run in a child process, so a crash shows up as a
failed test instead of stopping the test run.
"""

import dataclasses
import json
import random
import subprocess
import sys
import textwrap
import tracemalloc

import pytest

from citry._protocol.events import MAX_JSON_DEPTH, JsonNestingError, check_json_depth, loads_strict_json

from ._growth import assert_grows_in_step

# Deep enough to crash CPython 3.12 and 3.13 in a 512 KiB thread (4,000
# levels already does), and still small enough to build quickly.
_CRASH_DEPTH = 100_000


def _nested(depth):
    return "[" * depth + "]" * depth


def _deepest_outside_strings(text):
    """Return the deepest bracket nesting outside JSON strings, reading one character at a time."""
    depth = deepest = 0
    in_string = escaped = False
    for character in text:
        if in_string:
            # A backslash takes the next character with it, whatever it is.
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            deepest = max(deepest, depth)
        elif character in "]}":
            depth -= 1
    return deepest


class TestCheckJsonDepth:
    def test_the_limit_is_200_levels(self):
        assert MAX_JSON_DEPTH == 200
        check_json_depth(_nested(200))
        with pytest.raises(JsonNestingError):
            check_json_depth(_nested(201))

    def test_objects_and_arrays_both_count(self):
        check_json_depth('{"a":' * 100 + "[" * 100 + "]" * 100 + "}" * 100)
        with pytest.raises(JsonNestingError):
            check_json_depth('{"a":' * 101 + "[" * 100 + "]" * 100 + "}" * 101)

    @pytest.mark.parametrize("kind", [str, bytes, bytearray])
    def test_text_bytes_and_bytearray_are_checked_alike(self, kind):
        deep = _nested(300)
        data = deep if kind is str else kind(deep.encode())
        with pytest.raises(JsonNestingError):
            check_json_depth(data)

    def test_brackets_inside_strings_do_not_count(self):
        check_json_depth('["' + "[" * 1000 + '"]')
        # An escaped quote does not end the string, so the brackets after it
        # are still text.
        check_json_depth('["\\"' + "{" * 1000 + '"]')

    def test_many_shallow_containers_pass(self):
        check_json_depth("[" + ",".join(["{}"] * 10_000) + "]")

    @pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"])
    def test_bytes_are_read_in_the_encoding_the_parser_detects(self, encoding):
        # In UTF-16 an escaped quote is `\\ 00 " 00`; read as raw bytes the
        # scanner would end the string early and miss the brackets after it.
        text = '["\\"",' + "[" * 1000 + '"'
        with pytest.raises(JsonNestingError):
            check_json_depth(text.encode(encoding))
        check_json_depth(_nested(200).encode(encoding))

    def test_text_that_is_not_json_is_left_to_the_parser(self):
        check_json_depth(12345)  # type: ignore[arg-type]

    def test_the_scan_takes_linear_time(self):
        def texts(units):
            return (
                # Brackets that never nest deeply.
                "[]" * units,
                # An unterminated string full of escapes. A string with no
                # closing quote runs to the end, so its brackets are text.
                '"' + "\\[" * units,
                # An unterminated string full of escaped quotes, after enough
                # brackets to need the scan: no escaped quote may start a new
                # scan to the end of the text.
                "[" * 200 + '"' + '\\"' * units,
                "[" * 201 + '"' + '\\"' * units,
            )

        def scan(texts):
            *shallow, too_deep = texts
            for text in shallow:
                check_json_depth(text)
            with pytest.raises(JsonNestingError):
                check_json_depth(too_deep)

        # Eight times as much text, up to a megabyte, may take about eight
        # times as long.
        assert_grows_in_step(scan, texts(62_500), texts(500_000), factor=8)

    @pytest.mark.parametrize(
        "body",
        ["a" * 1_000_000, "\\a" * 500_000, "[]" * 500_000, '\\"' * 500_000],
        ids=["plain", "escapes", "brackets", "escaped-quotes"],
    )
    @pytest.mark.parametrize("closed", [True, False], ids=["closed", "unclosed"])
    def test_a_long_string_costs_about_one_copy_of_the_text(self, body, closed):
        # Enough brackets outside the string make the full scan run. The
        # string is removed before counting, which copies the text once.
        text = "[" * 150 + "]" * 150 + "[" * 60 + '"' + body + ('"' + "]" * 60 if closed else "")
        tracemalloc.start()
        try:
            check_json_depth(text)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        assert peak < 3 * len(text)

    def test_the_scan_agrees_with_a_character_by_character_reading(self):
        # Random text built from the characters the scan cares about, with a
        # small limit so that both answers come up often.
        rng = random.Random(8)  # noqa: S311 - test data, not secrets
        alphabet = '[]{}"\\a,\n'
        for _ in range(20_000):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(40)))
            limit = rng.randrange(4)
            expected = _deepest_outside_strings(text) > limit
            try:
                check_json_depth(text, limit)
            except JsonNestingError:
                refused = True
            else:
                refused = False
            assert refused == expected, (text, limit)

    def test_strict_parsing_refuses_deep_text(self):
        assert loads_strict_json(_nested(5)) == [[[[[]]]]]
        with pytest.raises(JsonNestingError):
            loads_strict_json(_nested(_CRASH_DEPTH))


def test_state_too_deep_for_a_token_is_refused_when_the_token_is_made():
    # A token whose payload verification would refuse could never be used,
    # so making one fails with a message that names the component.
    from citry.ext.events.tokens import mint_state_token

    @dataclasses.dataclass
    class Deep:
        value: object

    value: object = 1
    for _ in range(199):
        value = [value]
    with pytest.raises(ValueError, match="nests lists and dicts too deeply"):
        mint_state_token(Deep(value), class_id="c1", secret="s" * 40, max_age=None, max_bytes=None)


# The child process builds a small app, then sends each request from a
# thread whose stack is 512 KiB, the size that crashes CPython 3.12 and 3.13.
_THREAD_SCRIPT = textwrap.dedent(
    """
    import base64
    import io
    import json
    import sys
    import threading
    from urllib.parse import quote

    from citry import Citry, Component
    from citry.contrib.wsgi import wsgi_app
    from citry.ext.events import event

    depth = int(sys.argv[1])
    app = Citry(
        secret="s" * 40,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    app.set_mounted_prefix("/citry")


    class Probe(Component):
        citry = app
        template = "<p>p</p>"

        class State:
            count: int = 0

        class Events:
            def save(self):
                return None

            @event(methods=("GET",))
            def peek(self, state):
                return {"count": state.count}


    deep = "[" * depth + "]" * depth
    # The i18n route refuses a body over 64 KiB before parsing it, so its
    # body stays under that while still nesting far past the limit.
    i18n_depth = min(depth, 20_000)
    deep_i18n = "[" * i18n_depth + "]" * i18n_depth
    payload = base64.urlsafe_b64encode(deep.encode()).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(b"x" * 32).rstrip(b"=").decode()
    forged = f"cev1.{payload}.{signature}"
    requests = {
        "events body": ("POST", "/ext/events/call", "", "application/citry-events+json", deep),
        "flat json body": (
            "POST",
            f"/ext/events/e/{Probe.class_id}/save",
            "",
            "application/json",
            deep,
        ),
        "state token in a GET query": (
            "GET",
            f"/ext/events/e/{Probe.class_id}/peek",
            "_citry_state_token=" + quote(forged),
            "",
            "",
        ),
        "i18n messages": ("POST", "/ext/i18n/messages", "", "application/json", deep_i18n),
    }
    citry_wsgi = wsgi_app(app)
    results = {}


    def send(name, method, path, query, content_type, body):
        data = body.encode()
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "SCRIPT_NAME": "/citry",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "80",
            "HTTP_HOST": "localhost",
            "HTTP_ORIGIN": "http://localhost",
            "HTTP_SEC_FETCH_SITE": "same-origin",
            "HTTP_X_CITRY_EVENTS": "1",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(len(data)),
            "wsgi.input": io.BytesIO(data),
            "wsgi.url_scheme": "http",
            "wsgi.errors": io.StringIO(),
        }
        statuses = []
        body = b"".join(citry_wsgi(environ, lambda status, _headers: statuses.append(status)))
        results[name] = [int(statuses[0].split()[0]), body.decode(errors="replace")[:300]]


    threading.stack_size(512 * 1024)
    for name, request in requests.items():
        thread = threading.Thread(target=send, args=(name, *request))
        thread.start()
        thread.join()
    print(json.dumps(results))
    """
)


def _run_in_small_thread(depth):
    completed = subprocess.run(
        [sys.executable, "-c", _THREAD_SCRIPT, str(depth)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    # A crash ends the child with a signal before it prints anything.
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout.strip().splitlines()[-1])


def test_deep_request_json_is_refused_in_a_thread_with_a_small_stack():
    results = _run_in_small_thread(_CRASH_DEPTH)
    # The batch route answers protocol errors inside a 200 envelope.
    assert results["events body"][0] == 200
    assert '"status":400,"code":"protocol_mismatch"' in results["events body"][1]
    assert results["flat json body"][0] == 400
    assert '"status":400,"code":"protocol_mismatch"' in results["flat json body"][1]
    # A token Citry cannot read answers invalid_state, as any malformed one does.
    assert results["state token in a GET query"][0] == 403
    assert '"code":"invalid_state"' in results["state token in a GET query"][1]
    assert results["i18n messages"][0] == 400
    assert "200 levels deep" in results["i18n messages"][1]


def test_shallow_request_json_gets_past_the_check():
    # These bodies are valid but shallow JSON of the wrong shape, so each
    # route answers with its usual shape error, which it can only give after
    # parsing the text.
    results = _run_in_small_thread(3)
    assert "must be a JSON object" in results["events body"][1]
    assert "must be a JSON object" in results["flat json body"][1]
    assert results["i18n messages"][0] == 400
    assert "i18n browser request has unknown or missing fields" in results["i18n messages"][1]
