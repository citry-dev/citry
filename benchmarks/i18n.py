"""
Measure the final server i18n path against an equivalent literal tree.

Run this with a release build of ``citry-core``. The workload and thresholds
come from ``docs/design/i18n.md`` section 14.3: 100 warm message resolutions,
20 named formats, five warmups, and 30 measured samples.
"""

from __future__ import annotations

import argparse
import gzip
import importlib
import json
import math
import platform
import re
import statistics
import sys
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from citry import Citry, Component, FormatRegistry, NumberFormat
from citry_core.i18n import CatalogCompiler

if TYPE_CHECKING:
    from citry.ext.i18n import I18nExtension

MESSAGE_COUNT = 100
FORMAT_COUNT = 20
WARMUPS = 5
SAMPLES = 30
ITERATIONS_PER_SAMPLE = 5
LARGE_MESSAGES_PER_LOCALE = 10_000
LARGE_LOCALES = ("en-US", "cs-CZ", "ar-EG")
LARGE_BUILD_SECONDS_MAX = 8.0
LARGE_ARTIFACT_BYTES_MAX = 20 * 1024 * 1024
LARGE_ARTIFACT_GZIP_BYTES_MAX = 2 * 1024 * 1024
LARGE_PEAK_RSS_BYTES_MAX = 768 * 1024 * 1024


def _scenario() -> tuple[type[Any], type[Any], type[Any], dict[str, object]]:
    configured = Citry(
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "formats": FormatRegistry(number={"measurement": NumberFormat()}),
            }
        },
    )
    i18n = cast("I18nExtension", configured.extensions.get_extension("i18n"))
    message_source = "\n".join(
        f"benchmark-message-{index:03d} = Translated {index:03d}" for index in range(MESSAGE_COUNT)
    )
    localized_template = "\n".join(
        [f'<span>{{{{ tr("benchmark-message-{index:03d}") }}}}</span>' for index in range(MESSAGE_COUNT)]
        + ['<span>{{ fmt.number(amount, format="measurement") }}</span>' for _ in range(FORMAT_COUNT)]
    )

    class LocalizedTree(Component):
        citry = configured

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Decimal]:
            return {"amount": Decimal("1234.5")}

        template = localized_template
        messages = message_source

    # The class above completes the project catalog inventory. Bind the
    # benchmark context only after that revision is current.
    context = i18n.make_context(locale="en-US")
    service = i18n.for_context(context)
    formatted = service.format.number(Decimal("1234.5"), format="measurement")
    literal_template = "\n".join(
        [f"<span>Translated {index:03d}</span>" for index in range(MESSAGE_COUNT)]
        + [f"<span>{formatted}</span>" for _ in range(FORMAT_COUNT)]
    )

    class LiteralConfiguredTree(Component):
        citry = configured
        template = literal_template

    unconfigured = Citry(autodiscover=False)

    class LiteralUnconfiguredTree(Component):
        citry = unconfigured
        template = literal_template

    return LocalizedTree, LiteralConfiguredTree, LiteralUnconfiguredTree, {"citry_i18n": context}


def _visible(html: str) -> str:
    """Remove only random render markers before comparing the three trees."""
    return re.sub(r' data-cid-[^=]+=""', "", html)


def _render_ms(component: type[Any], provides: dict[str, object] | None) -> float:
    started = time.perf_counter_ns()
    for _ in range(ITERATIONS_PER_SAMPLE):
        component().render(provides=provides).serialize()
    return (time.perf_counter_ns() - started) / 1_000_000 / ITERATIONS_PER_SAMPLE


def _summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median_ms": round(statistics.median(values), 4),
        "p95_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 4),
        "stdev_ms": round(statistics.stdev(values), 4),
    }


