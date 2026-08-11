"""Tests for the component registry."""

import gc
import importlib
import subprocess
import sys
import textwrap
import threading
from concurrent.futures import ThreadPoolExecutor
from weakref import ref

import pytest

from citry import (
    AlreadyRegistered,
    Citry,
    CitryLifecycleInProgress,
    Component,
    Extension,
    InMemoryCache,
    NotRegistered,
)
from citry.lifecycle import _LifecycleCoordinator


class TestLifecycleCoordinator:
    def test_base_exception_between_claim_and_body_releases_owner(self):
        class InterruptAfterFirstRelease:
            def __init__(self):
                self.lock = threading.Lock()
                self.interrupt = True

            def __enter__(self):
                self.lock.acquire()
                return self

            def __exit__(self, *_args):
                self.lock.release()
                if self.interrupt:
                    self.interrupt = False
                    raise KeyboardInterrupt
                return False

        coordinator = _LifecycleCoordinator()
        coordinator._state_lock = InterruptAfterFirstRelease()

        with pytest.raises(KeyboardInterrupt), coordinator.operation("probe"):
            pass

        assert coordinator._state is None
        competitor_errors: list[BaseException] = []

        def claim_after_interrupt():
            try:
                with coordinator.operation("retry"):
                    pass
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                competitor_errors.append(err)

        competitor = threading.Thread(target=claim_after_interrupt)
        competitor.start()
        competitor.join(5)

        assert not competitor.is_alive()
        assert competitor_errors == []

    def test_component_class_gc_does_not_reenter_a_held_lifecycle_lock(self):
        # Run the real non-reentrant lock scenario in a child process so a
        # regression fails on a bounded timeout rather than wedging pytest.
        script = textwrap.dedent(
            """
            import gc
            import weakref

            from citry import Citry, Component

            app = Citry(autodiscover=False)

            class Temporary(Component):
                citry = app

            app.unregister(Temporary)
            temporary_ref = weakref.ref(Temporary)
            lock = app._registry._lifecycle._state_lock
            lock.acquire()
            try:
                del Temporary
                gc.collect()
                assert temporary_ref() is None
            finally:
                lock.release()

            print("CLASS-GC-WITH-HELD-LIFECYCLE-LOCK-COMPLETED")
            """
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Component class garbage collection blocked while the lifecycle lock was held.")

        assert completed.returncode == 0, completed.stderr
        assert "CLASS-GC-WITH-HELD-LIFECYCLE-LOCK-COMPLETED" in completed.stdout


class TestRegistration:
    def test_registry_strongly_owns_a_class_until_explicit_unregistration(self):
        app = Citry(autodiscover=False)

        class Temporary(Component):
            citry = app

        temporary_ref = ref(Temporary)
        del Temporary
        gc.collect()

        registered_class = temporary_ref()
        assert registered_class is not None
        assert app.has("temporary") is True

        app.unregister(registered_class)
        del registered_class
        gc.collect()
        assert temporary_ref() is None

    def test_auto_registered_on_class_definition(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        assert c.has("mycomp")

    def test_multiple_components(self):
        c = Citry()

        class CompA(Component):
            citry = c

        class CompB(Component):
            citry = c

        assert c.has("compa")
        assert c.has("compb")


class TestAtomicRegistration:
    def test_success_publishes_every_component_and_yields_none(self):
        app = Citry(autodiscover=False)

        with app.atomic_registration() as transaction_value:

            class First(Component):
                citry = app

            class Second(Component):
                citry = app

        assert transaction_value is None
        assert app.get("first") is First
        assert app.get("second") is Second

    def test_exception_restores_every_registration_from_the_block(self):
        app = Citry(autodiscover=False)

        class Existing(Component):
            citry = app

        existing_class_id = Existing.class_id

        with pytest.raises(RuntimeError, match="reject group"):  # noqa: PT012
            with app.atomic_registration():

                class First(Component):
                    citry = app

                class Second(Component):
                    citry = app

                raise RuntimeError("reject group")

        assert app.get("existing") is Existing
        assert app.get_component_by_class_id(existing_class_id) is Existing
        assert app.has("first") is False
        assert app.has("second") is False

    def test_base_exception_restores_the_block(self):
        class StopRegistration(BaseException):
            pass

        app = Citry(autodiscover=False)

        with pytest.raises(StopRegistration):  # noqa: PT012
            with app.atomic_registration():

                class Interrupted(Component):
                    citry = app

                raise StopRegistration

        assert app.has("interrupted") is False

    def test_nested_block_is_rejected_without_blocking_component_creation(self):
        app = Citry(autodiscover=False)

        with app.atomic_registration():

            class Outer(Component):
                citry = app

            with pytest.raises(RuntimeError, match="cannot run recursively"):
                with app.atomic_registration():
                    pass

            class AfterRejectedNestedBlock(Component):
                citry = app

        assert app.get("outer") is Outer
        assert app.get("afterrejectednestedblock") is AfterRejectedNestedBlock

    def test_error_caught_inside_the_block_commits_created_classes(self):
        app = Citry(autodiscover=False)

        with app.atomic_registration():

            class Retained(Component):
                citry = app

            with pytest.raises(RuntimeError, match="caught inside"):
                raise RuntimeError("caught inside")

        assert app.get("retained") is Retained

    def test_competing_thread_cannot_observe_a_partial_group(self):
        app = Citry(autodiscover=False)
        started = threading.Event()
        release = threading.Event()

        def register_group():
            with app.atomic_registration():

                class Pending(Component):
                    citry = app

                started.set()
                assert release.wait(5)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(register_group)
            assert started.wait(5)
            with pytest.raises(CitryLifecycleInProgress, match="atomic component registration"):
                app.has("pending")
            release.set()
            future.result(timeout=5)

        assert app.has("pending") is True

    def test_rollback_restores_state_without_firing_unregistration_hooks(self):
        unregistered = []

        class RecordUnregistration(Extension):
            name = "record_atomic_unregistration"

            def on_component_unregistered(self, ctx):
                unregistered.append(ctx.component_class)

        app = Citry(extensions=[RecordUnregistration], autodiscover=False)

        with pytest.raises(RuntimeError, match="reject group"):  # noqa: PT012
            with app.atomic_registration():

                class Temporary(Component):
                    citry = app

                raise RuntimeError("reject group")

        assert app.has("temporary") is False
        assert unregistered == []

    def test_unregistration_is_rejected_because_the_block_is_additive(self):
        app = Citry(autodiscover=False)

        class Existing(Component):
            citry = app

        with app.atomic_registration():
            with pytest.raises(RuntimeError, match="block is additive"):
                app.unregister(Existing)

        assert app.get("existing") is Existing

    def test_hook_created_components_roll_back_with_the_primary_class(self):
        class CreateAuxiliary(Extension):
            name = "create_atomic_auxiliary"

            def on_component_class_created(self, ctx):
                if ctx.component_class.__name__ == "Primary":

                    class Auxiliary(Component):
                        citry = ctx.citry

        app = Citry(extensions=[CreateAuxiliary], autodiscover=False)

        with pytest.raises(RuntimeError, match="after class creation"):  # noqa: PT012
            with app.atomic_registration():

                class Primary(Component):
                    citry = app

                raise RuntimeError("after class creation")

        assert app.has("primary") is False
        assert app.has("auxiliary") is False

    def test_rejected_later_hook_rolls_back_without_vetoable_cleanup(self):
        cleanup_calls = []

        class RejectSecond(Extension):
            name = "reject_second_atomic_component"

            def on_component_registered(self, ctx):
                if ctx.component_class.__name__ == "Second":
                    raise RuntimeError("reject second")

            def on_component_unregistered(self, ctx):
                cleanup_calls.append(ctx.component_class)
                raise RuntimeError("reject cleanup")

        app = Citry(extensions=[RejectSecond], autodiscover=False)

        with pytest.raises(RuntimeError, match="reject second"):  # noqa: PT012
            with app.atomic_registration():

                class First(Component):
                    citry = app

                class Second(Component):
                    citry = app

        assert app.has("first") is False
        assert app.has("second") is False
        assert cleanup_calls == []


class TestNameNormalization:
    def test_pascal_case_lowered(self):
        c = Citry()

        class MyCard(Component):
            citry = c

        assert c.has("mycard")

    def test_pascal_case_also_registers_kebab(self):
        c = Citry()

        class MyCard(Component):
            citry = c

        assert c.has("my-card")
        assert c.get("mycard") is c.get("my-card")

    def test_single_word_no_duplicate(self):
        c = Citry()

        class Card(Component):
            citry = c

        assert c.has("card")
        assert c.get("card") is Card

    def test_explicit_name_override(self):
        c = Citry()

        class MyWidget(Component):
            citry = c
            name = "fancy-widget"

        assert c.has("fancy-widget")

    def test_case_insensitive_lookup(self):
        c = Citry()

        class MyCard(Component):
            citry = c

        assert c.get("MyCard") is MyCard
        assert c.get("MYCARD") is MyCard
        assert c.get("mycard") is MyCard


class TestGet:
    def test_get_returns_class(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        assert c.get("mycomp") is MyComp

    def test_get_not_registered_raises(self):
        c = Citry()
        with pytest.raises(NotRegistered):
            c.get("nonexistent")


class TestHas:
    def test_has_registered(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        assert c.has("mycomp") is True

    def test_has_not_registered(self):
        c = Citry()
        assert c.has("nonexistent") is False


class TestComponentsDict:
    def test_components_dict(self):
        c = Citry()

        class Card(Component):
            citry = c

        comps = c.components
        assert "card" in comps
        assert comps["card"] is Card


class TestBuiltinLifecycle:
    def test_initialize_prepares_the_complete_citry_instance(self, tmp_path, monkeypatch):
        app = Citry(dirs=[tmp_path])
        scans = 0

        def scan(_dirs, **_kwargs):
            nonlocal scans
            scans += 1
            return []

        citry_module = importlib.import_module("citry.citry")
        monkeypatch.setattr(citry_module, "import_component_modules", scan)

        assert app.initialize() is None
        assert scans == 1
        assert app._discovered is True
        assert app._tag_rules_cache is not None

    def test_failed_creation_rolls_back_and_retries(self):
        class FailOnce(Extension):
            name = "fail_once"
            failed = False

            def on_component_registered(self, ctx):
                if ctx.name == "component" and not self.failed:
                    self.failed = True
                    ctx.citry._tag_rules()
                    raise RuntimeError("component registration failed")

        c = Citry(extensions=[FailOnce])

        with pytest.raises(RuntimeError, match="component registration failed"):
            _ = c.components

        assert c._registry._name_to_cls == {}
        assert dict(c._classes_by_id) == {}
        assert c._tag_rules_cache is None
        assert c._registry._builtins_registered is False
        assert set(c.components) == {
            "provide",
            "cache",
            "component",
            "element",
            "error-fallback",
            "js",
            "css",
            "i18n",
            "trans",
        }

    def test_other_thread_cannot_observe_builtin_that_rolls_back(self):
        started = threading.Event()
        release = threading.Event()
        doomed: list[type[Component]] = []
        owner_errors: list[BaseException] = []

        class RejectFirstProvide(Extension):
            name = "reject_first_provide"
            rejected = False

            def on_component_registered(self, ctx):
                if ctx.name == "Provide" and not self.rejected:
                    self.rejected = True
                    doomed.append(ctx.component_class)
                    started.set()
                    assert release.wait(5)
                    raise RuntimeError("reject first Provide")

        app = Citry(extensions=[RejectFirstProvide])

        def initialize_builtins():
            try:
                app.initialize()
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        owner = threading.Thread(target=initialize_builtins)
        owner.start()
        assert started.wait(5)

        with pytest.raises(CitryLifecycleInProgress):
            app.get("provide")

        release.set()
        owner.join(5)

        assert not owner.is_alive()
        assert len(owner_errors) == 1
        assert str(owner_errors[0]) == "reject first Provide"
        assert app._registry._name_to_cls == {}
        assert dict(app._classes_by_id) == {}

        app.initialize()

        assert app.get("provide") is not doomed[0]

    def test_class_created_failure_is_not_published_as_success(self):
        class AlwaysFail(Extension):
            name = "always_fail"

            def on_component_class_created(self, ctx):
                if ctx.component_class.__name__ == "Provide":
                    raise RuntimeError("provide class rejected")

        c = Citry(extensions=[AlwaysFail])

        for _attempt in range(3):
            with pytest.raises(RuntimeError, match="provide class rejected"):
                _ = c.components
            assert c._registry._name_to_cls == {}
            assert c._registry._builtins_registered is False
            assert c._registry._initializing_builtins is False

    def test_base_exception_rolls_back_and_retries(self):
        class StopInitialization(BaseException):
            pass

        class FailOnce(Extension):
            name = "fail_once_base_exception"
            failed = False

            def on_component_registered(self, ctx):
                if ctx.name == "Provide" and not self.failed:
                    self.failed = True
                    raise StopInitialization

        c = Citry(extensions=[FailOnce])

        with pytest.raises(StopInitialization):
            _ = c.components
        assert c._registry._name_to_cls == {}
        assert c._registry._builtins_registered is False
        assert set(c.components) == {
            "provide",
            "cache",
            "component",
            "element",
            "error-fallback",
            "js",
            "css",
            "i18n",
            "trans",
        }

    def test_builtin_token_from_another_registry_is_rejected(self):
        c = Citry()
        other = Citry()

        def make_with_wrong_token():
            class Provide(Component, _citry_builtin=other._registry._builtin_registration_token):
                citry = c
                name = "provide"

        c._create_builtin_components = make_with_wrong_token

        for _attempt in range(2):
            with pytest.raises(RuntimeError, match="outside built-in initialization"):
                _ = c.components
            assert c._registry._name_to_cls == {}
            assert c._registry._builtins_registered is False

    def test_reserved_name_protection_stays_active_during_builtin_creation(self):
        errors = []

        class TryReservedName(Extension):
            name = "try_reserved_name"

            def on_component_class_created(self, ctx):
                if ctx.component_class.__name__ != "Provide":
                    return
                try:

                    class Css(Component):
                        citry = ctx.citry

                except AlreadyRegistered as err:
                    errors.append(str(err))

        c = Citry(extensions=[TryReservedName])

        assert set(c.components) == {
            "provide",
            "cache",
            "component",
            "element",
            "error-fallback",
            "js",
            "css",
            "i18n",
            "trans",
        }
        assert len(errors) == 1
        assert "reserved for the built-in <c-css>" in errors[0]

    def test_registered_hook_can_lookup_the_current_builtin(self):
        seen = []

        class LookupProvide(Extension):
            name = "lookup_provide"

            def on_component_registered(self, ctx):
                if ctx.name == "Provide":
                    seen.append(ctx.citry.get("provide") is ctx.component_class)

        c = Citry(extensions=[LookupProvide])

        assert c.has("css") is True
        assert seen == [True]

    def test_clear_during_builtin_creation_raises_and_rolls_back(self):
        class ClearDuringCreation(Extension):
            name = "clear_during_creation"

            def on_component_registered(self, ctx):
                if ctx.name == "Provide":
                    ctx.citry.clear()

        c = Citry(extensions=[ClearDuringCreation])

        for _attempt in range(2):
            with pytest.raises(RuntimeError, match=r"clear\(\) cannot run"):
                _ = c.components
            assert c._registry._name_to_cls == {}
            assert c._registry._builtins_registered is False

    def test_builtin_cannot_be_unregistered(self):
        c = Citry()

        with pytest.raises(ValueError, match=r"built-in <c-provide> cannot be unregistered"):
            c.unregister("provide")
        with pytest.raises(ValueError, match=r"built-in <c-provide> cannot be unregistered"):
            c.unregister(c.get("provide"))

        assert c.has("provide") is True

    def test_retired_builtin_class_cannot_be_registered_after_clear(self):
        c = Citry(autodiscover=False)
        old_provide = c.get("provide")

        c.register(old_provide, name="legacy-provide")
        assert c.get("legacy-provide") is old_provide

        c.clear()

        with pytest.raises(ValueError, match="Cannot register retired built-in component 'Provide'"):
            c.register(old_provide, name="legacy-provide")

        c.initialize()
        assert c.get("provide") is not old_provide
        assert c.has("legacy-provide") is False

    def test_clear_resets_all_citry_registration_state(self):
        c = Citry()
        retained = c.get("provide")

        c.clear()

        with pytest.raises(KeyError, match=retained.class_id):
            c.get_component_by_class_id(retained.class_id)
        assert set(c.components) == {
            "provide",
            "cache",
            "component",
            "element",
            "error-fallback",
            "js",
            "css",
            "i18n",
            "trans",
        }


class TestManualRegister:
    def test_manual_register_with_name(self):
        c = Citry()

        class Card(Component):
            citry = c

        c.register(Card, name="card-alias")
        assert c.has("card-alias")
        assert c.get("card-alias") is Card

    @pytest.mark.parametrize("name", [None, "card-alias"])
    def test_foreign_component_is_rejected_without_mutating_either_engine(self, name):
        events = []

        class RecordRegistrations(Extension):
            name = "record_registrations"

            def on_component_registered(self, ctx):
                events.append(ctx.name)

        source = Citry()
        target = Citry(extensions=[RecordRegistrations])

        class Card(Component):
            citry = source

        source_components = source.components
        target_components = target.components
        target_rules = target._tag_rules_cache
        events.clear()

        with pytest.raises(ValueError, match="only be registered with its owning Citry instance"):
            target.register(Card, name=name)

        assert source.components == source_components
        assert target.components == target_components
        assert target._tag_rules_cache is target_rules
        assert events == []
        assert target.has("card-alias") is False

    def test_component_owner_cannot_change_after_class_definition(self):
        first = Citry()
        second = Citry()

        class Card(Component):
            citry = first

        Card.citry = first
        with pytest.raises(AttributeError, match=r"Cannot change Card\.citry"):
            Card.citry = second
        with pytest.raises(AttributeError, match=r"Cannot delete Card\.citry"):
            del Card.citry

        assert Card.citry is first
        assert first.get("card") is Card
        assert second.has("card") is False

    def test_nested_declarations_cannot_be_rebound_after_class_definition(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Kwargs:
                title: str

            class Events:
                def save(self):
                    return None

        original_kwargs = Card.Kwargs
        original_events = Card.Events
        Card.Kwargs = original_kwargs

        with pytest.raises(AttributeError, match=r"Cannot rebind Card\.Kwargs"):
            Card.Kwargs = type("Replacement", (), {})
        with pytest.raises(AttributeError, match=r"Cannot delete Card\.Events"):
            del Card.Events
        with pytest.raises(AttributeError, match=r"Cannot rebind Card\.State"):
            Card.State = type("LateState", (), {"value": 1})

        assert Card.Kwargs is original_kwargs
        assert Card.Events is original_events

    def test_root_component_default_owner_cannot_change(self):
        with pytest.raises(AttributeError, match=r"Cannot change Component\.citry"):
            Component.citry = Citry()

    def test_component_subclass_must_keep_its_concrete_base_owner(self):
        first = Citry()
        second = Citry()

        class Base(Component):
            citry = first

        with pytest.raises(ValueError, match=r"component base 'Base'.*another Citry instance"):

            class ForeignChild(Base):
                citry = second

        class LocalChild(Base):
            pass

        assert LocalChild.citry is first
        assert first.get("localchild") is LocalChild
        assert second.has("foreignchild") is False

    def test_class_created_hook_cannot_move_a_component_to_another_engine(self):
        other = Citry()

        class MoveOwner(Extension):
            name = "move_owner"

            def on_component_class_created(self, ctx):
                if ctx.component_class.__name__ == "Card":
                    ctx.component_class.citry = other

        app = Citry(extensions=[MoveOwner])

        with pytest.raises(AttributeError, match=r"Cannot change Card\.citry"):

            class Card(Component):
                citry = app

        assert app.has("card") is False
        assert other.has("card") is False

    def test_registration_function_creates_a_distinct_component_tree_per_engine(self):
        def register_components(app):
            class PackageCard(Component):
                citry = app
                name = "package-card"

            return PackageCard

        first = Citry()
        second = Citry()
        first_card = register_components(first)
        second_card = register_components(second)

        assert first_card is not second_card
        assert first.get("package-card") is first_card
        assert second.get("package-card") is second_card

    def test_reregister_same_class_is_noop(self):
        c = Citry()

        class Card(Component):
            citry = c

        c.register(Card)


class TestConcurrentRegistryLifecycle:
    def test_failed_registration_rejects_competing_mutations(self):
        started = threading.Event()
        release = threading.Event()
        owner_errors: list[BaseException] = []

        class RejectFragile(Extension):
            name = "reject_fragile"

            def on_component_registered(self, ctx):
                if ctx.name == "fragile-alias":
                    started.set()
                    assert release.wait(5)
                    raise RuntimeError("reject fragile")

        target = Citry(extensions=[RejectFragile], autodiscover=False)

        class Existing(Component):
            citry = target

        class Fragile(Component):
            citry = target

        class Other(Component):
            citry = target

        target.register(Existing, name="existing-alias")

        def register_fragile():
            try:
                target.register(Fragile, name="fragile-alias")
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        owner = threading.Thread(target=register_fragile)
        owner.start()
        assert started.wait(5)

        with pytest.raises(CitryLifecycleInProgress):
            target.register(Other, name="other-alias")
        with pytest.raises(CitryLifecycleInProgress):
            target.unregister("existing-alias")
        with pytest.raises(CitryLifecycleInProgress):
            target.clear()

        release.set()
        owner.join(5)

        assert not owner.is_alive()
        assert len(owner_errors) == 1
        assert str(owner_errors[0]) == "reject fragile"
        assert target.has("existing-alias") is True
        assert target.has("fragile-alias") is False
        assert target.has("other-alias") is False

        target.register(Other, name="other-alias")
        target.unregister("existing-alias")
        assert target.has("other-alias") is True
        assert target.has("existing-alias") is False

    def test_class_created_hook_is_inside_lifecycle(self):
        started = threading.Event()
        release = threading.Event()
        owner_errors: list[BaseException] = []

        class PauseClassCreation(Extension):
            name = "pause_class_creation"

            def on_component_class_created(self, ctx):
                if ctx.component_class.__name__ == "ThreadCard":
                    started.set()
                    assert release.wait(5)

        target = Citry(extensions=[PauseClassCreation], autodiscover=False)

        class Other(Component):
            citry = target

        def define_component():
            try:

                class ThreadCard(Component):
                    citry = target

            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        owner = threading.Thread(target=define_component)
        owner.start()
        assert started.wait(5)

        with pytest.raises(CitryLifecycleInProgress):
            target.register(Other, name="other-alias")
        with pytest.raises(CitryLifecycleInProgress):

            class Rejected(Component):
                citry = target

        release.set()
        owner.join(5)

        assert not owner.is_alive()
        assert owner_errors == []
        assert target.has("threadcard") is True

    def test_clear_owns_lifecycle_through_cache_callback(self):
        started = threading.Event()
        release = threading.Event()
        owner_errors: list[BaseException] = []

        class PausingCache(InMemoryCache):
            def clear(self):
                started.set()
                assert release.wait(5)
                super().clear()

        app = Citry(cache=PausingCache(), autodiscover=False)

        class Card(Component):
            citry = app

        app.initialize()

        def clear():
            try:
                app.clear()
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        owner = threading.Thread(target=clear)
        owner.start()
        assert started.wait(5)

        with pytest.raises(CitryLifecycleInProgress, match=r"Citry\.clear\(\)"):
            app.has("card")
        with pytest.raises(CitryLifecycleInProgress, match=r"Citry\.clear\(\)"):
            app.register(Card, name="copy")

        release.set()
        owner.join(5)

        assert not owner.is_alive()
        assert owner_errors == []
        assert app.has("card") is False

    def test_clear_callback_cannot_reenter_lifecycle(self):
        errors: list[RuntimeError] = []
        app = None

        class ReentrantCache(InMemoryCache):
            def clear(self):
                assert app is not None
                try:
                    app.has("missing")
                except RuntimeError as err:
                    errors.append(err)
                super().clear()

        app = Citry(cache=ReentrantCache(), autodiscover=False)

        app.clear()

        assert len(errors) == 1
        assert "Citry.clear()" in str(errors[0])

    def test_initialized_instance_supports_concurrent_reads(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template = """
            <p>{{ title }}</p>
            """

            class Kwargs:
                title: str

        app.initialize()
        barrier = threading.Barrier(8)
        errors: list[BaseException] = []

        def read_ready_state():
            try:
                barrier.wait(5)
                for _index in range(100):
                    assert app.get("card") is Card
                    assert app.has("card") is True
                    assert app.get_component_by_class_id(Card.class_id) is Card
                    assert "c-card" in app._tag_rules()
                    assert len(set(app.components.values())) >= 1
                    repr(app)
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                errors.append(err)

        threads = [threading.Thread(target=read_ready_state) for _index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(5)

        assert all(not thread.is_alive() for thread in threads)
        assert errors == []


class TestUnregister:
    def test_unregister_by_class(self):
        c = Citry()

        class Card(Component):
            citry = c

        assert c.has("card")
        c.unregister(Card)
        assert not c.has("card")

    def test_unregister_by_class_removes_all_names(self):
        c = Citry()

        class MyCard(Component):
            citry = c

        assert c.has("mycard")
        assert c.has("my-card")
        c.unregister(MyCard)
        assert not c.has("mycard")
        assert not c.has("my-card")

    def test_unregister_by_name(self):
        c = Citry()

        class Card(Component):
            citry = c

        c.unregister("card")
        assert not c.has("card")

    def test_unregister_not_registered_raises(self):
        c = Citry()
        with pytest.raises(NotRegistered):
            c.unregister("nonexistent")

    def test_unregister_leaves_unrelated_component_registered(self):
        c = Citry()

        class Card(Component):
            citry = c

        class Table(Component):
            citry = c

        c.unregister(Card)

        assert not c.has("card")
        assert c.get("table") is Table

    def test_const_cache_is_evicted_only_after_the_final_alias(self):
        c = Citry()

        class MyCard(Component):
            citry = c
            template = """
            <p>card</p>
            """

        str(MyCard())
        assert len(c._const_body_cache) == 1

        c.unregister("mycard")
        assert c.get("my-card") is MyCard
        assert len(c._const_body_cache) == 1

        c.unregister("my-card")
        assert len(c._const_body_cache) == 0

    def test_rejected_unregister_preserves_const_cache(self):
        class RejectUnregister(Extension):
            name = "reject_unregister"

            def on_component_unregistered(self, ctx):
                raise RuntimeError("keep component")

        c = Citry(extensions=[RejectUnregister])

        class Card(Component):
            citry = c
            template = """
            <p>card</p>
            """

        str(Card())

        with pytest.raises(RuntimeError, match="keep component"):
            c.unregister(Card)

        assert c.get("card") is Card
        assert len(c._const_body_cache) == 1

    def test_unregister_hook_reregistration_preserves_const_cache(self):
        class Reregister(Extension):
            name = "reregister"

            def on_component_unregistered(self, ctx):
                ctx.citry.register(ctx.component_class, ctx.name)

        c = Citry(extensions=[Reregister])

        class Card(Component):
            citry = c
            template = """
            <p>card</p>
            """

        str(Card())
        c.unregister(Card)

        assert c.get("card") is Card
        assert len(c._const_body_cache) == 1


class TestDuplicateDetection:
    def test_duplicate_name_raises(self):
        c = Citry()

        class Card(Component):
            citry = c

        with pytest.raises(AlreadyRegistered):

            class Card2(Component):
                citry = c
                name = "card"

    @pytest.mark.parametrize("reserved_name", ["if", "elif", "else", "for", "empty", "raw", "fill", "slot"])
    def test_structural_tag_name_raises(self, reserved_name):
        c = Citry()

        with pytest.raises(AlreadyRegistered, match=rf"structural <c-{reserved_name}>"):

            class Unreachable(Component):
                citry = c
                name = reserved_name


class TestNameValidation:
    def test_valid_names(self):
        c = Citry()
        for valid_name in ["card", "my-card", "Card123", "a.b", "my_comp"]:

            class Tmp(Component):
                citry = c
                name = valid_name

            c.clear()

    def test_invalid_name_starts_with_digit(self):
        c = Citry()
        with pytest.raises(ValueError, match="Invalid component name"):

            class Bad(Component):
                citry = c
                name = "123card"

    def test_invalid_name_has_spaces(self):
        c = Citry()
        with pytest.raises(ValueError, match="Invalid component name"):

            class Bad(Component):
                citry = c
                name = "my card"

    def test_invalid_name_with_final_newline(self):
        c = Citry()
        with pytest.raises(ValueError, match="Invalid component name"):

            class Bad(Component):
                citry = c
                name = "card\n"
