"""
Benchmark comparing eval() on each call vs lambda wrapper approach vs pure functions.

This benchmark demonstrates the performance difference between:
1. Pure function: Direct Python function (no eval, no sandboxing) - baseline
2. Old approach: Calling eval(compiled_code, namespace, {}) on each evaluation
3. New approach: Wrapping in lambda and calling the function directly

This shows:
- How much overhead the sandboxing/lambda wrapper adds vs pure functions
- How much the lambda optimization saves vs eval() on each call

Run from the repository root:

    .venv/bin/python packages/py/citry_core/tests/benchmark_safe_eval.py
    .venv/bin/python packages/py/citry_core/tests/benchmark_safe_eval.py --iterations 20000

IMPORTANT: build the Rust extension in release mode first
(`uv run maturin develop --release` in packages/py/citry_core). The default
debug build skews every number (see docs/codebase.md, "Build the Python
package").

Not collected by pytest (the filename does not match ``test_*``); this is a
script, not a test, because timings depend on the machine and would make flaky
assertions.
"""

import argparse
import time
from collections.abc import Callable
from statistics import mean, stdev
from typing import Any

from citry_core.safe_eval import safe_eval


def benchmark_eval_vs_lambda(
    source: str,
    context: dict[str, Any],
    pure_func: Callable[[dict[str, Any]], Any] | None = None,
    num_iterations: int = 10000,
) -> None:
    """
    Benchmark pure function vs lambda wrapper vs old eval() approach.

    Args:
        source: Expression to evaluate
        context: Context dictionary for evaluation
        pure_func: Optional pure Python function that does the same computation
                  without eval/sandboxing. If None, will be skipped.
        num_iterations: Number of times to call evaluate()

    """
    print(f"\n{'=' * 60}")
    print(f"Benchmarking: {source}")
    print(f"Iterations: {num_iterations:,}")
    print(f"{'=' * 60}")

    # Current approach: lambda wrapper (already implemented)
    compiled_lambda = safe_eval(source)

    # Simulate the old approach: eval() on each call. This reconstructs a design
    # that already shipped as the lambda wrapper, and it couples to safe_eval's
    # internal interceptor names imported below. If a safe_eval refactor breaks
    # this half, drop it rather than repairing it: the decision it measures is
    # settled.
    from citry_core import _rust
    from citry_core.safe_eval.eval import (
        assign,
        attribute,
        call,
        format,
        interpolation,
        slice,
        subscript,
        template,
        variable,
    )

    transformed_code = _rust.safe_eval.safe_eval(source)
    compiled_code_old = compile(transformed_code, f"Expression <{source}>", "eval")

    def evaluate_old_approach(context: dict[str, Any]) -> Any:
        """Old approach: create namespace dict and call eval() each time"""
        eval_namespace = {
            "variable": variable,
            "attribute": attribute,
            "subscript": subscript,
            "call": call,
            "assign": assign,
            "slice": slice,
            "interpolation": interpolation,
            "template": template,
            "format": format,
            "source": source,
            "context": context,
        }
        return eval(compiled_code_old, eval_namespace, {})

    # Pure eval() approach: evaluate original code directly (no transformation/sandboxing)
    try:
        compiled_code_pure_eval = compile(source, f"Expression <{source}>", "eval")
    except SyntaxError:
        # Some expressions might not be valid Python (e.g., lambdas need to be assigned)
        # For those cases, we'll skip the pure eval benchmark
        compiled_code_pure_eval = None

    def evaluate_pure_eval(context: dict[str, Any]) -> Any:
        """Pure eval() approach: eval original code with context as namespace"""
        if compiled_code_pure_eval is None:
            return None
        # Pass context directly as the namespace for evaluation
        return eval(compiled_code_pure_eval, context, {})

    # Verify all approaches produce the same result
    result_lambda = compiled_lambda(context)
    result_old = evaluate_old_approach(context)

    # For lambdas and other callables, we can't directly compare equality
    if callable(result_lambda) and callable(result_old):
        # Try calling with test args to verify they behave the same
        try:
            test_args = (1, 2)  # Simple test args
            assert result_lambda(*test_args) == result_old(*test_args), (
                "Lambda and old approach results differ when called"
            )
        except (TypeError, ValueError):
            # Can't verify, but that's okay
            pass
    else:
        assert result_lambda == result_old, f"Results differ: {result_lambda} != {result_old}"

    # Pure eval might not work for all expressions (e.g., lambdas), so check if it works
    result_pure_eval = None
    if compiled_code_pure_eval is not None:
        try:
            result_pure_eval = evaluate_pure_eval(context)
            # For simple expressions, verify it matches
            if not callable(result_pure_eval) and not callable(result_lambda):
                # Only compare non-callable results (callables are hard to compare)
                try:
                    assert result_pure_eval == result_lambda, (
                        f"Pure eval result differs: {result_pure_eval} != {result_lambda}"
                    )
                except (AssertionError, TypeError):
                    # Some edge cases might differ, that's okay for benchmarking
                    pass
        except Exception:
            # Pure eval might fail for expressions that need sandboxing
            compiled_code_pure_eval = None

    if pure_func is not None:
        result_pure = pure_func(context)
        # For lambdas (which return functions), we can't compare the functions directly,
        # but we can test that they behave the same if possible
        if callable(result_pure) and callable(result_lambda):
            # If both are callable, try calling them with test args
            try:
                test_args = (1, 2)  # Simple test args
                assert result_pure(*test_args) == result_lambda(*test_args), (
                    "Pure function lambda result differs when called"
                )
            except (TypeError, ValueError):
                # If they don't accept the test args, skip comparison
                pass
        else:
            assert result_pure == result_lambda, f"Pure function result differs: {result_pure} != {result_lambda}"

    # Warm up
    for _ in range(100):
        compiled_lambda(context)
        evaluate_old_approach(context)
        if pure_func is not None:
            pure_func(context)
        if compiled_code_pure_eval is not None:
            evaluate_pure_eval(context)

    # Benchmark pure function (if provided)
    times_pure = []
    if pure_func is not None:
        for _ in range(num_iterations):
            start = time.perf_counter()
            pure_func(context)
            times_pure.append(time.perf_counter() - start)

    # Benchmark pure eval() approach (if applicable)
    times_pure_eval = []
    if compiled_code_pure_eval is not None:
        for _ in range(num_iterations):
            start = time.perf_counter()
            evaluate_pure_eval(context)
            times_pure_eval.append(time.perf_counter() - start)

    # Benchmark lambda approach (current)
    times_lambda = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        compiled_lambda(context)
        times_lambda.append(time.perf_counter() - start)

    # Benchmark old eval() approach (with transformation)
    times_old = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        evaluate_old_approach(context)
        times_old.append(time.perf_counter() - start)

    # Calculate statistics
    def stats(times: list[float]) -> dict[str, float]:
        total = sum(times)
        avg = mean(times)
        std = stdev(times) if len(times) > 1 else 0.0
        return {
            "total": total,
            "avg": avg,
            "min": min(times),
            "max": max(times),
            "std": std,
        }

    stats_lambda = stats(times_lambda)
    stats_old = stats(times_old)

    if pure_func is not None:
        stats_pure = stats(times_pure)

    if compiled_code_pure_eval is not None:
        stats_pure_eval = stats(times_pure_eval)

    # Print results
    print("\nResults:")
    if pure_func is not None and compiled_code_pure_eval is not None:
        # Full comparison: pure func, pure eval, lambda, old eval
        print(f"\n{'Metric':<20} {'Pure Func':<20} {'Pure Eval':<20} {'Lambda (New)':<20} {'Eval+Transform':<20}")
        print("-" * 100)
        print(
            f"{'Total time':<20} {stats_pure['total'] * 1000:>8.2f} ms      "
            f"{stats_pure_eval['total'] * 1000:>8.2f} ms      "
            f"{stats_lambda['total'] * 1000:>8.2f} ms      "
            f"{stats_old['total'] * 1000:>8.2f} ms"
        )
        print(
            f"{'Avg per call':<20} {stats_pure['avg'] * 1e6:>8.2f} μs      "
            f"{stats_pure_eval['avg'] * 1e6:>8.2f} μs      "
            f"{stats_lambda['avg'] * 1e6:>8.2f} μs      "
            f"{stats_old['avg'] * 1e6:>8.2f} μs"
        )

        overhead_lambda_vs_pure = (stats_lambda["avg"] - stats_pure["avg"]) / stats_pure["avg"] * 100
        overhead_lambda_vs_pure_eval = (
            (stats_lambda["avg"] - stats_pure_eval["avg"]) / stats_pure_eval["avg"] * 100
            if compiled_code_pure_eval
            else None
        )
        overhead_transform = (
            (stats_old["avg"] - stats_pure_eval["avg"]) / stats_pure_eval["avg"] * 100
            if compiled_code_pure_eval
            else None
        )
        improvement = (stats_old["total"] - stats_lambda["total"]) / stats_old["total"] * 100
        print(
            f"\nLambda overhead vs pure func: {overhead_lambda_vs_pure:.1f}% slower ({stats_lambda['avg'] / stats_pure['avg']:.2f}x)"
        )
        if compiled_code_pure_eval:
            print(
                f"Lambda overhead vs pure eval: {overhead_lambda_vs_pure_eval:.1f}% slower ({stats_lambda['avg'] / stats_pure_eval['avg']:.2f}x)"
            )
            print(
                f"Transformation overhead: {overhead_transform:.1f}% slower ({stats_old['avg'] / stats_pure_eval['avg']:.2f}x)"
            )
        print(
            f"Lambda vs eval()+transform improvement: {improvement:.1f}% faster ({stats_old['total'] / stats_lambda['total']:.2f}x speedup)"
        )
    elif pure_func is not None:
        print(
            f"\n{'Metric':<20} {'Pure Func':<20} {'Lambda (New)':<20} {'Eval (Old)':<20} {'vs Pure':<15} {'vs Eval':<15}"
        )
        print("-" * 110)
        print(
            f"{'Total time':<20} {stats_pure['total'] * 1000:>8.2f} ms      "
            f"{stats_lambda['total'] * 1000:>8.2f} ms      "
            f"{stats_old['total'] * 1000:>8.2f} ms      "
            f"{stats_lambda['total'] / stats_pure['total']:>6.2f}x slower  "
            f"{stats_old['total'] / stats_lambda['total']:>6.2f}x speedup"
        )
        print(
            f"{'Avg per call':<20} {stats_pure['avg'] * 1e6:>8.2f} μs      "
            f"{stats_lambda['avg'] * 1e6:>8.2f} μs      "
            f"{stats_old['avg'] * 1e6:>8.2f} μs      "
            f"{stats_lambda['avg'] / stats_pure['avg']:>6.2f}x slower  "
            f"{stats_old['avg'] / stats_lambda['avg']:>6.2f}x speedup"
        )

        overhead = (stats_lambda["avg"] - stats_pure["avg"]) / stats_pure["avg"] * 100
        improvement = (stats_old["total"] - stats_lambda["total"]) / stats_old["total"] * 100
        print(f"\nLambda overhead vs pure: {overhead:.1f}% slower ({stats_lambda['avg'] / stats_pure['avg']:.2f}x)")
        print(
            f"Lambda vs eval() improvement: {improvement:.1f}% faster ({stats_old['total'] / stats_lambda['total']:.2f}x speedup)"
        )
    else:
        print(f"\n{'Metric':<20} {'Lambda (New)':<20} {'Eval (Old)':<20} {'Speedup':<15}")
        print("-" * 75)
        print(
            f"{'Total time':<20} {stats_lambda['total'] * 1000:>8.2f} ms      "
            f"{stats_old['total'] * 1000:>8.2f} ms      "
            f"{stats_old['total'] / stats_lambda['total']:>6.2f}x"
        )
        print(
            f"{'Avg per call':<20} {stats_lambda['avg'] * 1e6:>8.2f} μs      "
            f"{stats_old['avg'] * 1e6:>8.2f} μs      "
            f"{stats_old['avg'] / stats_lambda['avg']:>6.2f}x"
        )

        improvement = (stats_old["total"] - stats_lambda["total"]) / stats_old["total"] * 100
        print(
            f"\nImprovement: {improvement:.1f}% faster ({stats_old['total'] / stats_lambda['total']:.2f}x speedup)"
        )


