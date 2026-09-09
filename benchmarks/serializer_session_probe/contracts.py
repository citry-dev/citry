"""Compare frame programs and retain serializer boundary failures."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.serializer_session_probe import adapter  # noqa: E402

from citry import CitryContext, CitryRender  # noqa: E402
from citry.citry_render import RenderFrame  # noqa: E402


def program(rows: list[Any], changed: bool) -> dict[str, Any]:
    """Retain the reference's top-down marker and reverse-order assembly rules."""
    session = adapter.NATIVE.Session("c-render-id") if changed else None
    frames = {}
    inherited_values = {}
    placeholder_map = {"extension": '<template c-render-id="extension"></template>'}
    try:
        for key, parent, html, own_plain, own_valued, children in rows:
            if session is not None:
                session.add_frame(key, parent, html, own_plain, own_valued, children, placeholder_map)
                continue
            added = {}
            if parent is not None:
                added = {child: attrs for child, _html, attrs in frames[parent][1]}
            inherited = added.get(key, [])
            plain = list(dict.fromkeys([*own_plain, *inherited]))
            valued = [*own_valued, *(inherited_values[parent] if inherited else [])]
            segments, placeholders = (
                adapter.MARK(html, plain, "c-render-id") if html and (plain or children) else ([html], [])
            )
            if valued and plain:
                segments, placeholders = adapter.VALUED(segments, placeholders, plain, valued)
            if key in frames:
                raise RuntimeError(
                    "The same rendered component id was encountered more than once during serialization; "
                    "render a fresh occurrence for each physical position."
                )
            frames[key] = segments, placeholders
            inherited_values[key] = valued
            for child, text, _ in placeholders:
                if child in placeholder_map:
                    placeholder_map[child] = text
        if session is not None:
            html = session.finish()
        else:
            finished = {}
            for key in reversed(frames):
                segments, placeholders = frames[key]
                parts = [segments[0]]
                for (child, text, _), segment in zip(placeholders, segments[1:], strict=True):
                    parts.extend((finished.get(child, text), segment))
                finished[key] = "".join(parts)
            html = finished[""]
        return {"html": html, "placeholders": placeholder_map}
    except (ValueError, RuntimeError, TypeError) as error:
        return {"error_type": type(error).__name__, "error": str(error)}


def surrogate(changed: bool, *, marker: bool) -> dict[str, Any]:
    """Exercise Python strings that UTF-8 extraction cannot represent."""
    adapter.install(changed)
    frame = (
        RenderFrame(
            render_id="c1", class_id="cls", class_name="Example", is_component_root=True, root_markers=('x="\ud800"',)
        )
        if marker
        else None
    )
    render = CitryRender(parts=["<b>text</b>" if marker else "\ud800"], context=CitryContext(), frame=frame)
    try:
        return {"html": render.serialize(deps_strategy="ignore")}
    except (ValueError, RuntimeError, TypeError) as error:
        return {"error_type": type(error).__name__, "error": str(error)}
    finally:
        adapter.install(changed=False)


def capacity() -> dict[str, Any]:
    """A compact repeated-reference program reaches the native capacity boundary."""
    session = adapter.NATIVE.Session("c-render-id")
    for index in range(64):
        key = str(index) if index else ""
        text = f'<template c-render-id="{index + 1}"></template>' * 2 if index < 63 else "x"
        session.add_frame(key, None, text, [], [], index < 63, {})
    try:
        session.finish()
    except BaseException as error:  # noqa: BLE001 - retain a PyO3 panic as a failed probe
        return {"error_type": type(error).__name__, "error": str(error)}
    raise RuntimeError("The impossible-capacity probe unexpectedly returned")


def main() -> None:
    ph = '<template c-render-id="child"></template>'
    cases = {
        "empty": [("", None, "", [], [], False)],
        "unknown": [("", None, ph, ["root"], [], True)],
        "inherited": [("", None, ph, ["root"], [], True), ("child", "", "<b>x</b>", ["child"], [], False)],
        "nested": [
            ("", None, f"<div>{ph}</div>", ["root"], [], True),
            ("child", "", "<b>x</b>", ["child"], [], False),
        ],
        "valued": [
            ("", None, ph, ["root"], ['x="outer"'], True),
            ("child", "", "<b>x</b>", ["child"], ['x="inner"'], False),
        ],
        "last_placeholder": [
            ("", None, f"{ph}<div>{ph}</div>", ["root"], [], True),
            ("child", "", "<b>x</b>", [], [], False),
        ],
        "literal_self": [("", None, '<template c-render-id=""></template>', ["root"], [], True)],
        "earlier_reference": [
            ("", None, ph, [], [], True),
            ("child", "", '<template c-render-id=""></template>', [], [], True),
        ],
        "extension": [("", None, '<template c-render-id="extension"></template>', ["root"], [], False)],
        "raw_text": [("", None, f"<script>{ph}</script><!-- x --><br>", ["root"], [], True)],
        "malformed": [("", None, '<p broken="', ["root"], [], True)],
        "duplicate": [("", None, "a", [], [], False), ("", None, "b", [], [], False)],
        "invalid_valued": [("", None, "<b>x</b>", ["root"], ["x=bad"], False)],
        "valued_newline": [("", None, "<b>x</b>", ["root"], ['x="a"\n'], False)],
    }
    reports = []
    for name, rows in cases.items():
        reference, candidate = program(rows, changed=False), program(rows, changed=True)
        reports.append(
            {"case": name, "reference": reference, "candidate": candidate, "matches": reference == candidate}
        )
    for marker in (False, True):
        reference, candidate = surrogate(changed=False, marker=marker), surrogate(changed=True, marker=marker)
        reports.append(
            {
                "case": f"surrogate_marker_{marker}",
                "reference": reference,
                "candidate": candidate,
                "matches": reference == candidate,
            }
        )
    report = {
        "experiment_only": True,
        "cases": reports,
        "capacity": capacity(),
        "python": sys.version,
        "artifact_sha256": hashlib.sha256(adapter.ARTIFACT.read_bytes()).hexdigest(),
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(adapter.__file__),
                Path(adapter.ser.__file__),
                Path(__file__).parent / "src/lib.rs",
            )
        },
    }
    path = ROOT / "benchmarks/results/performance-render/serializer-session-contracts.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(reports),
                "failures": [row["case"] for row in reports if not row["matches"]],
                "capacity": report["capacity"],
            }
        )
    )


if __name__ == "__main__":
    main()
