"""TypeScript findings in component JavaScript and templates reach the authored source."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest
import pytest_lsp
from lsprotocol import types
from pygls.exceptions import JsonRpcInvalidParams
from pytest_lsp import ClientServerConfig, LanguageClient

from citry._checker import CheckReport
from citry.commands.check import _with_type_findings
from citry_lsp.engine import (
    DocumentState,
    ProjectionSourceMapping,
    TypeCheckProjection,
    browser_diagnostics,
    browser_projection,
    template_lint_diagnostics,
    type_check_projections,
)
from citry_lsp.project import load_project
from citry_lsp.project_check import check_project_python_types
from citry_lsp.protocol import PROTOCOL_VERSION, TYPE_CHECK_METHOD
from citry_lsp.semantic import _json_type_from_ty_display, infer_js_data_value_types
from citry_lsp.server import CitryLanguageServer
from citry_lsp.type_analysis import TyAnalyzer
from citry_lsp.typescript import (
    TypeScriptFinding,
    TypeScriptUnavailableError,
    check_document_types,
    check_project_types,
    find_typescript_compiler,
    map_type_check_findings,
    parse_tsc_output,
    parse_type_check_response,
    run_typescript_compiler,
    run_typescript_compiler_async,
)

# The Node workspace installs TypeScript here; the checks that run it skip without it.
_REPOSITORY_NODE_PROJECT = Path(__file__).resolve().parents[4] / "packages" / "js" / "citry-client"


@lru_cache(maxsize=1)
def _tsc() -> tuple[str, ...] | None:
    try:
        return find_typescript_compiler(_REPOSITORY_NODE_PROJECT)
    except TypeScriptUnavailableError:
        return None


def _command() -> tuple[str, ...]:
    command = _tsc()
    if command is None:
        pytest.skip("repo-local tsc is unavailable; install the Node workspace for this integration check")
    return command


_APP = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Lane(Component):
    citry = engine
    template_file = 'lane.html'
    js_file = 'lane.js'
class Card(Component):
    citry = engine
    template_file = 'card.html'
    js_file = 'card.js'
"""

# Each line of `finish()` holds one mistake the check must catch.
_LANE_JS = """$component({
  emits: {
    'drop-task'(/** @type {{taskId: number}} */ payload) { return true; },
  },
  data() { return { dragging: false }; },
  methods: {
    clearDropTarget() { this.dragging = false; },
    startDrag(/** @type {number} */ id) { this.dragging = true; },
    finish() {
      this.clearDropTarget = true;
      this.$emit('drop-task', 'x');
      this.startDargg();
      this.startDrag(1, 2);
      this.$el.fooBar;
      this.$el.focus();
      this.$emit('drop-task', { taskId: 1 });
    },
  },
});
"""
_LANE_HTML = """<button @click="startDrag('a')" @focus="$emit('drop-task', 'y')">Go</button>"""
_CARD_HTML = """<c-Lane @drop-task="$event.taskId.toFixed(); $event.nope"></c-Lane>"""


def _documents(tmp_path: Path, files: dict[str, tuple[str, str]], app: str = _APP):
    (tmp_path / "app.py").write_text(app, encoding="utf-8")
    for name, (_language, source) in files.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status
    documents: dict[str, DocumentState] = {}
    for name, (language, source) in files.items():
        document = DocumentState((tmp_path / name).as_uri(), language, source, 1)
        document.update(source, 1, project)
        documents[document.uri] = document
    return project, documents


def _findings(tmp_path: Path, name: str, project, documents) -> list[tuple[str, str, tuple[int, int, int, int]]]:
    """Check one document and return each finding's code, the authored text it covers, and its range."""
    document = documents[(tmp_path / name).as_uri()]
    citry = browser_diagnostics(document, project, documents)
    lines = document.source.split("\n")
    found = []
    for diagnostic in check_document_types(document, project, documents, _command(), citry):
        value = diagnostic.range
        assert value.start.line == value.end.line
        assert diagnostic.source == "Citry (ts)"
        assert diagnostic.severity == types.DiagnosticSeverity.Error
        found.append(
            (
                str(diagnostic.code),
                lines[value.start.line][value.start.character : value.end.character],
                (value.start.line, value.start.character, value.end.line, value.end.character),
            )
        )
    return found


_BOUND_APP = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Bound(Component):
    citry = engine
    template_file = 'bound.html'
    def js_data(self, kwargs, slots):
        return {'enabled': True, 'color': 'red', 'name': 'title'}
