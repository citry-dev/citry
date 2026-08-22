"""Focused browser contracts for CTagsInput."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.ctags_input import CTagsInput

pytestmark = pytest.mark.e2e


def _page_html() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-tags-input-e2e", (CField, CTagsInput)))

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>TagsInput browser contract</title>
              <script>window.__tagEvents=[];window.__submits=[];</script>
              <c-css />
            </head>
            <body
              x-data="{
                controlledValue: ['alpha'],
                controlledDraft: 'beta',
                valueOnlyValue: ['alpha'],
                acceptValue: false,
                acceptDraft: false,
                isDisabled: false,
                isReadonly: false,
                tagPlaceholder: undefined,
                tagMax: undefined,
                removeOnReset: false,
                mutateDraftOnReset: false,
                mutateDraftOnValue: false,
              }"
            >
              <form id="tag-form" @submit.prevent="window.__submits.push(new FormData($event.target).getAll('label'))">
                <c-CTagsInput
                  id="uncontrolled"
                  name="label"
                  form="tag-form"
                  c-value="initial_values"
                  input_value="draft"
                  max_tags="4"
                  placeholder="Server placeholder"
                  required
                  c-input_attrs="label"
                  $c-props="{
                    disabled: isDisabled,
                    readonly: isReadonly,
                    placeholder: tagPlaceholder,
                    maxTags: tagMax,
                    onValueChange: (next, detail) => window.__tagEvents.push(['value', next, detail]),
                    onInputValueChange: (next, detail) => window.__tagEvents.push(['draft', next, detail]),
                    onValueInvalid: (reason, detail) => window.__tagEvents.push(['invalid', reason, detail]),
                  }"
                />
                <button id="submit" type="submit">Submit</button>
                <button id="reset" type="reset">Reset</button>
              </form>
              <c-CTagsInput
                id="controlled"
                form="controlled-form"
                c-input_attrs="controlled_label"
                $c-props="{
                  value: controlledValue,
                  inputValue: controlledDraft,
                  disabled: isDisabled,
                  readonly: isReadonly,
                  placeholder: tagPlaceholder,
                  onValueChange: (next, detail) => {
                    window.__tagEvents.push(['controlled-value', next, detail]);
                    if (detail.source === 'reset' && removeOnReset) {
                      document.querySelector('#controlled')?.closest('.cui-tags-input')?.remove();
                    }
                    if (detail.source === 'reset' && mutateDraftOnReset) controlledDraft = 'owner';
                    if (detail.source !== 'reset' && mutateDraftOnValue) controlledDraft = 'owner';
                    if (acceptValue) controlledValue = next;
                  },
                  onInputValueChange: (next, detail) => {
                    window.__tagEvents.push(['controlled-draft', next, detail]);
                    if (acceptDraft) controlledDraft = next;
                  },
                  onValueInvalid: (reason, detail) => window.__tagEvents.push(['controlled-invalid', reason, detail]),
                }"
              />
              <form id="controlled-form"></form>
              <button id="controlled-reset" type="reset" form="controlled-form">Reset controlled</button>
              <c-CTagsInput
                id="value-only"
                input_value="beta"
                c-input_attrs="value_only_label"
                $c-props="{
                  value: valueOnlyValue,
                  onValueChange: (next, detail) => {
                    window.__tagEvents.push(['value-only', next, detail]);
                    if (acceptValue) valueOnlyValue = next;
                  },
                }"
              />
              <c-CField control_id="field-tags" required>
                <c-fill name="label">Field labels</c-fill>
                <c-fill name="default"><c-CTagsInput name="field-label" /></c-fill>
                <c-fill name="description">Add one or more labels</c-fill>
                <c-fill name="error">Labels are required</c-fill>
              </c-CField>
              <fieldset id="disabled-fieldset" disabled>
                <legend>Legend <span id="legend-target"></span></legend>
                <div id="fieldset-target"></div>
              </fieldset>
              <div id="outside-target">
                <c-CTagsInput
                  id="fieldset-tags"
                  name="fieldset-label"
                  form="tag-form"
                  c-value="fieldset_values"
                  readonly
                  c-input_attrs="fieldset_label"
                />
              </div>
              <button id="accept-value" type="button" @click="acceptValue=true">Accept value</button>
              <button id="accept-draft" type="button" @click="acceptDraft=true">Accept draft</button>
              <button id="disable" type="button" @click="isDisabled=!isDisabled">Disable</button>
              <button id="readonly" type="button" @click="isReadonly=!isReadonly">Readonly</button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "label": {"aria-label": "Labels"},
                "controlled_label": {"aria-label": "Controlled labels"},
                "value_only_label": {"aria-label": "Value-only labels"},
                "fieldset_label": {"aria-label": "Fieldset labels"},
                "fieldset_values": ("fieldset-value",),
                "initial_values": ("alpha", "beta"),
            }

    return str(Page())


def _load(page) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="tags-input"]')]
          .every(root => root.hasAttribute('data-citry-tags-input-initialized'))"""
    )
    return errors


