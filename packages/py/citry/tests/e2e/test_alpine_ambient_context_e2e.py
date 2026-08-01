"""Browser acceptance for rendered client provide, inject, and unprovide."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def test_rendered_component_ancestors_settle_before_sibling_slot_descendants(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Reader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = `${inject("outer")}:${inject("inner")}`;
          });
        """
        template = """
          <output class="rendered-order-reader" x-text="value"></output>
        """

    class InnerProvider(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("inner", "inner");
          });
        """
        template = """
          <section>
            <c-slot />
          </section>
        """

    class OuterProvider(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("outer", "outer");
          });
        """
        template = """
          <main>
            <c-slot />
          </main>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-outer-provider>
                <c-inner-provider>
                  <c-reader />
                </c-inner-provider>
                <c-inner-provider>
                  <c-reader />
                </c-inner-provider>
              </c-outer-provider>
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function(
        "[...document.querySelectorAll('.rendered-order-reader')]"
        ".every((element) => element.textContent === 'outer:inner')"
    )

    assert page.locator(".rendered-order-reader").all_inner_texts() == ["outer:inner", "outer:inner"]


def test_component_context_supports_values_symbols_boundaries_and_rootless_consumers(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Reader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            const service = inject("service", null);
            scope.value = service?.name ?? "missing";
            scope.symbolValue = inject(Symbol.for("citry:test-symbol"), "missing");
            scope.undefinedValue = inject("defined-undefined", "fallback") === undefined ? "present" : "wrong";
            scope.undefinedDefault = inject("missing-with-default", undefined) === undefined ? "default" : "wrong";
            try {
              inject("missing-without-default");
            } catch (error) {
              window.__ambientMissingError = error.message;
            }
            window.__ambientReaderIdentity = service === window.__ambientService;
          });
        """
        template = """
          <output
            class="reader"
            x-text="value + ':' + symbolValue + ':' + undefinedValue + ':' + undefinedDefault"
          ></output>
        """

    class RootlessReader(Component):
        citry = c
        js = """
          $component(({ inject }) => {
            window.__ambientRootless = inject("service").name;
          });
        """
        template = """
          rootless
        """

    class BlockedReader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("service", null)?.name ?? "missing";
          });
        """
        template = """
          <output class="blocked-reader" x-text="value"></output>
        """

    class RestoredReader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("service").name;
          });
        """
        template = """
          <output class="restored-reader" x-text="value"></output>
        """

    class Restorer(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("service", { name: "restored" });
          });
        """
        template = """
          <div class="restorer">
            <c-restored-reader />
          </div>
        """

    class Boundary(Component):
        citry = c
        js = """
          $component(({ inject, unprovide }) => {
            window.__ambientBoundaryOwnValue = inject("service").name;
            unprovide("service");
          });
        """
        template = """
          <section class="boundary">
            <c-blocked-reader />
            <c-restorer />
          </section>
        """

    class Provider(Component):
        citry = c
        js = """
          $component(({ inject, provide, reactive, scope }) => {
            const service = reactive({ name: "outer" });
            window.__ambientService = service;
            scope.ownValue = inject("service", "missing");
            provide("service", service);
            provide(Symbol.for("citry:test-symbol"), "symbol");
            provide("defined-undefined", undefined);
            Promise.resolve().then(() => {
              try {
                provide("late", true);
              } catch (error) {
                window.__ambientLateHookError = error.message;
              }
            });
          });
        """
        template = """
          <main class="provider">
            <output class="own-value" x-text="ownValue"></output>
            <c-reader />
            <c-rootless-reader />
            <c-boundary />
          </main>
        """

    class MultiRootProvider(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("multi-root", "shared");
          });
        """
        template = """
          <output class="multi-root-reader" x-text="$inject('multi-root')"></output>
          <output class="multi-root-reader" x-text="$inject('multi-root')"></output>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-provider />
              <c-multi-root-provider />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.restored-reader')?.textContent === 'restored'")
    page.wait_for_function("window.__ambientLateHookError")

    assert page.locator(".own-value").inner_text() == "missing"
    assert page.locator(".reader").inner_text() == "outer:symbol:present:default"
    assert page.locator(".blocked-reader").inner_text() == "missing"
    assert page.locator(".restored-reader").inner_text() == "restored"
    assert page.locator(".multi-root-reader").all_inner_texts() == ["shared", "shared"]
    assert page.evaluate("window.__ambientRootless") == "outer"
    assert page.evaluate("window.__ambientBoundaryOwnValue") == "outer"
    assert page.evaluate("window.__ambientReaderIdentity") is True
    assert "missing-without-default" in page.evaluate("window.__ambientMissingError")
    assert "synchronous $component initialization" in page.evaluate("window.__ambientLateHookError")


def test_alpine_magics_are_descendant_only_and_attribute_cleanup_is_exact(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class MagicTree(Component):
        citry = c
        template = """
          <section
            class="magic-provider"
            x-data="{
              own: 'unset',
              lateError: '',
              invalidError: '',
              init() {
                $provide('data-init', 'from-data-init');
              },
              late() {
                try {
                  $provide('late', true);
                } catch (error) {
                  this.lateError = error.message;
                }
              },
              invalid() {
                try {
                  $inject(2);
                } catch (error) {
                  this.invalidError = error.message;
                }
              }
            }"
            x-init="$provide('theme', { name: 'outer' }); own = $inject('theme', 'missing')"
          >
            <output class="magic-own" x-text="own"></output>
            <output class="magic-reader" x-text="$inject('theme').name"></output>
            <output class="magic-data-init" x-text="$inject('data-init')"></output>
            <div class="magic-boundary" x-init="$unprovide('theme')">
              <output class="magic-blocked" x-text="$inject('theme', 'missing')"></output>
              <div x-init="$provide('theme', { name: 'restored' })">
                <output class="magic-restored" x-text="$inject('theme').name"></output>
              </div>
            </div>
            <button class="magic-late" @click="late()">late</button>
            <output class="magic-late-error" x-text="lateError"></output>
            <button class="magic-invalid" @click="invalid()">invalid</button>
            <output class="magic-invalid-error" x-text="invalidError"></output>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-magic-tree />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.magic-restored')?.textContent === 'restored'")

    assert page.locator(".magic-own").inner_text() == "missing"
    assert page.locator(".magic-reader").inner_text() == "outer"
    assert page.locator(".magic-data-init").inner_text() == "from-data-init"
    assert page.locator(".magic-blocked").inner_text() == "missing"
    assert page.locator(".magic-restored").inner_text() == "restored"

    page.locator(".magic-late").click()
    page.wait_for_function("document.querySelector('.magic-late-error')?.textContent.includes('initial evaluation')")
    page.locator(".magic-invalid").click()
    page.wait_for_function(
        "document.querySelector('.magic-invalid-error')?.textContent.includes('non-empty string or a symbol')"
    )

    result = page.evaluate(
        """
        async () => {
          const provider = document.querySelector('.magic-provider');
          const reader = document.querySelector('.magic-reader');
          const errors = {};
          for (const name of ['provide', 'inject', 'unprovide']) {
            try {
              Alpine.magic(name, () => null);
            } catch (error) {
              errors['public:' + name] = error.message;
            }
            try {
              Citry.alpine._magic(name, () => null);
            } catch (error) {
              errors['extension:' + name] = error.message;
            }
          }
          provider.setAttribute(
            'x-init',
            `window.__ambientDuringReplacement = Alpine.evaluate(
              $el.querySelector('.magic-reader'),
              "$inject('theme', 'missing')",
            ); $provide('theme', { name: 'changed' })`,
          );
          await new Promise((resolve) => setTimeout(resolve));
          const changed = Alpine.evaluate(reader, "$inject('theme').name");
          provider.removeAttribute('x-init');
          await new Promise((resolve) => setTimeout(resolve));
          const removed = Alpine.evaluate(reader, "$inject('theme', 'missing')");
          return {
            changed,
            duringReplacement: window.__ambientDuringReplacement,
            removed,
            frames: Citry.alpine._debug().runtime.ambientMagicFrames,
            errors,
          };
        }
        """
    )
    assert result["changed"] == "changed"
    assert result["duringReplacement"] == "missing"
    assert result["removed"] == "missing"
    assert result["frames"] == 3
    assert "non-empty string or a symbol" in page.locator(".magic-invalid-error").inner_text()
    for name in ("provide", "inject", "unprovide"):
        assert f"${name} is reserved by Citry" in result["errors"][f"public:{name}"]
        assert f"${name} is reserved by Citry" in result["errors"][f"extension:{name}"]


