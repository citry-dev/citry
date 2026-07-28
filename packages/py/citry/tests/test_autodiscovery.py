"""Tests for component-module autodiscovery."""

import importlib
import logging
import sys
import threading
from pathlib import Path
from textwrap import dedent

import pytest

from citry import Citry, CitryLifecycleInProgress, Component
from citry.autodiscovery import find_component_modules


@pytest.fixture
def project(tmp_path, monkeypatch):
    """
    Build an importable project tree under ``tmp_path`` and put it on sys.path.

    Returns a ``write(relpath, content)`` helper. ``tmp_path`` is prepended to
    ``sys.path`` so the tree's packages import by their real dotted names (the
    same condition autodiscovery requires of real projects). Every module the
    test imports - directly or through autodiscovery - is removed from
    ``sys.modules`` on teardown, so package names do not leak between tests.
    """
    before = set(sys.modules)
    monkeypatch.syspath_prepend(str(tmp_path))

    def write(relpath: str, content: str = "") -> Path:
        path = tmp_path / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    yield write

    for name in set(sys.modules) - before:
        sys.modules.pop(name, None)


def _build_app(write, pkg: str, *, autodiscover: bool = True) -> None:
    """Write a package whose ``app`` module holds a Citry bound to ``components/``."""
    write(f"{pkg}/__init__.py")
    write(f"{pkg}/components/__init__.py")
    write(
        f"{pkg}/app.py",
        dedent(f"""
            from pathlib import Path
            from citry import Citry

            app = Citry(dirs=[Path(__file__).parent / "components"], autodiscover={autodiscover})
        """),
    )


def _component(pkg: str, class_name: str, *, template: str = "<div>x</div>") -> str:
    """Source for a component module that binds to ``pkg.app.app``."""
    return dedent(f'''
        from citry import Component
        from {pkg}.app import app


        class {class_name}(Component):
            citry = app
            template = """
            {template}
            """
    ''')


def _load_app(pkg: str):
    """Import the package's app module and return its Citry instance."""
    return importlib.import_module(f"{pkg}.app").app


# ----- find_component_modules (the path -> import-name mechanics) -----