def _values(page, root: str) -> list[str]:
    return page.locator(f"#{root}-native option:checked").evaluate_all(
        "options => options.map(option => option.value)"
    )


def test_handoff_uncontrolled_enter_remove_formdata_and_reset(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    native = page.locator("#uncontrolled-native")
    assert editor.is_visible()
    assert native.get_attribute("aria-hidden") == "true"
    assert native.get_attribute("tabindex") == "-1"
    assert page.locator('label[for="uncontrolled"]').count() == 0
    assert _values(page, "uncontrolled") == ["alpha", "beta"]

    editor.fill("gamma")
    editor.press("Enter")
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma"]
    assert editor.input_value() == ""
    assert page.locator('.cui-tags-input:has(#uncontrolled) [data-citry-ui-part="tag"]').count() == 3
    page.locator('.cui-tags-input:has(#uncontrolled) [data-citry-ui-part="remove"][data-value="beta"]').click()
    assert _values(page, "uncontrolled") == ["alpha", "gamma"]
    assert page.evaluate("() => document.activeElement?.id") == "uncontrolled"

    page.locator("#submit").click()
    assert page.evaluate("window.__submits") == [["alpha", "gamma"]]
    page.locator("#reset").click()
    page.wait_for_function(
        """() => document.querySelector('#uncontrolled').value === 'draft'
          && [...document.querySelector('#uncontrolled-native').selectedOptions]
            .map(option => option.value).join(',') === 'alpha,beta'"""
    )
    assert _values(page, "uncontrolled") == ["alpha", "beta"]
    assert editor.input_value() == "draft"
    assert errors == []


def test_controlled_value_rejection_preserves_uncontrolled_or_controlled_draft_until_acceptance(page) -> None:
    errors = _load(page)
    editor = page.locator("#controlled")
    editor.press("Enter")
    assert _values(page, "controlled") == ["alpha"]
    assert editor.input_value() == "beta"
    assert page.evaluate("window.__tagEvents.filter(event => event[0] === 'controlled-value').length") == 1
    assert page.evaluate("window.__tagEvents.filter(event => event[0] === 'controlled-draft').length") == 0

    page.locator("#accept-value").click()
    editor.press("Enter")
    page.wait_for_function("() => document.querySelector('#controlled-native').selectedOptions.length === 2")
    assert _values(page, "controlled") == ["alpha", "beta"]
    assert editor.input_value() == "beta"
    assert page.evaluate("window.__tagEvents.filter(event => event[0] === 'controlled-draft').length") == 1
    assert errors == []


def test_value_controlled_draft_uncontrolled_clears_only_after_exact_acceptance(page) -> None:
    errors = _load(page)
    editor = page.locator("#value-only")
    editor.press("Enter")
    assert _values(page, "value-only") == ["alpha"]
    assert editor.input_value() == "beta"
    assert page.evaluate("window.__tagEvents.filter(event => event[0] === 'value-only').length") == 1

    page.locator("#accept-value").click()
    editor.press("Enter")
    page.wait_for_function("() => document.querySelector('#value-only-native').selectedOptions.length === 2")
    assert _values(page, "value-only") == ["alpha", "beta"]
    assert editor.input_value() == ""
    assert errors == []


def test_owner_draft_mutation_cancels_stale_acceptance_clear(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          const state=Alpine.$data(document.body);
          state.acceptValue=true;state.mutateDraftOnValue=true;window.__tagEvents=[];
        }"""
    )
    page.locator("#controlled").press("Enter")
    page.wait_for_function("() => document.querySelector('#controlled').value === 'owner'")
    assert _values(page, "controlled") == ["alpha", "beta"]
    assert (
        page.evaluate(
            """() => window.__tagEvents.filter(event =>
          event[0] === 'controlled-draft' && event.at(-1)?.source === 'enter').length"""
        )
        == 0
    )
    assert errors == []


@pytest.mark.parametrize("blocked", ["disabled", "readonly"])
def test_blocked_transition_cancels_pending_controlled_draft_acceptance(page, blocked: str) -> None:
    errors = _load(page)
    editor = page.locator("#controlled")
    editor.press("Enter")
    page.evaluate(
        """([blocked]) => {
          const state=Alpine.$data(document.body);
          if(blocked==='disabled')state.isDisabled=true;else state.isReadonly=true;
        }""",
        [blocked],
    )
    page.wait_for_function(
        """([blocked]) => blocked==='disabled'
          ? document.querySelector('#controlled').disabled
          : document.querySelector('#controlled').readOnly""",
        arg=[blocked],
    )
    page.evaluate("Alpine.$data(document.body).controlledValue=['alpha','beta']")
    page.wait_for_function("() => document.querySelector('#controlled-native').selectedOptions.length === 2")
    assert editor.input_value() == "beta"
    assert page.evaluate("window.__tagEvents.filter(event => event[0] === 'controlled-draft').length") == 0
    assert errors == []


def test_controlled_remove_announces_only_after_exact_owner_acceptance(page) -> None:
    errors = _load(page)
    page.evaluate("Alpine.$data(document.body).acceptValue=true")
    page.locator('.cui-tags-input:has(#controlled) [data-citry-ui-part="remove"][data-value="alpha"]').click()
    page.wait_for_function("() => document.querySelector('#controlled-native').selectedOptions.length === 0")
    page.wait_for_function(
        """() => document.querySelector('.cui-tags-input:has(#controlled) [role=status]')
          .textContent === 'Removed \u2068alpha\u2069'"""
    )
    assert errors == []


def test_atomic_paste_duplicate_max_and_delimiter_restore(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.fill("tail")
    page.evaluate(
        """() => {
          const input=document.querySelector('#uncontrolled');
          input.setSelectionRange(0,4);
          const event=new Event('paste',{bubbles:true,cancelable:true});
          Object.defineProperty(event,'clipboardData',{value:{getData:()=> 'gamma,delta,rest'}});
          input.dispatchEvent(event);
        }"""
    )
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma", "delta"]
    assert editor.input_value() == "rest"
    status = page.locator('.cui-tags-input:has(#uncontrolled) [data-citry-ui-part="status"]')
    page.wait_for_function(
        "() => document.querySelector('.cui-tags-input:has(#uncontrolled) [role=status]').textContent"
    )
    assert status.text_content() == "Added \u2068gamma\u2069 Added \u2068delta\u2069"

    page.evaluate(
        """() => {
          const input=document.querySelector('#uncontrolled');
          input.value='keep';input.setSelectionRange(0,4);
          input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText'}));
          const event=new Event('paste',{bubbles:true,cancelable:true});
          Object.defineProperty(event,'clipboardData',{value:{getData:()=> 'alpha,new,tail'}});
          input.dispatchEvent(event);
        }"""
    )
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma", "delta"]
    assert editor.input_value() == "keep"
    invalid = page.evaluate("window.__tagEvents.filter(event => event[0] === 'invalid').at(-1)")
    assert invalid[1] == "duplicate"
    assert errors == []


def test_max_overflow_rejects_entire_paste_batch(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          const input=document.querySelector('#uncontrolled');
          const event=new Event('paste',{bubbles:true,cancelable:true});
          Object.defineProperty(event,'clipboardData',{value:{getData:()=> 'gamma,delta,epsilon,tail'}});
          input.dispatchEvent(event);
        }"""
    )
    assert _values(page, "uncontrolled") == ["alpha", "beta"]
    assert page.locator("#uncontrolled").input_value() == "draft"
    invalid = page.evaluate("window.__tagEvents.filter(event => event[0] === 'invalid').at(-1)")
    assert invalid[1] == "maximum"
    assert errors == []