"""

_BOUND_HTML = (
    '<div :draggable="\'treu\'" :style="1" :data-id="1" :class="{ on: enabled }">'
    '<p :draggable="enabled" :style="{ color: color }" :translate="\'\'" :hidden="\'until-found\'"></p>'
    "<my-el :draggable=\"'treu'\"></my-el><p :draggable.prop=\"'treu'\"></p>"
    '<p v-bind:hidden="1" :[name]="1" v-bind="{ draggable: \'treu\' }"></p>'
    '<slot :name="1"></slot></div>'
)


def test_native_bindings_are_checked_against_vue_attribute_types(tmp_path):
    project, documents = _documents(tmp_path, {"bound.html": ("citry-html", _BOUND_HTML)}, app=_BOUND_APP)

    # Valid values pass, including `translate=""`, which the HTML Standard
    # allows and the static attribute-value rule accepts. The long
    # `v-bind:` form is checked too. A custom element, a `.prop` binding, a
    # dynamic or object `v-bind`, and a `<slot>` prop are left alone.
    assert [(code, text) for code, text, _range in _findings(tmp_path, "bound.html", project, documents)] == [
        ("citry.typescript.ts2345", "'treu'"),
        ("citry.typescript.ts2345", "1"),
        ("citry.typescript.ts2345", "1"),
    ]


def test_bound_attribute_helper_is_never_offered_as_a_completion(tmp_path):
    project, documents = _documents(tmp_path, {"bound.html": ("citry-html", _BOUND_HTML)}, app=_BOUND_APP)
    document = documents[(tmp_path / "bound.html").as_uri()]
    cursor = _BOUND_HTML.index(':draggable="enabled') + len(':draggable="en')

    projection = browser_projection(
        document,
        types.Position(0, cursor),
        project,
        documents,
    )

    assert projection is not None
    assert "__citryBindAttribute" in projection.owned_root_names


@pytest.fixture
def lane_project(tmp_path):
    return _documents(
        tmp_path,
        {
            "lane.js": ("javascript", _LANE_JS),
            "lane.html": ("citry-html", _LANE_HTML),
            "card.html": ("citry-html", _CARD_HTML),
            "card.js": ("javascript", "$component({});\n"),
        },
    )


def test_component_javascript_mistakes_reach_their_authored_text(tmp_path, lane_project):
    project, documents = lane_project

    assert _findings(tmp_path, "lane.js", project, documents) == [
        # A method is not a boolean.
        ("citry.typescript.ts2322", "this.clearDropTarget", (9, 6, 9, 26)),
        # The payload does not match the `emits` validator.
        ("citry.typescript.ts2345", "'x'", (10, 30, 10, 33)),
        # One argument too many.
        ("citry.typescript.ts2554", "2", (12, 24, 12, 25)),
        # `$el` is the template's <button>.
        ("citry.typescript.ts2339", "fooBar", (13, 15, 13, 21)),
    ]


def test_a_mistake_citry_reports_is_not_reported_again(tmp_path, lane_project):
    project, documents = lane_project
    document = documents[(tmp_path / "lane.js").as_uri()]
    citry = browser_diagnostics(document, project, documents)

    # TypeScript finds `this.startDargg()` on its own ...
    alone = check_document_types(document, project, documents, _command(), ())
    assert "citry.typescript.ts2551" in {item.code for item in alone}
    # ... but Citry's own rule explains it, so only Citry's finding remains.
    assert "citry.component-js.unknown-member" in {item.code for item in citry}
    assert not any(text == "startDargg" for _code, text, _range in _findings(tmp_path, "lane.js", project, documents))


def test_template_expressions_are_checked_against_the_component(tmp_path, lane_project):
    project, documents = lane_project

    assert _findings(tmp_path, "lane.html", project, documents) == [
        ("citry.typescript.ts2345", "'a'", (0, 26, 0, 29)),
        # A template's `$emit` checks the payload against the validator too.
        ("citry.typescript.ts2345", "'y'", (0, 59, 0, 62)),
    ]
    # A listener on a child tag reads the child's emitted value.
    assert _findings(tmp_path, "card.html", project, documents) == [
        ("citry.typescript.ts2339", "nope", (0, 52, 0, 56)),
    ]


_INLINE_APP = '''from citry import Citry, Component
engine = Citry(autodiscover=False)
class Board(Component):
    citry = engine
    def js_data(self, kwargs, slots):
        return {"helpOpen": False, "mode": "view"}
    template = """
      <section @board:notice="$event.detail.message" @click="$event.target.value">
        <button @click="helpOpen = !helpOpen; mode = 'edit'; move(1)">Help</button>
        <c-Board @c-drop-task="{task: $event.taskId}" />
      </section>
    """
    js = """
      $component({
        inject: ['theme'],
        methods: {
          move(/** @type {string} */ lane) {
            this.theme.accent;
            this.$refs.status?.focus();
            this.$el.querySelector('#x')?.focus();
            window.htmx.process(this.$el);
            Citry.vue.inject('theme').accent;
            this.missing = 1;
          },
        },
      });
    """
'''


def test_inline_python_assets_map_through_indentation_without_false_positives(tmp_path):
    project, documents = _documents(tmp_path, {}, app=_INLINE_APP)
    document = DocumentState((tmp_path / "app.py").as_uri(), "python", _INLINE_APP, 1)
    document.update(_INLINE_APP, 1, project)
    documents[document.uri] = document

    # Ordinary browser code stays quiet: a custom DOM event's `detail`, an
    # event target, a `js_data()` value that starts as `False`, a ref, a
    # selector query, a page global on `window`, and an injection. Only the
    # two real mistakes are reported, on the Python file's own lines.
    assert _findings(tmp_path, "app.py", project, documents) == [
        ("citry.typescript.ts2345", "1", (8, 66, 8, 67)),
        ("citry.typescript.ts2339", "missing", (22, 17, 22, 24)),
    ]


def test_syntax_errors_in_python_javascript_are_reported(tmp_path):
    app = _INLINE_APP.replace("this.missing = 1;", "const = 1;")
    project, documents = _documents(tmp_path, {}, app=app)
    document = DocumentState((tmp_path / "app.py").as_uri(), "python", app, 1)
    document.update(app, 1, project)
    documents[document.uri] = document

    found = _findings(tmp_path, "app.py", project, documents)

    assert ("citry.typescript.ts1134", "=", (22, 18, 22, 19)) in found


def test_generated_text_unreported_codes_and_template_names_are_dropped():
    mapping = ProjectionSourceMapping(
        types.Range(types.Position(3, 10), types.Position(3, 20)),
        types.Range(types.Position(40, 0), types.Position(40, 10)),
    )
    projections = (
        TypeCheckProjection("template:0", "", (mapping,)),
        TypeCheckProjection("js:0", "", (mapping,)),
    )

    def finding(file_id: str, code: int, start: int, end: int, category: str = "error") -> TypeScriptFinding:
        value = types.Range(types.Position(40, start), types.Position(40, end))
        return TypeScriptFinding(file_id, value, code, "message", category)  # type: ignore[arg-type]

    mapped = map_type_check_findings(
        projections,
        (
            finding("js:0", 2322, 2, 5),
            # Crosses into generated text.
            finding("js:0", 2322, 5, 12),
            # A warning, an implicit-any opinion, and a template's unknown name.
            finding("js:0", 2322, 2, 5, "warning"),
            finding("js:0", 7006, 2, 5),
            finding("template:0", 2304, 2, 5),
            # The same unknown name in component JavaScript is kept.
            finding("js:0", 2304, 6, 8),
            finding("missing:0", 2322, 2, 5),
        ),
    )

    assert [(item.code, item.range.start.character, item.range.end.character) for item in mapped] == [
        ("citry.typescript.ts2322", 12, 15),
        ("citry.typescript.ts2304", 16, 18),
    ]


def test_a_citry_finding_on_the_same_text_wins():
    mapping = ProjectionSourceMapping(
        types.Range(types.Position(0, 0), types.Position(0, 10)),
        types.Range(types.Position(5, 0), types.Position(5, 10)),
    )
    projection = TypeCheckProjection("js:0", "", (mapping,))
    finding = TypeScriptFinding("js:0", types.Range(types.Position(5, 2), types.Position(5, 6)), 2345, "m")
    citry = types.Diagnostic(
        types.Range(types.Position(0, 1), types.Position(0, 3)),
        "undeclared",
        code="citry.browser.undeclared-emit",
    )
    unrelated = types.Diagnostic(
        types.Range(types.Position(0, 1), types.Position(0, 3)),
        "csp",
        code="citry.csp.incompatible-browser-code",
    )

    assert map_type_check_findings((projection,), (finding,), (citry,)) == ()
    assert len(map_type_check_findings((projection,), (finding,), (unrelated,))) == 1


def test_tsc_output_is_read_with_chained_messages():
    source = "// @ts-check\nthis.clearDropTarget = true;\n"
    output = (
        "projection-0.js(2,1): error TS2322: Type 'boolean' is not assignable to type '() => void'.\n"
        "  The detail line.\n"
        "/somewhere/vue.d.ts(9,9): error TS2300: Duplicate identifier 'x'.\n"
    )

    (finding,) = parse_tsc_output(output, {"projection-0.js": ("js:0", source)})

    assert finding.file_id == "js:0"
    assert finding.code == 2322
    assert finding.message.endswith("\nThe detail line.")
    assert finding.range == types.Range(types.Position(1, 0), types.Position(1, 20))


def test_tsc_output_is_read_when_the_folder_name_has_parentheses():
    output = "../tmp (x)/projection-0.js(1,1): error TS2322: m\n"

    (finding,) = parse_tsc_output(output, {"projection-0.js": ("js:0", "value")})

    assert finding.range.end == types.Position(0, 5)


def test_a_configuration_error_stops_the_check():
    with pytest.raises(TypeScriptUnavailableError, match="TS5023"):
        parse_tsc_output("error TS5023: Unknown compiler option 'x'.\n", {})


def test_tsc_is_found_in_the_nearest_node_modules(tmp_path, monkeypatch):
    monkeypatch.setattr("citry_lsp.typescript.shutil.which", lambda name: "/bin/node" if name == "node" else None)
    tsc = tmp_path / "node_modules" / ".bin" / "tsc"
    tsc.parent.mkdir(parents=True)
    tsc.write_text("", encoding="utf-8")
    nested = tmp_path / "app" / "components"
    nested.mkdir(parents=True)

    assert find_typescript_compiler(nested) == (str(tsc),)


def test_missing_node_or_tsc_names_what_to_install(tmp_path, monkeypatch):
    monkeypatch.setattr("citry_lsp.typescript.shutil.which", lambda _name: None)
    with pytest.raises(TypeScriptUnavailableError, match=r"Node\.js was not found"):
        find_typescript_compiler(tmp_path)
    monkeypatch.setattr("citry_lsp.typescript.shutil.which", lambda name: "/bin/node" if name == "node" else None)
    with pytest.raises(TypeScriptUnavailableError, match="npm install --save-dev typescript"):
        find_typescript_compiler(tmp_path)


def test_client_answers_are_validated():
    answer = {
        "version": 1,
        "files": [
            {
                "id": "js:0",
                "diagnostics": [
                    {
                        "range": {"start": {"line": 1, "character": 2}, "end": {"line": 1, "character": 4}},
                        "code": 2322,
                        "message": "m",
                        "category": "error",
                    }
                ],
            }
        ],
    }

    parsed = parse_type_check_response(answer, ["js:0"])
    assert parsed is not None
    (finding,) = parsed
    assert finding.range.end == types.Position(1, 4)
    # The client could not run TypeScript this time.
    assert parse_type_check_response(None, ["js:0"]) is None
    for invalid in (
        {"version": 2, "files": []},
        {"version": 1, "files": [{"id": "js:9", "diagnostics": []}]},
        {"version": 1, "files": [{"id": "js:0", "diagnostics": [{"code": "2322"}]}]},
    ):
        with pytest.raises(ValueError, match="citry/typeCheck"):
            parse_type_check_response(invalid, ["js:0"])


def test_minified_component_javascript_is_not_checked(tmp_path):
    app = _APP.replace("js_file = 'lane.js'", "js_file = 'lane.min.js'")
    project, documents = _documents(
        tmp_path,
        {"lane.min.js": ("javascript", "$component({methods:{a(){this.b=1}}});"), "lane.html": ("citry-html", "<p/>")},
        app=app,
    )

    assert type_check_projections(documents[(tmp_path / "lane.min.js").as_uri()], project, documents) == ()


# --- The language server asks the client to run TypeScript -------------------


@pytest_lsp.fixture(config=ClientServerConfig(server_command=[sys.executable, "-m", "citry_lsp"]))
async def type_check_client(client: LanguageClient, tmp_path):
    (tmp_path / "app.py").write_text(_APP, encoding="utf-8")
    for name, source in (("lane.js", _LANE_JS), ("lane.html", _LANE_HTML), ("card.html", _CARD_HTML)):
        (tmp_path / name).write_text(source, encoding="utf-8")
    (tmp_path / "card.js").write_text("$component({});\n", encoding="utf-8")
    client.type_check_requests = []  # type: ignore[attr-defined]

    @client.feature("citry/status")
    def receive_status(_client: LanguageClient, _params: object) -> None:
        return None

    @client.feature(TYPE_CHECK_METHOD)
    def type_check(_client: LanguageClient, params: object) -> dict[str, object]:
        # Answer as VS Code's TypeScript server does, by running TypeScript on the files.
        client.type_check_requests.append(params)  # type: ignore[attr-defined]
        files = [(item.id, item.source) for item in params.files]  # type: ignore[attr-defined]
        findings = run_typescript_compiler(_command(), files)
        return {
            "version": 1,
            "files": [
                {
                    "id": file_id,
                    "diagnostics": [
                        {
                            "range": {
                                "start": {"line": item.range.start.line, "character": item.range.start.character},
                                "end": {"line": item.range.end.line, "character": item.range.end.character},
                            },
                            "code": item.code,
                            "message": item.message,
                            "category": item.category,
                        }
                        for item in findings
                        if item.file_id == file_id
                    ],
                }
                for file_id, _source in files
            ],
        }

    await client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={
                "protocolVersion": PROTOCOL_VERSION,
                "app": "app:engine",
                "typeCheckClient": {"version": 1},
            },
        )
    )
    yield
    await client.shutdown_session()


@pytest.mark.asyncio
async def test_the_editor_receives_typescript_findings_from_the_client(type_check_client, tmp_path):
    _command()
    uri = (tmp_path / "lane.js").as_uri()
    type_check_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "javascript", 1, _LANE_JS))
    )

    # Citry publishes its own findings first and adds TypeScript's when the client answers.
    for _attempt in range(200):
        codes = [diagnostic.code for diagnostic in type_check_client.diagnostics.get(uri, ())]
        if "citry.typescript.ts2554" in codes:
            break
        await asyncio.sleep(0.05)
    assert sorted(code for code in codes if str(code).startswith("citry.typescript.")) == [
        "citry.typescript.ts2322",
        "citry.typescript.ts2339",
        "citry.typescript.ts2345",
        "citry.typescript.ts2554",
    ]
    assert "citry.component-js.unknown-member" in codes
    (request,) = type_check_client.type_check_requests[:1]
    assert request.textDocument.uri == uri
    assert [item.id for item in request.files] == ["js:0"]


async def _typescript_ranges(client: LanguageClient, uri: str, expected: set[int]) -> set[int]:
    """Wait until the document's TypeScript findings start at exactly `expected` characters."""
    found: set[int] = set()
    for _attempt in range(200):
        found = {
            diagnostic.range.start.character
            for diagnostic in client.diagnostics.get(uri, ())
            if str(diagnostic.code).startswith("citry.typescript.")
        }
        if found == expected:
            break
        await asyncio.sleep(0.05)
    return found


