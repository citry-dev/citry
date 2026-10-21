"""A rerun reuses what an earlier run stored for unchanged cases, and runs again whatever could have changed."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import tomllib
from typing import TYPE_CHECKING

import pytest
from citry_errors import cache, cli, parallel, report, work
from citry_errors.config import BENCH_ROOT, REPO_ROOT, ConfigError, Framework, load_framework, load_frameworks
from citry_errors.execute import StageOutput, run_stages
from citry_errors.runtime import JourneyRecord, Observation
from conftest import MISTAKES

if TYPE_CHECKING:
    from pathlib import Path

    from conftest import Toy

EVERYTHING = ["toy/baseline", *(f"toy/{mistake}" for mistake in MISTAKES)]


def _reused(run_dir: Path) -> list[str]:
    return json.loads((run_dir / "run.json").read_text())["reused"]


def _files(run_dir: Path) -> dict[str, bytes]:
    """Every file a run wrote, apart from run.json, which names the run's own reuse."""
    return {
        path.relative_to(run_dir).as_posix(): path.read_bytes()
        for path in sorted(run_dir.rglob("*"))
        if path.is_file() and path.name != "run.json"
    }


def test_a_rerun_with_nothing_changed_reuses_every_case_and_writes_the_same_run(toy: Toy) -> None:
    first = toy.run(jobs=3)
    observed = len(toy.observed)
    second = toy.run(jobs=3)
    assert _reused(first) == []
    assert _reused(second) == EVERYTHING
    # No browser check ran again, and every file of the run folder is the same.
    assert len(toy.observed) == observed
    assert _files(second) == _files(first)


def test_no_cache_runs_every_case_again_and_stores_the_fresh_output(toy: Toy) -> None:
    toy.run()
    observed = len(toy.observed)
    forced = toy.run(no_cache=True)
    assert _reused(forced) == []
    assert len(toy.observed) == 2 * observed
    assert _reused(toy.run()) == EVERYTHING


def test_a_changed_case_runs_again_and_the_others_are_reused(toy: Toy) -> None:
    toy.run()
    port = toy.root / "cases" / "m02-changed" / "toy" / "port.toml"
    port.write_text(
        port.read_text()
        .replace('new = "CHANGED"', 'new = "CHANGED twice"')
        .replace('contains = "CHANGED"', 'contains = "CHANGED twice"')
    )
    rerun = toy.run()
    assert "toy/m02-changed" not in _reused(rerun)
    assert set(_reused(rerun)) == set(EVERYTHING) - {"toy/m02-changed"}


def test_a_changed_clean_app_runs_every_case_of_its_framework_again(toy: Toy) -> None:
    toy.run()
    (toy.root / "frameworks" / "toy" / "baseline" / "notes.txt").write_text("a new file in the clean app\n")
    assert _reused(toy.run()) == []


def test_rewording_the_notes_or_the_server_limit_keeps_the_stored_output(toy: Toy) -> None:
    toy.run()
    definition = toy.root / "frameworks" / "toy" / "framework.toml"
    definition.write_text(
        definition.read_text().replace('name = "Toy"\n', 'name = "Toy"\nnotes = "x"\nmax_servers = 2\n')
    )
    assert _reused(toy.run()) == EVERYTHING
    # A change to a command does change what the tools print.
    definition.write_text(definition.read_text().replace('label = "toy check"', 'label = "toy check"\ntimeout = 299'))
    assert _reused(toy.run()) == []


def test_a_change_to_the_runner_code_that_makes_raw_output_runs_everything_again(
    toy: Toy, monkeypatch: pytest.MonkeyPatch
) -> None:
    toy.run()
    monkeypatch.setattr(cache, "environment_digest", lambda: "another runner")
    assert _reused(toy.run()) == []


def test_the_environment_digest_follows_the_runner_lockfile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "runner").mkdir()
    for name in ("pyproject.toml", "uv.lock"):
        (tmp_path / "runner" / name).write_text("one")
    monkeypatch.setattr(cache, "BENCH_ROOT", tmp_path)
    before = cache.environment_digest()
    assert cache.environment_digest() == before
    (tmp_path / "runner" / "uv.lock").write_text("two")
    assert cache.environment_digest() != before


