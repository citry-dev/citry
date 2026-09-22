"""Browser tests for the production CCombobox."""

# ruff: noqa: E501 - embedded Vue expressions remain readable in browser fixtures

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _local_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        js = """
          $component({data(){const comboDemo=Citry.vue.reactive({
            value:undefined,inputValue:undefined,open:undefined,items:undefined,variant:undefined,
          }); window.__comboDemo=comboDemo; return {state:{comboDemo}};}});
        """
        css = """
          :where(.combobox-brand) {
            --cui-combobox-background: rgb(21 43 65);
            --cui-combobox-foreground: rgb(245 246 247);
            --cui-combobox-border-color: rgb(78 205 196);
            --cui-combobox-radius: 1rem;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <section
                class="combobox-brand"
                style="color-scheme: dark"
              >
                <c-CForm id="people-form">
                  <c-CField required>
                    <c-fill name="label">
                      Account owner
                    </c-fill>
                    <c-fill name="default">
                      <c-CCombobox
                        name="owner_id"
                        c-options="options"
                        c-attrs="root_attrs"
                        c-input_attrs="input_attrs"
                        :value="state.comboDemo.value"
                        :inputValue="state.comboDemo.inputValue"
                        :open="state.comboDemo.open"
                        :items="state.comboDemo.items"
                        :variant="state.comboDemo.variant"
                        :onValueChange="(value, detail) => {
                            window.__comboValue = { value, detail };
                            (window.__comboEvents ||= []).push({ type: 'value', detail });
                          }"
                        :onInputValueChange="(value, detail) => {
                            window.__comboInput = { value, detail };
                            (window.__comboEvents ||= []).push({ type: 'input', detail });
                          }"
                        :onOpenChange="(value, detail) => {
                            window.__comboOpen = { value, detail };
                            (window.__comboEvents ||= []).push({ type: 'open', detail });
                          }"
                      >
                        <c-fill name="empty">
                          No matching people.
                        </c-fill>
                      </c-CCombobox>
                    </c-fill>
                    <c-fill name="description">
                      Search by display name.
                    </c-fill>
                    <c-fill name="error">
                      Select an account owner.
                    </c-fill>
                  </c-CField>
                </c-CForm>
              </section>
              <button id="set-controlled" type="button" @click="
                state.comboDemo.value = 'linus';
                state.comboDemo.inputValue = 'Linus Torvalds';
              ">
                Set controlled
              </button>
              <button id="release-control" type="button" @click="
                state.comboDemo.value = undefined;
                state.comboDemo.inputValue = undefined;
              ">
                Release control
              </button>
              <button id="replace-items" type="button" @click="
                state.comboDemo.items = [
                  { value: 'margaret', label: 'Margaret Hamilton' },
                  { value: 'ada', label: 'Ada Lovelace' },
                ];
              ">
                Replace items
              </button>
              <button id="outside" type="button">
                Outside action
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "options": (
                    citry_ui.CComboboxOption("ada", "Ada Lovelace"),
                    citry_ui.CComboboxOption("grace", "Grace Hopper", disabled=True),
                    citry_ui.CComboboxOption("linus", "Linus Torvalds"),
                ),
                "root_attrs": {"data-workflow": "people"},
                "input_attrs": {"data-probe": "owner-search"},
            }

    return str(Page())


def _remote_page(
    *,
    initial_value: str | None = None,
    initial_options: tuple[citry_ui.CComboboxOption, ...] = (),
    min_chars: int = 2,
    initial_open: bool = False,
    manual_requests: bool = False,
) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        js = """
          $component({data(){const remoteDemo=Citry.vue.reactive({
            loading:false,disabled:false,readonly:false,inputValue:undefined,show:true,
            loader:({query,signal,requestId})=>{
              window.__remoteRequests=window.__remoteRequests||[];
              const request={query,signal,requestId}; window.__remoteRequests.push(request);
              if(query==='throw') throw new Error('synchronous failure');
              if(query==='malformed') return [{value:'broken'}];
              request.promise=new Promise((resolve,reject)=>{
                const delay=query==='ad'||query==='pending'?100:10;
                request.complete=()=>{if(query==='error'){reject(new Error('remote failed'));return;}
                  resolve([{value:query===''||query==='Old Mars'?'mars':query+'-value',label:query===''||query==='Old Mars'?'Mars':query==='ada'?'<img src=x onerror=alert(1)> Ada':query.toUpperCase()}]);};
                if(!document.body.hasAttribute('data-manual-requests')) setTimeout(request.complete,delay);
              }); return request.promise;
            },
          }); window.__remoteDemo=remoteDemo; return {state:{remoteDemo}};}});
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body c-data-manual-requests="manual_requests">
              <template v-if="state.remoteDemo.show">
                <c-CCombobox
                  name="person_id"
                  c-options="initial_options"
                  c-value="initial_value"
                  c-open="initial_open"
                  c-min_chars="min_chars"
                  c-debounce_ms="0"
                  c-attrs="root_attrs"
                  :loading="state.remoteDemo.loading"
                  :disabled="state.remoteDemo.disabled"
                  :readonly="state.remoteDemo.readonly"
                  :inputValue="state.remoteDemo.inputValue"
                  :loadOptions="state.remoteDemo.loader"
                  :onLoadError="(error, detail) => {
                      window.__remoteError = { message: error.message, detail };
                    }"
                >
                  <c-fill name="loading">
                    Searching...
                  </c-fill>
                  <c-fill name="empty">
                    No remote people.
                  </c-fill>
                  <c-fill name="error">
                    Search failed.
                  </c-fill>
                </c-CCombobox>
              </template>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "initial_open": initial_open,
                "initial_options": initial_options,
                "initial_value": initial_value,
                "min_chars": min_chars,
                "manual_requests": manual_requests,
                "root_attrs": {"data-remote-combobox": ""},
            }

    return str(Page())


