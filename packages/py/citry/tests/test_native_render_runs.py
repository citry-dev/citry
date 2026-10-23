"""
Level B1 of the native render path: one Rust object records a whole call run during serialize.

When Rust read every row of a call run (the rows one ``c-for`` places at one
component call site), assembly records the run with one run object
(``_NativeRun``) instead of one Python record per row, and the manifest
writer writes the rows' items from it. Any row or state the run object
cannot handle exactly sends the whole run back to the per-row loop, which
raises its own errors.

Page cases run on both paths in this process (``render_both`` in
``tests/_render_paths.py``) and compare the bytes or the error and the
callbacks' calls, and state how many run objects the Rust path wrote and
how many runs it declined, so a silent decline cannot pass. The rest check
the binding directly with synthetic maps, because a page cannot reach
several of its refusals.
"""

from __future__ import annotations

import dataclasses
import gc
from collections import defaultdict
from types import SimpleNamespace
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue import events, native_render
from citry._vue.direct_capture import _DIGEST_JSON, _RUN_ROW_CHECK_MESSAGES, _DigestPrefix
from citry._vue.events import DirectVueEventsProducer, default_events_producer
from citry._vue.protocol import _occurrence_items_with_runs
from citry._vue.serialization import _script_json
from citry.citry_render import SimpleVueRecord
from citry.extension import Extension

from ._render_paths import NONCE, render_both, run_on_path
from .test_native_render_rows import build_board, make_rows

pytestmark = pytest.mark.skipif(not native_render.SUPPORTED, reason="this interpreter takes the Python render path")

# The outputs each page case serializes; each reads the run's rows differently.
OUTPUTS: dict[str, dict[str, Any]] = {
    "hydrated": {},
    "ssr_false": {"ssr": False},
    "static": {"deps_strategy": "simple"},
    "fragment": {"deps_strategy": "fragment"},
    "hydration_declined": {"deps_position": "append"},
}


class _BrowserHook(Extension):
    """An extension with a browser hook, which keeps the page off the precompile path."""

    name = "native_runs_browser_hook"

    def prepare_browser_render(self, ctx: Any) -> None:
        return None


def _group(prefix: str, count: int) -> list[dict[str, Any]]:
    return [
        {"key": f"{prefix}{index}", "attrs": {"id": f"{prefix}-{index}"}, "title": f"{prefix} {index}"}
        for index in range(count)
    ]


# The list component's template for the cases that change it; every other
# case places one run of rows.
_LIST_TEMPLATES = {
    "nested_runs": """
        <section>
          <div c-for="group in groups">
            <c-Row
              c-for="row in group"
              #c-key="row['key']"
              c-row="row"
            />
          </div>
        </section>
    """,
    "two_runs_with_sibling": """
        <section>
          <c-Row
            c-for="row in groups[0]"
            #c-key="row['key']"
            c-row="row"
          />
          <c-Plain label="between" />
          <c-Row
            c-for="row in groups[1]"
            #c-key="row['key']"
            c-row="row"
          />
        </section>
    """,
    "ordinary_run": """
        <section>
          <c-Plain
            c-for="row in groups[0]"
            #c-key="row['key']"
            c-label="row['title']"
          />
          <c-Row
            c-for="row in groups[1]"
            #c-key="row['key']"
            c-row="row"
          />
        </section>
    """,
}
_LIST_TEMPLATES["nested_dup_key"] = _LIST_TEMPLATES["nested_runs"]
_ONE_RUN = """
    <section>
      <c-Row
        c-for="row in groups[0]"
        #c-key="row['key']"
        c-row="row"
      />
    </section>
"""