def test_a_stored_case_that_now_needs_its_browser_check_runs_only_that_check(
    toy: Toy, monkeypatch: pytest.MonkeyPatch
) -> None:
    toy.run()
    # As if a scoring change stopped the static catch of m01 counting.
    real = cli._static_catch
    monkeypatch.setattr(
        cli,
        "_static_catch",
        lambda stages: "" if any(s.label == "toy check" and s.error for s in stages) else real(stages),
    )
    observed = len(toy.observed)
    rerun = toy.run()
    caught = {"m01-bad", "m03-bad-again", "m06-bad-third"}
    assert sorted(toy.observed[observed:]) == sorted(caught)
    # Only the browser check ran; the static output was reused, but the case is not listed as reused whole.
    assert set(_reused(rerun)) == set(EVERYTHING) - {f"toy/{mistake}" for mistake in caught}
    records = {record["mistake"]: record for record in toy.records(rerun)}
    assert records["m01-bad"]["runtime"] is not None
    # The next run finds the browser check stored with the case.
    assert _reused(toy.run()) == EVERYTHING


def test_a_server_that_never_answered_is_checked_again_next_run(toy: Toy) -> None:
    toy.silent_servers.add("m02-changed")
    toy.run()
    toy.silent_servers.clear()
    rerun = toy.run()
    assert set(_reused(rerun)) == set(EVERYTHING) - {"toy/m02-changed"}
    records = {record["mistake"]: record for record in toy.records(rerun)}
    assert records["m02-changed"]["strict"] == "silent"


def test_nothing_is_stored_from_a_run_whose_clean_app_had_problems(toy: Toy) -> None:
    # A clean app that fails can mean a broken environment, which would fail every case the same way.
    toy.silent_servers.add("baseline")
    toy.run()
    toy.silent_servers.clear()
    assert _reused(toy.run()) == []
    assert _reused(toy.run()) == EVERYTHING


def test_a_browser_check_whose_journey_stopped_is_run_again_next_time(toy: Toy) -> None:
    toy.stopped_journeys.add("m02-changed")
    toy.run()
    toy.stopped_journeys.clear()
    assert set(_reused(toy.run())) == set(EVERYTHING) - {"toy/m02-changed"}


def test_a_run_without_browser_checks_leaves_them_to_the_next_run(toy: Toy) -> None:
    toy.run(skip_runtime=True)
    observed = len(toy.observed)
    rerun = toy.run()
    # The static output was reused everywhere; only the cases no tool reported needed their browser check.
    caught = ["toy/m01-bad", "toy/m03-bad-again", "toy/m06-bad-third"]
    assert _reused(rerun) == caught
    assert len(toy.observed) == observed + 1 + len(MISTAKES) - len(caught)
    assert _reused(toy.run()) == EVERYTHING


def test_a_damaged_entry_is_run_again_instead_of_stopping_the_run(tmp_path: Path) -> None:
    observation = Observation(server_log=["GET / 200"])
    cache.store(tmp_path, "key", [StageOutput(["tool"], exit_code=0)], observation, b"GET / 200\n")
    (tmp_path / "server.log").unlink()
    entry = cache.load(tmp_path, "key")
    # Without its log, the stored browser check is not used; the stage output still is.
    assert entry is not None
    assert entry.observation is None
    (tmp_path / "stages.json").write_text("not json")
    assert cache.load(tmp_path, "key") is None


def test_an_entry_a_run_stopped_writing_is_not_used(tmp_path: Path) -> None:
    stages = [StageOutput(["tool"], "out", "", 0, 10)]
    cache.store(tmp_path, "key", stages, None, None)
    assert cache.load(tmp_path, "key") is not None
    assert cache.load(tmp_path, "other key") is None
    # The key is written last, so an entry without it is incomplete.
    (tmp_path / "key").unlink()
    assert cache.load(tmp_path, "key") is None


@pytest.mark.parametrize(("exit_code", "kept"), [(0, True), (1, True), (None, False), (-2, False), (-9, False)])
def test_timed_out_or_killed_stages_are_not_stored(exit_code: int | None, kept: bool) -> None:
    assert cache.keeps([StageOutput(["tool"], exit_code=0), StageOutput(["tool"], exit_code=exit_code)]) is kept