def _peak_rss_bytes() -> int | None:
    """Return this process's peak RSS using the platform's documented unit."""
    if sys.platform == "win32":
        return None
    resource = importlib.import_module("resource")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def _large_catalog() -> tuple[dict[str, object], dict[str, bool]]:
    """Compile a production-sized multilingual catalog and check bounded cost."""
    message_ids = [f"large-message-{index:05d}" for index in range(LARGE_MESSAGES_PER_LOCALE)]
    catalogs = []
    for locale in LARGE_LOCALES:
        source = "\n".join(
            f"{message_id} = {locale} message {index:05d}" for index, message_id in enumerate(message_ids)
        )
        catalogs.append(
            {
                "path": f"large/{locale}.ftl",
                "package": "large",
                "layer": "large",
                "precedence": 0,
                "locale": locale,
                "source": source,
            }
        )
    request = {
        "schema_version": 1,
        "active_locales": list(LARGE_LOCALES),
        "fallbacks": {},
        "packages": [
            {
                "name": "large",
                "source_locale": "en-US",
                "exports": message_ids,
            }
        ],
        "catalogs": catalogs,
    }
    started = time.perf_counter()
    compiled = CatalogCompiler().compile(
        json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    )
    elapsed = time.perf_counter() - started
    artifact = compiled.artifact_json().encode()
    compressed = gzip.compress(artifact, mtime=0)
    peak_rss = _peak_rss_bytes()
    measured: dict[str, object] = {
        "artifact_bytes": len(artifact),
        "artifact_gzip_bytes": len(compressed),
        "build_seconds": round(elapsed, 4),
        "locales": len(LARGE_LOCALES),
        "messages_per_locale": LARGE_MESSAGES_PER_LOCALE,
        "messages_total": LARGE_MESSAGES_PER_LOCALE * len(LARGE_LOCALES),
        "peak_rss_bytes": peak_rss,
    }
    gates = {
        "artifact_within_budget": len(artifact) <= LARGE_ARTIFACT_BYTES_MAX,
        "artifact_gzip_within_budget": len(compressed) <= LARGE_ARTIFACT_GZIP_BYTES_MAX,
        "build_time_within_budget": elapsed <= LARGE_BUILD_SECONDS_MAX,
        "peak_rss_within_budget": peak_rss is None or peak_rss <= LARGE_PEAK_RSS_BYTES_MAX,
    }
    return measured, gates


def run() -> dict[str, object]:
    """Run the bounded release benchmark and return its checked report."""
    localized, literal, unconfigured, provides = _scenario()
    rendered = {
        "localized": _visible(localized().render(provides=provides).serialize()),
        "literal": _visible(literal().render().serialize()),
        "unconfigured": _visible(unconfigured().render().serialize()),
    }
    if len(set(rendered.values())) != 1:
        raise RuntimeError("the i18n benchmark trees do not render equivalent visible HTML")

    targets = (
        ("literal", literal, None),
        ("localized", localized, provides),
        ("unconfigured", unconfigured, None),
    )
    for _ in range(WARMUPS):
        for _name, component, root_provides in targets:
            _render_ms(component, root_provides)

    samples: dict[str, list[float]] = {name: [] for name, _component, _provides in targets}
    rotations = (targets, targets[1:] + targets[:1], targets[2:] + targets[:2])
    for sample_index in range(SAMPLES):
        for name, component, root_provides in rotations[sample_index % len(rotations)]:
            samples[name].append(_render_ms(component, root_provides))

    summaries = {name: _summary(values) for name, values in samples.items()}
    literal_summary = summaries["literal"]
    localized_summary = summaries["localized"]
    added_median = localized_summary["median_ms"] - literal_summary["median_ms"]
    added_p95 = localized_summary["p95_ms"] - literal_summary["p95_ms"]
    median_budget = max(literal_summary["median_ms"] * 0.15, 2.0)
    p95_budget = max(literal_summary["p95_ms"] * 0.20, 3.0)
    gates = {
        "added_median_within_budget": added_median <= median_budget,
        "added_p95_within_budget": added_p95 <= p95_budget,
    }
    large_catalog, large_gates = _large_catalog()
    gates.update({f"large_catalog_{name}": passed for name, passed in large_gates.items()})
    report = {
        "environment": {
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "gates": gates,
        "operations": {
            "message_resolutions": MESSAGE_COUNT,
            "named_format_calls": FORMAT_COUNT,
        },
        "result": "PASS" if all(gates.values()) else "FAIL",
        "samples_per_tree": SAMPLES,
        "summaries": summaries,
        "thresholds": {
            "added_median_ms": round(median_budget, 4),
            "added_p95_ms": round(p95_budget, 4),
        },
        "measured": {
            "added_median_ms": round(added_median, 4),
            "added_p95_ms": round(added_p95, 4),
            "large_catalog": large_catalog,
        },
        "large_catalog_thresholds": {
            "artifact_bytes": LARGE_ARTIFACT_BYTES_MAX,
            "artifact_gzip_bytes": LARGE_ARTIFACT_GZIP_BYTES_MAX,
            "build_seconds": LARGE_BUILD_SECONDS_MAX,
            "peak_rss_bytes": LARGE_PEAK_RSS_BYTES_MAX,
        },
        "warmups_per_tree": WARMUPS,
    }
    if not all(gates.values()):
        raise RuntimeError(json.dumps(report, indent=2, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the complete machine-readable report")
    args = parser.parse_args()
    report = run()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        measured = report["measured"]
        if type(measured) is not dict:
            raise RuntimeError("the i18n benchmark report has invalid measured values")
        print(f"i18n PASS: added median {measured['added_median_ms']} ms; added p95 {measured['added_p95_ms']} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
