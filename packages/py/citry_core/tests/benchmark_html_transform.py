"""
Benchmark for the Rust HTML transformer (citry_core.html_transform).

Times a single-pass transform_html() over a large generated HTML document (void
elements, nested divs, scripts, CDATA, sections). This is the primitive the
serialize step uses to stamp per-component markers, and it is the dominant fixed
cost of serialize (docs/design/performance.md, issue #7).

Run from the repository root:

    .venv/bin/python packages/py/citry_core/tests/benchmark_html_transform.py
    .venv/bin/python packages/py/citry_core/tests/benchmark_html_transform.py --elements 11000 --iterations 10

IMPORTANT: build the Rust extension in release mode first
(`uv run maturin develop --release` in packages/py/citry_core). The default
debug build is far slower and skews every number (see docs/codebase.md, "Build
the Python package").

Not collected by pytest (the filename does not match ``test_*``); this is a
script, not a test, because timings depend on the machine and would make flaky
assertions.
"""

import argparse
import timeit
from statistics import mean, stdev

from citry_core.html_transform import transform_html


def generate_large_html(num_elements: int) -> str:
    """Generate a large HTML document with various features for benchmarking."""
    elements = []
    for i in range(num_elements):
        # Mix of different elements and features.
        if i % 5 == 0:
            # Void element with multiple attributes.
            elements.append(f'<img src="image{i}.jpg" alt="Image {i}" class="img-{i}" loading="lazy" />')
        elif i % 5 == 1:
            # Nested divs with attributes.
            elements.append(
                f"""
                <div class="container-{i}" data-index="{i}">
                    <div class="inner-{i}">
                        <p>Content {i}</p>
                        <!-- Comment {i} -->
                    </div>
                </div>
            """
            )
        elif i % 5 == 2:
            # Script tag with content.
            elements.append(
                f"""
                <script type="text/javascript">
                    // Script {i}
                    console.log("Script {i}");
                    /* Multi-line
                       comment {i} */
                </script>
            """
            )
        elif i % 5 == 3:
            # CDATA section.
            elements.append(
                f"""
                <![CDATA[
                    Raw content {i}
                    <not-a-tag>
                ]]>
            """
            )
        else:
            # Regular element with attributes.
            elements.append(
                f"""
                <section id="section-{i}" class="section-{i}">
                    <h2>Heading {i}</h2>
                    <p class="text-{i}">Paragraph {i}</p>
                </section>
            """
            )

    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Benchmark Page</title>
            <meta charset="utf-8">
        </head>
        <body>
            {"".join(elements)}
        </body>
        </html>
    """


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the Rust HTML transformer.")
    parser.add_argument(
        "--elements",
        type=int,
        default=27_000,
        help="number of generated elements (default 27000, ~5 MB; 11000 is ~2 MB)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="number of timed transform runs (default 5)",
    )
    args = parser.parse_args()

    html = generate_large_html(args.elements)
    root_attributes = ["data-root-id"]
    all_attributes = ["data-v-123"]

    def run() -> str:
        result, _ = transform_html(
            html,
            root_attributes,
            all_attributes,
            track_added_attributes_for_tags_with_this_attribute="data-id",
        )
        return result

    # Correctness check before timing: the transform must actually add the
    # attributes, or the numbers measure nothing useful. This run also warms up.
    warmed = run()
    assert "data-root-id" in warmed, "transform did not add the root attribute"
    assert "data-v-123" in warmed, "transform did not add the all-elements attribute"

    print(f"\nBenchmarking transform_html: {len(html) // 1_000} KB of HTML, {args.iterations} runs")

    times = timeit.repeat(run, number=1, repeat=args.iterations)

    print("\nTransform:")
    print(f"  Total: {sum(times):.3f}s")
    print(f"  Min:   {min(times):.3f}s")
    print(f"  Max:   {max(times):.3f}s")
    print(f"  Avg:   {mean(times):.3f}s")
    print(f"  Std:   {stdev(times) if len(times) > 1 else 0.0:.3f}s")


if __name__ == "__main__":
    main()