def test_failed_component_setup_rolls_back_its_provides(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Reader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("failed-provider", "missing");
          });
        """
        template = """
          <output class="failed-provider-reader" x-text="value"></output>
        """

    class FailedProvider(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("failed-provider", "must-not-leak");
            throw new Error("intentional setup failure");
          });
        """
        template = """
          <section>
            <c-reader />
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-failed-provider />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.failed-provider-reader')?.textContent === 'missing'")

    assert page.locator(".failed-provider-reader").inner_text() == "missing"


def test_nested_component_frames_keep_nearest_order_on_one_shared_root(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Reader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("shared-root-order");
          });
        """
        template = """
          <output class="shared-root-reader" x-text="value"></output>
        """

    class Inner(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("shared-root-order", "inner");
          });
        """
        template = """
          <c-reader />
        """

    class Outer(Component):
        citry = c
        js = """
          $component(({ provide }) => {
            provide("shared-root-order", "outer");
          });
        """
        template = """
          <c-inner />
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-outer />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.shared-root-reader')?.textContent === 'inner'")

    assert page.locator(".shared-root-reader").inner_text() == "inner"


def test_root_magic_is_nearer_for_descendants_but_outside_its_component_hook(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Reader(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("same-root-order");
          });
        """
        template = """
          <output class="same-root-reader" x-text="value"></output>
        """

    class MixedProvider(Component):
        citry = c
        js = """
          $component(({ inject, provide }) => {
            window.__sameRootCapturedInject = () => inject("same-root-order", "missing");
            provide("same-root-order", "hook");
          });
        """
        template = """
          <section x-init="$provide('same-root-order', 'magic')">
            <c-reader />
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <main x-init="$provide('same-root-order', 'incoming')">
                <c-mixed-provider />
              </main>
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.same-root-reader')?.textContent === 'magic'")

    assert page.locator(".same-root-reader").inner_text() == "magic"
    assert page.evaluate("window.__sameRootCapturedInject()") == "incoming"