def run_case(name: str) -> dict[str, object]:
    """
    Render one small page per case on every output; return each output's bytes or error and the callback log.

    The page is a root component with a list component that places
    ``simple='vue'`` rows with ``c-for``. Each case changes one thing:

    - ``plain``: four rows, one run;
    - ``dup_key_in_run``: two rows of one run share a ``#c-key``;
    - ``nested_runs``: a nested loop makes two runs of one call site under
      one owner, so the second run's keys are checked against the first's;
    - ``nested_dup_key``: the same, with a key repeated across the two runs;
    - ``two_runs_with_sibling``: two call sites with an ordinary component
      between them;
    - ``ordinary_run``: a run of an ordinary component beside a row run;
    - ``js_data_row``: one row's ``js_data`` returns a value, so its run
      takes the per-row loop;
    - ``browser_hook`` and ``custom_tag``: pages kept off the precompile path;
    - ``threshold``: the page mounts in the browser instead of hydrating;
    - ``on_dependencies``: a component class defines ``on_dependencies``;
    - ``rows_in_root``: the rows are written in the root template;
    - ``csp_nonce``: strict CSP with a nonce;
    - ``unregistered_after_render``: the row class leaves the registry between
      render and serialize, so assembly's registry check fails.
    """
    log: list[str] = []
    options: dict[str, Any] = {}
    if name == "browser_hook":
        options["extensions"] = [_BrowserHook]
    if name == "threshold":
        options["ssr_element_threshold"] = 100_000
    if name == "csp_nonce":
        options["security_csp"] = "strict"
    engine = Citry(autodiscover=False, **options)
    engine.set_mounted_prefix("/citry")

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: dict

        @staticmethod
        def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
            log.append(f"template_data {kwargs.row['key']}")
            return {"attrs": kwargs.row["attrs"], "title": kwargs.row["title"]}

        @staticmethod
        def js_data(kwargs: Any, _slots: Any) -> dict[str, Any] | None:
            log.append(f"js_data {kwargs.row['key']}")
            return {"note": "x"} if kwargs.row.get("js") else None

        template = """
            <article c-bind="attrs"><span>{{ title }}</span></article>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    class Plain(Component):
        citry = engine

        class Kwargs:
            label: str

        template = """
            <p>{{ label }}</p>
        """

    class RowList(Component):
        citry = engine

        class Kwargs:
            groups: list

        template = _LIST_TEMPLATES.get(name, _ONE_RUN)
        js = """
            $component({data(){return {open: true};}});
        """

    if name == "on_dependencies":

        def on_dependencies(_self: Any, _ctx: Any) -> None:
            log.append("on_dependencies")

        RowList.on_dependencies = on_dependencies  # type: ignore[attr-defined]

    page_body = (
        """
        <c-Row
          c-for="row in groups[0]"
          #c-key="row['key']"
          c-row="row"
        />
        """
        if name == "rows_in_root"
        else """
        <c-RowList c-groups="groups" />
        """
    )

    class RowPage(Component):
        citry = engine

        class Kwargs:
            groups: list

        template = f"""
            <html><head></head><body><main>{page_body}</main></body></html>
        """

    groups = [_group("a", 4), _group("b", 3)]
    if name == "dup_key_in_run":
        groups[0][2]["key"] = groups[0][0]["key"]
    if name == "nested_dup_key":
        groups[1][1]["key"] = groups[0][3]["key"]
    if name == "js_data_row":
        groups[0][1]["js"] = True
    if name == "custom_tag":
        producer = default_events_producer(engine)

        def component_tag(self: Any, type_key: str) -> str:
            log.append(f"component_tag {type_key.rsplit('.', 1)[-1]}")
            return DirectVueEventsProducer.component_tag(self, type_key)

        producer.component_tag = component_tag.__get__(producer)  # type: ignore[method-assign]

    outputs = OUTPUTS
    if name == "csp_nonce":
        outputs = {"csp": {"security_csp": "strict", "csp_nonce": NONCE}}
    if name == "unregistered_after_render":
        outputs = {"hydrated": {}}
    result: dict[str, object] = {}
    for label, serialize_options in outputs.items():
        try:
            rendered = RowPage(groups=groups).render()
            if name == "unregistered_after_render":
                engine.unregister(Row)
            result[label] = rendered.serialize(**serialize_options)
        except Exception as error:  # noqa: BLE001 - compared between the paths
            result[label] = f"{type(error).__name__}: {error}"
    result["log"] = log
    return result


# For each case, over all its outputs: run objects the Rust path built, call
# runs ``try_new`` declined, and run objects the page manifests held
# (observed, then locked). Four of the five outputs assemble on the
# precompile path; static HTML writes no manifest. Pages kept off the
# precompile path never reach the run object. A repeated key in one run
# fails ``try_new``; a key repeated across two runs fails the second run's
# ``commit``, so the render fails and no manifest holds either run, and the per-row loop raises Python's
# own error.
CASE_RUNS = {
    "plain": (4, 0, 4),
    "dup_key_in_run": (0, 4, 0),
    "nested_runs": (8, 0, 8),
    "nested_dup_key": (8, 0, 0),
    "two_runs_with_sibling": (8, 0, 8),
    "ordinary_run": (4, 0, 4),
    "js_data_row": (0, 4, 0),
    "browser_hook": (0, 0, 0),
    "custom_tag": (0, 0, 0),
    "threshold": (4, 0, 4),
    "on_dependencies": (4, 0, 4),
    "rows_in_root": (4, 0, 4),
    "csp_nonce": (1, 0, 1),
    # The registry check fails before any run object is asked for.
    "unregistered_after_render": (0, 0, 0),
}


@pytest.mark.parametrize("name", sorted(CASE_RUNS))
def test_page_cases_write_the_same_bytes_on_both_paths(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    render_both(lambda: run_case(name), monkeypatch, runs=CASE_RUNS[name])


def test_the_run_object_records_every_run_of_the_board(monkeypatch: pytest.MonkeyPatch) -> None:
    # The board at 140 rows in five phases of 28, the benchmark board's shape:
    # every call run must reach the run object, with no decline and no row
    # rebuilt, or level B1 has silently switched itself off.
    run = run_on_path(lambda: build_board(make_rows(140), phase_size=28).render().serialize(), monkeypatch, rust=True)
    assert (run.runs_built, run.runs_declined, run.runs_written, run.run_rows_written) == (5, 0, 5, 140)
    assert (run.rows_read, run.rows_rebuilt) == (140, 0)
    python = run_on_path(
        lambda: build_board(make_rows(140), phase_size=28).render().serialize(), monkeypatch, rust=False
    )
    assert python.result == run.result
    assert (python.runs_built, python.runs_written) == (0, 0)


# ---------------------------------------------------------------------------
# Assembly: the run object writes what the per-row loop writes
# ---------------------------------------------------------------------------


def _assemble_both(monkeypatch: pytest.MonkeyPatch, rows: int) -> tuple[Any, Any]:
    """Assemble one Rust-read render on the precompile path with the run object and with the per-row loop."""
    captured: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    original = events.assemble_typed_render

    def capture(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("native_rows"):
            captured.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(native_render, "ACTIVE", True)
    monkeypatch.setattr(events, "assemble_typed_render", capture)
    build_board(make_rows(rows)).render().serialize()
    ((args, kwargs),) = captured
    with_runs = original(*args, **kwargs)
    # With the flag off, the records still hold Rust's rows, so assembly
    # takes the per-row loop for them (level A alone).
    monkeypatch.setattr(native_render, "ACTIVE", False)
    per_row = original(*args, **kwargs)
    return with_runs, per_row


def _occurrence_fields(item: Any) -> tuple[object, ...]:
    return (
        item.id,
        item.type_key,
        item.definition_id,
        dict(item.server_data),
        {key: dict(value) if key == "calls" else value for key, value in item.prepared_data.items()},
        item.parent_id,
        item.placement_key,
        item._native,
    )


def test_the_run_object_assembles_what_the_per_row_loop_assembles(monkeypatch: pytest.MonkeyPatch) -> None:
    # The bytes cannot show a map entry that only a later error would read,
    # so compare the assemblies themselves, field by field.
    with_runs, per_row = _assemble_both(monkeypatch, 30)
    native_occurrence = native_render.NativeOccurrence
    held = [item for item in with_runs.view.occurrences if type(item) is native_occurrence]
    assert len(held) == 30
    assert all(type(item) is not native_occurrence for item in per_row.view.occurrences)
    assert [_occurrence_fields(item) for item in with_runs.view.occurrences] == [
        _occurrence_fields(item) for item in per_row.view.occurrences
    ]
    # Definitions in the same order, since that order reaches the manifest.
    assert with_runs.view.definitions == per_row.view.definitions
    assert list(with_runs.compile_inputs.items()) == list(per_row.compile_inputs.items())
    assert dict(with_runs.render_to_occurrence) == dict(per_row.render_to_occurrence)
    assert dict(with_runs.occurrence_to_render) == dict(per_row.occurrence_to_render)
    assert with_runs.view.markers == per_row.view.markers
    assert with_runs.view.root_id == per_row.view.root_id


def test_the_manifest_writer_writes_each_run_row_as_its_own_item(monkeypatch: pytest.MonkeyPatch) -> None:
    with_runs, per_row = _assemble_both(monkeypatch, 12)
    native = native_render.native
    assert native is not None
    run_items = _occurrence_items_with_runs(with_runs.view, {item.id: item.id for item in with_runs.view.definitions})
    runs = [item for item in run_items if type(item) is native_render.NativeRun]
    assert [len(run) for run in runs] == [10, 2]
    ids = {item.id: item.id for item in with_runs.view.definitions}
    natives = {item.id: item._native for item in per_row.view.occurrences if item._native is not None}
    per_row_items = [
        {
            "id": item.id,
            "typeKey": item.type_key,
            "definitionId": item.definition_id,
            "serverData": item.server_data,
            "preparedData": item.prepared_data,
            "parentId": item.parent_id,
            "placementKey": item.placement_key,
            "renderId": per_row.occurrence_to_render[item.id],
        }
        for item in per_row.view.occurrences
    ]
    for item in run_items:
        if type(item) is dict:
            item["renderId"] = with_runs.occurrence_to_render[item["id"]]  # type: ignore[index]
    assert native._encode_occurrences(run_items, {}, _script_json, ids) == native._encode_occurrences(
        per_row_items, natives, _script_json
    )


# ---------------------------------------------------------------------------
# The binding's refusals, with synthetic maps
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class _Run:
    """The arguments ``try_new`` takes for one real run of Rust-read records."""

    members: list[Any]
    record_type: type
    component_class: Any
    fragment: Any
    source: Any
    source_span: Any
    placement_prefix_json: str
    child_prefix_json: str
    parent_id: str
    type_key: str
    definition_id: str

    def args(self) -> tuple[Any, ...]:
        return tuple(getattr(self, field.name) for field in dataclasses.fields(self))

    def member_base(self) -> tuple[object, ...]:
        return (self.source, *self.source_span, self.type_key)


_PARENT = "citryOccurrence0123456789abcdef01234567"
_ROUTE: tuple[str, ...] = ()


def _records(count: int, monkeypatch: pytest.MonkeyPatch) -> list[SimpleVueRecord]:
    """Render a board on the Rust path and return the records of its first call run."""
    monkeypatch.setattr(native_render, "ACTIVE", True)
    rendered = build_board(make_rows(count), phase_size=count).render()
    pending = [rendered]
    while pending:
        current = pending.pop()
        records = [part for part in current.parts if type(part) is SimpleVueRecord]
        if records:
            assert all(record.native is not None for record in records)
            return records
        pending.extend(part for part in current.parts if hasattr(part, "parts"))
    msg = "the render holds no simple='vue' record"
    raise AssertionError(msg)


def _run(records: list[SimpleVueRecord]) -> _Run:
    first = records[0]
    metadata = first.call_metadata
    assert metadata is not None
    member_base = (metadata.source, *metadata.source_span, first.class_id)
    return _Run(
        list(records),
        SimpleVueRecord,
        first.component_class,
        first.fragment,
        metadata.source,
        metadata.source_span,
        _DIGEST_JSON.encode((member_base, _ROUTE))[:-1],
        _DIGEST_JSON.encode((_PARENT,))[:-1],
        _PARENT,
        first.class_id,
        "citryDefinitionTest",
    )


def _try_new(run: _Run) -> Any:
    native = native_render.native
    assert native is not None
    return native._NativeRun.try_new(*run.args())


class _Text(str):
    __slots__ = ()


def _with_metadata(record: SimpleVueRecord, **changes: Any) -> SimpleVueRecord:
    metadata = record.call_metadata
    assert metadata is not None
    return dataclasses.replace(record, call_metadata=dataclasses.replace(metadata, **changes))


# Each case changes one thing about a valid run; try_new must refuse it.
_TRY_NEW_DECLINES: dict[str, Any] = {
    "no members": lambda run: dataclasses.replace(run, members=[]),
    "a member that is not a record": lambda run: dataclasses.replace(run, members=[*run.members[:2], object()]),
    "a row Python evaluated": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], native=None)]
    ),
    "a row with js_data": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], js_data={"x": 1})]
    ),
    "a row with root markers": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], root_markers=("data-ccss-x",))]
    ),
    "another class id": lambda run: dataclasses.replace(run, type_key=run.type_key + "x"),
    "another class object": lambda run: dataclasses.replace(run, component_class=object()),
    "another fragment": lambda run: dataclasses.replace(run, fragment=object()),
    "another source": lambda run: dataclasses.replace(run, source=str(run.source) + " "),
    # An equal span in another tuple object: the run's prefix was hashed
    # from the first row's objects, so equal is not enough.
    "another span": lambda run: dataclasses.replace(run, source_span=(run.source_span[0], run.source_span[1])),
    "a key that is not a str": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], _with_metadata(run.members[2], explicit_key=3)]
    ),
    "a str subclass key": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], _with_metadata(run.members[2], explicit_key=_Text("k2"))]
    ),
    "a key with no UTF-8 form": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], _with_metadata(run.members[2], explicit_key="bad \ud800")]
    ),
    "a str subclass render id": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], render_id=_Text("r2"))]
    ),
    "a render id with no UTF-8 form": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], render_id="bad \ud800")]
    ),
    "a repeated key": lambda run: dataclasses.replace(
        run,
        members=[
            *run.members[:2],
            _with_metadata(run.members[2], explicit_key=run.members[0].call_metadata.explicit_key),
        ],
    ),
    "a repeated render id": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], render_id=run.members[0].render_id)]
    ),
    "a str subclass parent id": lambda run: dataclasses.replace(run, parent_id=_Text(run.parent_id)),
    "a str subclass type key": lambda run: dataclasses.replace(run, type_key=_Text(run.type_key)),
    "a type key with no UTF-8 form": lambda run: dataclasses.replace(run, type_key="bad \ud800"),
    "a str subclass definition id": lambda run: dataclasses.replace(run, definition_id=_Text(run.definition_id)),
    "a later row with no call metadata": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], call_metadata=None)]
    ),
    "a row whose native is not a _NativeRow": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], native=object())]
    ),
    "a later row of another class id": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], class_id=run.type_key + "x")]
    ),
    "a str subclass class id": lambda run: dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], class_id=_Text(run.type_key))]
    ),
    "an empty class id": lambda run: dataclasses.replace(
        run,
        type_key="",
        members=[dataclasses.replace(member, class_id="") for member in run.members],
    ),
}


@pytest.mark.parametrize("case", sorted(_TRY_NEW_DECLINES))
def test_try_new_declines_a_run_it_cannot_record_exactly(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    run = _run(_records(4, monkeypatch))
    assert _try_new(run) is not None
    assert _try_new(_TRY_NEW_DECLINES[case](run)) is None


def test_try_new_computes_the_ids_python_computes(monkeypatch: pytest.MonkeyPatch) -> None:
    records = _records(6, monkeypatch)
    run = _run(records)
    native_run = _try_new(run)
    placement = _DigestPrefix(run.member_base(), _ROUTE)
    child = _DigestPrefix(_PARENT)
    expected = []
    for record in records:
        assert record.call_metadata is not None
        placement_key = f"citryPlacement{placement.digest(('explicit', record.call_metadata.explicit_key))[:24]}"
        expected.append((f"citryOccurrence{child.digest(placement_key)[:24]}", placement_key, record.render_id))
    assert len(native_run) == 6
    assert native_run.member_ids() == [child_id for child_id, _, _ in expected]
    occurrences = native_run.occurrences()
    assert [(item.id, item.placement_key, item.render_id) for item in occurrences] == expected
    assert [item.index for item in occurrences] == list(range(6))
    assert all(item.run is native_run for item in occurrences)
    assert all(item._native is record.native for item, record in zip(occurrences, records, strict=True))
    assert {(item.type_key, item.parent_id, item.definition_id) for item in occurrences} == {
        (run.type_key, _PARENT, run.definition_id)
    }
    assert (native_run.parent_id, native_run.type_key, native_run.definition_id) == (
        _PARENT,
        run.type_key,
        run.definition_id,
    )
    assert repr(occurrences[1]) == f"_NativeOccurrence(id={expected[1][0]!r}, index=1)"


def _live_maps() -> dict[str, Any]:
    """Fresh copies of the assembly state ``commit`` checks and writes."""
    return {
        "seen_render_ids": {"r-other"},
        "seen_occurrence_ids": {"citryOccurrenceother"},
        "local_identity_keys": {(("other",), (), "other")},
        "supplied_fills": defaultdict(list),
        "occurrence_to_render": {"citryOccurrenceother": "r-other"},
        "render_to_occurrence": {"r-other": "citryOccurrenceother"},
        "occurrence_types": {"citryOccurrenceother": "t"},
        "occurrence_parents": {"citryOccurrenceother": None},
        "occurrence_placement_keys": {"citryOccurrenceother": None},
    }


def _commit(native_run: Any, run: _Run, maps: dict[str, Any]) -> bool:
    return bool(
        native_run.commit(
            maps["seen_render_ids"],
            maps["seen_occurrence_ids"],
            maps["local_identity_keys"],
            run.member_base(),
            _ROUTE,
            maps["supplied_fills"],
            maps["occurrence_to_render"],
            maps["render_to_occurrence"],
            maps["occurrence_types"],
            maps["occurrence_parents"],
            maps["occurrence_placement_keys"],
        )
    )


def _snapshot(maps: dict[str, Any]) -> dict[str, object]:
    return {
        name: (sorted(map(repr, value)) if isinstance(value, set) else list(value.items()))
        for name, value in maps.items()
    }


# Each case puts one of the last row's ids into the live state, the way an
# earlier occurrence of the same assembly would; commit must refuse the
# whole run and write nothing, so the per-row loop meets the state it expects.
_COMMIT_DECLINES = {
    "a render id already seen": lambda maps, row, _base: maps["seen_render_ids"].add(row.render_id),
    "a child id already seen": lambda maps, row, _base: maps["seen_occurrence_ids"].add(row.id),
    "an identity another run took": lambda maps, row, base: maps["local_identity_keys"].add(
        (base, _ROUTE, row.run_key)
    ),
    "fills addressed to a row": lambda maps, row, _base: maps["supplied_fills"][row.id].append(object()),
    "an empty fill entry a read left": lambda maps, row, _base: maps["supplied_fills"][row.id],
}


@pytest.mark.parametrize("case", sorted(_COMMIT_DECLINES))
def test_commit_refuses_a_conflict_and_writes_nothing(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    records = _records(4, monkeypatch)
    run = _run(records)
    native_run = _try_new(run)
    last = native_run.occurrences()[-1]
    assert records[-1].call_metadata is not None
    row = SimpleNamespace(id=last.id, render_id=last.render_id, run_key=records[-1].call_metadata.explicit_key)
    maps = _live_maps()
    _COMMIT_DECLINES[case](maps, row, run.member_base())
    before = _snapshot(maps)
    assert _commit(native_run, run, maps) is False
    assert _snapshot(maps) == before


def test_commit_writes_every_row_in_row_order(monkeypatch: pytest.MonkeyPatch) -> None:
    records = _records(4, monkeypatch)
    run = _run(records)
    native_run = _try_new(run)
    maps = _live_maps()
    assert _commit(native_run, run, maps) is True
    rows = native_run.occurrences()
    ids = [item.id for item in rows]
    # Dicts keep insertion order, so the entries follow the rows' order
    # after the entry that was already there.
    assert list(maps["occurrence_to_render"].items())[1:] == [(item.id, item.render_id) for item in rows]
    assert list(maps["render_to_occurrence"].items())[1:] == [(item.render_id, item.id) for item in rows]
    assert list(maps["occurrence_types"].items())[1:] == [(row_id, run.type_key) for row_id in ids]
    assert list(maps["occurrence_parents"].items())[1:] == [(row_id, _PARENT) for row_id in ids]
    assert list(maps["occurrence_placement_keys"].items())[1:] == [(item.id, item.placement_key) for item in rows]
    assert maps["seen_render_ids"] == {"r-other", *(item.render_id for item in rows)}
    assert maps["seen_occurrence_ids"] == {"citryOccurrenceother", *ids}
    keys = [record.call_metadata.explicit_key for record in records if record.call_metadata is not None]
    assert maps["local_identity_keys"] == {
        (("other",), (), "other"),
        *((run.member_base(), _ROUTE, key) for key in keys),
    }
    # supplied_fills is only read, never written.
    assert dict(maps["supplied_fills"]) == {}


def test_check_invariants_names_the_first_row_that_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    run = _run(_records(4, monkeypatch))
    native_run = _try_new(run)
    rows = native_run.occurrences()
    # A clean run adds each row's placement and reports nothing.
    placements: set[tuple[str, str]] = set()
    references: defaultdict[str, list[str]] = defaultdict(list)
    # An empty entry left by a defaultdict read is no reference.
    references[rows[0].id]
    assert native_run.check_invariants(references, placements) is None
    assert placements == {(_PARENT, item.placement_key) for item in rows}
    # Another call referencing row 2 fails check 0 there.
    references[rows[2].id].append("citryOccurrenceother")
    assert native_run.check_invariants(references, set()) == (2, 0)
    # A placement another occurrence took fails check 1 at that row.
    assert native_run.check_invariants(defaultdict(list), {(_PARENT, rows[1].placement_key)}) == (1, 1)
    assert native_run.check_invariants(defaultdict(list), placements) == (0, 1)
    # Each check's index names the message the per-row final loop raises.
    assert _RUN_ROW_CHECK_MESSAGES == (
        "prepared nonroot occurrence must have one exact physical-parent call reference",
        "prepared occurrence placement key is duplicated within one physical parent",
    )


class _Interrupting:
    """A ``js_data`` whose truth test raises ``KeyboardInterrupt``."""

    def __bool__(self) -> bool:
        raise KeyboardInterrupt


class _Failing:
    """A ``js_data`` whose truth test raises an ordinary exception."""

    def __bool__(self) -> bool:
        msg = "js_data truth failed"
        raise ValueError(msg)


def test_try_new_declines_on_an_exception_but_lets_an_interrupt_through(monkeypatch: pytest.MonkeyPatch) -> None:
    # An ordinary error while reading a row declines, so the per-row loop
    # meets it at its own row; an interrupt must never be swallowed.
    run = _run(_records(3, monkeypatch))
    failing = dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], js_data=_Failing())]
    )
    assert _try_new(failing) is None
    interrupting = dataclasses.replace(
        run, members=[*run.members[:2], dataclasses.replace(run.members[2], js_data=_Interrupting())]
    )
    with pytest.raises(KeyboardInterrupt):
        _try_new(interrupting)


def test_holds_any_finds_a_run_row_by_its_child_id(monkeypatch: pytest.MonkeyPatch) -> None:
    native_run = _try_new(_run(_records(3, monkeypatch)))
    rows = native_run.occurrences()
    assert native_run.holds_any({rows[2].id, "citryOccurrenceother"}) is True
    assert native_run.holds_any(["citryOccurrenceother", 3, "bad \ud800"]) is False
    assert native_run.holds_any([]) is False


def test_run_objects_are_not_tracked_and_their_rows_are_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    native_run = _try_new(_run(_records(3, monkeypatch)))
    row = native_run.occurrences()[0]
    # Neither holds anything that could refer back to it, so the cyclic
    # collector has nothing to do with them.
    assert not gc.is_tracked(native_run)
    assert not gc.is_tracked(row)
    assert dict(row.server_data) == {}
    assert list(row.prepared_data) == ["calls"]
    assert dict(row.prepared_data["calls"]) == {}
    with pytest.raises(TypeError):
        row.prepared_data["x"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        row.prepared_data["calls"]["x"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        row.server_data["x"] = 1  # type: ignore[index]


def test_the_encoder_refuses_a_run_without_its_compiled_id(monkeypatch: pytest.MonkeyPatch) -> None:
    run = _run(_records(3, monkeypatch))
    native_run = _try_new(run)
    native = native_render.native
    assert native is not None
    with pytest.raises(ValueError, match="needs definition_ids"):
        native._encode_occurrences([native_run], {}, _script_json)
    with pytest.raises(ValueError, match="has no compiled id"):
        native._encode_occurrences([native_run], {}, _script_json, {})
    with pytest.raises(ValueError, match="is not a str"):
        native._encode_occurrences([native_run], {}, _script_json, {run.definition_id: 3})
    # Any other item that is not a dict is still refused.
    with pytest.raises(ValueError, match="is not a dict"):
        native._encode_occurrences([native_run.occurrences()[0]], {}, _script_json, {run.definition_id: "d"})


def test_a_run_whose_rows_are_not_adjacent_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    # The writer puts a run's rows in one block; a view that split them would
    # be an assembly bug, and must fail rather than drop the later rows.
    with_runs, _per_row = _assemble_both(monkeypatch, 12)
    native_occurrence = native_render.NativeOccurrence
    held = [item for item in with_runs.view.occurrences if type(item) is native_occurrence]
    other = next(item for item in with_runs.view.occurrences if type(item) is not native_occurrence)
    view = SimpleNamespace(occurrences=(held[0], other, held[1]))
    with pytest.raises(AssertionError, match="not adjacent"):
        _occurrence_items_with_runs(view, {item.id: item.id for item in with_runs.view.definitions})  # type: ignore[arg-type]