def test_nonempty_draft_blocks_submit_and_invalid_redirects_focus(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.fill("unfinished")
    page.locator("#submit").click()
    assert page.evaluate("window.__submits") == []
    page.wait_for_function("() => document.activeElement?.id === 'uncontrolled'")
    assert page.evaluate("() => document.activeElement?.id") == "uncontrolled"
    assert page.locator('[data-citry-ui-part="tags-input"]').first.get_attribute("data-invalid") == ""
    editor.fill("")
    assert page.locator('[data-citry-ui-part="tags-input"]').first.get_attribute("data-invalid") is None
    assert errors == []


def test_controlled_draft_restore_clears_native_invalid_episode(page) -> None:
    errors = _load(page)
    root = page.locator(".cui-tags-input:has(#controlled)")
    page.evaluate("document.querySelector('#controlled-form').requestSubmit()")
    page.wait_for_function(
        "() => document.querySelector('.cui-tags-input:has(#controlled)').hasAttribute('data-invalid')"
    )
    page.locator("#controlled").fill("changed")
    page.wait_for_function("() => document.querySelector('#controlled').value === 'beta'")
    assert root.get_attribute("data-invalid") is None
    assert page.locator("#controlled").get_attribute("aria-invalid") is None
    assert errors == []


def test_disabled_entry_clears_native_invalid_episode_and_pending_focus(page) -> None:
    errors = _load(page)
    root = page.locator(".cui-tags-input:has(#uncontrolled)")
    page.locator("#uncontrolled").fill("unfinished")
    page.locator("#submit").click()
    page.wait_for_function("() => document.querySelector('#uncontrolled').getAttribute('aria-invalid') === 'true'")
    page.locator("#disable").click()
    page.wait_for_function("() => document.querySelector('#uncontrolled').disabled")
    assert root.get_attribute("data-invalid") is None
    assert page.locator("#uncontrolled").get_attribute("aria-invalid") is None
    assert errors == []


def test_readonly_and_disabled_transport_transitions(page) -> None:
    errors = _load(page)
    page.locator("#readonly").click()
    page.wait_for_function("() => document.querySelector('#uncontrolled').readOnly")
    removals = page.locator('.cui-tags-input:has(#uncontrolled) [data-citry-ui-part="remove"]')
    assert removals.count() == 2
    assert all(removals.nth(index).is_disabled() for index in range(removals.count()))
    removals.first.evaluate("button => button.click()")
    removals.first.dispatch_event("click")
    assert _values(page, "uncontrolled") == ["alpha", "beta"]
    assert page.locator('[data-citry-tags-input-readonly-values] input[name="label"]').count() == 2
    data = page.evaluate("() => new FormData(document.querySelector('#tag-form')).getAll('label')")
    assert data == ["alpha", "beta"]
    page.locator("#disable").click()
    assert page.evaluate("() => new FormData(document.querySelector('#tag-form')).getAll('label')") == []
    assert errors == []


def test_composition_defers_delimiter_commit_until_composition_end(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.evaluate(
        """input => {
          input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:''}));
          input.value='ime,';
          input.dispatchEvent(new InputEvent('input',{bubbles:true,data:'ime,',isComposing:true}));
        }"""
    )
    assert _values(page, "uncontrolled") == ["alpha", "beta"]
    editor.evaluate(
        """input => {
          input.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:'ime,'}));
          input.dispatchEvent(new InputEvent('input',{bubbles:true,data:null,isComposing:false}));
        }"""
    )
    page.wait_for_function("() => document.querySelector('#uncontrolled-native').selectedOptions.length === 3")
    assert _values(page, "uncontrolled") == ["alpha", "beta", "ime"]
    assert editor.input_value() == ""
    assert errors == []


def test_live_composition_draft_blocks_form_submit_before_composition_end(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.fill("")
    page.evaluate(
        """() => {
          const input=document.querySelector('#uncontrolled');
          input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));
          input.value='ime';
          input.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:true}));
          document.querySelector('#tag-form').requestSubmit();
        }"""
    )
    assert page.evaluate("window.__submits") == []
    assert page.locator("#uncontrolled-native").evaluate("element => element.validity.customError") is True
    assert _values(page, "uncontrolled") == ["alpha", "beta"]
    assert errors == []


def test_event_composing_without_local_start_preserves_controlled_editor_until_final_input(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          const state=Alpine.$data(document.body);
          state.controlledDraft='';window.__controlledSubmits=0;
          document.querySelector('#controlled-form').addEventListener('submit', event => {
            event.preventDefault();window.__controlledSubmits += 1;
          });
        }"""
    )
    page.wait_for_function("() => document.querySelector('#controlled').value === ''")
    page.evaluate(
        """() => {
          const input=document.querySelector('#controlled');
          input.value='ime';
          input.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:true}));
          document.querySelector('#controlled-form').requestSubmit();
        }"""
    )
    assert page.locator("#controlled").input_value() == "ime"
    assert page.locator("#controlled-native").evaluate("element => element.validity.customError") is True
    assert page.evaluate("window.__controlledSubmits") == 0
    page.locator("#controlled").evaluate(
        "input => input.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:false}))"
    )
    page.wait_for_function("() => document.querySelector('#controlled').value === ''")
    assert page.locator("#controlled-native").evaluate("element => element.validity.customError") is False
    assert errors == []


def test_keyboard_highlight_remove_and_rtl_physical_arrows_keep_editor_focus(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.fill("")
    editor.press("Backspace")
    highlighted = page.locator(".cui-tags-input:has(#uncontrolled) [data-highlighted]")
    assert highlighted.get_attribute("data-value") == "beta"
    editor.press("Backspace")
    assert _values(page, "uncontrolled") == ["alpha"]
    assert page.evaluate("() => document.activeElement?.id") == "uncontrolled"

    page.locator(".cui-tags-input:has(#uncontrolled)").evaluate("root => root.dir='rtl'")
    editor.press("Escape")
    editor.press("ArrowRight")
    assert highlighted.get_attribute("data-value") == "alpha"
    editor.press("Delete")
    assert _values(page, "uncontrolled") == []
    assert errors == []


def test_field_id_handoff_required_ax_mirror_and_label_focus(page) -> None:
    errors = _load(page)
    editor = page.locator("#field-tags")
    native = page.locator("#field-tags-native")
    assert editor.get_attribute("data-citry-field-control") == ""
    assert editor.get_attribute("aria-labelledby") == "field-tags-label"
    assert native.get_attribute("aria-labelledby") == "field-tags-label"
    assert editor.get_attribute("aria-required") == "true"
    assert native.get_attribute("required") == ""
    page.locator('label[for="field-tags"]').click()
    assert page.evaluate("() => document.activeElement?.id") == "field-tags"
    assert errors == []


def test_dynamic_disabled_fieldset_ancestry_and_first_legend_exemption(page) -> None:
    errors = _load(page)
    editor = page.locator("#fieldset-tags")
    root = page.locator(".cui-tags-input:has(#fieldset-tags)")
    assert not editor.is_disabled()
    assert root.get_attribute("data-disabled") is None
    assert root.locator('[data-citry-tags-input-readonly-values] input[name="fieldset-label"]').count() == 1

    page.evaluate(
        """() => document.querySelector('#fieldset-target').append(
          document.querySelector('.cui-tags-input:has(#fieldset-tags)'))"""
    )
    page.wait_for_function("() => document.querySelector('#fieldset-tags').matches(':disabled')")
    assert root.get_attribute("data-disabled") == ""
    assert root.locator("[data-citry-tags-input-readonly-values] input").count() == 0
    assert page.evaluate("() => new FormData(document.querySelector('#tag-form')).getAll('fieldset-label')") == []

    page.evaluate(
        """() => document.querySelector('#legend-target').append(
          document.querySelector('.cui-tags-input:has(#fieldset-tags)'))"""
    )
    page.wait_for_function("() => !document.querySelector('#fieldset-tags').matches(':disabled')")
    assert root.get_attribute("data-disabled") is None
    assert root.locator('[data-citry-tags-input-readonly-values] input[name="fieldset-label"]').count() == 1

    page.evaluate(
        """() => document.querySelector('#outside-target').append(
          document.querySelector('.cui-tags-input:has(#fieldset-tags)'))"""
    )
    assert not editor.is_disabled()
    assert errors == []


def test_valid_client_config_survives_invalid_episode_then_null_releases(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          const state=Alpine.$data(document.body);
          state.isDisabled=true;state.tagPlaceholder='Client placeholder';state.tagMax=5;
        }"""
    )
    page.wait_for_function("() => document.querySelector('#uncontrolled').disabled")
    assert page.locator("#uncontrolled").get_attribute("placeholder") == "Client placeholder"
    page.evaluate(
        """() => {
          const state=Alpine.$data(document.body);
          state.isDisabled='invalid';state.tagPlaceholder=7;state.tagMax=0;
        }"""
    )
    assert page.locator("#uncontrolled").is_disabled()
    assert page.locator("#uncontrolled").get_attribute("placeholder") == "Client placeholder"
    page.evaluate(
        """() => {
          const state=Alpine.$data(document.body);
          state.isDisabled=null;state.tagPlaceholder=null;state.tagMax=null;
        }"""
    )
    page.wait_for_function("() => !document.querySelector('#uncontrolled').disabled")
    assert page.locator("#uncontrolled").get_attribute("placeholder") == "Server placeholder"
    assert sum("received invalid client value" in error for error in errors) == 5


