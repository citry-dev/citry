"""Check simple-name evaluation against the general sandbox and error path."""

from typing import Any

import pytest

import citry_core.safe_eval.error as error_module
import citry_core.safe_eval.eval as evaluator
from citry_core.safe_eval import SecurityError, safe_eval


def compile_both(source, monkeypatch):
    """Compile through each path without changing the variable interceptor."""
    candidate = safe_eval(source)
    assert candidate.__qualname__ == "_simple_name_evaluator.<locals>.evaluate"
    with monkeypatch.context() as patch:
        patch.setattr(evaluator, "_DEFAULT_VARIABLE", None)
        reference = safe_eval(source)
    assert reference.__qualname__ == "_exec_func_with_error_handling.<locals>.evaluate"
    assert candidate._source_code == reference._source_code
    return candidate, reference


def test_name_reads_current_mapping_once_per_call(monkeypatch):
    def check(compiled):
        lookups = []

        class Context(dict):
            def __getitem__(self, name):
                lookups.append(name)
                return super().__getitem__(name)

        context = Context(value=object())
        assert compiled(context) is context.get("value")
        context["value"] = object()
        assert compiled(context) is context.get("value")
        assert compiled({"value": 42}) == 42
        assert lookups == ["value", "value"]

    for compiled in compile_both("value", monkeypatch):
        check(compiled)


def test_name_preserves_compiled_key_identity(monkeypatch):
    source = "".join(["pro", "duct"])  # noqa: FLY002 - Exercise a source string constructed at runtime.
    candidate, reference = compile_both(source, monkeypatch)
    keys = []

    class Context(dict):
        def __getitem__(self, name):
            keys.append(name)
            return 42

    policy_names = []

    def policy(name):
        policy_names.append(name)
        return True

    monkeypatch.setattr(evaluator, "is_safe_variable", policy)
    # Each evaluator's positional and keyword call must pass the same constant.
    # The keyword call executes its own retained generated lambda.
    for compiled in (candidate, reference):
        assert compiled(Context()) == compiled(context=Context()) == 42
        assert keys[-2] is keys[-1]
        assert policy_names[-2] is policy_names[-1] is keys[-1]


def test_name_preserves_compiled_error_offsets(monkeypatch):
    source = "value" * 60
    candidate, reference = compile_both(source, monkeypatch)
    positions = []
    formatter = error_module.format_error_with_context

    def capture(error, text, start, end, kind):
        positions.append((text, start, end))
        return formatter(error, text, start, end, kind)

    monkeypatch.setattr(error_module, "format_error_with_context", capture)
    for compiled in (candidate, reference):
        with pytest.raises(KeyError):
            compiled({})
        with pytest.raises(KeyError):
            compiled(context={})
        assert positions[-2][0] is positions[-1][0] is source
        assert positions[-2][1] is positions[-1][1]
        assert positions[-2][2] is positions[-1][2]


@pytest.mark.parametrize("error_type", [KeyError, ValueError, StopIteration, KeyboardInterrupt])
@pytest.mark.parametrize("processed", [False, True])
def test_name_preserves_lookup_error_without_repeating_it(monkeypatch, error_type, processed):
    def check(compiled):
        failure = error_type("lookup failed")
        if processed:
            failure._error_processed = True
        lookups = []

        class Context(dict):
            def __getitem__(self, name):
                lookups.append(name)
                raise failure

        with pytest.raises(error_type) as raised:
            compiled(Context())
        assert raised.value is failure
        assert lookups == ["value"]
        return failure.args, getattr(failure, "_error_processed", False), failure.__cause__

    results = [check(compiled) for compiled in compile_both("value", monkeypatch)]
    assert results[0] == results[1]


@pytest.mark.parametrize("source", ["value", "_secret"])
def test_name_preserves_missing_and_private_errors(monkeypatch, source):
    results = []
    for compiled in compile_both(source, monkeypatch):
        with pytest.raises((KeyError, SecurityError)) as raised:
            compiled({})
        results.append((type(raised.value), raised.value.args))
    assert results[0] == results[1]