def test_indirect_magic_write_belongs_to_the_directive_that_called_it(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class IndirectProvider(Component):
        citry = c
        template = """
          <main
            x-data="{
              install() {
                $provide('indirect-directive', 'active');
              }
            }"
          >
            <section
              class="indirect-provider"
              data-decoy="install()"
              x-ref="install()"
              x-init="install()"
              x-effect="install()"
            >
              <output
                class="indirect-reader"
                x-text="$inject('indirect-directive', 'missing')"
              ></output>
            </section>
          </main>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-indirect-provider />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.indirect-reader')?.textContent === 'active'")

    result = page.evaluate(
        """
        async () => {
          const provider = document.querySelector('.indirect-provider');
          const reader = document.querySelector('.indirect-reader');
          provider.removeAttribute('x-effect');
          await new Promise((resolve) => setTimeout(resolve));
          const afterEffectRemoval = Alpine.evaluate(
            reader,
            "$inject('indirect-directive', 'missing')",
          );
          provider.removeAttribute('x-init');
          await new Promise((resolve) => setTimeout(resolve));
          const afterInitRemoval = Alpine.evaluate(
            reader,
            "$inject('indirect-directive', 'missing')",
          );
          return {
            afterEffectRemoval,
            afterInitRemoval,
            frames: Citry.alpine._debug().runtime.ambientMagicFrames,
          };
        }
        """
    )

    assert result == {
        "afterEffectRemoval": "active",
        "afterInitRemoval": "missing",
        "frames": 0,
    }


def test_stored_inject_keeps_the_element_where_the_magic_was_read(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class AsyncReader(Component):
        citry = c
        template = """
          <section x-init="$provide('async-route', 'outer')">
            <main x-data="{ read: $inject }">
              <div x-init="$provide('async-route', 'inner')">
                <output
                  class="async-route-reader"
                  x-text="await Promise.resolve().then(() => read('async-route'))"
                ></output>
              </div>
            </main>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-async-reader />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.async-route-reader')?.textContent === 'outer'")

    assert page.locator(".async-route-reader").inner_text() == "outer"


def test_ancestor_magic_settles_before_descendant_component_hook(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("theme").name;
          });
        """
        template = """
          <output class="mixed-child" x-text="value"></output>
        """

    class Parent(Component):
        citry = c
        template = """
          <section x-init="$provide('theme', { name: 'magic-parent' })">
            <c-child />
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-parent />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.mixed-child')?.textContent === 'magic-parent'")

    assert page.locator(".mixed-child").inner_text() == "magic-parent"


