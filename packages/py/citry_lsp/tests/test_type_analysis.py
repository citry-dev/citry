"""Tests for the pinned Python analyzer adapter."""

from __future__ import annotations

import asyncio
import sys
import venv
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, cast

import pytest
from lsprotocol import types
from pygls.client import JsonRPCClient

from citry.analysis import TemplatePythonQuery, TemplatePythonRoot, build_inferred_template_shadow
from citry_lsp import type_analysis
from citry_lsp.type_analysis import (
    TyAnalyzer,
    TyDocument,
    TyUnavailableError,
    _bounded_client_request,
    _is_ty_vendored_stdlib_path,
    _safe_completion_item,
    _stop_client,
    offset_at_position,
    position_at_offset,
    virtual_document_uri,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def short_ty_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise shutdown escalation without paying production wall-clock bounds."""
    monkeypatch.setattr(type_analysis, "_CLIENT_STOP_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(type_analysis, "_PROCESS_STOP_TIMEOUT_SECONDS", 0.1)


def test_utf16_positions_round_trip_without_splitting_astral_characters() -> None:
    source = "first\n😀value.lower()\n"
    offset = source.index("lower") + 3

    position = position_at_offset(source, offset)

    assert position == types.Position(1, 11)
    assert offset_at_position(source, position) == offset
    assert offset_at_position(source, types.Position(1, 1)) is None


@pytest.mark.parametrize(
    "path",
    [
        PurePosixPath("/Users/dev/.cache/ty/vendored/typeshed/revision/stdlib/builtins.pyi"),
        PureWindowsPath("C:/Users/dev/AppData/Local/ty/cache/vendored/typeshed/revision/stdlib/builtins.pyi"),
    ],
)
def test_ty_vendored_stdlib_path_accepts_platform_cache_layouts(path: PurePath) -> None:
    assert _is_ty_vendored_stdlib_path(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePosixPath("/workspace/ty/vendored/typeshed/revision/stubs/package.pyi"),
        PureWindowsPath("C:/cache/other/vendored/typeshed/revision/stdlib/builtins.pyi"),
    ],
)
def test_ty_vendored_stdlib_path_rejects_unowned_stub_locations(path: PurePath) -> None:
    assert not _is_ty_vendored_stdlib_path(path)


def test_ty_cleanup_escalation_fits_inside_the_editor_server_stop_bound() -> None:
    worst_case = 2 * (type_analysis._CLIENT_STOP_TIMEOUT_SECONDS + type_analysis._PROCESS_STOP_TIMEOUT_SECONDS)

    assert worst_case < 1.5


@pytest.mark.asyncio
async def test_cancelled_child_request_consumes_a_late_response_without_cancelling_its_future() -> None:
    pending: asyncio.Future[object] = asyncio.get_running_loop().create_future()
    request_started = asyncio.Event()
    notifications: list[tuple[str, object]] = []

    class Protocol:
        def send_request_async(self, *_args, **_kwargs):
            request_started.set()
            return pending

        def notify(self, method: str, params: object) -> None:
            notifications.append((method, params))

    client = cast("JsonRPCClient", type("Client", (), {"protocol": Protocol()})())
    requesting = asyncio.create_task(_bounded_client_request(client, "probe", {}, 1.0))
    await request_started.wait()

    requesting.cancel()

    with pytest.raises(asyncio.CancelledError):
        await requesting
    assert not pending.cancelled()
    assert [method for method, _params in notifications] == [types.CANCEL_REQUEST]

    pending.set_result({"late": True})
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_close_preempts_an_active_analyzer_request(tmp_path: Path) -> None:
    pending: asyncio.Future[object] = asyncio.get_running_loop().create_future()
    request_started = asyncio.Event()
    notifications: list[str] = []

    class Protocol:
        def send_request_async(self, method, _params=None, **_kwargs):
            result: asyncio.Future[object] = asyncio.get_running_loop().create_future()
            if method == types.TEXT_DOCUMENT_HOVER:
                request_started.set()
                return pending
            result.set_result(None)
            return result

        def notify(self, method: str, _params: object) -> None:
            notifications.append(method)

    class Client:
        protocol = Protocol()
        stopped = False
        _server = None

        async def stop(self):
            self.stopped = True

    analyzer = TyAnalyzer(tmp_path)
    analyzer._client = cast("JsonRPCClient", Client())
    document = TyDocument((tmp_path / "probe.py").as_uri(), "value = 1\nvalue\n")
    hovering = asyncio.create_task(analyzer.hover(document, types.Position(1, 3)))
    await request_started.wait()

    await analyzer.close()

    with pytest.raises(asyncio.CancelledError):
        await hovering
    assert not pending.cancelled()
    assert types.CANCEL_REQUEST in notifications
    pending.set_result(None)
    await asyncio.sleep(0)


@pytest.mark.parametrize(
    ("receiver", "label", "detail"),
    [
        ("GeneratorType", "gi_code", "CodeType"),
        ("GeneratorType", "gi_frame", "FrameType | None"),
        ("CoroutineType", "cr_code", "CodeType"),
        ("CoroutineType", "cr_frame", "FrameType | None"),
        ("AsyncGeneratorType", "ag_code", "CodeType"),
        ("AsyncGeneratorType", "ag_frame", "FrameType | None"),
    ],
)
def test_runtime_internal_completion_filter_uses_receiver_identity(
    receiver: str,
    label: str,
    detail: str,
) -> None:
    assert detail
    assert not _safe_completion_item(label, member_owner=receiver)
    assert _safe_completion_item(label, member_owner="Custom")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("annotation", "partial"),
    [
        ("types.CodeType", "co"),
        ("types.FrameType", "f"),
        ("types.TracebackType", "tb"),
    ],
)
async def test_analyzer_withholds_all_internal_receiver_members(
    tmp_path: Path,
    annotation: str,
    partial: str,
) -> None:
    source = f"import types\ndef probe(value: {annotation}):\n    value.{partial}\n"
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(
            document,
            types.Position(2, len(f"    value.{partial}")),
        )
    finally:
        await analyzer.close()

    assert not items


@pytest.mark.asyncio
async def test_internal_looking_member_on_an_ordinary_instance_stays_available(tmp_path: Path) -> None:
    source = "class Custom:\n    co_argcount: int\nvalue = Custom()\nvalue.co\n"
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, types.Position(3, len("value.co")))
    finally:
        await analyzer.close()

    assert "co_argcount" in {item.label for item in items}


@pytest.mark.asyncio
@pytest.mark.parametrize("class_name", ["CodeType", "FrameType", "TracebackType"])
async def test_user_class_named_like_an_internal_receiver_stays_available(
    tmp_path: Path,
    class_name: str,
) -> None:
    source = (
        f"class {class_name}:\n    def hello(self) -> str:\n        return 'hello'\nvalue = {class_name}()\nvalue.he\n"
    )
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, types.Position(4, len("value.he")))
    finally:
        await analyzer.close()

    assert "hello" in {item.label for item in items}


@pytest.mark.asyncio
async def test_unrelated_types_import_does_not_hide_an_imported_user_class(tmp_path: Path) -> None:
    (tmp_path / "mine.py").write_text(
        "class CodeType:\n    def hello(self) -> str:\n        return 'hello'\n",
        encoding="utf-8",
    )
    source = "import types\nfrom mine import CodeType\ndef probe(value: CodeType):\n    value.he\n"
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, types.Position(3, len("    value.he")))
    finally:
        await analyzer.close()

    assert "hello" in {item.label for item in items}


@pytest.mark.asyncio
async def test_local_same_name_does_not_unblock_a_qualified_internal_type(tmp_path: Path) -> None:
    source = (
        "import types\n"
        "class CodeType:\n"
        "    def hello(self) -> str:\n"
        "        return 'hello'\n"
        "def probe(value: types.CodeType):\n"
        "    value.co\n"
    )
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, types.Position(5, len("    value.co")))
    finally:
        await analyzer.close()

    assert not items


@pytest.mark.asyncio
async def test_internal_type_inside_a_container_does_not_hide_container_members(tmp_path: Path) -> None:
    source = "import types\ndef probe(values: list[types.CodeType]):\n    values.ap\n"
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, types.Position(2, len("    values.ap")))
    finally:
        await analyzer.close()

    assert "append" in {item.label for item in items}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("class_name", "member", "partial"),
    [
        ("Custom", "gi_code", "gi"),
        ("Astr", "format", "fo"),
        ("Mystr", "format_map", "fo"),
    ],
)
async def test_internal_looking_custom_members_stay_available(
    tmp_path: Path,
    class_name: str,
    member: str,
    partial: str,
) -> None:
    if member == "gi_code":
        source = (
            "class CodeType: pass\n"
            f"class {class_name}:\n"
            "    gi_code: CodeType\n"
            f"value = {class_name}()\n"
            f"value.{partial}\n"
        )
    else:
        source = (
            f"class {class_name}:\n"
            f"    def {member}(self) -> str:\n"
            "        return 'hello'\n"
            f"value = {class_name}()\n"
            f"value.{partial}\n"
        )
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(
            document,
            types.Position(len(source.splitlines()) - 1, len(f"value.{partial}")),
        )
    finally:
        await analyzer.close()

    assert member in {item.label for item in items}


@pytest.mark.asyncio
async def test_builtin_str_format_members_are_withheld(tmp_path: Path) -> None:
    source = "value = 'hello'\nvalue.fo\n"
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, types.Position(1, len("value.fo")))
    finally:
        await analyzer.close()

    labels = {item.label for item in items}
    assert "format" not in labels
    assert "format_map" not in labels


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source",
    [
        "import types\ndef code() -> types.CodeType: ...\ncode().co\n",
        ("import types\nfrom typing import cast\nvalue: object\ncast(types.CodeType, value).co\n"),
        ("import types\nfirst: types.CodeType\nsecond: types.CodeType\n(first if True else second).co\n"),
    ],
)
async def test_internal_receiver_expression_shapes_are_withheld(tmp_path: Path, source: str) -> None:
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    final_line = source.splitlines()[-1]
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(
            document,
            types.Position(len(source.splitlines()) - 1, len(final_line)),
        )
    finally:
        await analyzer.close()

    assert not items


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source",
    [
        "def text() -> str: ...\ntext().fo\n",
        "first = 'a'\nsecond = 'b'\n(first if True else second).fo\n",
        "from typing import cast\nvalue: object\ncast(str, value).fo\n",
    ],
)
async def test_builtin_str_expression_shapes_hide_format_methods(tmp_path: Path, source: str) -> None:
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    final_line = source.splitlines()[-1]
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(
            document,
            types.Position(len(source.splitlines()) - 1, len(final_line)),
        )
    finally:
        await analyzer.close()

    labels = {item.label for item in items}
    assert "format" not in labels
    assert "format_map" not in labels


def test_virtual_document_is_a_deterministic_python_sibling(tmp_path: Path) -> None:
    source_file = tmp_path / "components" / "card.py"

    first = virtual_document_uri(source_file, "def:card/value")
    second = virtual_document_uri(source_file, "def:card/value")

    assert first == second
    assert first.startswith(source_file.parent.resolve().as_uri())
    assert first.rsplit("/", 1)[-1].startswith("__citry_")
    assert first.endswith(".py")


@pytest.mark.asyncio
async def test_ty_adapter_returns_exact_type_definition_locations(tmp_path: Path) -> None:
    source = "class User: pass\ndef render(value: User) -> None:\n    value\n"
    document = TyDocument((tmp_path / "probe.py").as_uri(), source)
    analyzer = TyAnalyzer(tmp_path)
    try:
        locations = await analyzer.type_definition(document, types.Position(2, len("    val")))
    finally:
        await analyzer.close()

    assert len(locations) == 1
    assert locations[0].uri == document.uri
    assert locations[0].range.start == types.Position(0, len("class "))


@pytest.mark.asyncio
async def test_ty_adapter_rejects_a_partial_type_definition_location_link(tmp_path: Path, monkeypatch) -> None:
    analyzer = TyAnalyzer(tmp_path)

    async def ready_client():
        return object()

    async def sync_documents(*_args):
        return None

    async def request(*_args):
        return [
            {
                "targetUri": (tmp_path / "generated.py").as_uri(),
                "targetRange": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 4},
                },
            },
            {
                "uri": (tmp_path / "safe.py").as_uri(),
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 4},
                },
            },
        ]

    monkeypatch.setattr(analyzer, "_ready_client", ready_client)
    monkeypatch.setattr(analyzer, "_sync_documents", sync_documents)
    monkeypatch.setattr(analyzer, "_request", request)

    locations = await analyzer.type_definition(
        TyDocument((tmp_path / "probe.py").as_uri(), "value\n"),
        types.Position(0, 2),
    )

    assert not locations
    assert analyzer.failure is None


@pytest.mark.asyncio
async def test_ty_adapter_returns_filtered_completion_hover_and_diagnostics(tmp_path: Path) -> None:
    (tmp_path / "mine.py").write_text("class BaseMeta(type): pass\n", encoding="utf-8")
    analyzer = TyAnalyzer(tmp_path)
    source = "def probe(value: str | None) -> None:\n    if value:\n        value.lo\n    value.missing\n"
    document = TyDocument((tmp_path / ".citry_probe.py").as_uri(), source)
    try:
        completions = await analyzer.completion(
            document,
            types.Position(2, len("        value.lo")),
        )
        hint = await analyzer.hover(document, types.Position(2, len("        value")))
        diagnostics = await analyzer.diagnostics(document)
        custom_source = (
            "class Custom:\n"
            "    def format(self) -> str:\n"
            "        return ''\n"
            "def custom(value: Custom) -> None:\n"
            "    value.fo\n"
        )
        custom = await analyzer.completion(
            TyDocument(document.uri, custom_source),
            types.Position(4, len("    value.fo")),
        )
        safe_mro_source = (
            "class Custom:\n"
            "    __mro__: tuple[object, ...]\n"
            "    __name__: str\n"
            "    __qualname__: str\n"
            "    def mro(self) -> str:\n"
            "        return ''\n"
            "value = Custom()\n"
            "value.mr\n"
        )
        safe_mro = await analyzer.completion(
            TyDocument(document.uri, safe_mro_source),
            types.Position(7, len("value.mr")),
        )
        unsafe_mro_source = "class User: pass\nklass = User\nklass.m\n"
        unsafe_mro = await analyzer.completion(
            TyDocument(document.uri, unsafe_mro_source),
            types.Position(2, len("klass.m")),
        )
        custom_meta_source = (
            "class Meta(type):\n"
            "    def mro(cls) -> list[type]:\n"
            "        return []\n"
            "class User(metaclass=Meta): pass\n"
            "User.m\n"
        )
        custom_meta_mro = await analyzer.completion(
            TyDocument(document.uri, custom_meta_source),
            types.Position(4, len("User.m")),
        )
        typed_class_source = (
            "class Meta(type):\n"
            "    def mro(cls) -> list[type]:\n"
            "        return []\n"
            "class User(metaclass=Meta): pass\n"
            "def probe(cls: type[User]) -> None:\n"
            "    cls.m\n"
        )
        typed_class_mro = await analyzer.completion(
            TyDocument(document.uri, typed_class_source),
            types.Position(5, len("    cls.m")),
        )
        returned_class_source = (
            "class Meta(type):\n"
            "    def mro(cls) -> list[type]:\n"
            "        return []\n"
            "class User(metaclass=Meta): pass\n"
            "def selected() -> type[User]:\n"
            "    return User\n"
            "selected().m\n"
        )
        returned_class_mro = await analyzer.completion(
            TyDocument(document.uri, returned_class_source),
            types.Position(6, len("selected().m")),
        )
        typed_meta_source = (
            "class Meta(type):\n"
            "    def mro(cls) -> list[type]:\n"
            "        return []\n"
            "class User(metaclass=Meta): pass\n"
            "def probe(cls: Meta) -> None:\n"
            "    cls.m\n"
        )
        typed_meta_mro = await analyzer.completion(
            TyDocument(document.uri, typed_meta_source),
            types.Position(5, len("    cls.m")),
        )
        returned_meta_source = (
            "class Meta(type):\n"
            "    def mro(cls) -> list[type]:\n"
            "        return []\n"
            "class User(metaclass=Meta): pass\n"
            "def selected() -> Meta:\n"
            "    return User\n"
            "selected().m\n"
        )
        returned_meta_mro = await analyzer.completion(
            TyDocument(document.uri, returned_meta_source),
            types.Position(6, len("selected().m")),
        )
        imported_meta_source = (
            "from mine import BaseMeta\n"
            "class Meta(BaseMeta):\n"
            "    def mro(cls) -> list[type]:\n"
            "        return []\n"
            "class User(metaclass=Meta): pass\n"
            "def probe(cls: Meta) -> None:\n"
            "    cls.m\n"
        )
        imported_meta_mro = await analyzer.completion(
            TyDocument(document.uri, imported_meta_source),
            types.Position(6, len("    cls.m")),
        )
        prefixed_meta_mro = []
        for meta_source in (typed_meta_source, imported_meta_source):
            for prefix in ("mr", "mro"):
                prefixed_source = meta_source.rsplit("cls.m", 1)[0] + f"cls.{prefix}\n"
                prefixed_meta_mro.append(
                    await analyzer.completion(
                        TyDocument(document.uri, prefixed_source),
                        types.Position(len(prefixed_source.splitlines()) - 1, len(f"    cls.{prefix}")),
                    )
                )
    finally:
        await analyzer.close()

    by_label = {item.label: item for item in completions}
    assert "lower" in by_label
    assert "format" not in by_label
    assert not any(label.startswith("_") for label in by_label)
    assert by_label["lower"].detail == "bound method str.lower() -> str"
    assert hint is not None
    assert "str" in hint.contents.value
    assert any(item.code == "unresolved-attribute" and "missing" in item.message for item in diagnostics)
    assert "format" in {item.label for item in custom}
    assert "mro" in {item.label for item in safe_mro}
    assert "mro" not in {item.label for item in unsafe_mro}
    assert "mro" not in {item.label for item in custom_meta_mro}
    assert "mro" not in {item.label for item in typed_class_mro}
    assert "mro" not in {item.label for item in returned_class_mro}
    assert "mro" not in {item.label for item in typed_meta_mro}
    assert "mro" not in {item.label for item in returned_meta_mro}
    assert "mro" not in {item.label for item in imported_meta_mro}
    assert all("mro" not in {item.label for item in result} for result in prefixed_meta_mro)


@pytest.mark.asyncio
async def test_ty_adapter_resolves_relative_imports_from_a_virtual_package_sibling(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "models.py").write_text(
        "class User:\n    def wave(self) -> str:\n        return 'hello'\n",
        encoding="utf-8",
    )
    source_file = package / "component.py"
    source = (
        "from .models import User\n"
        "class Component:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n"
    )
    source_file.write_text(source, encoding="utf-8")
    shadow = build_inferred_template_shadow(
        source,
        "Component",
        (TemplatePythonRoot("user", "always"),),
        TemplatePythonQuery("user.wa", 0, 7, "interpolation"),
        source_module="pkg.component",
    )
    assert shadow is not None
    document = TyDocument(virtual_document_uri(source_file, "component"), shadow.source)
    cursor = shadow.copies[0].shadow_end
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await analyzer.completion(document, position_at_offset(shadow.source, cursor))
    finally:
        await analyzer.close()

    assert "wave" in {item.label for item in items}


@pytest.mark.asyncio
async def test_ty_adapter_uses_the_interpreter_environment_selected_for_citry_lsp(
    tmp_path: Path,
    monkeypatch,
) -> None:
    selected = tmp_path / "selected-environment"
    await asyncio.to_thread(venv.create, selected, with_pip=False)
    purelib = (
        selected / "Lib" / "site-packages"
        if sys.platform == "win32"
        else selected / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    )
    package = purelib / "only_selected"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(
        "class User:\n    def wave(self) -> str:\n        return 'hello'\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    source = "from only_selected import User\nvalue = User()\nvalue.wa\n"
    document = TyDocument((workspace / "probe.py").as_uri(), source)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    analyzer = TyAnalyzer(workspace, python_prefix=selected)
    try:
        items = await analyzer.completion(
            document,
            types.Position(2, len("value.wa")),
        )
    finally:
        await analyzer.close()

    assert "wave" in {item.label for item in items}


@pytest.mark.asyncio
async def test_close_document_canonicalizes_a_symlinked_editor_uri(tmp_path: Path) -> None:
    source_file = tmp_path / "real.py"
    source_file.write_text("value = 1\n", encoding="utf-8")
    alias = tmp_path / "alias.py"
    try:
        alias.symlink_to(source_file)
    except OSError:
        pytest.skip("file symlinks are unavailable")

    notices: list[tuple[str, object]] = []

    class Protocol:
        def notify(self, method: str, params: object) -> None:
            notices.append((method, params))

    class Client:
        protocol = Protocol()

    analyzer = TyAnalyzer(tmp_path)
    canonical_uri = source_file.resolve().as_uri()
    analyzer._client = cast("JsonRPCClient", Client())
    analyzer._documents[canonical_uri] = ("value = 2\n", 1)

    await analyzer.close_document(alias.as_uri())

    assert canonical_uri not in analyzer._documents
    assert [method for method, _params in notices] == [types.TEXT_DOCUMENT_DID_CLOSE]


@pytest.mark.asyncio
async def test_malformed_analyzer_response_disables_the_generation(tmp_path: Path, monkeypatch) -> None:
    analyzer = TyAnalyzer(tmp_path)

    async def ready_client():
        return object()

    async def sync_documents(*_args):
        return None

    async def request(*_args):
        return {"items": "not-a-list"}

    monkeypatch.setattr(analyzer, "_ready_client", ready_client)
    monkeypatch.setattr(analyzer, "_sync_documents", sync_documents)
    monkeypatch.setattr(analyzer, "_request", request)

    with pytest.raises(TyUnavailableError, match="invalid completion"):
        await analyzer.completion(
            TyDocument((tmp_path / "probe.py").as_uri(), "value.lo\n"),
            types.Position(0, len("value.lo")),
        )
    assert analyzer.failure is not None


@pytest.mark.asyncio
async def test_stop_client_terminates_a_non_cooperative_child(short_ty_shutdown: None) -> None:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "import time; time.sleep(60)",
    )
    client = JsonRPCClient()
    client._server = process
    try:
        await _stop_client(client, graceful=False)
        assert process.returncode is not None
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
async def test_stop_client_terminates_child_after_client_stop_fails(short_ty_shutdown: None) -> None:
    class BrokenClient(JsonRPCClient):
        async def stop(self) -> None:
            raise RuntimeError("reader already closed")

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "import time; time.sleep(60)",
    )
    client = BrokenClient()
    client._server = process
    try:
        await _stop_client(client, graceful=False)
        assert process.returncode is not None
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
async def test_cancelled_startup_still_terminates_the_spawned_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    short_ty_shutdown: None,
) -> None:
    initialize_started = asyncio.Event()
    never = asyncio.Event()
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "import time; time.sleep(60)",
    )

    class Protocol:
        async def send_request_async(self, *_args, **_kwargs):
            initialize_started.set()
            await never.wait()

        def notify(self, *_args) -> None:
            return None

    class Client:
        protocol = Protocol()
        _server = process

        async def start_io(self, *_args, **_kwargs) -> None:
            return None

        async def stop(self) -> None:
            raise RuntimeError("reader already closed")

    client = Client()
    monkeypatch.setattr(type_analysis, "_configured_client", lambda _python_prefix: client)
    analyzer = TyAnalyzer(tmp_path)
    monkeypatch.setattr(analyzer, "_validated_executable", lambda: tmp_path / "python")
    starting = asyncio.create_task(analyzer._ready_client())
    try:
        await initialize_started.wait()
        starting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await starting
        assert analyzer._client is None
        assert process.returncode is not None
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
async def test_repeated_cancelled_startups_never_accumulate_owned_children(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    short_ty_shutdown: None,
) -> None:
    clients: list[object] = []
    startup_queue: asyncio.Queue[None] = asyncio.Queue()
    active_processes = 0

    class Process:
        returncode = None

        def __init__(self, pending: asyncio.Future[object]) -> None:
            nonlocal active_processes
            self.pending = pending
            active_processes += 1

        def terminate(self) -> None:
            self._finish(-15)

        def kill(self) -> None:
            self._finish(-9)

        def _finish(self, returncode: int) -> None:
            nonlocal active_processes
            if self.returncode is None:
                self.returncode = returncode
                active_processes -= 1
                if not self.pending.done():
                    self.pending.set_exception(ConnectionError("child stopped"))

        async def wait(self) -> int:
            assert self.returncode is not None
            return self.returncode

    class Protocol:
        def __init__(self) -> None:
            self.pending: asyncio.Future[object] = asyncio.get_running_loop().create_future()

        def send_request_async(self, *_args, **_kwargs):
            startup_queue.put_nowait(None)
            return self.pending

        def notify(self, *_args) -> None:
            return None

    class Client:
        stopped = False

        def __init__(self) -> None:
            self.protocol = Protocol()
            self._server = Process(self.protocol.pending)
            clients.append(self)

        async def start_io(self, *_args, **_kwargs) -> None:
            return None

        async def stop(self) -> None:
            raise RuntimeError("reader already closed")

    monkeypatch.setattr(type_analysis, "_configured_client", lambda _python_prefix: Client())
    analyzer = TyAnalyzer(tmp_path)
    monkeypatch.setattr(analyzer, "_validated_executable", lambda: tmp_path / "ty")

    for _ in range(8):
        starting = asyncio.create_task(analyzer._ready_client())
        await startup_queue.get()
        starting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await starting
        assert active_processes == 0
        assert analyzer._client is None

    assert len(clients) == 8


@pytest.mark.asyncio
async def test_cancelled_close_finishes_terminating_the_owned_child(
    tmp_path: Path,
    short_ty_shutdown: None,
) -> None:
    stop_started = asyncio.Event()
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "import time; time.sleep(60)",
    )

    class Protocol:
        async def send_request_async(self, *_args, **_kwargs):
            return None

        def notify(self, *_args) -> None:
            return None

    class Client:
        protocol = Protocol()
        _server = process

        async def stop(self) -> None:
            stop_started.set()
            await process.wait()

    analyzer = TyAnalyzer(tmp_path)
    analyzer._client = Client()
    closing = asyncio.create_task(analyzer.close())
    try:
        await stop_started.wait()
        closing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await closing
        assert process.returncode is not None
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
async def test_cancelled_invalid_response_cleanup_still_terminates_the_child(
    tmp_path: Path,
    short_ty_shutdown: None,
) -> None:
    stop_started = asyncio.Event()
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "import time; time.sleep(60)",
    )

    class Protocol:
        def notify(self, *_args) -> None:
            return None

    class Client:
        protocol = Protocol()
        _server = process

        async def stop(self) -> None:
            stop_started.set()
            await process.wait()

    analyzer = TyAnalyzer(tmp_path)
    analyzer._client = Client()
    failing = asyncio.create_task(analyzer._invalid_response("completion"))
    try:
        await stop_started.wait()
        failing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await failing
        assert analyzer._client is None
        assert process.returncode is not None
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
async def test_close_makes_an_active_multi_request_operation_terminal(tmp_path: Path) -> None:
    analyzer = TyAnalyzer(tmp_path)
    document = TyDocument((tmp_path / "probe.py").as_uri(), "value = 'hello'\nvalue.lo\n")
    request_finished = asyncio.Event()
    release_request = asyncio.Event()
    original_request = analyzer._request
    request_count = 0

    async def delayed_request(*args):
        nonlocal request_count
        result = await original_request(*args)
        request_count += 1
        if request_count == 1:
            request_finished.set()
            await release_request.wait()
        return result

    analyzer._request = delayed_request
    active = asyncio.create_task(analyzer.completion(document, types.Position(1, len("value.lo"))))
    await request_finished.wait()
    closing = asyncio.create_task(analyzer.close())
    await asyncio.sleep(0)
    release_request.set()
    with pytest.raises(TyUnavailableError, match="generation is closed"):
        await active
    await closing

    with pytest.raises(TyUnavailableError, match="generation is closed"):
        await analyzer.completion(document, types.Position(1, len("value.lo")))