def test_invalid_controlled_axis_does_not_block_independent_valid_config(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          const state=Alpine.$data(document.body);
          state.controlledValue=7;state.isDisabled=true;state.tagPlaceholder='Still reconciled';
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector('#controlled').disabled
          && document.querySelector('#controlled').placeholder === 'Still reconciled'"""
    )
    assert _values(page, "controlled") == ["alpha"]
    assert sum("CTagsInput value received invalid client value" in error for error in errors) == 1


def test_controlled_reset_stops_after_value_callback_removes_root(page) -> None:
    errors = _load(page)
    page.evaluate("Alpine.$data(document.body).removeOnReset=true;window.__tagEvents=[]")
    page.locator("#controlled-reset").click()
    page.wait_for_function("() => !document.querySelector('#controlled')")
    reset_events = page.evaluate("window.__tagEvents.filter(event => event.at(-1)?.source === 'reset')")
    assert [event[0] for event in reset_events] == ["controlled-value"]
    assert errors == []


def test_controlled_reset_owner_draft_mutation_cancels_stale_draft_request(page) -> None:
    errors = _load(page)
    page.evaluate("Alpine.$data(document.body).mutateDraftOnReset=true;window.__tagEvents=[]")
    page.locator("#controlled-reset").click()
    page.wait_for_function("() => document.querySelector('#controlled').value === 'owner'")
    reset_events = page.evaluate("window.__tagEvents.filter(event => event.at(-1)?.source === 'reset')")
    assert [event[0] for event in reset_events] == ["controlled-value"]
    assert errors == []


def test_newer_same_task_reset_cancels_stale_controlled_reset_callbacks(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          window.__tagEvents=[];
          const form=document.querySelector('#controlled-form');
          form.reset();form.reset();
        }"""
    )
    page.wait_for_function("() => window.__tagEvents.filter(event => event.at(-1)?.source === 'reset').length === 2")
    reset_events = page.evaluate("window.__tagEvents.filter(event => event.at(-1)?.source === 'reset')")
    assert [event[0] for event in reset_events] == ["controlled-value", "controlled-draft"]
    page.wait_for_timeout(50)
    assert len(page.evaluate("window.__tagEvents.filter(event => event.at(-1)?.source === 'reset')")) == 2
    assert errors == []