class TestFindComponentModules:
    def test_maps_files_to_import_names(self, project):
        project("pkga/__init__.py")
        project("pkga/comps/__init__.py")
        card = project("pkga/comps/card.py", "x = 1")

        mods = find_component_modules([card.parent])

        assert mods == ["pkga.comps", "pkga.comps.card"]

    def test_maps_nested_subpackages(self, project):
        # A subpackage under a component dir maps to its full dotted path,
        # including the subpackage itself (from its __init__.py).
        project("pkge/__init__.py")
        project("pkge/comps/__init__.py")
        card = project("pkge/comps/card.py", "x = 1")
        project("pkge/comps/sub/__init__.py")
        project("pkge/comps/sub/widget.py", "x = 1")

        mods = find_component_modules([card.parent])

        assert mods == ["pkge.comps", "pkge.comps.card", "pkge.comps.sub", "pkge.comps.sub.widget"]

    def test_skips_underscore_files_and_dirs(self, project):
        project("pkgb/__init__.py")
        project("pkgb/comps/__init__.py")
        card = project("pkgb/comps/card.py", "x = 1")
        project("pkgb/comps/_hidden.py", "raise RuntimeError('must not import')")
        project("pkgb/comps/_priv/__init__.py")
        project("pkgb/comps/_priv/inner.py", "raise RuntimeError('must not import')")

        mods = find_component_modules([card.parent])

        assert mods == ["pkgb.comps", "pkgb.comps.card"]

    def test_skips_dot_prefixed_files_and_dirs(self, project):
        # Editor and OS junk lands in component dirs (emacs .#card.py lock
        # files, macOS ._card.py copies, caches like .cache/). None of it has
        # a valid import name, so it must never become an import candidate,
        # and a dot-prefixed directory hides its whole subtree.
        project("pkgf/__init__.py")
        project("pkgf/comps/__init__.py")
        card = project("pkgf/comps/card.py", "x = 1")
        project("pkgf/comps/.hidden.py", "raise RuntimeError('must not import')")
        project("pkgf/comps/.cache/__init__.py")
        project("pkgf/comps/.cache/inner.py", "raise RuntimeError('must not import')")

        mods = find_component_modules([card.parent])

        assert mods == ["pkgf.comps", "pkgf.comps.card"]

    def test_skips_files_and_dirs_with_dots_in_their_names(self, project):
        # A dot anywhere in a file's stem or a directory's name (backup copies
        # like card.old.py, versioned dirs like assets.v2/) cannot appear in a
        # dotted import name, so such paths must never become import
        # candidates. A dotted directory hides its whole subtree, and a
        # directory merely *named* like a .py file is not a module either.
        project("pkgg/__init__.py")
        project("pkgg/comps/__init__.py")
        card = project("pkgg/comps/card.py", "x = 1")
        project("pkgg/comps/card.old.py", "raise RuntimeError('must not import')")
        project("pkgg/comps/ab..cd.py", "raise RuntimeError('must not import')")
        project("pkgg/comps/assets.v2/widget.py", "raise RuntimeError('must not import')")
        project("pkgg/comps/sub.py/inner.py", "raise RuntimeError('must not import')")

        mods = find_component_modules([card.parent])

        assert mods == ["pkgg.comps", "pkgg.comps.card"]

    def test_skips_symlinks_that_resolve_to_dotted_or_missing_paths(self, project):
        # A symlink's own name can be clean while its target hides behind a
        # dot-prefixed name. The import name comes from the resolved target,
        # so such a link has no valid import name and is skipped, as is a link
        # whose target is gone. A link to a regular module elsewhere in the
        # package still resolves and is discovered under the target's name.
        project("pkgh/__init__.py")
        project("pkgh/comps/__init__.py")
        card = project("pkgh/comps/card.py", "x = 1")
        hidden = project("pkgh/comps/.hidden.py", "raise RuntimeError('must not import')")
        cached = project("pkgh/comps/.cache/real.py", "raise RuntimeError('must not import')")
        shared = project("pkgh/shared_comp.py", "x = 1")
        try:
            (card.parent / "alias.py").symlink_to(hidden)
        except OSError:
            # Windows runners may lack the privilege to create symlinks.
            pytest.skip("symlinks not available on this platform")
        (card.parent / "alias2.py").symlink_to(cached)
        (card.parent / "dangling.py").symlink_to(card.parent / "gone.py")
        (card.parent / "twin.py").symlink_to(shared)

        mods = find_component_modules([card.parent])

        assert mods == ["pkgh.comps", "pkgh.comps.card", "pkgh.shared_comp"]

    def test_ignores_non_python_files(self, project):
        # Component dirs also hold template/js/css assets; only .py files
        # become import candidates. Each asset has a stem no .py file shares,
        # so a suffix-filter regression shows up as an extra module instead of
        # deduplicating into an existing name.
        project("pkgd/__init__.py")
        project("pkgd/comps/__init__.py")
        card = project("pkgd/comps/card.py", "x = 1")
        project("pkgd/comps/layout.html", "<p>x</p>")
        project("pkgd/comps/helper.js", "console.log(1)")
        project("pkgd/comps/style.css", "p {}")

        mods = find_component_modules([card.parent])

        assert mods == ["pkgd.comps", "pkgd.comps.card"]

    def test_nonexistent_dir_contributes_nothing(self, tmp_path):
        # A dir with no .py files (or that does not exist) is simply empty, not
        # an error: an asset-only dirs entry contributes no modules.
        assert find_component_modules([tmp_path / "missing"]) == []

    def test_raises_when_dir_not_on_import_path(self, tmp_path):
        # tmp_path is NOT on sys.path here, so a .py file under it has no import
        # name and discovery must say so loudly rather than guess.
        (tmp_path / "loose.py").write_text("x = 1")

        with pytest.raises(ValueError, match="not on the Python import path"):
            find_component_modules([tmp_path])

    def test_dedupes_across_dirs(self, project):
        project("pkgc/__init__.py")
        project("pkgc/comps/__init__.py")
        card = project("pkgc/comps/card.py", "x = 1")
        comps = card.parent

        # The same directory twice yields each module once.
        assert find_component_modules([comps, comps]) == ["pkgc.comps", "pkgc.comps.card"]