@pytest.mark.asyncio
async def test_a_component_javascript_change_rechecks_its_open_template(type_check_client, tmp_path):
    _command()
    js_uri = (tmp_path / "lane.js").as_uri()
    html_uri = (tmp_path / "lane.html").as_uri()
    for uri, language, source in ((js_uri, "javascript", _LANE_JS), (html_uri, "citry-html", _LANE_HTML)):
        type_check_client.text_document_did_open(
            types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, language, 1, source))
        )
    # `startDrag('a')` and the `$emit` payload `'y'` are both wrong.
    assert await _typescript_ranges(type_check_client, html_uri, {26, 59}) == {26, 59}

    # Only the JavaScript changes: `startDrag` now takes a string.
    changed = _LANE_JS.replace("/** @type {number} */ id", "/** @type {string} */ id")
    type_check_client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            types.VersionedTextDocumentIdentifier(version=2, uri=js_uri),
            [types.TextDocumentContentChangeWholeDocument(changed)],
        )
    )

    assert await _typescript_ranges(type_check_client, html_uri, {59}) == {59}


def _configured(tmp_path, options: dict[str, object]) -> CitryLanguageServer:
    language_server = CitryLanguageServer()
    language_server.configure(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={"protocolVersion": PROTOCOL_VERSION, "app": None, **options},
        )
    )
    return language_server


