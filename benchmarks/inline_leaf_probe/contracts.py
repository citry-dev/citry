"""Check the inline contract and ensure comparison detects unrelated changes."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.inline_leaf_probe import adapter, checks, compare  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.template_function_probe.contracts import CustomText, HtmlObject  # noqa: E402

import citry.util.id as ids  # noqa: E402
from citry import Component, Const  # noqa: E402
from citry._protocol.client_graph import revision_for  # noqa: E402
from citry.util.html import Markup  # noqa: E402


def main() -> None:
    """Compare admitted cases and record the boundaries that are deliberately rejected."""
    module = scenario()
    ids._id_base = 123456

    class Host(Component):
        citry = module.app
        template = """
<div><c-heroicons c-for="icon in icons" c-bind="icon" /></div>
"""

    class SlotHost(Component):
        citry = module.app
        template = """
<c-heroicons name="home">body</c-heroicons>
"""

    class KeyHost(Component):
        citry = module.app
        template = """
<c-heroicons name="home" #c-key="'stable'" />
"""

    class HookHost(Component):
        citry = module.app

        def on_render(self) -> Any:
            return module.HeroIcon(name="home")

    class RecoveryHost(Component):
        citry = module.app

        def on_render(self) -> Any:
            _, error = yield
            if error is not None:
                return "<p>recovered</p>"
            return None

        template = """
<c-heroicons name="home" variant="bad" />
"""

    data = module.gen_render_data()
    compared = {}
    reference_large = None
    for label, values in (("large", data), ("one_output", {**data, "outputs": data["outputs"][:1]})):
        variants = {}
        for variant in ("reference", "identity", "inline"):
            with checks.installed(module, variant):
                variants[variant] = checks.observe(module, lambda values=values: module.render(values))
        for variant, result in variants.items():
            if result["html"] != variants["reference"]["html"] or result["graphs"] != variants["reference"]["graphs"]:
                raise AssertionError(f"Projected page mismatch: {label}/{variant}")
        if variants["inline"]["counts"]["selected_identities"] or variants["inline"]["counts"]["selected_invocations"]:
            raise AssertionError("Inline variant retained selected identity")
        if label == "large":
            reference_large = variants["reference"]
        compared[label] = {variant: checks.summary(result) for variant, result in variants.items()}
    # One installation per variant keeps its prepared body across changing roots.
    cases = [
        [{"name": "home"}],
        [{"name": Const(Const("home")), "size": 18, "attrs": {"title": "'\"<>&"}}],
        [{"name": "home", "attrs": {"class": ["a", {"b": True}], "style": {"color": "red"}}}],
        [{"name": "home", "variant": "solid", "color": "red"}] * 2 + [{"name": "home", "attrs": {"title": "changed"}}],
    ]
    results = {}
    for variant in ("reference", "identity", "inline"):
        with checks.installed(module, variant):
            results[variant] = [
                checks.observe(module, lambda values=values: str(Host(icons=values))) for values in cases
            ]
    for index in range(len(cases)):
        expected = results["reference"][index]
        for variant in results:
            actual = results[variant][index]
            if (actual["html"], actual["graphs"]) != (expected["html"], expected["graphs"]):
                raise AssertionError(f"Icon case mismatch: {index}/{variant}")
        compared[f"icons_{index}"] = {variant: checks.summary(results[variant][index]) for variant in results}
    errors = {}
    for label, values in (
        ("variant", {"name": "home", "variant": "bad"}),
        ("unknown_kwarg", {"name": "home", "extra": 1}),
    ):
        kinds = []
        for variant in ("reference", "identity", "inline"):
            with checks.installed(module, variant):
                try:
                    str(Host(icons=[values]))
                except (TypeError, ValueError) as error:
                    kinds.append(type(error).__name__)
                else:
                    raise AssertionError("Invalid application input was accepted")
        if len(set(kinds)) != 1:
            raise AssertionError("Application error class changed")
        errors[label] = kinds
    recovered = {}
    for variant in ("reference", "identity", "inline"):
        with checks.installed(module, variant):
            recovered[variant] = checks.observe(module, lambda: str(RecoveryHost()))
    if any(
        (row["html"], row["graphs"]) != (recovered["reference"]["html"], recovered["reference"]["graphs"])
        for row in recovered.values()
    ):
        raise AssertionError("Ancestor error recovery changed beyond removed identity")
    compared["recovery"] = {variant: checks.summary(row) for variant, row in recovered.items()}
    cycle = []
    cycle.append(cycle)
    invalid = {"markup": Markup("safe"), "html_callback": HtmlObject(), "subclass": CustomText("a"), "cycle": cycle}
    rejected = {}
    with checks.installed(module, "inline"):
        calls = {
            name: (lambda value=value: str(Host(icons=[{"name": "home", "attrs": {"title": value}}])))
            for name, value in invalid.items()
        }
        calls.update(
            {
                "slots": lambda: str(SlotHost()),
                "key": lambda: str(KeyHost()),
                "hook_descriptor": lambda: str(HookHost()),
                "root": lambda: str(module.HeroIcon(name="home")),
                "globals": lambda: str(Host(icons=[{"name": "home"}]).render(template_globals={"x": 1})),
                "alpine": lambda: str(Host(icons=[{"name": "home", "attrs": {"x-data": "{}"}}])),
            }
        )
        for label, call in calls.items():
            try:
                call()
            except (TypeError, ValueError) as error:
                rejected[label] = type(error).__name__
            else:
                raise AssertionError(f"Unsupported inline case accepted: {label}")
    # The projection must detect changes outside the explicit identity removal.
    raw = reference_large["raw_html"]
    names, selected = reference_large["names"], reference_large["selected"]
    expected = reference_large["html"]
    corruptions = {
        "svg_text": raw.replace("M4.26", "M4.27", 1),
        "caller_marker": raw.replace(
            "data-cid-" + next(key for key in names if key not in selected), "wrong-marker", 1
        ),
    }
    match = re.search(r'<script type="application/json" data-citry-graph>(.*?)</script>', raw, re.DOTALL)
    wire = json.loads(match[1])
    revision = wire["revision"]
    corruptions["bad_revision"] = raw.replace(revision, "0" * 64).replace(revision[:8], "00000000")
    wire["graphs"][0]["componentInstances"][0]["transparent"] = not wire["graphs"][0]["componentInstances"][0][
        "transparent"
    ]
    wire["revision"] = revision_for({key: value for key, value in wire.items() if key != "revision"})
    changed_wire = (
        raw.replace(match[1], json.dumps(wire, separators=(",", ":")))
        .replace(revision, wire["revision"])
        .replace(revision[:8], wire["revision"][:8])
    )
    corruptions["retained_browser_field"] = changed_wire
    detected = []
    for label, output in corruptions.items():
        try:
            actual = compare.html(output, names, selected)
        except (AssertionError, KeyError):
            detected.append(label)
        else:
            if actual == expected:
                raise AssertionError(f"Projection hid unrelated corruption: {label}")
            detected.append(label)
    paths = [
        Path(__file__),
        Path(adapter.__file__),
        Path(checks.__file__),
        Path(compare.__file__),
        Path(__file__).with_name("plan.md"),
    ]
    print(
        json.dumps(
            {
                "compared": compared,
                "errors": errors,
                "rejected": rejected,
                "detected_corruptions": detected,
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
