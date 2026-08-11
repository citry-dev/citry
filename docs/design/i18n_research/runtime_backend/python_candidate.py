"""Run the frozen Fluent Python candidate against the shared fixtures."""

# ruff: noqa: ANN001, ANN201, T201

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

from fluent.runtime import FluentBundle, FluentResource

FSI = "\u2068"
LRI = "\u2066"
RLI = "\u2067"
PDI = "\u2069"
HOSTILE_NAME = "אבג <Ada&Co>"
BIDI_CONTROLS = frozenset("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
BIDI_PARAGRAPH_BOUNDARIES = frozenset("\n\r\u001c\u001d\u001e\u0085\u2029")


def native(value):
    """Unwrap the small set of Fluent values accepted by this probe."""
    return getattr(value, "value", value)


def scalar_text(value):
    value = native(value)
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def number(value, *, profile, currency=None):
    value = scalar_text(value)
    profile = scalar_text(profile)
    currency = scalar_text(currency) if currency is not None else None
    suffix = f",currency={currency}" if currency is not None else ""
    return f"{FSI}NUM[value={value},profile={profile}{suffix}]{PDI}"


def datetime_value(value, *, profile):
    value = scalar_text(value)
    profile = scalar_text(profile)
    return f"{FSI}DATE[value={value},profile={profile}]{PDI}"


def isolate_text(value):
    value = scalar_text(value)
    if any(control in value for control in BIDI_CONTROLS):
        raise TypeError("CITRY_TEXT rejects embedded bidi controls")
    if any(boundary in value for boundary in BIDI_PARAGRAPH_BOUNDARIES):
        raise TypeError("CITRY_TEXT rejects embedded bidi paragraph boundaries")
    return f"{FSI}{value}{PDI}"


def keep_slot(value):
    value = native(value)
    if not isinstance(value, str) or not value.startswith("__CITRY_SLOT_"):
        raise TypeError("SLOT accepts only an opaque Citry slot marker")
    return value


def plural_category(locale, value, *, exact=None, mode="cardinal"):
    value = Decimal(str(native(value)))
    mode = scalar_text(mode)
    if mode == "ordinal":
        if locale != "en-US" or value != value.to_integral_value():
            return "other"
        integer = int(value)
        if integer % 100 in {11, 12, 13}:
            return "other"
        return {1: "one", 2: "two", 3: "few"}.get(integer % 10, "other")
    if mode != "cardinal":
        raise ValueError("unknown CITRY_PLURAL mode")
    if exact is not None:
        for item in scalar_text(exact).split(","):
            if value == Decimal(item):
                return f"exact-{item}"
    if locale == "cs-CZ":
        if value != value.to_integral_value():
            return "many"
        return "one" if value == 1 else "few" if 2 <= value <= 4 else "other"
    return "one" if value == 1 else "other"


def marker_for(seed: str, locale: str) -> str:
    return f"__CITRY_SLOT_{seed}_{locale.replace('-', '_')}_terms_link__"


def validate_catalog_source(source: str):
    if any(control in source for control in BIDI_CONTROLS):
        raise TypeError("authored catalog contains a prohibited bidi-control character")


def validate_decoded_catalog_text(value: str):
    if any(control in value for control in BIDI_CONTROLS):
        raise TypeError("decoded catalog contains a prohibited bidi-control character")


def isolate_known_direction_paragraphs(value: str, direction: str) -> str:
    initiator = LRI if direction == "ltr" else RLI
    output = []
    start = 0
    index = 0
    while index < len(value):
        if value[index] not in BIDI_PARAGRAPH_BOUNDARIES:
            index += 1
            continue
        output.append(f"{initiator}{value[start:index]}{PDI}")
        end = index + 1
        if value[index] == "\r" and end < len(value) and value[end] == "\n":
            end += 1
        output.append(value[index:end])
        start = end
        index = end
    output.append(f"{initiator}{value[start:]}{PDI}")
    return "".join(output)


def hostile_catalog_sources(control_hex: list[str], forms: list[str]):
    for hex_value in control_hex:
        for form in forms:
            if form == "literal":
                encoded = chr(int(hex_value, 16))
            elif form == "u4":
                encoded = f'{{ "\\u{hex_value}" }}'
            elif form == "U6":
                encoded = f'{{ "\\U{int(hex_value, 16):06X}" }}'
            else:
                raise RuntimeError(f"unknown hostile catalog escape form {form}")
            yield f"hostile = {encoded}"


def bundle_for(locale: str, source: str):
    validate_catalog_source(source)
    bundle = FluentBundle(
        [locale],
        functions={
            "NUMBER": number,
            "DATETIME": datetime_value,
            "SLOT": keep_slot,
            "CITRY_TEXT": isolate_text,
            "CITRY_PLURAL": lambda value, **named: plural_category(locale, value, **named),
        },
        use_isolating=False,
    )
    bundle.add_resource(FluentResource(source))
    return bundle


def validate_runtime_contract(message_id, args, marker):
    """Stand in for generated source contracts before Fluent resolution."""
    for value in args.values():
        if isinstance(value, str) and any(control in value for control in BIDI_CONTROLS):
            raise TypeError(f"{message_id} contains a prohibited bidi-control scalar")
        if isinstance(value, str) and any(boundary in value for boundary in BIDI_PARAGRAPH_BOUNDARIES):
            raise TypeError(f"{message_id} contains a prohibited bidi-paragraph scalar")
    if message_id in {"inbox-count", "acceptance", "invalid-plural-input", "ordinal-position"}:
        field = (
            "value"
            if message_id == "invalid-plural-input"
            else "position"
            if message_id == "ordinal-position"
            else "count"
        )
        value = args.get(field)
        valid_number = isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
        if not valid_number or not Decimal(str(value)).is_finite():
            raise TypeError(f"{message_id} ${field} must be a finite number before resolution")
    if message_id == "acceptance" and args.get("terms_link") != marker:
        raise TypeError("acceptance $terms_link must be the current opaque Slot marker")
    if message_id == "slot-function-scalar" and args.get("value") != marker:
        raise TypeError("slot-function-scalar $value must be a Slot before resolution")


def format_value(bundle, message_id, args, attribute=None, *, marker=None, validate=True):
    if validate:
        validate_runtime_contract(message_id, args, marker)
    message = bundle.get_message(message_id)
    if message is None:
        raise RuntimeError(f"missing message {message_id}")
    pattern = message.attributes[attribute] if attribute else message.value
    if pattern is None:
        raise RuntimeError(f"missing pattern {message_id}.{attribute}")
    value, errors = bundle.format_pattern(pattern, args)
    if errors:
        raise RuntimeError("; ".join(str(error) for error in errors))
    return value


def ensure_no_collision(source: str, args, marker: str):
    if marker in source:
        raise ValueError("slot marker collides with a catalog resource")
    if any(isinstance(value, str) and marker in value for value in args.values()):
        raise ValueError("slot marker collides with a scalar input")


def split_slot(value: str, marker: str):
    count = value.count(marker)
    if count == 0:
        raise ValueError("expected at least one slot marker, received 0")
    isolated_marker = f"{FSI}{marker}{PDI}"
    if isolated_marker in value:
        raise ValueError("slot marker was unexpectedly wrapped as scalar text")
    parts = value.split(marker)
    output = []
    for index, part in enumerate(parts):
        output.append({"kind": "text", "value": part})
        if index < count:
            output.append({"kind": "slot", "name": "terms_link", "occurrence": index})
    return output


def main():
    fixtures = Path(sys.argv[1])
    marker_seed = sys.argv[2]
    generated_layers = (fixtures / "layered-generated.ftl").read_text()
    hostile_config = json.loads((fixtures / "hostile-bidi-control.json").read_text())
    cases = {}
    markers = []
    resolution_markers_distinct = True
    sources = {}
    for locale in ("en-US", "cs-CZ"):
        marker = marker_for(marker_seed, locale)
        markers.append(marker)
        source = (fixtures / f"{locale}.ftl").read_text() + "\n" + generated_layers
        sources[locale] = source
        bundle = bundle_for(locale, source)
        args = {
            "account_name": HOSTILE_NAME,
            "amount": Decimal("1234.5"),
            "count": 2,
            "due_ms": 1782864000000,
            "position": 2,
            "terms_link": marker,
        }
        ensure_no_collision(source, {key: value for key, value in args.items() if key != "terms_link"}, marker)
        rich = split_slot(format_value(bundle, "acceptance", args, marker=marker), marker)
        second_marker = marker_for(f"{marker_seed}_resolution_2", locale)
        resolution_markers_distinct &= second_marker != marker
        second_args = {**args, "terms_link": second_marker}
        ensure_no_collision(
            source,
            {key: value for key, value in second_args.items() if key != "terms_link"},
            second_marker,
        )
        second_rich = split_slot(format_value(bundle, "acceptance", second_args, marker=second_marker), second_marker)
        if second_rich != rich:
            raise RuntimeError(f"{locale} changed normalized rich output across fresh markers")
        cases[locale] = {
            "summary": format_value(bundle, "account-summary", args, marker=marker),
            "attribute": format_value(bundle, "account-actions", args, "aria-label", marker=marker),
            "plural_0": format_value(bundle, "inbox-count", {**args, "count": 0}, marker=marker),
            "plural_negative_zero": format_value(
                bundle, "inbox-count", {**args, "count": Decimal("-0")}, marker=marker
            ),
            "plural_1": format_value(bundle, "inbox-count", {**args, "count": 1}, marker=marker),
            "plural_2": format_value(bundle, "inbox-count", args, marker=marker),
            "plural_1_5": format_value(bundle, "inbox-count", {**args, "count": Decimal("1.5")}, marker=marker),
            "plural_2_5": format_value(bundle, "inbox-count", {**args, "count": Decimal("2.5")}, marker=marker),
            "plural_5": format_value(bundle, "inbox-count", {**args, "count": 5}, marker=marker),
            "ordinal_1": format_value(bundle, "ordinal-position", {**args, "position": 1}, marker=marker),
            "ordinal_2": format_value(bundle, "ordinal-position", args, marker=marker),
            "ordinal_3": format_value(bundle, "ordinal-position", {**args, "position": 3}, marker=marker),
            "ordinal_4": format_value(bundle, "ordinal-position", {**args, "position": 4}, marker=marker),
            "ordinal_11": format_value(bundle, "ordinal-position", {**args, "position": 11}, marker=marker),
            "ordinal_21": format_value(bundle, "ordinal-position", {**args, "position": 21}, marker=marker),
            "balance": format_value(bundle, "balance", args, marker=marker),
            "due_date": format_value(bundle, "due-date", args, marker=marker),
            "layered_reference": format_value(bundle, "citry-lib-wrapper", args, marker=marker),
            "multiline_fallback_isolated": isolate_known_direction_paragraphs(
                format_value(bundle, "multiline-fallback", args, marker=marker), "ltr"
            ),
            "rich": rich,
        }

    marker = markers[0]
    invalid = bundle_for("en-US", (fixtures / "invalid.ftl").read_text())
    rejections = {}
    for rejection_name, message_id, args in (
        ("unknown-variable", "unknown-variable", {}),
        ("unknown-function", "unknown-function", {"value": 1}),
        ("slot-function-scalar", "slot-function-scalar", {"value": "ordinary scalar"}),
        ("invalid-plural-input", "invalid-plural-input", {"value": "not a number"}),
        ("invalid-plural-nan", "invalid-plural-input", {"value": float("nan")}),
        ("invalid-plural-infinity", "invalid-plural-input", {"value": float("inf")}),
    ):
        try:
            format_value(invalid, message_id, args, marker=marker)
        except (RuntimeError, TypeError) as error:
            rejections[rejection_name] = str(error)
    for name, value in (
        ("slot_marker_omitted", "marker omitted"),
        ("slot_marker_wrapped", f"{FSI}{marker}{PDI}"),
    ):
        try:
            split_slot(value, marker)
        except ValueError as error:
            rejections[name] = str(error)
    try:
        ensure_no_collision(sources["en-US"] + marker, {}, marker)
    except ValueError as error:
        rejections["slot_catalog_collision"] = str(error)
    try:
        ensure_no_collision(sources["en-US"], {"hostile": marker}, marker)
    except ValueError as error:
        rejections["slot_scalar_collision"] = str(error)
    dangerous_bidi = f"prefix{PDI}\u202eoverride\u202c"
    en_bundle = bundle_for("en-US", sources["en-US"])
    for name, message_id, bad_args in (
        ("bidi-control-plain", "account-summary", {"account_name": dangerous_bidi}),
        (
            "bidi-control-rich",
            "acceptance",
            {"account_name": dangerous_bidi, "count": 2, "terms_link": marker},
        ),
    ):
        try:
            format_value(en_bundle, message_id, bad_args, marker=marker)
        except TypeError as error:
            rejections[name] = str(error)
    paragraph_rejections = {"plain": 0, "rich": 0}
    for hex_value in hostile_config["paragraph_boundary_hex"]:
        boundary = chr(int(hex_value, 16))
        bad_value = f"before{boundary}אבג"
        for sink, message_id, bad_args in (
            ("plain", "account-summary", {"account_name": bad_value}),
            (
                "rich",
                "acceptance",
                {"account_name": bad_value, "count": 2, "terms_link": marker},
            ),
        ):
            try:
                format_value(en_bundle, message_id, bad_args, marker=marker)
            except TypeError:
                paragraph_rejections[sink] += 1
    expected_paragraph_rejections = len(hostile_config["paragraph_boundary_hex"])
    for sink, count in paragraph_rejections.items():
        if count != expected_paragraph_rejections:
            raise RuntimeError(
                f"{sink} rejected {count} bidi paragraph boundaries, expected {expected_paragraph_rejections}"
            )
        rejections[f"paragraph-boundary-{sink}"] = f"rejected all {count} Unicode bidi paragraph boundaries"

    catalog_rejections = 0
    for hostile_catalog in hostile_catalog_sources(
        hostile_config["bidi_control_hex"], hostile_config["fluent_escape_forms"]
    ):
        try:
            hostile_bundle = bundle_for("en-US", hostile_catalog)
            decoded = format_value(hostile_bundle, "hostile", {}, validate=False)
            validate_decoded_catalog_text(decoded)
        except TypeError:
            catalog_rejections += 1
    expected_catalog_rejections = len(hostile_config["bidi_control_hex"]) * len(hostile_config["fluent_escape_forms"])
    if catalog_rejections != expected_catalog_rejections:
        raise RuntimeError(f"rejected {catalog_rejections} catalog bidi cases, expected {expected_catalog_rejections}")
    rejections["bidi-control-catalog"] = f"rejected all {catalog_rejections} literal and escaped bidi-control cases"

    paragraph_isolation_cases = [chr(int(value, 16)) for value in hostile_config["paragraph_boundary_hex"]] + ["\r\n"]
    for boundary in paragraph_isolation_cases:
        actual = isolate_known_direction_paragraphs(f"left{boundary}אבג", "ltr")
        expected = f"{LRI}left{PDI}{boundary}{LRI}אבג{PDI}"
        if actual != expected:
            raise RuntimeError(f"paragraph isolation failed for {boundary.encode()!r}")

    expected_rejections = {
        "bidi-control-catalog",
        "bidi-control-plain",
        "bidi-control-rich",
        "invalid-plural-infinity",
        "invalid-plural-input",
        "invalid-plural-nan",
        "paragraph-boundary-plain",
        "paragraph-boundary-rich",
        "slot-function-scalar",
        "slot_catalog_collision",
        "slot_marker_omitted",
        "slot_marker_wrapped",
        "slot_scalar_collision",
        "unknown-function",
        "unknown-variable",
    }
    if set(rejections) != expected_rejections:
        raise RuntimeError(
            f"rejection mismatch: expected {sorted(expected_rejections)}, received {sorted(rejections)}"
        )
    unsafe_runtime_behaviors = {
        "slot_as_selector": format_value(
            invalid,
            "slot-as-selector",
            {"terms_link": marker},
            marker=marker,
            validate=False,
        ),
    }
    print(
        json.dumps(
            {
                "candidate": "python",
                "cases": cases,
                "marker_properties": {
                    "distinct_per_locale": len(set(markers)) == len(markers),
                    "distinct_per_resolution": resolution_markers_distinct,
                },
                "bidi_properties": {
                    "catalog_cases_rejected": catalog_rejections,
                    "catalog_escape_forms": hostile_config["fluent_escape_forms"],
                    "paragraph_boundaries_rejected_per_scalar_sink": expected_paragraph_rejections,
                    "whole_message_paragraph_cases_isolated": len(paragraph_isolation_cases),
                },
                "rejections": rejections,
                "unsafe_runtime_behaviors": unsafe_runtime_behaviors,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