# ----- the lazy trigger and the autodiscover() method -----


class TestInitialize:
    def test_component_inspection_triggers_lazy_discovery(self, project):
        _build_app(project, "inspect_lazy")
        project("inspect_lazy/components/card.py", _component("inspect_lazy", "LazyCard"))
        app = _load_app("inspect_lazy")

        catalog = app.inspect_components()

        assert tuple(component.name for component in catalog.components) == ("lazy-card",)
        assert app._discovered is True
        assert app._registry._builtins_registered is True

    def test_prepares_discovery_builtins_and_tag_rules(self, project):
        _build_app(project, "initialize1")
        project(
            "initialize1/components/card.py",
            dedent('''
                from citry import Component
                from initialize1.app import app


                class Card(Component):
                    citry = app
                    template = """
                    <p>{{ title }}</p>
                    """

                    class Kwargs:
                        title: str
            '''),
        )
        app = _load_app("initialize1")

        assert app.initialize() is None
        assert app._discovered is True
        assert app._registry._builtins_registered is True
        assert app._tag_rules_cache is not None
        assert "c-card" in app._tag_rules_cache
        assert set(app.components) >= {
            "provide",
            "cache",
            "component",
            "element",
            "error-fallback",
            "js",
            "css",
            "card",
        }

    def test_respects_autodiscover_false(self, project):
        _build_app(project, "initialize_off", autodiscover=False)
        project("initialize_off/components/card.py", _component("initialize_off", "Card"))
        app = _load_app("initialize_off")

        app.initialize()

        assert "initialize_off.components.card" not in sys.modules
        assert app.has("card") is False
        assert app._registry._builtins_registered is True
        assert app._tag_rules_cache is not None

        app.autodiscover()
        app.initialize()

        assert app.has("card") is True

    def test_failure_releases_lifecycle_and_retries(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        attempts = 0

        def scan(_dirs, **_kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise KeyboardInterrupt
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        with pytest.raises(KeyboardInterrupt):
            app.initialize()

        assert app.initialize() is None
        assert attempts == 2

    def test_recursive_initialize_raises_and_remains_retryable(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        recurse = True

        def scan(_dirs, **_kwargs):
            nonlocal recurse
            if recurse:
                recurse = False
                app.initialize()
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        with pytest.raises(RuntimeError, match=r"initialize\(\).*recursively"):
            app.initialize()

        assert app.initialize() is None

    def test_rebuilds_rules_after_registration(self):
        app = Citry(autodiscover=False)
        app.initialize()

        class Card(Component):
            citry = app
            template = """
            <p>{{ title }}</p>
            """

            class Kwargs:
                title: str

        assert app._tag_rules_cache is None

        app.initialize()

        assert app._tag_rules_cache is not None
        assert "c-card" in app._tag_rules_cache


class TestConcurrentDiscovery:
    def test_other_thread_cannot_observe_partial_discovery(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        started = threading.Event()
        release = threading.Event()
        discovered_classes: list[type[Component]] = []
        owner_errors: list[BaseException] = []

        def scan(_dirs, **_kwargs):
            class Card(Component):
                citry = app

            discovered_classes.append(Card)
            started.set()
            assert release.wait(5)
            return []

        def owner_lookup():
            try:
                assert app.has("card") is True
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)
        owner = threading.Thread(target=owner_lookup)
        owner.start()
        assert started.wait(5)

        observers = [
            lambda: app.get("card"),
            lambda: app.has("card"),
            lambda: app.components,
            lambda: app.get_component_by_class_id(discovered_classes[0].class_id),
            lambda: repr(app),
            lambda: app._tag_rules(),
        ]
        for observe in observers:
            with pytest.raises(CitryLifecycleInProgress, match="component discovery"):
                observe()

        release.set()
        owner.join(5)

        assert not owner.is_alive()
        assert owner_errors == []
        assert app.has("card") is True

    def test_import_lock_cycle_fails_fast(self, project, monkeypatch):
        _build_app(project, "import_cycle")
        project("import_cycle/components/_sync.py")
        project(
            "import_cycle/components/held.py",
            dedent("""
                from import_cycle.app import app
                from import_cycle.components import _sync

                _sync.module_started.set()
                assert _sync.allow_lookup.wait(5)
                try:
                    app.has("missing")
                except BaseException as err:
                    _sync.lookup_error = err
                finally:
                    _sync.lookup_done.set()
            """),
        )
        sync = importlib.import_module("import_cycle.components._sync")
        sync.module_started = threading.Event()
        sync.allow_lookup = threading.Event()
        sync.lookup_done = threading.Event()
        sync.lookup_error = None
        app = _load_app("import_cycle")
        discovery_reached_locked_module = threading.Event()
        owner_errors: list[BaseException] = []
        importer_errors: list[BaseException] = []
        autodiscovery_module = importlib.import_module("citry.autodiscovery")
        original_import_module = autodiscovery_module.import_module

        def observed_import(module_name):
            if module_name == "import_cycle.components.held":
                discovery_reached_locked_module.set()
            return original_import_module(module_name)

        def import_held():
            try:
                importlib.import_module("import_cycle.components.held")
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                importer_errors.append(err)

        def initialize():
            try:
                app.initialize()
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        monkeypatch.setattr(autodiscovery_module, "import_module", observed_import)
        importer = threading.Thread(target=import_held, daemon=True)
        importer.start()
        assert sync.module_started.wait(5)
        owner = threading.Thread(target=initialize, daemon=True)
        owner.start()
        assert discovery_reached_locked_module.wait(5)

        sync.allow_lookup.set()
        assert sync.lookup_done.wait(5)
        importer.join(5)
        owner.join(5)

        assert not importer.is_alive()
        assert not owner.is_alive()
        assert importer_errors == []
        assert owner_errors == []
        assert isinstance(sync.lookup_error, CitryLifecycleInProgress)


class TestLazyDiscovery:
    def test_first_lookup_triggers_discovery(self, project):
        _build_app(project, "lazy1")
        project("lazy1/components/card.py", _component("lazy1", "Card"))
        app = _load_app("lazy1")

        # Nothing imported the card module yet; the latch is unset.
        assert app._discovered is False
        # The lookup itself imports it and registers Card.
        assert app.has("card") is True
        assert app._discovered is True
        assert "card" in app.components

    def test_tag_rules_path_triggers_discovery(self, project):
        # _tag_rules() reads the whole registry, so discovery must run before it.
        _build_app(project, "lazy2")
        project("lazy2/components/card.py", _component("lazy2", "Card"))
        app = _load_app("lazy2")

        assert app._discovered is False
        app._tag_rules()
        assert app._discovered is True
        assert app.has("card")

    def test_runs_only_once(self, project):
        _build_app(project, "lazy3")
        project("lazy3/components/card.py", _component("lazy3", "Card"))
        app = _load_app("lazy3")

        app.has("card")  # first lookup discovers

        # A module added after the first scan is NOT picked up: discovery is a
        # one-time bootstrap, not a watcher.
        project("lazy3/components/late.py", _component("lazy3", "Late"))
        assert app.has("late") is False

    def test_off_skips_discovery(self, project):
        _build_app(project, "off1", autodiscover=False)
        project("off1/components/card.py", _component("off1", "Card"))
        app = _load_app("off1")

        assert app.has("card") is False  # never imported
        # ...but the explicit method still works on demand.
        imported = app.autodiscover()
        assert "off1.components.card" in imported
        assert app.has("card") is True

    def test_no_dirs_is_a_noop(self):
        # The default-instance condition: autodiscover on, but no dirs to scan.
        c = Citry()  # autodiscover defaults to True
        assert c.has("provide") is True  # built-ins still work
        assert c._discovered is True  # latch set, nothing imported

    def test_failed_scan_rolls_back_partial_registrations_and_retries(self, project):
        _build_app(project, "retry1")
        project(
            "retry1/components/a_card.py",
            _component("retry1", "Card") + "\napp.register(Card, name='card-alias')\n",
        )
        broken = project(
            "retry1/components/z_broken.py",
            _component("retry1", "Ghost") + "\napp._tag_rules()\n" + "raise RuntimeError('broken component module')\n",
        )
        app = _load_app("retry1")

        for _attempt in range(3):
            with pytest.raises(RuntimeError, match="broken component module"):
                app.has("card")
            assert app._discovered is False
            assert set(app._registry._name_to_cls) == {"card", "card-alias"}
            assert {comp_cls.__name__ for comp_cls in app._classes_by_id.values()} == {"Card"}
            assert app._tag_rules_cache is None
            assert app._registry._builtins_registered is False
            assert "retry1.components.a_card" in sys.modules
            assert "retry1.components.z_broken" not in sys.modules

        broken.write_text(_component("retry1", "Badge"))
        importlib.invalidate_caches()

        assert app.has("card") is True
        assert app.has("card-alias") is True
        assert app.has("badge") is True
        assert app.has("ghost") is False
        assert app._discovered is True

    def test_failed_scan_preserves_successful_imported_dependency_registrations(self, project):
        _build_app(project, "retry_dependency")
        project(
            "retry_dependency/components/_shared.py",
            _component("retry_dependency", "Shared"),
        )
        project(
            "retry_dependency/components/_helper.py",
            "from ._shared import Shared\n"
            + _component("retry_dependency", "HelperCard")
            + "\napp.register(HelperCard, name='helper-alias')\n"
            + "app.register(Shared, name='shared-helper-alias')\n"
            + "provide = app.get('provide')\n"
            + "app.register(provide, name='provide-alias')\n",
        )
        broken = project(
            "retry_dependency/components/broken.py",
            "from . import _helper\n"
            "from retry_dependency.app import app\n"
            "app.register(_helper.HelperCard, name='parent-alias')\n"
            "app.unregister(_helper.HelperCard)\n"
            + _component("retry_dependency", "Ghost")
            + "\napp._tag_rules()\n"
            + "raise RuntimeError('broken after helper import')\n",
        )
        app = _load_app("retry_dependency")
        importlib.import_module("retry_dependency.components._shared")

        with pytest.raises(RuntimeError, match="broken after helper import"):
            app.has("missing")

        assert list(app._registry._name_to_cls) == [
            "shared",
            "helpercard",
            "helper-card",
            "helper-alias",
            "shared-helper-alias",
        ]
        assert {comp_cls.__name__ for comp_cls in app._classes_by_id.values()} == {"Shared", "HelperCard"}
        assert app._registry._builtins_registered is False
        assert app._tag_rules_cache is None
        assert app._discovered is False

        broken.write_text("from . import _helper\n" + _component("retry_dependency", "Badge"))
        importlib.invalidate_caches()

        assert app.has("helpercard") is True
        assert app.has("helper-card") is True
        assert app.has("helper-alias") is True
        assert app.has("badge") is True
        assert app.has("ghost") is False
        assert app._discovered is True

    def test_failed_scan_preserves_dependency_file_loaded_while_rollback_starts(self, project, monkeypatch):
        _build_app(project, "retry_dependency_file")
        asset = project("retry_dependency_file/components/dependency.js", "console.log('dependency')")
        project(
            "retry_dependency_file/components/_helper.py",
            dedent("""
                from citry import Component
                from retry_dependency_file.app import app


                class Dependency(Component):
                    citry = app
                    js_file = "dependency.js"
            """),
        )
        project(
            "retry_dependency_file/components/broken.py",
            "from . import _helper\nraise RuntimeError('broken after dependency import')\n",
        )
        app = _load_app("retry_dependency_file")
        restore_started = threading.Event()
        allow_restore = threading.Event()
        errors: list[BaseException] = []
        original_restore = app._restore_registration_state

        def paused_restore(state, **kwargs):
            restore_started.set()
            assert allow_restore.wait(5)
            return original_restore(state, **kwargs)

        def discover():
            try:
                app.has("missing")
            except BaseException as error:  # noqa: BLE001 - worker failures are asserted below
                errors.append(error)

        monkeypatch.setattr(app, "_restore_registration_state", paused_restore)
        worker = threading.Thread(target=discover)
        worker.start()
        assert restore_started.wait(5)

        helper = importlib.import_module("retry_dependency_file.components._helper")
        assert helper.Dependency.get_js() == "console.log('dependency')"
        allow_restore.set()
        worker.join(5)

        assert not worker.is_alive()
        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)
        assert app._registry._name_to_cls["dependency"] is helper.Dependency
        assert app.get_components_for_file(asset) == [helper.Dependency]

    def test_implicit_reentry_does_not_start_a_nested_scan(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        calls = 0

        def scan(_dirs, **_kwargs):
            nonlocal calls
            calls += 1
            assert app.has("missing") is False
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        assert app.has("missing") is False
        assert calls == 1
        assert app._discovered is True

    def test_find_failure_is_retryable(self, tmp_path, monkeypatch):
        (tmp_path / "visible_after_retry.py").write_text("value = 1\n")
        app = Citry(dirs=[tmp_path])

        with pytest.raises(ValueError, match="not on the Python import path"):
            app.has("missing")
        assert app._discovered is False

        monkeypatch.syspath_prepend(str(tmp_path))
        importlib.invalidate_caches()

        assert app.has("missing") is False
        assert app._discovered is True


class TestAutodiscoverMethod:
    def test_returns_imported_module_names(self, project):
        _build_app(project, "m1", autodiscover=False)
        project("m1/components/card.py", _component("m1", "Card"))
        project("m1/components/badge.py", _component("m1", "Badge"))
        app = _load_app("m1")

        imported = app.autodiscover()

        assert set(imported) >= {"m1.components.card", "m1.components.badge"}
        assert app.has("card")
        assert app.has("badge")

    def test_scans_cleanly_past_dot_prefixed_junk(self, project):
        # A dot-prefixed file or directory inside a component dir (editor
        # lock files, OS metadata copies, tool caches) must not crash the
        # scan; only the real modules are imported.
        _build_app(project, "mdot", autodiscover=False)
        project("mdot/components/card.py", _component("mdot", "Card"))
        project("mdot/components/.hidden.py", "raise RuntimeError('must not import')")
        project("mdot/components/.cache/junk.py", "raise RuntimeError('must not import')")
        app = _load_app("mdot")

        imported = app.autodiscover()

        assert imported == ["mdot.components", "mdot.components.card"]
        assert app.has("card")

    def test_is_idempotent(self, project):
        _build_app(project, "m2", autodiscover=False)
        project("m2/components/card.py", _component("m2", "Card"))
        app = _load_app("m2")

        app.autodiscover()
        # A second call re-imports nothing new and does not raise
        # (re-registering the same class is a no-op).
        app.autodiscover()
        assert app.has("card")

    def test_rescan_does_not_reexecute_loaded_modules(self, project):
        # The contract behind idempotency: an already-loaded module is walked
        # for components, never re-run (the guarantee at the center of
        # djc #1598). Replacing the module on a rescan would break the first
        # assert; re-running its body would raise AlreadyRegistered from the
        # Card class statement before either assert fires. Holding the module
        # and its Card keeps both checks anchored to the first execution.
        _build_app(project, "rescan", autodiscover=False)
        project("rescan/components/card.py", _component("rescan", "Card"))
        app = _load_app("rescan")

        app.autodiscover()
        module = sys.modules["rescan.components.card"]
        card_class = module.Card

        app.autodiscover()

        assert sys.modules["rescan.components.card"] is module
        assert module.Card is card_class
        assert app.has("card")

    def test_emits_debug_logs(self, project, caplog):
        _build_app(project, "m_log", autodiscover=False)
        project("m_log/components/card.py", _component("m_log", "Card"))
        app = _load_app("m_log")

        with caplog.at_level(logging.DEBUG, logger="citry"):
            app.autodiscover()

        msgs = [r.getMessage() for r in caplog.records if r.name == "citry"]
        assert any(m.startswith("Autodiscovery found") for m in msgs)
        assert any(m.startswith("Importing component module") and "m_log.components.card" in m for m in msgs)

    def test_explicit_dirs_argument(self, project):
        # autodiscover(dirs=...) imports an extra location without disabling the
        # automatic scan of settings.dirs.
        _build_app(project, "m3")
        project("m3/extra/__init__.py")
        widget = project("m3/extra/widget.py", _component("m3", "Widget"))
        app = _load_app("m3")

        imported = app.autodiscover(dirs=[widget.parent])

        assert "m3.extra.widget" in imported
        # The explicit-dirs call did not consume the one-time settings.dirs scan.
        assert app._discovered is False
        assert app.has("widget")

    def test_failed_explicit_dirs_scan_leaves_configured_scan_pending(self, project):
        _build_app(project, "extra_retry")
        project("extra_retry/components/card.py", _component("extra_retry", "Card"))
        project("extra_retry/extra/__init__.py")
        broken = project(
            "extra_retry/extra/broken.py",
            _component("extra_retry", "Ghost") + "\nraise RuntimeError('extra scan failed')\n",
        )
        app = _load_app("extra_retry")

        with pytest.raises(RuntimeError, match="extra scan failed"):
            app.autodiscover(dirs=[broken.parent])
        assert app._discovered is False
        assert app.has("ghost") is False

        assert app.has("card") is True
        assert app._discovered is True

    def test_failed_no_arg_scan_marks_complete_only_after_retry(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path], autodiscover=False)
        attempts = 0

        def scan(_dirs, **_kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("discovery failed")
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        with pytest.raises(RuntimeError, match="discovery failed"):
            app.autodiscover()
        assert app._discovered is False

        assert app.autodiscover() == []
        assert app._discovered is True
        assert attempts == 2

    def test_direct_reentry_raises_without_starting_a_nested_scan(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        calls = 0

        def scan(_dirs, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                app.autodiscover()
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        with pytest.raises(RuntimeError, match="already running"):
            app.has("missing")
        assert calls == 1
        assert app._discovering is False
        assert app._discovered is False

        assert app.autodiscover() == []
        assert calls == 2
        assert app._discovered is True

    def test_clear_during_discovery_raises_and_leaves_discovery_retryable(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        calls = 0

        def scan(_dirs, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                app.clear()
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        with pytest.raises(RuntimeError, match=r"clear\(\) cannot run"):
            app.has("missing")
        assert app._discovering is False
        assert app._discovered is False

        assert app.autodiscover() == []
        assert calls == 2
        assert app._discovered is True


class TestEndToEnd:
    def test_component_referenced_in_template_is_discovered(self, project):
        # A root component renders <c-card>; Card lives in a sibling module that
        # only autodiscovery imports. Rendering must find it.
        _build_app(project, "e2e")
        project("e2e/components/card.py", _component("e2e", "Card", template="<span>card</span>"))
        app = _load_app("e2e")

        class Page(Component):
            citry = app
            template = """
            <div><c-card /></div>
            """

        html = Page().render().serialize()

        assert ">card</span>" in html
        assert app.has("card")

    def test_clear_then_lookup_rebuilds_the_registry(self, project):
        # clear() re-arms discovery; the next lookup re-runs the scan and
        # rebuilds the registry. The module is already imported, so this works
        # only because the scan re-registers its components by walking it.
        _build_app(project, "clr")
        project("clr/components/card.py", _component("clr", "Card"))
        app = _load_app("clr")

        assert app.has("card")
        app.clear()
        assert app._discovered is False  # re-armed

        # The very next lookup rediscovers and the component is back, identical
        # to before the clear().
        assert app.has("card") is True
        assert app._discovered is True

    def test_explicit_autodiscover_repopulates_after_clear(self, project):
        # The same rebuild via the explicit method rather than a lazy lookup.
        _build_app(project, "clr2", autodiscover=False)
        project("clr2/components/card.py", _component("clr2", "Card"))
        app = _load_app("clr2")

        app.autodiscover()
        assert app.has("card")

        app.clear()
        assert app.has("card") is False  # cleared

        app.autodiscover()  # walks the already-imported module and re-registers
        assert app.has("card") is True

    def test_walk_registers_a_pre_imported_module(self, project):
        # If a component module is imported before discovery runs (so the
        # metaclass already registered it), discovery still ends in the same
        # place: the walk finds it already registered and leaves it be.
        _build_app(project, "pre")
        project("pre/components/card.py", _component("pre", "Card"))
        app = _load_app("pre")
        importlib.import_module("pre.components.card")  # pre-import before any lookup

        assert app.has("card") is True
        assert sorted(app.components).count("card") == 1  # not double-registered