def _complete_remote_request(page, index: int) -> None:
    # Tests choose the response order even when the loader ignores an aborted signal.
    page.wait_for_function(
        "index => typeof window.__remoteRequests?.[index]?.complete === 'function'",
        arg=index,
    )
    page.evaluate(
        """async index => {
          const request = window.__remoteRequests[index];
          request.complete();
          await request.promise;
        }""",
        index,
    )


def _controlled_remote_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        js = """
          $component({data(){const controlledRemote=Citry.vue.reactive({
            inputValue:'',loader:async({query,signal,requestId})=>{
              window.__controlledRequests=window.__controlledRequests||[];
              window.__controlledRequests.push({query,signal,requestId});
              return [{value:query,label:query.toUpperCase(),description:'Remote star catalog result'}];
            },
          }); window.__controlledRemote=controlledRemote; return {state:{controlledRemote}};}});
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-CCombobox
                c-min_chars="2"
                c-debounce_ms="0"
                :inputValue="state.controlledRemote.inputValue"
                :loadOptions="state.controlledRemote.loader"
                :onInputValueChange="(query, detail) => {
                    window.__controlledInput = { query, detail };
                    state.controlledRemote.inputValue = query;
                  }"
              />
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _behavior_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-CCombobox
                id="moon"
                c-options="options"
                open_on_focus
                auto_highlight
              />
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "options": (
                    citry_ui.CComboboxOption("europa", "Europa", "Icy moon of Jupiter"),
                    citry_ui.CComboboxOption("titan", "Titan", "Moon with a dense atmosphere"),
                )
            }

    return str(Page())


def _load(page, html: str) -> None:
    page.set_content(html, wait_until="load")
    page.wait_for_function("document.querySelector('.cui-combobox')?.hasAttribute('data-citry-combobox-initialized')")


def test_local_keyboard_selection_skips_disabled_options_and_submits_canonical_value(page):
    _load(page, _local_page())
    root = page.locator(".cui-combobox")
    input_value = page.get_by_role("combobox")

    input_value.focus()
    input_value.press("ArrowDown")
    assert input_value.get_attribute("aria-expanded") == "true"
    assert page.locator('[data-citry-ui-part="option"][data-highlighted]').get_attribute("data-value") == "ada"
    input_value.press("ArrowDown")
    assert page.locator('[data-citry-ui-part="option"][data-highlighted]').get_attribute("data-value") == "linus"
    input_value.press("Enter")

    assert input_value.input_value() == "Linus Torvalds"
    assert input_value.get_attribute("aria-expanded") == "false"
    assert (
        page.evaluate("Object.fromEntries(new FormData(document.querySelector('#people-form'))).owner_id") == "linus"
    )
    assert page.evaluate("window.__comboValue.value") == "linus"
    assert page.evaluate("window.__comboValue.detail.reason") == "option"
    assert root.get_attribute("data-workflow") == "people"
    assert input_value.get_attribute("data-probe") == "owner-search"


def test_local_filter_pointer_clear_and_required_validation(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")
    field = page.locator(".cui-field")

    input_value.fill("ada")
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=option]').length === 1")
    assert page.locator('[data-citry-ui-part="option"][data-highlighted]').count() == 0
    page.locator('[data-citry-ui-part="option"]').click()
    assert input_value.input_value() == "Ada Lovelace"

    page.get_by_role("button", name="Show options").click()
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=option]').length === 3")
    page.get_by_role("button", name="Clear selection").click()
    assert input_value.input_value() == ""
    assert page.evaluate("new FormData(document.querySelector('#people-form')).get('owner_id')") == ""
    assert page.evaluate("document.querySelector('[role=combobox]').reportValidity()") is False
    page.wait_for_function("document.querySelector('.cui-field').hasAttribute('data-invalid')")
    assert field.get_attribute("data-invalid") == ""


def test_controlled_value_query_and_client_items_rehydrate_by_stable_value(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    page.locator("#set-controlled").click()
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "linus"

    input_value.fill("Refused")
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")

    page.locator("#replace-items").click()
    page.locator("#release-control").click()
    input_value.fill("")
    input_value.press("ArrowDown")
    assert page.locator('[data-citry-ui-part="option"]').all_inner_texts() == [
        "Margaret Hamilton",
        "Ada Lovelace",
    ]


def test_presence_data_values_stay_empty_across_initial_and_controlled_renders(page):
    _load(page, _local_page())
    root = page.locator(".cui-combobox")
    field = page.locator(".cui-field")
    disabled_option = page.locator('[data-citry-ui-part="option"][data-value="grace"]')

    assert field.get_attribute("data-required") == ""
    assert root.get_attribute("data-open") is None
    assert disabled_option.get_attribute("data-disabled") == ""

    page.locator("#set-controlled").click()
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")
    assert field.get_attribute("data-required") == ""

    # Keep the input controlled while clearing its query so the disabled Grace
    # option is present for the second presence-value assertion.
    page.evaluate("window.__comboDemo.inputValue = ''")
    page.wait_for_function("document.querySelector('[role=combobox]').value === ''")
    page.wait_for_function(
        "document.querySelector('[data-citry-ui-part=option][data-value=grace]')?.hasAttribute('data-disabled')"
    )
    assert disabled_option.get_attribute("data-disabled") == ""

    page.get_by_role("combobox").fill("ada")
    page.wait_for_function("document.querySelector('.cui-combobox').hasAttribute('data-open')")
    assert root.get_attribute("data-open") == ""
    page.get_by_role("combobox").press("Escape")
    page.wait_for_function("!document.querySelector('.cui-combobox').hasAttribute('data-open')")
    assert root.get_attribute("data-open") is None


def test_value_query_and_open_ownership_remain_independent(page):
    _load(page, _local_page())
    root = page.locator(".cui-combobox")
    input_value = page.get_by_role("combobox")

    page.evaluate("window.__comboDemo.value = 'linus'")
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")

    input_value.fill("ada")
    page.wait_for_function("document.querySelector('.cui-combobox').hasAttribute('data-open')")
    assert input_value.input_value() == "ada"
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "linus"
    assert page.evaluate("window.__comboValue.value") is None

    page.locator('[data-citry-ui-part="option"]').click()
    assert input_value.input_value() == "Ada Lovelace"
    assert root.get_attribute("data-open") is None
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "linus"
    assert page.evaluate("window.__comboValue.value") == "ada"


def test_outside_press_reconciles_query_before_notifying_close(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    page.evaluate("window.__comboDemo.value = 'linus'")
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")
    input_value.fill("ada")
    page.wait_for_function("document.querySelector('.cui-combobox').hasAttribute('data-open')")
    page.evaluate("window.__comboEvents = []")
    page.evaluate(
        """() => {
          const outside = document.querySelector('#outside');
          outside.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
          outside.focus();
        }"""
    )
    page.wait_for_function("!document.querySelector('.cui-combobox').hasAttribute('data-open')")

    assert page.evaluate("window.__comboEvents.map(event => [event.type, event.detail.reason])") == [
        ["input", "blur"],
        ["open", "outside"],
    ]


def test_tab_reconciles_selected_label_before_notifying_close(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    page.evaluate("window.__comboDemo.value = 'linus'")
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")
    input_value.fill("ada")
    page.wait_for_function("document.querySelector('.cui-combobox').hasAttribute('data-open')")
    page.evaluate("window.__comboEvents = []")
    input_value.press("Tab")
    page.wait_for_function("!document.querySelector('.cui-combobox').hasAttribute('data-open')")

    assert input_value.input_value() == "Linus Torvalds"
    assert page.evaluate("window.__comboEvents.map(event => [event.type, event.detail.reason])") == [
        ["input", "blur"],
        ["open", "blur"],
    ]


@pytest.mark.parametrize(
    ("action", "reason"),
    [("outside", "outside"), ("tab", "blur")],
)
def test_controlled_open_notifies_one_close_request_per_focus_departure(page, action, reason):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")
    page.evaluate("window.__comboDemo.open = true")
    page.wait_for_function("document.querySelector('.cui-combobox').hasAttribute('data-open')")
    input_value.focus()
    page.evaluate("window.__comboEvents = []")

    if action == "outside":
        page.evaluate(
            """() => {
              const outside = document.querySelector('#outside');
              outside.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
              outside.focus();
            }"""
        )
    else:
        input_value.press("Tab")
    page.wait_for_timeout(20)

    assert page.evaluate("window.__comboEvents.map(event => [event.type, event.detail.reason])") == [
        ["open", reason],
    ]


def test_orphan_selection_keeps_identity_and_rehydrates_when_item_arrives(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    page.evaluate("window.__comboDemo.value = 'mars'")
    page.wait_for_function("document.querySelector('[data-citry-combobox-form-value]').value === 'mars'")
    assert input_value.input_value() == ""
    assert input_value.get_attribute("required") is None
    assert input_value.get_attribute("aria-required") == "true"
    assert input_value.evaluate("element => element.validity.valid") is True

    page.evaluate("window.__comboDemo.items = [{ value: 'mars', label: 'Mars', description: 'The red planet' }]")
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Mars'")
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "mars"


def test_client_item_replacement_preserves_an_unselected_query(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    input_value.fill("ad")
    page.evaluate("window.__comboDemo.items = [{ value: 'ada', label: 'Ada Lovelace' }]")
    page.wait_for_timeout(20)

    assert input_value.input_value() == "ad"


def test_controlled_form_reset_reasserts_value_and_query(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    page.locator("#set-controlled").click()
    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Linus Torvalds'")
    page.evaluate("document.querySelector('#people-form').reset()")
    page.wait_for_timeout(20)

    assert input_value.input_value() == "Linus Torvalds"
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "linus"


def test_focus_opening_auto_highlight_descriptions_and_hidden_clear(page):
    _load(page, _behavior_page())
    root = page.locator("#moon-root")
    input_value = page.get_by_role("combobox")
    clear = page.locator('[data-citry-ui-part="clear"]')

    assert clear.evaluate("element => getComputedStyle(element).display") == "none"
    input_value.focus()
    page.wait_for_function("document.querySelector('#moon-root').hasAttribute('data-open')")
    highlighted = page.locator('[data-citry-ui-part="option"][data-highlighted]')
    assert highlighted.get_attribute("data-value") == "europa"
    assert highlighted.get_attribute("aria-selected") == "true"
    assert page.locator('[data-citry-ui-part="option-description"]').first.inner_text() == "Icy moon of Jupiter"

    input_value.press("Enter")
    assert root.get_attribute("data-open") is None
    assert clear.evaluate("element => getComputedStyle(element).display") != "none"


def test_public_tokens_override_variants_and_public_selectors_style_options(page):
    _load(page, _local_page())
    control = page.locator('.cui-combobox [data-citry-ui-part="control"]')

    page.evaluate("window.__comboDemo.variant = 'filled'")
    page.wait_for_function("document.querySelector('.cui-combobox').dataset.variant === 'filled'")
    assert control.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(21, 43, 65)"
    assert control.evaluate("element => getComputedStyle(element).borderColor") == "rgb(78, 205, 196)"

    page.evaluate("window.__comboDemo.variant = 'plain'")
    page.wait_for_function("document.querySelector('.cui-combobox').dataset.variant === 'plain'")
    assert control.evaluate("element => getComputedStyle(element).borderRadius") == "16px"

    page.add_style_tag(content='[data-workflow="people"] [data-citry-ui-part="option"] { color: rgb(251 146 60); }')
    page.get_by_role("combobox").press("ArrowDown")
    assert (
        page.locator('[data-citry-ui-part="option"]').first.evaluate("element => getComputedStyle(element).color")
        == "rgb(251, 146, 60)"
    )


def test_empty_client_value_is_invalid_and_releases_selection_control(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")

    page.evaluate("window.__comboDemo.value = ''")
    page.wait_for_timeout(20)
    input_value.press("ArrowDown")
    input_value.press("Enter")

    assert any("CCombobox value received invalid client value" in error for error in errors)
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "ada"


def test_native_reset_restores_server_selection_and_query(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")
    input_value.press("ArrowDown")
    input_value.press("Enter")
    assert input_value.input_value() == "Ada Lovelace"

    page.evaluate("document.querySelector('#people-form').reset()")
    page.wait_for_function(
        "document.querySelector('[role=combobox]').value === ''"
        " && document.querySelector('[data-citry-combobox-form-value]').value === ''"
    )
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == ""


def test_canceled_native_reset_preserves_selection_and_query(page):
    _load(page, _local_page())
    input_value = page.get_by_role("combobox")
    input_value.press("ArrowDown")
    input_value.press("Enter")
    assert input_value.input_value() == "Ada Lovelace"

    page.evaluate(
        """() => {
          const form = document.querySelector('#people-form');
          form.addEventListener('reset', (event) => event.preventDefault(), { once: true });
          form.reset();
        }"""
    )
    page.wait_for_timeout(20)

    assert input_value.input_value() == "Ada Lovelace"
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "ada"


def test_remote_loader_aborts_and_rejects_stale_results_even_when_loader_ignores_signal(page):
    _load(page, _remote_page(manual_requests=True))
    input_value = page.get_by_role("combobox")

    input_value.fill("ad")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    input_value.fill("ada")
    page.wait_for_function("window.__remoteRequests?.length === 2")
    _complete_remote_request(page, 1)
    page.wait_for_function("document.querySelector('[data-citry-ui-part=option-label]')?.textContent.includes('Ada')")
    _complete_remote_request(page, 0)

    assert page.evaluate("window.__remoteRequests[0].signal.aborted") is True
    assert page.locator('[data-citry-ui-part="option-label"]').inner_text() == "<img src=x onerror=alert(1)> Ada"
    assert input_value.input_value() == "ada"
    assert page.locator("[data-remote-combobox] img").count() == 0
    assert page.locator('[data-citry-ui-part="option"]').get_attribute("data-value") == "ada-value"
    assert page.locator('[data-citry-ui-part="option"][data-highlighted]').count() == 0

    page.evaluate("window.__remoteDemo.loading = true")
    page.evaluate("window.__remoteDemo.loading = false")
    assert page.locator('[data-citry-ui-part="option"]').get_attribute("data-value") == "ada-value"


def test_controlled_query_loads_only_after_owner_commit(page):
    _load(page, _controlled_remote_page())
    input_value = page.get_by_role("combobox")

    input_value.fill("vega")
    page.wait_for_function("window.__controlledRequests?.length === 1")
    page.wait_for_function("document.querySelector('[data-citry-ui-part=option-label]')?.textContent === 'VEGA'")

    assert page.evaluate("window.__controlledRequests[0].query") == "vega"
    assert page.evaluate("window.__controlledInput.detail.controlled") is True
    assert page.locator('[data-citry-ui-part="option-description"]').inner_text() == "Remote star catalog result"


def test_ime_defers_remote_search_until_composition_ends(page):
    _load(page, _remote_page())
    input_value = page.get_by_role("combobox")

    input_value.dispatch_event("compositionstart")
    input_value.evaluate(
        "element => { element.value = 'ad'; element.dispatchEvent(new InputEvent('input', {bubbles: true})); }"
    )
    page.wait_for_timeout(20)
    assert page.evaluate("window.__remoteRequests?.length ?? 0") == 0

    input_value.dispatch_event("compositionend")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    assert page.evaluate("window.__remoteRequests[0].query") == "ad"


def test_minimum_characters_count_unicode_code_points(page):
    _load(page, _remote_page())
    input_value = page.get_by_role("combobox")

    input_value.fill("🚀")
    page.wait_for_timeout(20)
    assert page.evaluate("window.__remoteRequests?.length ?? 0") == 0
    assert input_value.get_attribute("aria-expanded") == "false"

    input_value.fill("🚀🚀")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    assert page.evaluate("window.__remoteRequests[0].query") == "🚀🚀"


def test_closing_aborts_remote_work_without_selecting_highlight(page):
    _load(page, _remote_page(manual_requests=True))
    input_value = page.get_by_role("combobox")

    input_value.fill("pending")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    input_value.press("Escape")

    assert page.evaluate("window.__remoteRequests[0].signal.aborted") is True
    _complete_remote_request(page, 0)
    assert input_value.get_attribute("aria-expanded") == "false"
    assert page.locator('[data-citry-ui-part="option"][data-selected]').count() == 0


def test_hidden_stale_remote_results_cannot_be_selected_while_loading(page):
    _load(page, _remote_page(manual_requests=True))
    input_value = page.get_by_role("combobox")

    input_value.fill("ok")
    _complete_remote_request(page, 0)
    page.wait_for_function("document.querySelector('[data-citry-ui-part=option]')?.dataset.value === 'ok-value'")
    input_value.fill("pending")
    page.wait_for_function("document.querySelector('[data-remote-combobox]').hasAttribute('data-loading')")
    input_value.press("ArrowDown")
    input_value.press("Home")
    input_value.press("Enter")

    assert input_value.input_value() == "pending"
    assert page.locator('[data-citry-ui-part="option"][data-highlighted]').count() == 0
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == ""


def test_changing_remote_loader_aborts_old_work_and_reloads_open_query(page):
    _load(page, _remote_page(manual_requests=True))
    input_value = page.get_by_role("combobox")

    input_value.fill("pending")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    page.evaluate("window.__remoteDemo.loader = null")
    page.wait_for_function("window.__remoteRequests[0].signal.aborted")
    _complete_remote_request(page, 0)
    assert page.locator('[data-citry-ui-part="option"][data-value="pending-value"]').count() == 0

    page.evaluate(
        """() => {
          window.__remoteDemo.loader = async ({ query }) => [{
            value: 'replacement-value',
            label: `Replacement for ${query}`,
          }];
        }"""
    )
    page.wait_for_function(
        "document.querySelector('[data-citry-ui-part=option]')?.dataset.value === 'replacement-value'"
    )

    assert page.locator('[data-citry-ui-part="option-label"]').inner_text() == "Replacement for pending"


@pytest.mark.parametrize("state", ["disabled", "readonly"])
def test_blocked_state_aborts_and_prevents_controlled_query_loading(page, state):
    _load(page, _remote_page(manual_requests=True))
    input_value = page.get_by_role("combobox")

    input_value.fill("pending")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    page.evaluate(
        """(state) => {
          const store = window.__remoteDemo;
          store[state] = true;
          store.inputValue = 'mars';
        }""",
        state,
    )
    page.wait_for_function("window.__remoteRequests[0].signal.aborted")
    _complete_remote_request(page, 0)
    page.wait_for_timeout(30)

    assert page.evaluate("window.__remoteRequests.length") == 1


@pytest.mark.parametrize(
    "initial_options",
    [
        (),
        (citry_ui.CComboboxOption("mars", "Old Mars"),),
    ],
)
def test_remote_results_rehydrate_initial_or_relabelled_selection(page, initial_options):
    _load(
        page,
        _remote_page(
            initial_value="mars",
            initial_options=initial_options,
            min_chars=0,
            initial_open=True,
        ),
    )
    input_value = page.get_by_role("combobox")

    page.wait_for_function("document.querySelector('[role=combobox]').value === 'Mars'")

    assert input_value.input_value() == "Mars"
    assert page.evaluate("document.querySelector('[data-citry-combobox-form-value]').value") == "mars"


@pytest.mark.parametrize(
    ("key", "expected"),
    [("ArrowDown", "first-value"), ("ArrowUp", "second-value")],
)
def test_closed_remote_arrow_keys_highlight_the_requested_edge_after_loading(page, key, expected):
    _load(page, _remote_page(min_chars=0))
    page.evaluate(
        """() => {
          window.__remoteDemo.loader = async () => [
            { value: 'first-value', label: 'First' },
            { value: 'second-value', label: 'Second' },
          ];
        }"""
    )
    input_value = page.get_by_role("combobox")

    input_value.press(key)
    page.wait_for_function("document.querySelector('[data-citry-ui-part=option][data-highlighted]')")

    assert page.locator('[data-citry-ui-part="option"][data-highlighted]').get_attribute("data-value") == expected


@pytest.mark.parametrize("query", ["throw", "malformed"])
def test_remote_synchronous_and_malformed_failures_use_safe_error_state(page, query):
    _load(page, _remote_page())
    input_value = page.get_by_role("combobox")

    input_value.fill(query)
    page.wait_for_function("document.querySelector('[data-remote-combobox]').hasAttribute('data-error')")

    assert page.locator('[data-citry-ui-part="error"]').inner_text().strip() == "Search failed."
    assert query not in page.locator('[data-citry-ui-part="error"]').inner_text()


def test_remote_error_recovers_and_does_not_render_exception_text(page):
    _load(page, _remote_page())
    input_value = page.get_by_role("combobox")

    input_value.fill("error")
    page.wait_for_function("document.querySelector('[data-remote-combobox]').hasAttribute('data-error')")
    assert page.locator('[data-citry-ui-part="error"]').is_visible()
    assert page.locator('[data-citry-ui-part="error"]').inner_text().strip() == "Search failed."
    assert page.evaluate("window.__remoteError.message") == "remote failed"

    input_value.fill("ok")
    page.wait_for_function("document.querySelector('[data-citry-ui-part=option]')?.dataset.value === 'ok-value'")
    assert page.locator("[data-remote-combobox]").get_attribute("data-error") is None


def test_remote_cleanup_aborts_pending_request_when_vue_unmounts(page):
    _load(page, _remote_page(manual_requests=True))
    input_value = page.get_by_role("combobox")
    input_value.fill("pending")
    page.wait_for_function("window.__remoteRequests?.length === 1")
    page.evaluate("window.__remoteDemo.show = false")
    page.wait_for_function("document.querySelector('[data-remote-combobox]') === null")
    page.wait_for_function("window.__remoteRequests[0].signal.aborted")
    _complete_remote_request(page, 0)

    assert page.locator("[data-remote-combobox]").count() == 0
