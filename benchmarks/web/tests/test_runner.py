"""Protect source isolation, profile validation and honest failure reporting."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import tomllib
from citry_bench import cli, compose, config, prepare
from citry_bench.browser import (
    collect_network_then_heap_after_gc,
    module,
    record_not_run_session,
    session_sequence,
    stored_sample,
    write_diagnostic_capture,
)
from citry_bench.results import append, report


@pytest.fixture
def web(tmp_path, monkeypatch):
    root = tmp_path / "web"
    (root / "profiles").mkdir(parents=True)
    (root / "apps/citry").mkdir(parents=True)
    (root / "apps/django_htmx_alpine").mkdir(parents=True)
    source = config.WEB / "profiles/smoke.toml"
    (root / "profiles/smoke.toml").write_text(source.read_text())
    monkeypatch.setattr(config, "WEB", root)
    return root


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("blocks = 1", "blocks = 0"),
        ("warmups = 0", "warmups = -1"),
        ("counts = [14]", "counts = [true]"),
        ('scenario_revision = "canonical-project-v1"', 'scenario_revision = "unknown"'),
        ('network = "loopback"', 'network = "wan"'),
        ("publication = false", "publication = true"),
    ],
)
def test_profile_rejects_unsupported_or_invalid_values(web, old, new):
    path = web / "profiles/smoke.toml"
    path.write_text(path.read_text().replace(old, new))
    with pytest.raises(ValueError, match=r"must|Unsupported|Publication requires"):
        config.profile("smoke")


def test_profile_rejects_unknown_fields(web):
    with (web / "profiles/smoke.toml").open("a") as stream:
        stream.write("\nrepititions = 10\n")
    with pytest.raises(ValueError, match="unknown"):
        config.profile("smoke")


def test_snapshot_includes_untracked_sources_and_excludes_environment(tmp_path):
    (tmp_path / "app.py").write_text("uncommitted source")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv/private.py").write_text("installed")
    first = config.source_manifest(tmp_path)
    assert set(first) == {"app.py"}
    (tmp_path / "app.py").write_text("changed source")
    assert first != config.source_manifest(tmp_path)


def test_snapshot_rejects_external_symlink(tmp_path):
    (tmp_path / "source").mkdir()
    (tmp_path / "secret").write_text("outside input")
    (tmp_path / "source/link.py").symlink_to(tmp_path / "secret")
    with pytest.raises(ValueError, match="symlinks"):
        config.source_manifest(tmp_path / "source")


def test_environment_removes_shared_python_settings(monkeypatch):
    for key in ("VIRTUAL_ENV", "PYTHONPATH", "UV_PROJECT_ENVIRONMENT"):
        monkeypatch.setenv(key, "/shared/dev")
    env = prepare.environment()
    assert not any(key in env for key in ("VIRTUAL_ENV", "PYTHONPATH", "UV_PROJECT_ENVIRONMENT"))
    assert env["PYTHONHASHSEED"] == "0"


def test_prepared_build_rejects_mutated_source_and_installed_bytes(tmp_path, monkeypatch):
    settings = {"apps": ["citry"], "name": "test"}
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "app.py").write_text("source")
    inputs = {"apps": {"citry": config.source_manifest(input_dir)}, "scenario": {}}
    build = tmp_path / "builds" / config.digest(inputs)
    app = build / "apps/citry"
    prepare.copy_sources(input_dir, app)
    (app / ".venv/bin").mkdir(parents=True)
    (app / ".venv/bin/python").write_text("binary")
    (tmp_path / "browsers").mkdir()
    marker = {
        "inputs": inputs,
        "artifacts": {"citry": prepare.artifact_manifest(app / ".venv")},
        "browser_artifacts": {},
        "build_sources": {"citry": config.generated_manifest(app)},
    }
    prepare.write_json(build / "prepared.json", marker)
    monkeypatch.setattr(prepare, "CACHE", tmp_path)
    monkeypatch.setattr(prepare, "identity", lambda _: inputs)
    assert prepare.prepared(settings)[0] == build
    (app / "generated").mkdir()
    with pytest.raises(ValueError, match="snapshot changed"):
        prepare.prepared(settings)
    (app / "generated").rmdir()
    (app / "app.py").write_text("tampered")
    with pytest.raises(ValueError, match="snapshot changed"):
        prepare.prepared(settings)
    (app / "app.py").write_text("source")
    (app / ".venv/bin/python").write_text("different binary")
    with pytest.raises(ValueError, match="Installed artifacts"):
        prepare.prepared(settings)


@pytest.mark.parametrize("build", ["release", "unrecorded", None])
def test_native_build_check_accepts_release_and_unknown_builds(build, monkeypatch):
    monkeypatch.delenv(prepare.ALLOW_DEBUG_NATIVE_ENV, raising=False)
    prepare.check_native_build("citry", {"citry_core_build": build})


def test_native_build_check_refuses_debug_unless_allowed(monkeypatch):
    monkeypatch.delenv(prepare.ALLOW_DEBUG_NATIVE_ENV, raising=False)
    with pytest.raises(ValueError, match=r"debug build of citry-core.*maturin build --release"):
        prepare.check_native_build("citry", {"citry_core_build": "debug"})
    monkeypatch.setenv(prepare.ALLOW_DEBUG_NATIVE_ENV, "1")
    prepare.check_native_build("citry", {"citry_core_build": "debug"})


def test_prepared_build_refuses_a_recorded_debug_native_build(tmp_path, monkeypatch):
    monkeypatch.delenv(prepare.ALLOW_DEBUG_NATIVE_ENV, raising=False)
    settings = {"apps": ["citry"], "name": "test"}
    inputs = {"apps": {}, "scenario": {}}
    build = tmp_path / "builds" / config.digest(inputs)
    app = build / "apps/citry"
    (app / ".venv/bin").mkdir(parents=True)
    (app / ".venv/bin/python").write_text("binary")
    (tmp_path / "browsers").mkdir()
    marker = {
        "inputs": inputs,
        "installed": {"citry": {"citry_core_build": "debug"}},
        "artifacts": {"citry": prepare.artifact_manifest(app / ".venv")},
        "browser_artifacts": {},
        "build_sources": {"citry": config.generated_manifest(app)},
    }
    prepare.write_json(build / "prepared.json", marker)
    monkeypatch.setattr(prepare, "CACHE", tmp_path)
    monkeypatch.setattr(prepare, "identity", lambda _: inputs)
    with pytest.raises(ValueError, match="debug build of citry-core"):
        prepare.prepared(settings)
    monkeypatch.setenv(prepare.ALLOW_DEBUG_NATIVE_ENV, "1")
    assert prepare.prepared(settings)[0] == build


def test_report_retains_failures_and_excludes_warmups(tmp_path):
    common = {"app": "citry", "count": 10, "action": "select", "warmup": False}
    for status, elapsed in (("ok", 10), ("timeout", None), ("error", 1)):
        append(tmp_path / "samples.jsonl", {**common, "status": status, "elapsed_ms": elapsed})
    append(tmp_path / "samples.jsonl", {**common, "status": "ok", "elapsed_ms": 100, "warmup": True})
    summary = report(tmp_path)
    assert summary["rows"][0]["attempts"] == 3
    assert summary["rows"][0]["successes"] == 1
    assert summary["rows"][0]["median_ms"] == 10
    assert json.loads((tmp_path / "summary.json").read_text())["publication"] is False
    assert (tmp_path / "report.html").is_file()


@pytest.mark.parametrize("absolute", [False, True], ids=["run-ids", "absolute-paths"])
def test_report_cli_resolves_latency_and_memory_runs(tmp_path, monkeypatch, absolute):
    runs = tmp_path / "runs"
    latency = runs / "latency"
    memory = runs / "memory"
    latency.mkdir(parents=True)
    memory.mkdir()
    calls = []
    monkeypatch.setattr(cli, "CACHE", tmp_path)
    monkeypatch.setattr(cli, "report", lambda path, *, memory_directory=None: calls.append((path, memory_directory)))
    arguments = [str(latency), "--memory-run", str(memory)] if absolute else ["latency", "--memory-run", "memory"]
    monkeypatch.setattr("sys.argv", ["citry-bench", "report", *arguments])

    assert cli.main() == 0
    assert calls == [(latency, memory)]


def test_scenario_modules_load_without_importing_application_dependencies():
    actions = module(config.WEB / "scenarios/project_board/actions.py")
    assertions = module(config.WEB / "scenarios/project_board/assertions.py")
    assert len(actions.ACTIONS) == 9
    assert len(assertions.initial_expected(14)["rows"]) == 14


def test_adapter_exclusions_require_a_list(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["{python}","app.py"]\nhealth="/health"\nsource_exclude="generated"\n'
    )
    with pytest.raises(ValueError, match="list of relative paths"):
        config.adapter(tmp_path)


def test_adapter_accepts_pinned_node_launch_path(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nruntime="node"\nnode=".toolchain/node/bin/node"\nlaunch=["{node}","server.mjs","{port}"]\nhealth="/health"\n'
    )
    declaration = config.adapter(tmp_path)
    assert declaration["node"] == ".toolchain/node/bin/node"
    assert declaration["runtime"] == "node"


def test_node_runtime_requires_a_pinned_node_path(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nruntime="node"\nlaunch=["server"]\nhealth="/health"\n'
    )
    with pytest.raises(ValueError, match="pinned node executable"):
        config.adapter(tmp_path)


def test_adapter_rejects_external_node_launch_path(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nnode="/usr/bin/node"\nlaunch=["{node}","server.mjs"]\nhealth="/health"\n'
    )
    with pytest.raises(ValueError, match="relative executable"):
        config.adapter(tmp_path)


def test_declared_generated_paths_do_not_enter_source_snapshot(tmp_path):
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated/binary").write_bytes(b"generated bytes")
    (tmp_path / "app.py").write_text("authored source")
    assert set(config.source_manifest(tmp_path, ("generated",))) == {"app.py"}
    assert set(config.source_manifest(tmp_path)) == {"app.py", "generated/binary"}


@pytest.mark.parametrize("kind", ["directory", "broken"])
def test_authored_snapshot_rejects_non_file_symlinks(tmp_path, kind):
    if kind == "directory":
        (tmp_path / "target").mkdir()
    (tmp_path / "link").symlink_to("target", target_is_directory=kind == "directory")
    with pytest.raises(ValueError, match="Source symlinks"):
        config.source_manifest(tmp_path)


def test_generated_inventory_tracks_node_modules_and_toolchain_links(tmp_path):
    package = tmp_path / "node_modules/package"
    package.mkdir(parents=True)
    (package / "cli.js").write_text("first")
    binary = tmp_path / ".toolchain/bin"
    binary.mkdir(parents=True)
    link = binary / "npm"
    link.symlink_to("../../node_modules/package/cli.js")
    (tmp_path / "package-link").symlink_to("node_modules/package", target_is_directory=True)
    first = config.generated_manifest(tmp_path)
    assert first[".toolchain/bin/npm"] == {"type": "symlink", "target": "../../node_modules/package/cli.js"}
    assert first["package-link"] == {"type": "symlink", "target": "node_modules/package"}
    assert "package-link/cli.js" not in first
    (package / "cli.js").write_text("changed")
    second = config.generated_manifest(tmp_path)
    assert first["node_modules/package/cli.js"] != second["node_modules/package/cli.js"]
    link.unlink()
    link.symlink_to("../../package-link/cli.js")
    assert second != config.generated_manifest(tmp_path)


@pytest.mark.parametrize("kind", ["broken", "cycle", "external", "ancestor", "siblings", "excluded"])
def test_generated_inventory_rejects_unverifiable_links(tmp_path, kind):
    app = tmp_path / "app"
    app.mkdir()
    if kind == "broken":
        (app / "link").symlink_to("missing")
    elif kind == "cycle":
        (app / "link").symlink_to("other")
        (app / "other").symlink_to("link")
    elif kind == "external":
        (tmp_path / "outside").write_text("outside")
        (app / "link").symlink_to("../outside")
    elif kind == "ancestor":
        (app / "child").mkdir()
        (app / "child/link").symlink_to("..", target_is_directory=True)
    elif kind == "siblings":
        (app / "one").mkdir()
        (app / "two").mkdir()
        (app / "one/link").symlink_to("../two", target_is_directory=True)
        (app / "two/link").symlink_to("../one", target_is_directory=True)
    else:
        (app / ".venv").mkdir()
        (app / ".venv/binary").write_text("separately inventoried")
        (app / "link").symlink_to(".venv/binary")
    with pytest.raises(ValueError, match=r"[Gg]enerated"):
        config.generated_manifest(app)


def test_generated_inventory_records_new_empty_outputs_but_ignores_runtime_cache(tmp_path):
    first = config.generated_manifest(tmp_path)
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__/app.pyc").write_bytes(b"mutable")
    assert config.generated_manifest(tmp_path) == first
    (tmp_path / "generated").mkdir()
    assert config.generated_manifest(tmp_path) != first


def test_profile_accepts_opt_in_hundredfold_output_scale(web):
    path = web / "profiles/smoke.toml"
    path.write_text(path.read_text().replace("counts = [14]", "counts = [1400]"))
    assert config.profile("smoke")["counts"] == [1400]


def test_successful_operations_do_not_store_debug_captures(tmp_path: Path) -> None:
    evidence = SimpleNamespace(
        raw=[{"operation": "current", "event": "response"}],
        sockets=[{"operation": "current", "event": "frame"}],
    )

    write_diagnostic_capture(tmp_path, "session", 1, "current", "ok", [], evidence)
    assert not (tmp_path / "captures").exists()

    write_diagnostic_capture(tmp_path, "session", 2, "current", "error", ["fault"], evidence)
    capture = json.loads((tmp_path / "captures/session-2-failure.json").read_text())
    assert capture == {
        "errors": ["fault"],
        "http": [{"operation": "current", "event": "response"}],
        "sockets": [{"operation": "current", "event": "frame"}],
    }


def test_successful_samples_omit_the_in_memory_semantic_snapshot() -> None:
    sentinel = "large-semantic-snapshot"
    ready = {"operation": "current", "revision": 2, "semantic": {"rows": [sentinel]}}
    successful = stored_sample({"status": "ok", "ready": ready})
    failed = stored_sample({"status": "error", "ready": ready})

    assert successful["ready"] == {"operation": "current", "revision": 2}
    assert sentinel not in json.dumps(successful)
    assert failed["ready"] is ready


def test_page_pair_uses_distinct_sessions_and_skips_the_second_load_after_failure(tmp_path, monkeypatch):
    identifiers = iter((SimpleNamespace(hex="first"), SimpleNamespace(hex="second")))
    calls = []

    def run_session(*args, **kwargs):
        calls.append((args, kwargs))
        return False

    skipped = []
    monkeypatch.setattr(cli, "uuid4", lambda: next(identifiers))
    monkeypatch.setattr(cli, "run_session", run_session)
    monkeypatch.setattr(cli, "record_not_run_session", lambda *args, **kwargs: skipped.append((args, kwargs)))
    info = {"run": "test", "block": 0, "app": "citry", "count": 14, "session_index": 0}

    assert not cli.run_page_pair(object(), "http://fixture", {}, tmp_path, info, adapter={})
    assert len(calls) == 1
    assert len(skipped) == 1
    assert calls[0][0][4]["session"] == "first"
    assert calls[0][0][4]["page_load"] == 1
    assert calls[0][1]["initial_only"] is True
    assert skipped[0][0][2]["session"] == "second"
    assert skipped[0][0][2]["page_load"] == 2
    assert skipped[0][1]["reason"] == "first page load did not complete correctly"


def test_page_pair_runs_actions_only_on_the_second_load(tmp_path, monkeypatch):
    identifiers = iter((SimpleNamespace(hex="first"), SimpleNamespace(hex="second")))
    calls = []

    def run_session(*args, **kwargs):
        calls.append((args, kwargs))
        return True

    monkeypatch.setattr(cli, "uuid4", lambda: next(identifiers))
    monkeypatch.setattr(cli, "run_session", run_session)
    info = {"run": "test", "block": 0, "app": "citry", "count": 14, "session_index": 0}

    assert cli.run_page_pair(object(), "http://fixture", {}, tmp_path, info, adapter={})
    assert [(call[0][4]["page_load"], call[0][4]["session"]) for call in calls] == [
        (1, "first"),
        (2, "second"),
    ]
    assert [call[1]["initial_only"] for call in calls] == [True, False]


def test_qualification_faults_run_only_after_successful_page_pairs(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "qualify_faults", lambda *args: calls.append(args) or [{"status": "passed"}])

    assert cli.qualification_faults_after_page_pairs(object(), "http://fixture", {}, 14, {}, page_pairs_ok=False) == []
    assert not calls
    assert cli.qualification_faults_after_page_pairs(object(), "http://fixture", {}, 14, {}, page_pairs_ok=True) == [
        {"status": "passed"}
    ]
    assert len(calls) == 1


def test_initial_only_and_not_run_sequences_keep_the_page_load_dimension(tmp_path):
    actions = SimpleNamespace(ACTIONS=[{"name": "select"}, {"name": "insert"}])
    settings = {"scenario": "project_board", "warmups": 0, "cycles": 1}
    assert session_sequence(settings, actions, initial_only=True) == [{"name": "initial"}]

    info = {"app": "citry", "count": 14, "session": "second", "page_load": 2}
    record_not_run_session(settings, tmp_path, info, reason="first page load did not complete correctly")
    rows = [json.loads(line) for line in (tmp_path / "samples.jsonl").read_text().splitlines()]
    assert [row["action"] for row in rows] == [
        "initial",
        "select",
        "filter",
        "clear-filter",
        "invalid-save",
        "save",
        "insert",
        "reorder",
        "remove",
        "probe",
    ]
    assert all(row["page_load"] == 2 and row["status"] == "not-run" for row in rows)


def test_adapter_rejects_unknown_rendering_location(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nrendering="unknown"\n'
    )
    with pytest.raises(ValueError, match="rendering"):
        config.adapter(tmp_path)


def test_adapter_requires_an_explicit_payload_kind_for_hybrid_rendering(tmp_path):
    path = tmp_path / "adapter.toml"
    path.write_text('[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nrendering="hybrid"\n')
    with pytest.raises(ValueError, match="update_payload"):
        config.adapter(tmp_path)
    path.write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nrendering="hybrid"\nupdate_payload="delta"\n'
    )
    assert config.adapter(tmp_path)["update_payload"] == "delta"


def test_adapter_rejects_payload_kind_on_nonhybrid_rendering(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nrendering="server"\nupdate_payload="json"\n'
    )
    with pytest.raises(ValueError, match="only valid for hybrid"):
        config.adapter(tmp_path)


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ('rendering="server"\nhydration_min_count=1400\n', "only valid for hybrid"),
        ('rendering="browser"\nhydration_min_count=1400\n', "only valid for hybrid"),
        ('rendering="hybrid"\nupdate_payload="json"\nhydration_min_count=0\n', "positive integer"),
        ('rendering="hybrid"\nupdate_payload="json"\nhydration_min_count="1400"\n', "positive integer"),
        ('rendering="hybrid"\nupdate_payload="json"\nhydration_min_count=true\n', "positive integer"),
    ],
)
def test_adapter_rejects_invalid_hydration_min_count(tmp_path, fields, message):
    (tmp_path / "adapter.toml").write_text('[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\n' + fields)
    with pytest.raises(ValueError, match=message):
        config.adapter(tmp_path)


def test_hybrid_adapter_mounts_boards_below_hydration_min_count_in_the_browser(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\n'
        'rendering="hybrid"\nupdate_payload="json"\nhydration_min_count=1400\n'
    )
    declared = config.adapter(tmp_path)
    assert [config.initial_rendering(declared, count) for count in (14, 140, 1400)] == [
        "browser",
        "browser",
        "hybrid",
    ]
    # Without the field every board size of a hybrid adapter starts from server HTML.
    assert config.initial_rendering({"rendering": "hybrid", "update_payload": "delta"}, 14) == "hybrid"
    assert config.initial_rendering({}, 14) == "server"


def test_citry_declares_server_html_for_every_board() -> None:
    # With its default settings Citry writes server HTML for Vue to hydrate
    # at every board size; the app's own test checks the pages agree.
    declaration = config.adapter(config.WEB / "apps" / "citry")

    assert declaration["rendering"] == "hybrid"
    assert declaration["update_payload"] == "json"
    assert [config.initial_rendering(declaration, count) for count in (14, 140, 1400)] == [
        "hybrid",
        "hybrid",
        "hybrid",
    ]


def test_adapter_accepts_first_chunk_timing_boundary(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\n'
        'rendering="hybrid"\nupdate_payload="delta"\ntiming_boundary="first-chunk"\n'
    )
    assert config.adapter(tmp_path)["timing_boundary"] == "first-chunk"


def test_adapter_declares_only_supported_local_wheels(tmp_path):
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nlocal_wheels=["citry", "citry-core"]\n'
    )
    assert config.adapter(tmp_path)["local_wheels"] == ["citry", "citry-core"]
    (tmp_path / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nlocal_wheels=["unknown"]\n'
    )
    with pytest.raises(ValueError, match="local_wheels"):
        config.adapter(tmp_path)


def test_heap_after_gc_waits_until_network_accounting_reads_response_bodies() -> None:
    calls = []

    def collect(operation, *_evidence):
        calls.append(("collect", operation))
        return {"errors": []}

    def read_heap_after_gc(operation, _page):
        calls.append(("gc", operation))

    network = SimpleNamespace(collect=collect)
    observer = SimpleNamespace(read_heap_after_gc=read_heap_after_gc)

    payload = collect_network_then_heap_after_gc(
        network, observer, object(), "probe", {}, {}, None, read_heap_after_gc=True
    )
    collect_network_then_heap_after_gc(network, observer, object(), "select", {}, {}, None, read_heap_after_gc=False)
    collect_network_then_heap_after_gc(network, None, object(), "plain", {}, {}, None, read_heap_after_gc=True)

    # Forced collection makes Chromium drop script bodies, so it must follow collect.
    assert calls == [("collect", "probe"), ("gc", "probe"), ("collect", "select"), ("collect", "plain")]
    assert payload == {"errors": []}


def test_every_profile_loads_and_only_the_local_build_profiles_name_local_wheels(tmp_path, monkeypatch):
    # Profiles that name wheels you build load only once those files exist, so
    # create placeholder files at the paths they name under a temporary root.
    names = sorted(path.stem for path in (config.WEB / "profiles").glob("*.toml"))
    assert names, "no profiles found"
    monkeypatch.setattr(config, "ROOT", tmp_path)
    with_wheels = []
    for name in names:
        wheels = tomllib.loads((config.WEB / "profiles" / f"{name}.toml").read_text()).get("local_wheels", {})
        for value in wheels.values():
            (tmp_path / value).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / value).write_bytes(b"placeholder")
        data = config.profile(name)
        assert data["name"] == name
        if wheels:
            with_wheels.append(name)
    # A profile installs only what the lockfiles pin, unless it is listed here
    # on purpose: the testing profile, and the profile that measured Citry
    # 0.6.1 before its release for the docs page.
    assert with_wheels == ["citry-local-wheels", "release-0.6.1-citry"]


def test_release_profile_is_the_cohort_plus_the_docs_page_board_size():
    cohort = tomllib.loads((config.WEB / "profiles/cohort.toml").read_text())
    release = tomllib.loads((config.WEB / "profiles/release-0.6.0.toml").read_text())
    assert release["counts"] == [*cohort["counts"], 1400]
    assert {**release, "name": "cohort", "counts": cohort["counts"]} == cohort


def test_release_rerun_profiles_keep_the_release_settings_of_the_numbers_they_join():
    # A release profile with local wheels measures some apps again, and the
    # docs page shows those numbers beside other apps' numbers from
    # release-0.6.0. The docs data script cannot check most settings, so only
    # the fields compose lets differ may differ. A copy of such a profile is
    # checked here too.
    release = tomllib.loads((config.WEB / "profiles/release-0.6.0.toml").read_text())
    reruns = sorted((config.WEB / "profiles").glob("release-*.toml"))
    reruns = [path for path in reruns if "local_wheels" in tomllib.loads(path.read_text())]
    assert reruns, "no release profile with local wheels found"
    per_run = compose.PER_RUN_FIELDS
    for path in reruns:
        rerun = tomllib.loads(path.read_text())
        # It measures Citry again, plus apps of the release run as controls.
        assert "citry" in rerun["apps"], path.name
        assert set(rerun["apps"]) <= set(release["apps"]), path.name
        assert {k: v for k, v in rerun.items() if k not in per_run} == {
            k: v for k, v in release.items() if k not in per_run
        }, path.name


def test_prepare_stops_when_a_lockfile_needs_wheels_the_profile_does_not_supply(tmp_path, monkeypatch):
    app = tmp_path / "apps/fixture"
    app.mkdir(parents=True)
    (app / "adapter.toml").write_text(
        '[app]\nname="fixture"\nlaunch=["python"]\nhealth="/health"\nlocal_wheels=["citry", "citry-core"]\n'
    )
    (app / "uv.lock").write_text(
        'version = 1\n\n[[package]]\nname = "citry"\nversion = "0.6.0"\n'
        'source = { registry = "../../../../.benchmarks/wheels/citry-0.6.0" }\n\n'
        '[[package]]\nname = "django"\nversion = "6.1.1"\nsource = { registry = "https://pypi.org/simple" }\n'
    )
    monkeypatch.setattr(prepare, "WEB", tmp_path)
    settings = {"apps": ["fixture"]}
    with pytest.raises(ValueError, match=r"fixture locks citry==0\.6\.0 from local wheels"):
        prepare.check_installable(settings)
    # The same lockfile installs once the profile replaces that package.
    prepare.check_installable({**settings, "local_wheels": {"citry": "citry.whl"}})
