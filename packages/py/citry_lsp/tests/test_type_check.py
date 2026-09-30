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

from citry_lsp.engine import (
    DocumentState,
    ProjectionSourceMapping,
    TypeCheckProjection,
    browser_diagnostics,
    type_check_projections,
)
from citry_lsp.project import load_project
from citry_lsp.protocol import PROTOCOL_VERSION, TYPE_CHECK_METHOD
from citry_lsp.server import CitryLanguageServer
from citry_lsp.typescript import (
    TypeScriptFinding,
    TypeScriptUnavailableError,
    check_document_types,
    find_typescript_compiler,
    map_type_check_findings,
    parse_tsc_output,
    parse_type_check_response,
    run_typescript_compiler,
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

    (finding,) = parse_type_check_response(answer, ["js:0"])
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
    invalid_options: tuple[dict[str, object], ...] = (
        {"typeCheck": "yes"},
        {"typeCheckClient": {"version": 2}},
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
    assert [(item["origin"], item["code"], item["message"].split(":", 1)[0]) for item in typed] == [
        (f"{(tmp_path / 'card.html').resolve()!s}:1:53", "citry.typescript.ts2339", "TS2339"),
        (f"{(tmp_path / 'lane.html').resolve()!s}:1:27", "citry.typescript.ts2345", "TS2345"),
        (f"{(tmp_path / 'lane.html').resolve()!s}:1:60", "citry.typescript.ts2345", "TS2345"),
        (f"{lane_js}:10:7", "citry.typescript.ts2322", "TS2322"),
        (f"{lane_js}:11:31", "citry.typescript.ts2345", "TS2345"),
        (f"{lane_js}:13:25", "citry.typescript.ts2554", "TS2554"),
        (f"{lane_js}:14:16", "citry.typescript.ts2339", "TS2339"),
    ]
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