def test_type_check_options_are_validated(tmp_path):
    assert _configured(tmp_path, {}).type_check is True
    assert _configured(tmp_path, {}).type_check_client is False
    assert _configured(tmp_path, {"typeCheck": False}).type_check is False
    assert _configured(tmp_path, {"typeCheckClient": {"version": 1}}).type_check_client is True
    # A client version this server does not know makes the server run `tsc` itself.
    assert _configured(tmp_path, {"typeCheckClient": {"version": 2, "extra": True}}).type_check_client is False
    invalid_options: tuple[dict[str, object], ...] = (
        {"typeCheck": "yes"},
        {"typeCheckClient": {"version": "1"}},
        {"typeCheckClient": True},
    )
    for invalid in invalid_options:
        with pytest.raises(JsonRpcInvalidParams, match="typeCheck"):
            _configured(tmp_path, invalid)


# --- `citry check --types` ------------------------------------------------------


def _run_check(tmp_path: Path, path_entries: list[str]) -> subprocess.CompletedProcess[str]:
    """Run `citry check --types --format json` in `tmp_path` with exactly `path_entries` on PATH."""
    environment = {**os.environ, "PATH": os.pathsep.join(path_entries), "NO_COLOR": "1"}
    environment.pop("FORCE_COLOR", None)
    return subprocess.run(
        [sys.executable, "-m", "citry", "--app", "app:engine", "check", "--types", "--format", "json"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_types_reports_findings_with_file_positions(tmp_path):
    tsc = Path(_command()[0])
    (tmp_path / "app.py").write_text(_APP, encoding="utf-8")
    for name, source in (("lane.js", _LANE_JS), ("lane.html", _LANE_HTML), ("card.html", _CARD_HTML)):
        (tmp_path / name).write_text(source, encoding="utf-8")
    (tmp_path / "card.js").write_text("$component({});\n", encoding="utf-8")

    node = shutil.which("node")
    assert node is not None
    # The package-manager shim for `tsc` is a shell script that needs the system tools.
    result = _run_check(tmp_path, [str(tsc.parent), str(Path(node).parent), "/usr/bin", "/bin"])

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    typed = [item for item in payload["findings"] if item["code"].startswith("citry.typescript.")]
    lane_js = str((tmp_path / "lane.js").resolve())
    assert [(item["origin"], item["code"]) for item in typed] == [
        (f"{(tmp_path / 'card.html').resolve()!s}:1:53", "citry.typescript.ts2339"),
        (f"{(tmp_path / 'lane.html').resolve()!s}:1:27", "citry.typescript.ts2345"),
        (f"{(tmp_path / 'lane.html').resolve()!s}:1:60", "citry.typescript.ts2345"),
        (f"{lane_js}:10:7", "citry.typescript.ts2322"),
        (f"{lane_js}:11:31", "citry.typescript.ts2345"),
        (f"{lane_js}:13:25", "citry.typescript.ts2554"),
        (f"{lane_js}:14:16", "citry.typescript.ts2339"),
    ]
    # JSON keeps TypeScript's message as it is; the text report prefixes the code.
    assert typed[0]["message"] == "Property 'nope' does not exist on type '{ taskId: number; }'."
    # The JSON range is the file's own zero-based position.
    assert typed[3]["range"]["start"] == {"line": 9, "column": 6}


def test_check_types_says_what_to_install_without_node(tmp_path):
    (tmp_path / "app.py").write_text(_APP, encoding="utf-8")
    for name, source in (("lane.js", _LANE_JS), ("lane.html", _LANE_HTML), ("card.html", _CARD_HTML)):
        (tmp_path / name).write_text(source, encoding="utf-8")
    (tmp_path / "card.js").write_text("$component({});\n", encoding="utf-8")

    empty = tmp_path / "empty-bin"
    empty.mkdir()
    result = _run_check(tmp_path, [str(empty)])

    assert result.returncode == 2
    assert "--types cannot run TypeScript: Node.js was not found on PATH" in result.stderr
    assert "npm install --save-dev typescript" in result.stderr


_TY_APP = """from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)
class Title(Component):
    citry = engine
    template_file = 'title.html'
    class TemplateData:
        title: str
    def template_data(self, kwargs, slots):
        return {"title": "Board"}
"""

# `title + 1` adds a number to a string; `missing` is Citry's own finding.
_TITLE_HTML = "<h3>{{ title + 1 }}</h3><p>{{ missing }}</p>"


def test_check_project_python_types_reports_ty_findings_like_the_editor(tmp_path):
    (tmp_path / "app.py").write_text(_TY_APP, encoding="utf-8")
    (tmp_path / "title.html").write_text(_TITLE_HTML, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status

    found = check_project_python_types(project, tmp_path)

    # ty's own unknown-name finding is dropped, as in the editor, because
    # Citry's unknown-variable rule owns that mistake.
    assert [
        (item.path.name, item.diagnostic.code, item.diagnostic.range.start.character, item.diagnostic.severity)
        for item in found
    ] == [("title.html", "citry.python.unsupported-operator", 7, types.DiagnosticSeverity.Error)]
    assert found[0].diagnostic.source == "Citry (ty)"


def test_check_types_reports_ty_findings_in_both_formats(tmp_path):
    tsc = Path(_command()[0])
    (tmp_path / "app.py").write_text(_TY_APP, encoding="utf-8")
    (tmp_path / "title.html").write_text(_TITLE_HTML, encoding="utf-8")
    node = shutil.which("node")
    assert node is not None
    path_entries = [str(tsc.parent), str(Path(node).parent), "/usr/bin", "/bin"]

    result = _run_check(tmp_path, path_entries)

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    typed = [item for item in payload["findings"] if item["code"].startswith("citry.python.")]
    assert [(item["origin"], item["code"], item["severity"]) for item in typed] == [
        (f"{(tmp_path / 'title.html').resolve()!s}:1:8", "citry.python.unsupported-operator", "error"),
    ]
    environment = {**os.environ, "PATH": os.pathsep.join(path_entries), "NO_COLOR": "1"}
    environment.pop("FORCE_COLOR", None)
    text = subprocess.run(
        [sys.executable, "-m", "citry", "--app", "app:engine", "check", "--types"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    # ty's rule name leads the message, as `ty check` prints it.
    assert f"{(tmp_path / 'title.html').resolve()!s}:1:8: error: unsupported-operator: Operator `+`" in text.stderr


def test_check_types_stops_when_ty_cannot_run(tmp_path, monkeypatch, capsys):
    (tmp_path / "app.py").write_text(_TY_APP, encoding="utf-8")
    (tmp_path / "title.html").write_text(_TITLE_HTML, encoding="utf-8")
    # TypeScript is not under test here; a missing ty executable makes the
    # real analyzer fail to start.
    monkeypatch.setattr("citry_lsp.typescript.find_typescript_compiler", lambda _cwd: ("tsc",))
    monkeypatch.setattr("citry_lsp.typescript.check_project_types", lambda *_args: ())
    monkeypatch.setattr("citry_lsp.type_analysis._installed_ty_executable", lambda: tmp_path / "missing-ty")
    monkeypatch.syspath_prepend(str(tmp_path))

    with pytest.raises(SystemExit) as exited:
        _with_type_findings(CheckReport((), None, ()), "app:engine", tmp_path)

    assert exited.value.code == 2
    assert "--types cannot run ty: Python expression analysis is unavailable" in capsys.readouterr().err


_INLINE_FILES = {
    "engine_setup.py": "from citry import Citry\nengine = Citry(autodiscover=False)\n",
    "app.py": """from citry import Component
from engine_setup import engine
import cards
class First(Component):
    citry = engine
    template = "<p>{{ title + 1 }}</p>"
    class TemplateData:
        title: str
    def template_data(self, kwargs, slots):
        return {"title": "First"}
""",
    "cards.py": """from citry import Component
from engine_setup import engine
class Second(Component):
    citry = engine
    template = "<p>{{ count + 'x' }}</p>"
    class TemplateData:
        count: int
    def template_data(self, kwargs, slots):
        return {"count": 1}
""",
}


@pytest.mark.parametrize("line_end", ["\n", "\r\n"], ids=["lf", "crlf"])
def test_check_project_python_types_reads_inline_templates_with_any_line_ending(tmp_path, line_end):
    # Two Python files with inline templates are both passed to ty as open
    # files, so their text must match what ty reads from disk, even with
    # CRLF line endings and a byte order mark.
    for name, source in _INLINE_FILES.items():
        prefix = "\ufeff" if name == "cards.py" else ""
        (tmp_path / name).write_bytes((prefix + source).replace("\n", line_end).encode("utf-8"))
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status

    found = check_project_python_types(project, tmp_path)

    assert sorted((item.path.name, item.diagnostic.code) for item in found) == [
        ("app.py", "citry.python.unsupported-operator"),
        ("cards.py", "citry.python.unsupported-operator"),
    ]


def _server_with_documents(tmp_path: Path, options: dict[str, object]) -> tuple[CitryLanguageServer, DocumentState]:
    project, documents = _documents(
        tmp_path,
        {
            "lane.js": ("javascript", _LANE_JS),
            "lane.html": ("citry-html", _LANE_HTML),
            "card.html": ("citry-html", _CARD_HTML),
            "card.js": ("javascript", "$component({});\n"),
        },
    )
    language_server = _configured(tmp_path, options)
    language_server.project = project
    language_server.documents = documents
    return language_server, documents[(tmp_path / "lane.js").as_uri()]


@pytest.mark.asyncio
async def test_the_server_runs_tsc_for_an_editor_without_a_typescript_client(tmp_path, monkeypatch):
    command = _command()
    monkeypatch.setattr("citry_lsp.server.find_typescript_compiler", lambda _workspace: command)
    language_server, document = _server_with_documents(tmp_path, {})
    citry = browser_diagnostics(document, language_server.project, language_server.documents)

    found = await language_server.typescript_diagnostics(document, citry)

    assert found is not None
    assert sorted(str(item.code) for item in found) == [
        "citry.typescript.ts2322",
        "citry.typescript.ts2339",
        "citry.typescript.ts2345",
        "citry.typescript.ts2554",
    ]
    # An unchanged document is answered from the last check instead of a new `tsc` run.
    language_server.type_findings[document.uri] = found

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("an unchanged document must not start tsc")

    monkeypatch.setattr("citry_lsp.server.run_typescript_compiler_async", forbidden)
    assert await language_server.typescript_diagnostics(document, citry) == found
    # The reused answer is filtered against Citry's current findings: a Citry
    # finding on the `'x'` payload now owns that mistake.
    owner = types.Diagnostic(
        types.Range(types.Position(10, 30), types.Position(10, 33)), "m", code="citry.browser.undeclared-emit"
    )
    again = await language_server.typescript_diagnostics(document, (*citry, owner))
    assert again is not None
    assert len(again) == len(found) - 1


@pytest.mark.asyncio
async def test_a_cancelled_or_slow_tsc_is_stopped(tmp_path):
    started = tmp_path / "started"
    # Stands in for a slow `tsc`; the extra arguments the runner adds are ignored.
    command = ("/bin/sh", "-c", f"touch {started}; exec sleep 30")
    task = asyncio.create_task(run_typescript_compiler_async(command, [("js:0", "")], timeout=30))
    for _attempt in range(100):
        if started.exists():
            break
        await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=5)

    with pytest.raises(TypeScriptUnavailableError, match="longer than"):
        await run_typescript_compiler_async(command, [("js:0", "")], timeout=0.2)


@pytest.mark.asyncio
async def test_a_missing_tsc_logs_once_and_is_looked_for_again_later(tmp_path, monkeypatch):
    searches: list[Path] = []

    def missing(workspace: Path) -> tuple[str, ...]:
        searches.append(workspace)
        raise TypeScriptUnavailableError("tsc was not found.")

    monkeypatch.setattr("citry_lsp.server.find_typescript_compiler", missing)
    language_server, document = _server_with_documents(tmp_path, {})
    logged: list[types.LogMessageParams] = []
    monkeypatch.setattr(language_server, "window_log_message", logged.append)

    assert await language_server.typescript_diagnostics(document, ()) == ()
    assert await language_server.typescript_diagnostics(document, ()) == ()
    assert len(searches) == 1
    assert len(logged) == 1
    assert "looks again every minute" in logged[0].message

    # A minute later the server looks again.
    language_server._typescript_missing_since = -1000.0
    assert await language_server.typescript_diagnostics(document, ()) == ()
    assert len(searches) == 2
    assert len(logged) == 1


def test_previous_findings_stay_only_on_untouched_lines(tmp_path):
    language_server, document = _server_with_documents(tmp_path, {})
    finding = types.Diagnostic(types.Range(types.Position(9, 6), types.Position(9, 26)), "m")
    language_server.type_findings[document.uri] = (finding,)
    language_server._type_findings_source[document.uri] = document.source

    assert language_server._previous_type_findings(document) == (finding,)
    # Editing another line keeps it; editing its line or adding a line drops it.
    for changed, kept in (
        (document.source.replace("dragging: false", "dragging: true"), True),
        (document.source.replace("this.clearDropTarget = true", "this.clearDropTarget = 1"), False),
        ("\n" + document.source, False),
    ):
        document.source = changed
        assert language_server._previous_type_findings(document) == ((finding,) if kept else ())


@pytest_lsp.fixture(config=ClientServerConfig(server_command=[sys.executable, "-m", "citry_lsp"]))
async def type_check_off_client(client: LanguageClient, tmp_path):
    (tmp_path / "app.py").write_text(_APP, encoding="utf-8")
    for name, source in (("lane.js", _LANE_JS), ("lane.html", _LANE_HTML), ("card.html", _CARD_HTML)):
        (tmp_path / name).write_text(source, encoding="utf-8")
    (tmp_path / "card.js").write_text("$component({});\n", encoding="utf-8")
    client.type_check_requests = []  # type: ignore[attr-defined]

    @client.feature("citry/status")
    def receive_status(_client: LanguageClient, _params: object) -> None:
        return None

    @client.feature(TYPE_CHECK_METHOD)
    def type_check(_client: LanguageClient, params: object) -> None:
        client.type_check_requests.append(params)  # type: ignore[attr-defined]

    await client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=tmp_path.as_uri(),
            initialization_options={
                "protocolVersion": PROTOCOL_VERSION,
                "app": "app:engine",
                "typeCheck": False,
                "typeCheckClient": {"version": 1},
            },
        )
    )
    yield
    await client.shutdown_session()


@pytest.mark.asyncio
async def test_type_check_off_sends_no_request_and_publishes_only_citry_findings(type_check_off_client, tmp_path):
    uri = (tmp_path / "lane.js").as_uri()
    type_check_off_client.text_document_did_open(
        types.DidOpenTextDocumentParams(types.TextDocumentItem(uri, "javascript", 1, _LANE_JS))
    )
    for _attempt in range(200):
        codes = [diagnostic.code for diagnostic in type_check_off_client.diagnostics.get(uri, ())]
        if "citry.component-js.unknown-member" in codes:
            break
        await asyncio.sleep(0.05)
    await asyncio.sleep(0.5)

    assert "citry.component-js.unknown-member" in codes
    assert not [code for code in codes if str(code).startswith("citry.typescript.")]
    assert type_check_off_client.type_check_requests == []


_INFERRED_APP = """from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from citry import Citry, Component
engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)

@dataclass
class Task:
    title: str

Label = str

class Rows(Component):
    citry = engine
    template_file = 'rows.html'
    js_file = 'rows.js'
    class Kwargs:
        names: list[str]
        flag: bool = False
    def labels(self) -> list[Label]:
        return []
    def task(self) -> Task:
        return Task("x")
    def js_data(self, kwargs: Kwargs, slots):
        return {
            "labels": self.labels(),
            "upper": [name.upper() for name in kwargs.names],
            "joined": ", ".join(kwargs.names),
            "mode": "a" if kwargs.flag else self.labels(),
            "task": self.task(),
        }
"""

# Each line before the last misuses one value that only ty can type. A
# `Task` instance cannot cross the JSON wire, so it stays `any`.
_INFERRED_JS = """$component({
  methods: {
    check() {
      this.labels.toFixed();
      this.upper.push(1);
      this.joined.toFixed();
      this.mode.toFixed();
      this.task.anything;
    },
  },
});
"""


async def _infer_js_data(tmp_path: Path, project, documents) -> None:
    analyzer = TyAnalyzer(tmp_path)
    try:
        await infer_js_data_value_types(analyzer, project, documents)
    finally:
        await analyzer.close()


def test_ty_types_the_js_data_values_citry_rules_leave_unknown(tmp_path):
    _command()
    project, documents = _documents(
        tmp_path,
        {"rows.html": ("citry-html", "<p></p>"), "rows.js": ("javascript", _INFERRED_JS)},
        app=_INFERRED_APP,
    )
    # Before ty answers, every value Citry's rules cannot type is `any`.
    assert _findings(tmp_path, "rows.js", project, documents) == []

    asyncio.run(_infer_js_data(tmp_path, project, documents))

    # A method's return type, a comprehension, a str method, and a
    # conditional expression each reach TypeScript.
    assert [(code, text) for code, text, _range in _findings(tmp_path, "rows.js", project, documents)] == [
        ("citry.typescript.ts2339", "toFixed"),
        ("citry.typescript.ts2345", "1"),
        ("citry.typescript.ts2551", "toFixed"),
        ("citry.typescript.ts2339", "toFixed"),
    ]


def test_check_types_reads_ty_js_data_types_before_typescript(tmp_path):
    tsc = Path(_command()[0])
    (tmp_path / "app.py").write_text(_INFERRED_APP, encoding="utf-8")
    (tmp_path / "rows.html").write_text("<p></p>", encoding="utf-8")
    (tmp_path / "rows.js").write_text(_INFERRED_JS, encoding="utf-8")
    node = shutil.which("node")
    assert node is not None

    result = _run_check(tmp_path, [str(tsc.parent), str(Path(node).parent), "/usr/bin", "/bin"])

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    rows_js = str((tmp_path / "rows.js").resolve())
    assert [item["origin"] for item in payload["findings"] if item["code"].startswith("citry.typescript.")] == [
        f"{rows_js}:4:19",
        f"{rows_js}:5:23",
        f"{rows_js}:6:19",
        f"{rows_js}:7:17",
    ]


@pytest.mark.parametrize(
    ("display", "expected"),
    [
        ("list[str]", "Array<string>"),
        ('Literal["a", "b"] | None', "string | null"),
        ("LiteralString", "string"),
        ("dict[str, int]", "{[key: string]: number}"),
        ("tuple[int, str]", "Array<number | string>"),
        # A type ty could not infer, a class, `Any`, or a shortened display
        # names no JSON value, so the part stays `any`.
        ("Unknown", None),
        ("list[Unknown]", None),
        ("Task", None),
        ("dict[str, Any]", None),
        ("int | str | ... omitted 3 union elements", None),
    ],
)
def test_ty_type_displays_become_json_types(display, expected):
    value = _json_type_from_ty_display(display)

    assert (value.javascript if value is not None else None) == expected


def test_a_bound_string_the_attribute_rule_reports_is_not_reported_by_typescript(tmp_path):
    command = _command()
    project, documents = _documents(
        tmp_path,
        {"bound.html": ("citry-html", '<div :draggable="\'treu\'" :dir="\'rlt\'" :style="1"></div>')},
        app=_BOUND_APP,
    )
    document = documents[(tmp_path / "bound.html").as_uri()]

    typed = check_project_types(project, tmp_path, command, documents)
    citry = template_lint_diagnostics(document, project, documents)

    # Vue types `draggable` as a boolean, so TypeScript would also reject
    # 'treu'; Citry's finding names the closest keyword, so only it is kept.
    # Vue types `dir` as any string, so only Citry reports 'rlt'.
    assert [(item.code, item.range.start.character) for item in citry] == [
        ("citry.template.invalid-attribute-value", 17),
        ("citry.template.invalid-attribute-value", 31),
    ]
    assert [(item.diagnostic.code, item.diagnostic.range.start.character) for item in typed] == [
        ("citry.typescript.ts2345", 46),
    ]


def _rows_project(tmp_path: Path, app: str = _INFERRED_APP):
    return _documents(
        tmp_path,
        {"rows.html": ("citry-html", '<p v-text="labels"></p>'), "rows.js": ("javascript", _INFERRED_JS)},
        app=app,
    )


def _labels_type(project, documents, tmp_path: Path) -> str:
    """Return the type the template's projection gives `labels`."""
    template = documents[(tmp_path / "rows.html").as_uri()]
    projection = browser_projection(template, types.Position(0, 12), project, documents)
    assert projection is not None
    lines = projection.source.splitlines()
    return lines[lines.index("var labels;") - 1]


def test_js_data_answers_survive_a_reload_and_follow_a_saved_edit(tmp_path):
    project, documents = _rows_project(tmp_path)
    asyncio.run(_infer_js_data(tmp_path, project, documents))
    assert _labels_type(project, documents, tmp_path) == "/** @type {Array<string>} */"

    # A reloaded project keeps using the answers, but asks ty again.
    reloaded, documents = _rows_project(tmp_path)
    reloaded.adopt_js_data_inferred_types(project, stale=True)
    assert _labels_type(reloaded, documents, tmp_path) == "/** @type {Array<string>} */"
    assert not reloaded.has_js_data_inferred_types(tmp_path / "app.py", _INFERRED_APP, "Rows")
    asyncio.run(_infer_js_data(tmp_path, reloaded, documents))
    assert reloaded.has_js_data_inferred_types(tmp_path / "app.py", _INFERRED_APP, "Rows")

    # A saved edit is asked about again, and only the newest text is kept.
    edited, documents = _rows_project(tmp_path, _INFERRED_APP.replace("Label = str", "Label = int"))
    edited.adopt_js_data_inferred_types(reloaded, stale=True)
    asyncio.run(_infer_js_data(tmp_path, edited, documents))
    assert _labels_type(edited, documents, tmp_path) == "/** @type {Array<number>} */"
    assert len(edited._js_data_inferred) == 1


def test_js_data_values_stay_any_when_the_module_uses_reveal_type(tmp_path):
    app = _INFERRED_APP.replace("def task(self) -> Task:", "def task(self) -> Task:  # reveal_type\n   ")
    project, documents = _rows_project(tmp_path, app)

    asyncio.run(_infer_js_data(tmp_path, project, documents))

    # The module's own `reveal_type` would hide ty's, so nothing is asked.
    assert _labels_type(project, documents, tmp_path) == "/** @type {any} */"


class _FailedAnalyzer:
    failure = "ty is not installed"

    async def diagnostics(self, *_args: object, **_kwargs: object) -> tuple[()]:
        raise AssertionError


def test_js_data_inference_does_nothing_without_ty(tmp_path, monkeypatch):
    project, documents = _rows_project(tmp_path)
    scanned: list[object] = []
    monkeypatch.setattr("citry_lsp.semantic.js_data_inference_requests", lambda *args: scanned.append(args) or ())

    asyncio.run(infer_js_data_value_types(_FailedAnalyzer(), project, documents))  # type: ignore[arg-type]

    # A ty that cannot run is not asked, and the sources are not scanned for it.
    assert scanned == []