def test_object_bind_provider_settles_before_descendant_component_hook(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("via-bind", "missing");
          });
        """
        template = """
          <output class="object-bind-reader" x-text="value"></output>
        """

    class Parent(Component):
        citry = c
        template = """
          <section x-bind="{ 'x-init': `$provide('via-bind', 'bound')` }">
            <c-child />
            <output
              class="object-bind-magic-reader"
              x-text="$inject('via-bind', 'missing')"
            ></output>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-parent />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.object-bind-reader')?.textContent === 'bound'")
    page.wait_for_function("document.querySelector('.object-bind-magic-reader')?.textContent === 'bound'")

    assert page.locator(".object-bind-reader").inner_text() == "bound"
    result = page.evaluate(
        """
        async () => {
          const provider = document.querySelector('[x-bind]');
          const reader = document.querySelector('.object-bind-magic-reader');
          provider.removeAttribute('x-bind');
          await new Promise((resolve) => setTimeout(resolve));
          return {
            value: Alpine.evaluate(reader, "$inject('via-bind', 'missing')"),
            frames: Citry.alpine._debug().runtime.ambientMagicFrames,
          };
        }
        """
    )

    assert result == {"value": "missing", "frames": 0}


def test_programmatic_alpine_bind_cleanup_removes_its_provider(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class BoundProvider(Component):
        citry = c
        template = """
          <section class="programmatic-provider" x-data="{}">
            <output
              class="programmatic-reader"
              x-text="$inject('programmatic', 'missing')"
            ></output>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-bound-provider />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    result = page.evaluate(
        """
        async () => {
          const provider = document.querySelector('.programmatic-provider');
          const reader = document.querySelector('.programmatic-reader');
          const cleanupFirst = Alpine.bind(provider, {
            'x-init': "$provide('programmatic', 'first')",
          });
          const cleanupSecond = Alpine.bind(provider, {
            'x-init': "$provide('programmatic', 'second')",
          });
          await new Promise((resolve) => setTimeout(resolve));
          const active = Alpine.evaluate(reader, "$inject('programmatic', 'missing')");
          const framesWhileActive = Citry.alpine._debug().runtime.ambientMagicFrames;
          cleanupFirst();
          await new Promise((resolve) => setTimeout(resolve));
          const afterFirstCleanup = Alpine.evaluate(reader, "$inject('programmatic', 'missing')");
          const framesAfterFirstCleanup = Citry.alpine._debug().runtime.ambientMagicFrames;
          cleanupSecond();
          await new Promise((resolve) => setTimeout(resolve));
          return {
            active,
            afterFirstCleanup,
            afterSecondCleanup: Alpine.evaluate(reader, "$inject('programmatic', 'missing')"),
            framesWhileActive,
            framesAfterFirstCleanup,
            framesAfterSecondCleanup: Citry.alpine._debug().runtime.ambientMagicFrames,
          };
        }
        """
    )

    assert result == {
        "active": "second",
        "afterFirstCleanup": "second",
        "afterSecondCleanup": "missing",
        "framesWhileActive": 1,
        "framesAfterFirstCleanup": 1,
        "framesAfterSecondCleanup": 0,
    }


def test_structural_move_re_resolves_injection_from_the_new_html_ancestors(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class RouteReader(Component):
        citry = c
        template = """
          <output class="moved-route-reader" x-text="$inject('route')"></output>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <section class="left-route" x-init="$provide('route', 'left')">
                <div class="complete-component-range">
                  <c-route-reader />
                </div>
              </section>
              <section class="right-route" x-init="$provide('route', 'right')"></section>
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.moved-route-reader')?.textContent === 'left'")

    page.evaluate(
        """
        document.querySelector('.right-route').append(
          document.querySelector('.complete-component-range'),
        )
        """
    )
    page.wait_for_function("document.querySelector('.moved-route-reader')?.textContent === 'right'")

    assert page.locator(".moved-route-reader").inner_text() == "right"


def test_mirrored_hook_injection_requires_every_placement_to_agree(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Consumer(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            try {
              scope.value = inject("theme");
              window.__ambientMirrorResults.push(scope.value);
            } catch (error) {
              scope.value = "conflict";
              window.__ambientMirrorResults.push(error.message);
            }
          });
        """
        template = """
          <output class="mirror-consumer" x-text="value ?? 'conflict'"></output>
        """

    class DefaultConsumer(Component):
        citry = c
        js = """
          $component(({ inject, scope }) => {
            scope.value = inject("theme", "fallback");
          });
        """
        template = """
          <output class="mirror-default-consumer" x-text="value"></output>
        """

    class Ping(Component):
        citry = c

        class Events:
            def ping(self) -> None:
                return None

        template = """
          <span>ping</span>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <script>window.__ambientMirrorResults = [];</script>
              <div class="equal-slot" x-init="$provide('theme', 'same')"></div>
              <div class="equal-slot" x-init="$provide('theme', 'same')"></div>
              <div class="conflict-slot" x-init="$provide('theme', 'first')"></div>
              <div class="conflict-slot" x-init="$provide('theme', 'second')"></div>
              <div class="missing-slot" x-init="$unprovide('theme')"></div>
              <div class="missing-slot"></div>
              <c-ping />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    equal_fragment = Consumer().render().serialize(deps_strategy="fragment")
    conflict_fragment = Consumer().render().serialize(deps_strategy="fragment")
    missing_fragment = DefaultConsumer().render().serialize(deps_strategy="fragment")
    page.evaluate(
        """
        async ([equalHtml, conflictHtml, missingHtml]) => {
          await Citry.events.applyActions([
            { action: 'render', target: '.equal-slot', swap: 'inner', html: equalHtml },
          ]);
          await Citry.events.applyActions([
            { action: 'render', target: '.conflict-slot', swap: 'inner', html: conflictHtml },
          ]);
          await Citry.events.applyActions([
            { action: 'render', target: '.missing-slot', swap: 'inner', html: missingHtml },
          ]);
        }
        """,
        [equal_fragment, conflict_fragment, missing_fragment],
    )
    page.wait_for_function("window.__ambientMirrorResults?.length === 2")

    results = page.evaluate("window.__ambientMirrorResults")
    assert results[0] == "same"
    assert "ambiguous" in results[1]
    assert page.locator(".mirror-consumer").all_inner_texts() == ["same", "same", "conflict", "conflict"]
    assert page.locator(".mirror-default-consumer").all_inner_texts() == ["fallback", "fallback"]


def test_slot_ambient_context_uses_rendered_site_and_teleport_uses_authored_origin(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Receiver(Component):
        citry = c
        template = """
          <section
            class="receiver"
            x-init="$provide('theme', { name: 'receiver' })"
          >
            <c-slot />
          </section>
        """

    class TeleportProvider(Component):
        citry = c
        template = """
          <section x-init="$provide('theme', { name: 'teleport-origin' })">
            <template x-teleport="#ambient-teleport-target">
              <output class="teleported-reader" x-text="$inject('theme').name"></output>
            </template>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <div id="ambient-teleport-target"></div>
              <main x-data="{ owner: 'caller' }">
                <c-receiver>
                  <output
                    class="fill-reader"
                    x-text="owner + ':' + $inject('theme').name"
                  ></output>
                </c-receiver>
              </main>
              <c-teleport-provider />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.fill-reader')?.textContent === 'caller:receiver'")
    page.wait_for_function("document.querySelector('.teleported-reader')?.textContent === 'teleport-origin'")

    assert page.locator(".fill-reader").inner_text() == "caller:receiver"
    assert page.locator("#ambient-teleport-target .teleported-reader").inner_text() == "teleport-origin"


def test_morph_replaces_magic_frames_and_retires_captured_hook_helpers(page: Any, serve_live: Any) -> None:
    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    c = Citry()
    c.set_mounted_prefix("/citry")

    class MorphProvider(Component):
        citry = c

        class Kwargs:
            value: str

        class Slots:
            pass

        class Events:
            def refresh(self) -> None:
                return None

        js = """
          $component(({ inject, provide }) => {
            window.__ambientMorphHelpers = window.__ambientMorphHelpers || [];
            window.__ambientMorphHelpers.push({ inject, provide });
          });
        """
        template = """
          <section
            class="morph-context-provider"
            c-bind="attrs"
          >
            <output
              class="morph-context-reader"
              x-text="$inject('morph-context')"
            ></output>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
            return {
                "attrs": {
                    "x-init": f"$provide('morph-context', '{kwargs.value}')",
                },
            }

    class Page(Component):
        citry = c
        template = """
          <html>
            <body>
              <c-morph-provider value="old" />
            </body>
          </html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.morph-context-reader')?.textContent === 'old'")

    fresh = MorphProvider(value="new").render().serialize(deps_strategy="fragment")
    page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const oldRoot = document.querySelector('.morph-context-provider');
          const oldId = oldRoot.getAttribute('data-cid');
          const anchor = internal.getAnchor(oldId);
          window.__ambientMorphAnchor = anchor;
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: 'render', target: 'render:' + oldId, swap: 'morph', html }],
            },
            { anchor, instance: oldId, event: 'refresh' },
          );
        }
        """,
        [fresh],
    )
    page.wait_for_function("document.querySelector('.morph-context-reader')?.textContent === 'new'")

    result = page.evaluate(
        """
        async () => {
          const internal = Citry.events._internal;
          const anchor = window.__ambientMorphAnchor;
          const afterMorph = document.querySelector('.morph-context-reader').textContent;
          const freshAfterMorph = Alpine.evaluate(
            document.querySelector('.morph-context-reader'),
            "$inject('morph-context')",
          );
          const framesAfterMorph = Citry.alpine._debug().runtime.ambientMagicFrames;
          let staleError = '';
          try {
            window.__ambientMorphHelpers[0].provide('stale', true);
          } catch (error) {
            staleError = error.message;
          }
          const currentId = anchor.componentId;
          anchor.epoch = 2;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [
                {
                  action: 'render',
                  target: 'render:' + currentId,
                  swap: 'morph',
                  html: '<p class="morph-context-retired">retired</p>',
                },
              ],
            },
            { anchor, instance: currentId, event: 'refresh' },
          );
          await new Promise((resolve) => setTimeout(resolve));
          return {
            afterMorph,
            freshAfterMorph,
            framesAfterMorph,
            framesAfterRetirement: Citry.alpine._debug().runtime.ambientMagicFrames,
            staleError,
          };
        }
        """
    )

    assert result["afterMorph"] == "new", messages
    assert result["freshAfterMorph"] == "new"
    assert result["framesAfterMorph"] == 1
    assert result["framesAfterRetirement"] == 0
    assert "disposed" in result["staleError"]
    assert page.locator(".morph-context-retired").inner_text() == "retired"
