"""
Browser proofs that re-renders keep what the user typed.

They also check that a server render can remove or replace an element that
carries a runtime directive, including one around a caller's slot content.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e


def _open(page: Any, serve_live: Any, engine: Citry, root: Component) -> list[str]:
    engine.set_mounted_prefix("/citry")
    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, root.render().serialize(), "") + "/")
    return faults


def _send(page: Any, selector: str) -> None:
    # Sending from script leaves the focus where the test put it.
    page.evaluate(
        "selector => Citry.events.send(document.querySelector(selector), 'advance', {})",
        selector,
    )


def test_a_constant_input_value_keeps_the_typed_text_until_the_template_changes_it(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-retained-constant-value", autodiscover=False)  # noqa: S106

    class Profile(Component):
        citry = engine

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Profile(step=state.step)

        def template_data(self, kwargs, slots):
            return {"step": kwargs.step, "renamed": kwargs.step >= 2}

        template = """
            <form class="profile">
              <c-if cond="renamed">
                <input class="role" name="role" value="Admin" />
              </c-if>
              <c-else>
                <input class="role" name="role" value="Owner" />
              </c-else>
              <output class="step">{{ step }}</output>
              <output class="clicks" v-text="clicks"></output>
              <button class="local" type="button" @click="clicks++">local</button>
            </form>
        """

        js = """
            $component({data: () => ({clicks: 0})});
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-profile /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelector('.clicks')?.textContent === '0'")
    role = page.locator(".role")
    assert role.input_value() == "Owner"

    role.fill("Editor")
    page.evaluate("window.__role = document.querySelector('.role')")
    # A local update re-renders the component. Vue never writes a constant
    # value again, so the typed text stays.
    page.locator(".local").click()
    page.wait_for_function("document.querySelector('.clicks').textContent === '1'")
    assert role.input_value() == "Editor"

    # A server render with the same template does not write it again either.
    _send(page, ".profile")
    page.wait_for_function("document.querySelector('.step').textContent === '1'")
    assert role.input_value() == "Editor"
    assert page.evaluate("document.querySelector('.role') === window.__role") is True

    # When the server's template writes another value, the element shows it,
    # because Citry must not leave a changed template's output stale.
    _send(page, ".profile")
    page.wait_for_function("document.querySelector('.step').textContent === '2'")
    assert role.input_value() == "Admin"
    assert role.get_attribute("value") == "Admin"
    assert faults == []