def test_reset_registry_rehomes_across_document_and_open_shadow_root(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.fill("gamma")
    editor.press("Enter")
    page.evaluate(
        """() => {
          const host=document.body.appendChild(document.createElement('div'));
          host.id='shadow-host';host.attachShadow({mode:'open'}).append(document.querySelector('#tag-form'));
        }"""
    )
    page.wait_for_timeout(50)
    page.locator("#shadow-host #reset").click()
    page.wait_for_function(
        """() => document.querySelector('#shadow-host').shadowRoot
          .querySelector('#uncontrolled-native').selectedOptions.length === 2"""
    )
    shadow_values = page.evaluate(
        """() => [...document.querySelector('#shadow-host').shadowRoot
          .querySelector('#uncontrolled-native').selectedOptions].map(option => option.value)"""
    )
    assert shadow_values == ["alpha", "beta"]
    assert (
        page.evaluate("() => document.querySelector('#shadow-host').shadowRoot.querySelector('#uncontrolled').value")
        == "draft"
    )
    assert errors == []


def test_canceled_reset_after_target_listener_preserves_state_and_callbacks(page) -> None:
    errors = _load(page)
    editor = page.locator("#uncontrolled")
    editor.fill("gamma")
    editor.press("Enter")
    page.evaluate(
        """() => {
          window.__tagEvents=[];
          document.querySelector('#tag-form').addEventListener('reset', event => event.preventDefault(), {once:true});
        }"""
    )
    page.locator("#reset").click()
    page.wait_for_timeout(50)
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma"]
    assert editor.input_value() == ""
    assert page.evaluate("window.__tagEvents") == []
    assert errors == []


def test_hostile_owned_id_mutation_repairs_without_duplicate_public_id(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          document.querySelector('#uncontrolled').id='hostile-editor';
          document.querySelector('#uncontrolled-native').id='hostile-native';
        }"""
    )
    page.wait_for_function(
        """() => document.querySelectorAll('#uncontrolled').length === 1
          && document.querySelector('#uncontrolled-native')"""
    )
    assert page.locator("#uncontrolled").get_attribute("data-citry-ui-part") == "input"
    assert errors == []


def test_same_marker_proxy_clone_is_replaced_by_retained_native_transport(page) -> None:
    errors = _load(page)
    page.evaluate(
        """() => {
          const native=document.querySelector('#uncontrolled-native');
          window.__retainedNative=native;
          native.replaceWith(native.cloneNode(true));
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector('.cui-tags-input:has(#uncontrolled)')
          .querySelector(':scope > [data-citry-tags-input-native]') === window.__retainedNative"""
    )
    page.locator("#uncontrolled").fill("gamma")
    page.locator("#uncontrolled").press("Enter")
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma"]
    assert page.evaluate("() => new FormData(document.querySelector('#tag-form')).getAll('label')") == [
        "alpha",
        "beta",
        "gamma",
    ]
    assert errors == []


def test_same_baseline_lifecycle_handoff_preserves_state_focus_selection_and_composition(page) -> None:
    errors = _load(page)
    page.locator("#uncontrolled").fill("gamma")
    page.locator("#uncontrolled").press("Enter")
    page.evaluate(
        """() => {
          const root=document.querySelector('.cui-tags-input:has(#uncontrolled)');
          const editor=document.querySelector('#uncontrolled');
          editor.value='compose,tail';editor.setSelectionRange(3,7);editor.focus();
          editor.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));
          editor.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:true}));
          window.__retainedEditor=editor;
          Alpine.destroyTree(root);Alpine.initTree(root);
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector('#uncontrolled') === window.__retainedEditor
          && document.querySelector('.cui-tags-input:has(#uncontrolled)')
            .hasAttribute('data-citry-tags-input-initialized')"""
    )
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma"]
    assert page.locator("#uncontrolled").input_value() == "compose,tail"
    assert page.evaluate(
        """() => [
          document.activeElement?.id,
          document.querySelector('#uncontrolled').selectionStart,
          document.querySelector('#uncontrolled').selectionEnd,
        ]"""
    ) == ["uncontrolled", 3, 7]
    page.locator("#uncontrolled").evaluate(
        """editor => {
          editor.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:'compose,tail'}));
          editor.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:false}));
        }"""
    )
    page.wait_for_function("() => document.querySelector('#uncontrolled-native').selectedOptions.length === 4")
    assert _values(page, "uncontrolled") == ["alpha", "beta", "gamma", "compose"]
    assert page.locator("#uncontrolled").input_value() == "tail"
    assert errors == []