def test_name_policy_stays_live_and_runs_before_lookup(monkeypatch):
    compiled_functions = compile_both("value", monkeypatch)

    def check(compiled):
        events = []
        allowed = True

        class Context(dict):
            def __getitem__(self, name):
                events.append(("lookup", name))
                return 42

        def policy(name):
            events.append(("policy", name))
            return allowed

        monkeypatch.setattr(evaluator, "is_safe_variable", policy)
        assert compiled(Context()) == 42
        allowed = False
        with pytest.raises(SecurityError):
            compiled(Context())
        assert events == [("policy", "value"), ("lookup", "value"), ("policy", "value")]

    for compiled in compiled_functions:
        check(compiled)


def test_name_policy_failure_keeps_operation_context(monkeypatch):
    def check(compiled):
        failure = StopIteration("policy failed")

        def policy(name):
            raise failure

        monkeypatch.setattr(evaluator, "is_safe_variable", policy)
        with pytest.raises(StopIteration) as raised:
            compiled({"value": 42})
        assert raised.value is failure
        return failure.args

    results = [check(compiled) for compiled in compile_both("value", monkeypatch)]
    assert results[0] == results[1]


@pytest.mark.parametrize(
    ("args", "kwargs"),
    [
        ((), {"context": {"value": 42}}),
        ((), {}),
        (({}, {}), {}),
        (({},), {"context": {}}),
        ((), {"variables": {"value": 42}}),
        ((None,), {}),
    ],
)
def test_name_keeps_argument_binding_and_errors(monkeypatch, args, kwargs):
    results = []
    for compiled in compile_both("value", monkeypatch):
        try:
            result = compiled(*args, **kwargs)
        except TypeError as error:
            results.append((type(error), error.args))
        else:
            results.append(result)
    assert results[0] == results[1]


def test_name_extra_validator_stays_live():
    names = []
    allowed = True

    def validator(name):
        names.append(name)
        return allowed

    compiled = safe_eval("value", validate_variable=validator)
    assert compiled({"value": 42}) == 42
    allowed = False
    with pytest.raises(SecurityError):
        compiled({"value": 42})
    assert names == ["value", "value"]


def test_name_uses_substituted_interceptor(monkeypatch):
    calls = []

    def variable(context, source, token, name):
        calls.append((context, source, token, name))
        return 17

    monkeypatch.setattr(evaluator, "variable", variable)
    compiled = safe_eval("value")
    assert compiled({}) == 17
    assert calls == [({}, "value", (0, 5), "value")]


def test_name_operation_formatter_failure_gets_expression_context(monkeypatch):
    def check(compiled):
        calls = []
        failure = ValueError("formatter failed")

        def formatter(error, source, start, end, kind):
            calls.append((type(error), source, start, end, kind))
            raise failure

        monkeypatch.setattr(error_module, "format_error_with_context", formatter)
        with pytest.raises(ValueError, match="formatter failed") as raised:
            compiled({})
        assert raised.value is failure
        assert calls == [(KeyError, "value", 0, 5, "variable")]
        return failure.args, failure._error_processed

    results = [check(compiled) for compiled in compile_both("value", monkeypatch)]
    assert results[0] == results[1]
    assert results[0][0][0].startswith("formatter failed\n\n")


class Source(str):
    """A string subclass must retain the general expression path."""

    __slots__ = ()

    def isidentifier(self):
        raise AssertionError("Source subclass must not be inspected by the optimization")


@pytest.mark.parametrize(
    ("source", "context", "expected"),
    [
        ("True", {}, True),
        ("False", {}, False),
        ("None", {}, None),
        ("café", {"café": 42}, 42),
        ("(value)", {"value": 42}, 42),
        ("value # comment", {"value": 42}, 42),
        (Source("value"), {"value": 42}, 42),
    ],
)
def test_other_name_spellings_and_literals_keep_their_values(source: str, context: dict[str, Any], expected: Any):
    assert safe_eval(source)(context) == expected