def main() -> None:
    """Run benchmarks with various expression types."""
    parser = argparse.ArgumentParser(description="Benchmark safe_eval dispatch strategies.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="override the per-expression iteration count (default: tuned per case)",
    )
    n = parser.parse_args().iterations

    print("Benchmark: Pure Function vs Lambda Wrapper vs eval() on Each Call")
    print("=" * 60)

    # Simple expression
    benchmark_eval_vs_lambda(
        "x + y * 2",
        {"x": 10, "y": 5},
        pure_func=lambda ctx: ctx["x"] + ctx["y"] * 2,
        num_iterations=n or 50000,
    )

    # Expression with function calls
    benchmark_eval_vs_lambda(
        "sum([x, y, z])",
        {"x": 1, "y": 2, "z": 3, "sum": sum},
        pure_func=lambda ctx: sum([ctx["x"], ctx["y"], ctx["z"]]),
        num_iterations=n or 50000,
    )

    # Expression with attribute access
    class Obj:
        def __init__(self, value):
            self.value = value

    obj = Obj(10)
    benchmark_eval_vs_lambda(
        "obj.value * 2",
        {"obj": obj},
        pure_func=lambda ctx: ctx["obj"].value * 2,
        num_iterations=n or 50000,
    )

    # Expression with subscript
    items = [10, 20, 30]
    benchmark_eval_vs_lambda(
        "items[0] + items[1]",
        {"items": items},
        pure_func=lambda ctx: ctx["items"][0] + ctx["items"][1],
        num_iterations=n or 50000,
    )

    # Complex expression
    benchmark_eval_vs_lambda(
        "(x + y) * z if z > 0 else x - y",
        {"x": 10, "y": 5, "z": 3},
        pure_func=lambda ctx: (ctx["x"] + ctx["y"]) * ctx["z"] if ctx["z"] > 0 else ctx["x"] - ctx["y"],
        num_iterations=n or 30000,
    )

    # Expression with lambda (returns a function)
    # Note: For this case, we can't easily create a pure function that returns
    # the exact same lambda object, but we can create equivalent behavior
    benchmark_eval_vs_lambda(
        "lambda a, b: a + b + x",
        {"x": 100},
        pure_func=lambda ctx: lambda a, b: a + b + ctx["x"],
        num_iterations=n or 30000,
    )

    print("\n" + "=" * 60)
    print("Benchmark complete!")


if __name__ == "__main__":
    main()