def test_a_server_value_keeps_the_typed_text_until_the_server_changes_it(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-retained-server-value", autodiscover=False)  # noqa: S106

    class Account(Component):
        citry = engine

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Account(step=state.step)

        def template_data(self, kwargs, slots):
            # The first two renders send the same values; the third changes them.
            changed = kwargs.step >= 2
            return {
                "step": kwargs.step,
                "email": "new@example.com" if changed else "ada@example.com",
                "bio": "Changed bio" if changed else "Bio",
                "plan": "pro" if changed else "free",
                "extra": {"value": "Spread changed" if changed else "Spread"},
            }

        # `.mirror` binds `value` to browser state, so Vue writes it on every
        # render. Its `c-name` makes the element carry Python attributes too,
        # which must not turn the browser binding into a server value.
        template = """
            <form class="account">
              <input class="email" c-value="email" />
              <input class="spread" c-bind="extra" />
              <textarea class="bio" c-value="bio"></textarea>
              <select class="plan" c-value="plan">
                <option value="free">Free</option>
                <option value="pro">Pro</option>
                <option value="team">Team</option>
              </select>
              <input class="mirror" :value="label" c-name="email" />
              <output class="step">{{ step }}</output>
              <output class="clicks" v-text="clicks"></output>
              <button class="local" type="button" @click="clicks++">local</button>
            </form>
        """

        js = """
            $component({data: () => ({clicks: 0, label: 'Mirror'})});
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-account /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelector('.clicks')?.textContent === '0'")
    values = """() => Object.fromEntries(['email', 'spread', 'bio', 'plan', 'mirror'].map(
      name => [name, document.querySelector('.' + name).value]))"""
    assert page.evaluate(values) == {
        "email": "ada@example.com",
        "spread": "Spread",
        "bio": "Bio",
        "plan": "free",
        "mirror": "Mirror",
    }

    page.locator(".email").fill("draft@example.com")
    page.locator(".spread").fill("Spread draft")
    page.locator(".bio").fill("Bio draft")
    page.locator(".plan").select_option("team")
    page.locator(".mirror").fill("Mirror draft")
    drafts = {
        "email": "draft@example.com",
        "spread": "Spread draft",
        "bio": "Bio draft",
        "plan": "team",
    }

    # A local update keeps every draft bound to a server value. The browser
    # binding keeps Vue's rule and shows its state again.
    page.locator(".local").click()
    page.wait_for_function("document.querySelector('.clicks').textContent === '1'")
    assert page.evaluate(values) == {**drafts, "mirror": "Mirror"}

    # A server render that sends the same values leaves the drafts alone.
    _send(page, ".account")
    page.wait_for_function("document.querySelector('.step').textContent === '1'")
    assert page.evaluate(values) == {**drafts, "mirror": "Mirror"}

    # When the server sends a different value, the element shows it.
    _send(page, ".account")
    page.wait_for_function("document.querySelector('.step').textContent === '2'")
    assert page.evaluate(values) == {
        "email": "new@example.com",
        "spread": "Spread changed",
        "bio": "Changed bio",
        "plan": "pro",
        "mirror": "Mirror",
    }

    # After that, a server render that repeats the new values keeps new drafts.
    page.locator(".email").fill("second draft")
    _send(page, ".account")
    page.wait_for_function("document.querySelector('.step').textContent === '3'")
    assert page.locator(".email").input_value() == "second draft"
    assert faults == []


def test_a_field_the_user_did_not_edit_follows_the_server(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-retained-unedited-fields", autodiscover=False)  # noqa: S106

    class Plans(Component):
        citry = engine

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Plans(step=state.step)

        def template_data(self, kwargs, slots):
            # The server keeps sending "pro" while the options around it change.
            options = ["free", "pro"] if kwargs.step == 0 else ["pro", "team"]
            return {"step": kwargs.step, "options": options, "plan": "pro", "label": "Plan"}

        # `.role` has a constant value next to a Python attribute, so Vue
        # merges the two; the constant must still keep the user's text.
        template = """
            <form class="plans">
              <select class="plan" c-value="plan">
                <option c-for="option in options" c-value="option">{{ option }}</option>
              </select>
              <input class="role" value="Owner" c-aria-label="label" />
              <output class="step">{{ step }}</output>
            </form>
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-plans /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelector('.plan')?.value === 'pro'")
    page.locator(".role").fill("Editor")

    # Vue reuses the option elements for the new list. The untouched select
    # still shows the value the server sent, not whichever option took the
    # old selected element.
    _send(page, ".plans")
    page.wait_for_function("document.querySelector('.step').textContent === '1'")
    assert page.locator(".plan").input_value() == "pro"
    assert page.locator(".role").input_value() == "Editor"

    # Once the user picks an option, an unchanged server value keeps it.
    page.locator(".plan").select_option("team")
    _send(page, ".plans")
    page.wait_for_function("document.querySelector('.step').textContent === '2'")
    assert page.locator(".plan").input_value() == "team"
    assert faults == []


def test_reordering_keyed_rows_keeps_the_slotted_input_its_focus_and_text(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-retained-keyed-slot-rows", autodiscover=False)  # noqa: S106

    class Grid(Component):
        citry = engine
        template = """
            <table><tbody>
              <tr c-for="row in rows" #c-key="row" c-data-row="row">
                <th>{{ row }}</th>
                <td><c-slot name="cell" c-row="row" /></td>
              </tr>
            </tbody></table>
        """

        def template_data(self, kwargs, slots):
            return {"rows": kwargs["rows"]}

    class Inventory(Component):
        citry = engine

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Inventory(step=state.step)

        def template_data(self, kwargs, slots):
            return {"rows": ["alpha", "beta"] if kwargs.step % 2 == 0 else ["beta", "alpha"]}

        template = """
            <section class="inventory">
              <c-grid c-rows="rows">
                <c-fill name="cell" data="{ row }">
                  <input c-name="row" c-aria-label="row + ' note'" />
                </c-fill>
              </c-grid>
            </section>
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-inventory /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelectorAll('[data-row]').length === 2")
    beta = page.locator('input[name="beta"]')
    beta.fill("draft 27")
    beta.focus()
    page.evaluate("window.__beta = document.querySelector('input[name=beta]')")

    _send(page, ".inventory")
    page.wait_for_function("document.querySelector('[data-row]').dataset.row === 'beta'")
    # The row moves with its key, and so does the slot inside it: the same
    # input element keeps the focus and the typed text.
    assert page.evaluate(
        """() => {
          const input = document.querySelector('input[name=beta]');
          return {
            same: input === window.__beta,
            focused: document.activeElement === input,
            value: input.value,
            inRow: input.closest('[data-row]').dataset.row,
          };
        }"""
    ) == {"same": True, "focused": True, "value": "draft 27", "inRow": "beta"}
    assert faults == []


def test_a_server_render_removes_and_restores_an_element_with_a_runtime_directive(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-retained-removed-directive-site", autodiscover=False)  # noqa: S106

    class GrandLeaf(Component):
        citry = engine
        template = """
            <b class="grand">grand</b>
        """

    class Leaf(Component):
        citry = engine
        template = """
            <span class="leaf"><c-grand-leaf /></span>
        """
        js = """
            $component({data() {
              globalThis.__leafMounts = (globalThis.__leafMounts || 0) + 1;
              return {};
            }});
        """

    class Toggle(Component):
        citry = engine

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Toggle(step=state.step)

        def template_data(self, kwargs, slots):
            return {"show": kwargs.step % 2 == 0, "step": kwargs.step}

        # `v-model` and `v-show` are runtime directives, so their elements are
        # replacement sites whose keys the browser compares itself: the server
        # keeps no page history. Removing the panel removes one site and moves
        # the wrapper's, so Vue replaces the wrapper and mounts the leaf and
        # its child again.
        template = """
            <section class="toggle">
              <output class="step">{{ step }}</output>
              <c-if cond="show">
                <div class="panel"><input class="draft" v-model="draft" /></div>
              </c-if>
              <div class="wrap" v-show="true"><c-leaf /></div>
            </section>
        """

        js = """
            $component({data: () => ({draft: ''})});
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-toggle /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelector('.wrap .leaf .grand') !== null")
    assert page.evaluate("globalThis.__leafMounts") == 1

    _send(page, ".toggle")
    page.wait_for_function("document.querySelector('.step').textContent === '1'")
    assert page.locator(".panel").count() == 0
    assert page.locator(".wrap .leaf .grand").count() == 1
    assert page.evaluate("globalThis.__leafMounts") == 2

    _send(page, ".toggle")
    page.wait_for_function("document.querySelector('.step').textContent === '2'")
    assert page.locator(".panel .draft").count() == 1
    assert page.locator(".wrap .leaf .grand").count() == 1
    assert page.evaluate("globalThis.__leafMounts") == 3
    assert faults == []


@pytest.mark.parametrize("through_middle", [False, True], ids=["direct", "passed-on"])
def test_a_server_render_replaces_an_element_around_a_slot_with_a_caller_component(
    page: Any, serve_live: Any, through_middle: bool
) -> None:
    engine = Citry(secret="vue-retained-replaced-slot-outlet", autodiscover=False)  # noqa: S106

    class Leaf(Component):
        citry = engine
        template = """
            <b class="leaf" v-text="note" @click="note = 'edited'"></b>
        """
        js = """
            $component({data() {
              globalThis.__leafMounts = (globalThis.__leafMounts || 0) + 1;
              return {note: 'fresh'};
            }});
        """

    class Frame(Component):
        citry = engine

        class Kwargs:
            show: bool = True

        def template_data(self, kwargs, slots):
            return {"show": kwargs.show}

        # Removing the panel moves the wrapper's replacement site, so Vue
        # replaces the wrapper. The leaf lives in the caller's fill, rendered
        # through the slot inside that wrapper, so it mounts again too.
        template = """
            <section class="frame">
              <c-if cond="show">
                <div class="panel"><input class="draft" v-model="draft" /></div>
              </c-if>
              <div class="wrap" v-show="true"><c-slot name="default" /></div>
            </section>
        """

        js = """
            $component({data: () => ({draft: ''})});
        """

    class Middle(Component):
        citry = engine

        class Kwargs:
            show: bool = True

        def template_data(self, kwargs, slots):
            return {"show": kwargs.show}

        # The leaf comes from Toggle and reaches the frame through this
        # component's own slot, so the browser follows the fill one level up.
        template = """
            <c-frame c-show="show">
              <c-fill name="default"><c-slot name="default" /></c-fill>
            </c-frame>
        """

    frame_call = "c-middle" if through_middle else "c-frame"

    class Toggle(Component):
        citry = engine

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Toggle(step=state.step)

        def template_data(self, kwargs, slots):
            return {"show": kwargs.step % 2 == 0, "step": kwargs.step}

        template = f"""
            <article class="toggle">
              <output class="step">{{{{ step }}}}</output>
              <{frame_call} c-show="show">
                <c-fill name="default"><c-leaf /></c-fill>
              </{frame_call}>
            </article>
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-toggle /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelector('.wrap .leaf')?.textContent === 'fresh'")
    assert page.evaluate("globalThis.__leafMounts") == 1
    page.locator(".wrap .leaf").click()
    page.wait_for_function("document.querySelector('.wrap .leaf').textContent === 'edited'")

    _send(page, ".toggle")
    page.wait_for_function("document.querySelector('.step').textContent === '1'")
    assert page.locator(".panel").count() == 0
    # The replaced wrapper mounts the caller's leaf again with fresh state.
    assert page.locator(".wrap .leaf").text_content() == "fresh"
    assert page.evaluate("globalThis.__leafMounts") == 2

    _send(page, ".toggle")
    page.wait_for_function("document.querySelector('.step').textContent === '2'")
    assert page.locator(".panel .draft").count() == 1
    assert page.locator(".wrap .leaf").count() == 1
    assert page.evaluate("globalThis.__leafMounts") == 3
    assert faults == []


def test_radio_and_checkbox_models_with_constant_values_keep_working(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-retained-constant-choices", autodiscover=False)  # noqa: S106

    class Picker(Component):
        citry = engine
        # Vue's v-model reads a checkbox or radio value from the VNode, so
        # these constant values must reach Vue under their usual name.
        template = """
            <form class="picker">
              <input class="ra" type="radio" v-model="picked" value="a" />
              <input class="rb" type="radio" v-model="picked" value="b" />
              <input class="cx" type="checkbox" v-model="tags" value="x" />
              <input class="cy" type="checkbox" v-model="tags" value="y" />
              <span class="state" v-text="picked + '|' + tags.join(',')"></span>
            </form>
        """
        js = """
            $component({data: () => ({picked: 'b', tags: ['y']})});
        """

    class Page(Component):
        citry = engine
        template = """
            <main><c-picker /></main>
        """

    faults = _open(page, serve_live, engine, Page())
    page.wait_for_function("document.querySelector('.state')?.textContent === 'b|y'")
    checked = "selector => document.querySelector(selector).checked"
    assert [page.evaluate(checked, name) for name in (".ra", ".rb", ".cx", ".cy")] == [False, True, False, True]

    page.locator(".ra").click()
    page.locator(".cx").click()
    page.wait_for_function("document.querySelector('.state').textContent === 'a|y,x'")
    assert [page.evaluate(checked, name) for name in (".ra", ".rb", ".cx", ".cy")] == [True, False, True, True]
    assert faults == []