def test_nothing_finished_after_ctrl_c_is_stored(tmp_path: Path) -> None:
    stop = threading.Event()
    stop.set()
    context = cli.Context(
        tmp_path,
        observe_runtime=True,
        reuse=True,
        environment="env",
        framework_digests={},
        stop=stop,
        tool_slots=threading.Semaphore(1),
        browser_slots=threading.Semaphore(1),
    )
    cli._store(context, tmp_path / "entry", "key", [StageOutput(["tool"], exit_code=0)], None, None)
    assert not (tmp_path / "entry").exists()


def test_a_stored_browser_check_reads_back_the_same(tmp_path: Path) -> None:
    observation = Observation(
        snapshot={"text": "x", "elements": [["P"]]},
        journeys={"search": JourneyRecord({"text": "y", "elements": []}, "")},
        console_errors=["boom"],
        server_log=["GET / 200"],
    )
    cache.store(tmp_path, "key", [StageOutput(["tool"], exit_code=0)], observation, b"GET / 200\n")
    entry = cache.load(tmp_path, "key")
    assert entry is not None
    assert entry.observation == observation
    assert entry.server_log is not None
    assert entry.server_log.read_bytes() == b"GET / 200\n"


def test_two_runs_cannot_use_one_cache_folder_at_once(tmp_path: Path) -> None:
    with cache.exclusive(tmp_path):
        with pytest.raises(ConfigError, match="another run is using"), cache.exclusive(tmp_path):
            pass
        # The refused run leaves the running one's process id in the lock file.
        assert (tmp_path / "run.lock").read_text() == str(os.getpid())
    # Released when the first run ends.
    with cache.exclusive(tmp_path):
        pass


def test_the_framework_digest_skips_folders_a_working_copy_leaves_out(toy: Toy) -> None:
    framework = load_frameworks(toy.root / "frameworks")["toy"]
    before = cache.framework_digest(framework, toy.cache / "envs" / "toy")
    (framework.baseline / "node_modules").mkdir()
    (framework.baseline / "node_modules" / "pkg.js").write_text("installed")
    assert cache.framework_digest(framework, toy.cache / "envs" / "toy") == before


def test_the_checkout_location_counts_only_for_a_framework_whose_commands_name_it(toy: Toy, tmp_path: Path) -> None:
    framework = load_frameworks(toy.root / "frameworks")["toy"]
    env = toy.cache / "envs" / "toy"
    moved = tmp_path / "other checkout" / "toy"
    shutil.copytree(framework.root, moved)
    assert cache.framework_digest(load_framework(moved), env) == cache.framework_digest(framework, env)
    # Once a command names a file in the checkout, that path reaches the output, so the location counts.
    for root in (framework.root, moved):
        definition = root / "framework.toml"
        definition.write_text(definition.read_text().replace('argv = ["unused', 'argv = ["{framework}/unused'))
    assert cache.framework_digest(load_framework(moved), env) != cache.framework_digest(
        load_framework(framework.root), env
    )


def test_stages_stop_before_the_next_tool_once_the_run_is_ending(toy: Toy) -> None:
    stop = threading.Event()
    stop.set()
    framework = load_frameworks(toy.root / "frameworks")["toy"]
    with pytest.raises(parallel.Stopped):
        run_stages(framework, framework.baseline, stop)


def test_the_framework_digest_follows_what_the_environment_installed(toy: Toy) -> None:
    framework = load_frameworks(toy.root / "frameworks")["toy"]
    env = toy.cache / "envs" / "toy"
    before = cache.framework_digest(framework, env)
    (env / ".venv").mkdir(parents=True)
    (env / ".venv" / "pyvenv.cfg").write_text("version_info = 3.12.9\n")
    assert cache.framework_digest(framework, env) != before


def test_setup_runs_again_when_its_command_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A setup step can build something besides installing the lockfiles, as
    # Tetra's builds its own component library, so a changed step must run.
    monkeypatch.setattr(work, "CACHE", tmp_path / "cache")
    (tmp_path / "baseline").mkdir()
    (tmp_path / "baseline" / "uv.lock").write_text("locked")

    def framework(command: str) -> Framework:
        return Framework("toy", "Toy", ("uv.lock",), ("sh", "-c", command), (), None, "", tmp_path)

    log = tmp_path / "setup.log"
    work.prepare(framework(f"echo first >> {log}"))
    work.prepare(framework(f"echo first >> {log}"))
    work.prepare(framework(f"echo second >> {log}"))
    assert log.read_text().split() == ["first", "second"]


def _package_from_disk(toy: Toy, tmp_path: Path) -> tuple[Framework, Path]:
    """
    Give the toy framework a package installed from a git checkout outside its folder, as Citry's app has.

    The checkout ignores build/, as this repository does, so a build left
    beside the sources is not one of them.
    """
    package = tmp_path / "checkout" / "pkg"
    package.mkdir(parents=True)
    (package / "pyproject.toml").write_text('[project]\nname = "pkg"\nversion = "1.0.0"\n')
    (package / "module.py").write_text("VALUE = 1\n")
    (package.parent / ".gitignore").write_text("build/\n")
    subprocess.run(["git", "init", "-q", str(package.parent)], check=True)
    (toy.root / "frameworks" / "toy" / "baseline" / "pyproject.toml").write_text(
        f'[tool.uv.sources]\npkg = {{ path = "{package.as_posix()}" }}\n'
    )
    return load_frameworks(toy.root / "frameworks")["toy"], package


def test_a_change_to_a_package_installed_from_disk_installs_it_again_and_runs_every_case(
    toy: Toy, tmp_path: Path
) -> None:
    framework, package = _package_from_disk(toy, tmp_path)
    env = toy.cache / "envs" / "toy"
    install, results = work._manifest_digest(framework), cache.framework_digest(framework, env)
    # Build output beside the sources is ignored by git, so it changes nothing.
    (package / "build").mkdir()
    (package / "build" / "module.py").write_text("VALUE = 1\n")
    assert (work._manifest_digest(framework), cache.framework_digest(framework, env)) == (install, results)
    # An edit that no lockfile and no file of the framework's folder records
    # still installs the package again and runs the cases again.
    (package / "module.py").write_text("VALUE = 2\n")
    assert work._manifest_digest(framework) != install
    assert cache.framework_digest(framework, env) != results
    # A new file the sources gain counts too, before anyone commits it.
    (package / "module.py").write_text("VALUE = 1\n")
    (package / "helper.py").write_text("")
    assert work._manifest_digest(framework) != install


def test_a_run_and_its_report_name_the_packages_installed_from_this_repository(toy: Toy, tmp_path: Path) -> None:
    framework, package = _package_from_disk(toy, tmp_path)
    # Only a package inside the repository has a commit to name.
    assert cli._from_checkout([framework], repo=toy.root) == {}
    record = cli._from_checkout([framework], repo=package.parent)
    [package_record] = record["toy"]
    assert (package_record["name"], package_record["version"], package_record["path"]) == ("pkg", "1.0.0", "pkg")
    # Nothing is committed in the made-up checkout, so the sources count as changed.
    assert package_record["changed"] is True
    # The run records the packages next to the commit, and the report names them.
    run_dir = toy.run()
    source = json.loads((run_dir / "run.json").read_text())
    assert "from_checkout" in source
    (run_dir / "run.json").write_text(json.dumps(source | {"from_checkout": record}))
    report.write(run_dir, tmp_path / "report")
    matrix = (tmp_path / "report" / "matrix.md").read_text()
    assert "Toy: pkg 1.0.0 built from this repository at commit" in matrix
    assert "plus uncommitted changes to them, not a published release." in matrix
    assert "Toy: pkg 1.0.0 built from this repository" in (tmp_path / "report" / "report.html").read_text()


def test_the_citry_app_takes_citry_core_at_the_version_citry_pins() -> None:
    # The Citry app overrides citry-core's version by hand (see its
    # pyproject.toml); a release that moves citry's pin must move it too, or
    # the benchmark would run citry against a citry-core it was not built for.
    def pin(requirements: list[str]) -> str:
        [found] = [requirement for requirement in requirements if requirement.startswith("citry-core==")]
        return found

    app = tomllib.loads((BENCH_ROOT / "frameworks" / "citry" / "baseline" / "pyproject.toml").read_text())
    citry = tomllib.loads((REPO_ROOT / "packages" / "py" / "citry" / "pyproject.toml").read_text())
    assert pin(app["tool"]["uv"]["override-dependencies"]) == pin(citry["project"]["dependencies"])
