---
title: Split Button
url: https://citry.dev/v/0.4.6/ui-library/components/split-button/
description: "Keep one dominant action visible beside a Menu of related actions."
---
# Split Button

Use `CSplitButton` when one action is clearly dominant and a short Menu holds
closely related alternatives. The primary and Menu trigger are separate native
Buttons with separate names and Tab stops.

Use `CButton` for one action, `CButtonGroup` for visible peers, and `CMenu` when
there is no dominant action. Use `CSelect` or `CCombobox` when the reader is
choosing a value rather than running an action.

Related guidance: [Button](/v/0.4.6/ui-library/components/button/),
[Button Group](/v/0.4.6/ui-library/components/button-group/),
[Menu](/v/0.4.6/ui-library/components/menu/), the
[WAI-ARIA APG Menu Button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/),
and the [native Button element](https://developer.mozilla.org/docs/Web/HTML/Reference/Elements/button).

## Split Button at a glance

Save the specimen directly or open related save actions. The Menu does not
repeat the dominant Save action.


### Split Button at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonAtAGlance(Component):
    template = """
      <section
        class="split-button-glance"
        x-data="{saved:0,last:'No action yet'}"
      >
        <p class="split-button-glance__eyebrow">Field journal</p>
        <h2>Alpine gentian specimen</h2>
        <p>Keep the primary save action visible and related work nearby.</p>
        <c-CSplitButton
          label="Save specimen actions"
          menu_label="More save specimen actions"
          c-primary_attrs="{'@click':'saved += 1; last = `Saved specimen ${saved}`'}"
          $c-props="{onAction:(value)=>last=value}"
        >
          <c-fill name="default">Save specimen</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="Save a copy">Save a copy</c-CMenuItem>
            <c-CMenuItem value="Export record">Export record</c-CMenuItem>
            <c-CMenuItem value="Archive specimen" intent="danger">
              Archive specimen
            </c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output x-text="last">No action yet</output>
      </section>
    """

    css = """
      :where(.split-button-glance) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-glance h2, .split-button-glance p) {
        margin: 0;
      }

      :where(.split-button-glance__eyebrow) {
        color: light-dark(#3f6b42, #9ed5a1);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = SplitButtonAtAGlance()

preview  # noqa: B018
````


## Compose the two actions

Supply a nonempty group `label`, a specific `menu_label`, visible primary
content, and at least one existing Menu declaration.


```citry-html
<c-CSplitButton
  label="Save specimen actions"
  menu_label="More save specimen actions"
>
  <c-fill name="default">Save specimen</c-fill>
  <c-fill name="menu">
    <c-CMenuItem value="save-copy">Save a copy</c-CMenuItem>
    <c-CMenuItem value="export">Export record</c-CMenuItem>
  </c-fill>
</c-CSplitButton>
```


Direct Python composition uses the same slots and public Menu declarations:


```citry
from citry_ui import CMenuItem, CSplitButton

save_actions = CSplitButton(
    label="Save specimen actions",
    menu_label="More save specimen actions",
    slots={
        "default": "Save specimen",
        "menu": (
            CMenuItem(
                value="save-copy",
                slots={"default": "Save a copy"},
            ),
            CMenuItem(
                value="export",
                slots={"default": "Export record"},
            ),
        ),
    },
)
```


The next example renders both composition forms.


### Template and Python composition

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/basic-actions/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CMenuItem, CSplitButton

citry.register_library(citry_ui)


class BasicSplitButtonActions(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_split_button": CSplitButton(
                label="Publish specimen actions",
                menu_label="More publish specimen actions",
                variant="outline",
                slots={
                    "default": "Publish specimen",
                    "menu": (
                        CMenuItem(
                            value="preview",
                            slots={"default": "Preview publication"},
                        ),
                        CMenuItem(
                            value="schedule",
                            slots={"default": "Schedule publication"},
                        ),
                    ),
                },
            )
        }

    template = """
      <section class="split-button-basic">
        <article>
          <p>Template composition</p>
          <c-CSplitButton
            label="Save specimen actions"
            menu_label="More save specimen actions"
          >
            <c-fill name="default">Save specimen</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="save-copy">Save a copy</c-CMenuItem>
              <c-CMenuItem value="export">Export record</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </article>
        <article>
          <p>Python composition</p>
          {{ python_split_button }}
        </article>
      </section>
    """

    css = """
      :where(.split-button-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-basic article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.split-button-basic p) {
        margin: 0;
        font-weight: 700;
      }
    """


preview = BasicSplitButtonActions()

preview  # noqa: B018
````


## Submit and reset native Forms

Only the primary Button participates in a Form. Set `type="submit"` or
`type="reset"`, then pass `name`, `value`, `form`, and submitter overrides
through `primary_attrs`. The Menu Button and Menu items never submit.


### Submit, reset, and related export actions

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonForms(Component):
    template = """
      <section
        class="split-button-forms"
        x-data="{result:'No Form action yet',owner:'accession-form'}"
      >
        <form
          id="accession-form"
          x-ref="accession"
          @submit.prevent="
            result = `Submitted ${new FormData($event.target, $event.submitter).get('action')}`
          "
          @reset="setTimeout(() => result = 'Reset accession', 0)"
        >
          <label>
            Accession name
            <input name="specimen" value="Alpine gentian" required />
          </label>
          <div class="split-button-forms__actions">
            <c-CSplitButton
              label="Commit accession actions"
              menu_label="More commit accession actions"
              type="submit"
              c-primary_attrs="{'name':'action','value':'commit'}"
            >
              <c-fill name="default">Commit accession</c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="export-draft">
                  Export draft
                </c-CMenuItem>
              </c-fill>
            </c-CSplitButton>
            <c-CSplitButton
              label="Reset accession actions"
              menu_label="More reset accession actions"
              type="reset"
              variant="outline"
            >
              <c-fill name="default">Reset accession</c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="restore-snapshot">
                  Restore saved snapshot
                </c-CMenuItem>
              </c-fill>
            </c-CSplitButton>
          </div>
        </form>

        <form
          id="secondary-accession-form"
          @submit.prevent="
            result = `Submitted to secondary Form with ${$event.submitter.value}`
          "
        >
          <label>
            Secondary accession
            <input name="secondary-specimen" value="Sea thrift" required />
          </label>
        </form>

        <label>
          External primary Form owner
          <select x-model="owner">
            <option value="accession-form">Main accession Form</option>
            <option value="secondary-accession-form">Secondary accession Form</option>
          </select>
        </label>

        <c-CSplitButton
          id="external-commit-actions"
          label="External commit actions"
          menu_label="More external commit actions"
          type="submit"
          size="sm"
          c-primary_attrs="{
            ':form':'owner',
            'name':'action',
            'value':'external-commit'
          }"
        >
          <c-fill name="default">Commit from outside</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="download">Download draft</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>

        <button
          type="button"
          @click="
            document.getElementById(owner).requestSubmit(
              document.getElementById('external-commit-actions-primary')
            )
          "
        >
          Request native submit
        </button>
        <output x-text="result">No Form action yet</output>
      </section>
    """

    css = """
      :where(.split-button-forms) {
        display: grid;
        gap: 1rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-forms form, .split-button-forms label) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.split-button-forms__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = SplitButtonForms()

preview  # noqa: B018
````


An open Menu closes internally before an uncontrolled primary default action.
Its public `onOpenChange` action notice runs afterward, so the callback cannot
cancel or duplicate the accepted native submit or reset. A valid
`form.requestSubmit(primary)` follows the same rule. Native constraint
validation can prevent submission before a submit event; that path leaves the
Menu unchanged.

Without JavaScript, an enabled primary submit or reset remains a useful native
Button, while server disabled or loading output uses CButton's native-safe
fallback. The Menu Button cannot toggle before initialization. A closed Menu
stays noninteractive in server flow, and an initially open Menu remains
readable; neither path can submit the Form.

## Control Menu visibility

Pass a Boolean client `open` to own Menu visibility. Omit it or pass `null` to
release control from the latest committed state. `onOpenChange` reports Menu
gestures and the primary action close request. Forced disabled or ancestor
closes cannot be refused.


### Control Split Button Menu visibility

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/controlled-menu/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSplitButtonMenu(Component):
    template = """
      <section
        class="split-button-controlled"
        x-data="{
          open:false,
          controlled:true,
          accept:true,
          lastReason:'none'
        }"
      >
        <c-CSplitButton
          label="Publication actions"
          menu_label="More publication actions"
          $c-props="{
            open: controlled ? open : null,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (controlled && accept) open = nextOpen;
            },
          }"
        >
          <c-fill name="default">Publish specimen</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="preview">Preview publication</c-CMenuItem>
            <c-CMenuItem value="schedule">Schedule publication</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>

        <label>
          <input type="checkbox" x-model="accept" />
          Accept Menu requests
        </label>
        <div role="group" aria-label="Menu owner controls">
          <button type="button" @click="controlled=true;open=true">
            Show
          </button>
          <button type="button" @click="controlled=true;open=false">
            Hide
          </button>
          <button type="button" @click="controlled=false">
            Release control
          </button>
        </div>
        <output>
          Ownership:
          <span x-text="controlled ? 'controlled' : 'released'">
            controlled
          </span>
          · Last reason:
          <span x-text="lastReason">none</span>
        </output>
      </section>
    """

    css = """
      :where(.split-button-controlled) {
        display: grid;
        gap: 0.85rem;
        justify-items: start;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-controlled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
    """


preview = ControlledSplitButtonMenu()

preview  # noqa: B018
````


Primary native events remain distinct from Menu callbacks. Pass `@click`
through `primary_attrs`, and use `onAction` for valued Menu commands and
choices.

## Choose presentation and placement

`variant`, `intent`, and `size` style both Buttons. `block` fills the available
inline size while the Menu Button keeps its target width. `placement` and
`match_width` use the full joined group as their anchor, not the narrow Menu
Button.


### Variants, sizes, and placement

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/variants-and-sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonVariantsAndSizes(Component):
    template = """
      <section
        class="split-button-variants"
        x-data="{
          variant:'solid',
          intent:'primary',
          size:'md',
          block:false,
          placement:'bottom-end',
          match_width:false
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <div class="split-button-variants__subject">
          <c-CSplitButton
            label="Live collection actions"
            menu_label="More live collection actions"
            $c-props="{
              variant,
              intent,
              size,
              block,
              placement,
              matchWidth: match_width
            }"
          >
            <c-fill name="default">Collect specimen</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="photograph">Photograph first</c-CMenuItem>
              <c-CMenuItem value="label">Print field label</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>
        <div class="split-button-variants__matrix">
          <c-CSplitButton
            label="Approve actions"
            menu_label="More approve actions"
            variant="outline"
            intent="success"
            size="sm"
          >
            <c-fill name="default">Approve</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="review">Return to review</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
          <c-CSplitButton
            label="Warning actions"
            menu_label="More warning actions"
            variant="ghost"
            intent="warn"
            size="lg"
          >
            <c-fill name="default">Flag specimen</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="quarantine" intent="danger">
                Quarantine specimen
              </c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>
      </section>
    """

    css = """
      :where(.split-button-variants) {
        display: grid;
        gap: 1.5rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-variants__subject) {
        inline-size: min(100%, 30rem);
      }

      :where(.split-button-variants__matrix) {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: start;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "solid",
        "options": (
            ("solid", "Solid"),
            ("outline", "Outline"),
            ("ghost", "Ghost"),
        ),
    },
    {
        "name": "intent",
        "label": "Intent",
        "type": "select",
        "default": "primary",
        "options": (
            ("primary", "Primary"),
            ("neutral", "Neutral"),
            ("success", "Success"),
            ("warn", "Warn"),
            ("danger", "Danger"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "bottom-end",
        "options": (
            ("bottom-start", "Bottom start"),
            ("bottom-end", "Bottom end"),
            ("top-start", "Top start"),
            ("top-end", "Top end"),
        ),
    },
    {"name": "block", "label": "Full width", "type": "checkbox", "default": False},
    {
        "name": "match_width",
        "label": "Match group width",
        "type": "checkbox",
        "default": False,
    },
)


preview = SplitButtonVariantsAndSizes()

preview  # noqa: B018
````


## Keep alternatives available while loading

`loading` affects only the primary action. It remains focusable, exposes busy
state, and blocks new activation while an otherwise enabled Menu remains
available. Use common `disabled` when both halves must be unavailable, or the
per-half inputs when only one action is unavailable.


### Disabled and loading states

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/disabled-and-loading/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonDisabledAndLoading(Component):
    template = """
      <section
        class="split-button-disabled-demo"
        x-data="{
          disabled: false,
          primaryDisabled: false,
          menuDisabled: false,
          loading: false,
          saves: 0,
          last: 'Ready',
        }"
      >
        <h2>Large specimen image</h2>
        <div class="split-button-disabled-demo__controls" aria-label="Split Button state">
          <label><input type="checkbox" x-model="disabled" /> Disable both</label>
          <label><input type="checkbox" x-model="primaryDisabled" /> Disable primary</label>
          <label><input type="checkbox" x-model="menuDisabled" /> Disable Menu</label>
          <label><input type="checkbox" x-model="loading" /> Save pending</label>
        </div>

        <c-CSplitButton
          label="Specimen image actions"
          menu_label="More specimen image actions"
          c-primary_attrs="{'@click':'saves += 1; last = `Saved ${saves} times`'}"
          $c-props="{
            disabled,
            primaryDisabled,
            menuDisabled,
            loading,
            onAction: (value) => last = value,
          }"
        >
          <c-fill name="default">Save image</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="Export TIFF">Export TIFF</c-CMenuItem>
            <c-CMenuItem value="Export JPEG">Export JPEG</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output aria-live="polite" x-text="last">Ready</output>

        <fieldset disabled>
          <legend>Disabled fieldset lifecycle</legend>
          <c-CSplitButton
            label="Fieldset-owned image actions"
            menu_label="More fieldset-owned image actions"
          >
            <c-fill name="default">Save fieldset image</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="export-fieldset">Export fieldset image</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </fieldset>
      </section>
    """

    css = """
      :where(.split-button-disabled-demo) {
        display: grid;
        gap: 1rem;
        justify-items: start;
        inline-size: min(100%, 34rem);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-disabled-demo h2) { margin: 0; }
      :where(.split-button-disabled-demo__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1rem;
      }
      :where(.split-button-disabled-demo__controls label) {
        display: inline-flex;
        gap: 0.4rem;
        align-items: center;
      }
      :where(.split-button-disabled-demo fieldset) {
        inline-size: 100%;
        padding: 1rem;
        border: 1px solid GrayText;
        border-radius: 0.75rem;
      }

      @media (forced-colors: active) {
        :where(.split-button-disabled-demo fieldset) { border-color: CanvasText; }
      }
    """


preview = SplitButtonDisabledAndLoading()

preview  # noqa: B018
````


Native disabled `fieldset` ancestry remains authoritative. When disabling the
Menu hides focused Menu content, focus moves to an enabled primary Button or a
safe modal/document fallback.

## Reuse the complete Menu collection

The `menu` slot accepts the current `CMenuItem`, `CMenuCheckboxItem`,
`CMenuRadioGroup`, `CMenuRadioItem`, `CMenuGroup`, `CMenuSeparator`, and
`CMenuSubmenu` declarations. Their values, callbacks, paths, parts, keyboard
rules, and content limits remain the CMenu contract.


### Commands, choices, groups, and submenus

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/menu-composition/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonMenuComposition(Component):
    template = """
      <section
        class="split-button-menu-composition"
        x-data="{publicRecord:true, format:'tiff', last:'No Menu action yet'}"
        dir="rtl"
      >
        <h2>Specimen publication</h2>
        <c-CSplitButton
          label="Specimen publication actions"
          menu_label="More specimen publication actions"
          c-close_on_select="False"
          $c-props="{onAction:(value, detail)=>last=`${detail.path.join(' / ') || 'root'}: ${value}`}"
        >
          <c-fill name="default">Publish specimen</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="copy-citation">Copy citation</c-CMenuItem>
            <c-CMenuItem href="#specimen-public-record">Open public record</c-CMenuItem>
            <c-CMenuCheckboxItem
              value="public-record"
              $c-props="{
                checked: publicRecord,
                onCheckedChange: (next) => publicRecord = next,
              }"
            >
              Publicly visible
            </c-CMenuCheckboxItem>
            <c-CMenuRadioGroup
              value="tiff"
              $c-props="{
                value: format,
                onValueChange: (next) => format = next,
              }"
            >
              <c-fill name="label">Export format</c-fill>
              <c-fill name="default">
                <c-CMenuRadioItem value="tiff">TIFF</c-CMenuRadioItem>
                <c-CMenuRadioItem value="jpeg">JPEG</c-CMenuRadioItem>
              </c-fill>
            </c-CMenuRadioGroup>
            <c-CMenuSeparator />
            <c-CMenuGroup>
              <c-fill name="label">Archive destination</c-fill>
              <c-fill name="default">
                <c-CMenuSubmenu value="regional-archive">
                  <c-fill name="label">Regional archive</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="alpine">Alpine collection</c-CMenuItem>
                    <c-CMenuItem value="coastal">Coastal collection</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenuGroup>
            <c-CMenuItem value="withdraw" intent="danger">Withdraw record</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output aria-live="polite" x-text="last">No Menu action yet</output>
        <p id="specimen-public-record">The linked public record remains native navigation.</p>
      </section>
    """

    css = """
      :where(.split-button-menu-composition) {
        display: grid;
        gap: 0.875rem;
        justify-items: start;
        min-block-size: 23rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-menu-composition h2, .split-button-menu-composition p) { margin: 0; }
      :where(.split-button-menu-composition output) {
        max-inline-size: 100%;
        overflow-wrap: anywhere;
      }
    """


preview = SplitButtonMenuComposition()

preview  # noqa: B018
````


Do not repeat the primary action in the Menu. Give the Menu Button a full
secondary name such as “More save specimen actions”, not only “More”.

## Use the two-stop keyboard model

Tab visits the primary Button and then the Menu Button in DOM order in both
LTR and RTL. Enter and Space activate the focused native Button. Arrow Down or
Arrow Up on the Menu Button opens and focuses the first or last item. The
primary does not gain Menu arrow behavior.


### Focus and keyboard behavior

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/focus-and-keyboard/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonFocusAndKeyboard(Component):
    template = """
      <section
        class="split-button-keyboard-demo"
        x-data="{trace:[], loading:false, primaryDisabled:false, menuDisabled:false}"
      >
        <h2>Keyboard specimen workflow</h2>
        <p>
          Tab reaches the primary and Menu Button in DOM order. Enter or Space activates the
          focused Button. In the Menu, use arrows, Home, End, typeahead, and Escape.
        </p>
        <div class="split-button-keyboard-demo__controls">
          <label><input type="checkbox" x-model="loading" /> Primary loading</label>
          <label><input type="checkbox" x-model="primaryDisabled" /> Primary disabled</label>
          <label><input type="checkbox" x-model="menuDisabled" /> Menu disabled</label>
        </div>

        <div class="split-button-keyboard-demo__row" dir="ltr">
          <span>LTR</span>
          <c-CSplitButton
            label="Keyboard save actions"
            menu_label="More keyboard save actions"
            c-primary_attrs="{'@focus':'trace.push(`LTR primary`)'}"
            c-trigger_attrs="{'@focus':'trace.push(`LTR menu`)'}"
            $c-props="{loading, primaryDisabled, menuDisabled}"
          >
            <c-fill name="default">Save field note</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="duplicate">Duplicate note</c-CMenuItem>
              <c-CMenuItem value="export">Export note</c-CMenuItem>
              <c-CMenuItem value="archive">Archive note</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>

        <div class="split-button-keyboard-demo__row" dir="rtl">
          <span>RTL</span>
          <c-CSplitButton
            label="إجراءات حفظ العينة"
            menu_label="المزيد من إجراءات حفظ العينة"
            c-primary_attrs="{'@focus':'trace.push(`RTL primary`)'}"
            c-trigger_attrs="{'@focus':'trace.push(`RTL menu`)'}"
          >
            <c-fill name="default">حفظ ملاحظة العينة</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="duplicate-rtl">نسخ الملاحظة</c-CMenuItem>
              <c-CMenuItem value="export-rtl">تصدير الملاحظة</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>

        <output aria-live="polite" x-text="trace.length ? trace.join(' → ') : 'Focus trace is empty'">
          Focus trace is empty
        </output>
        <button type="button" @click="trace=[]">Clear focus trace</button>
      </section>
    """

    css = """
      :where(.split-button-keyboard-demo) {
        display: grid;
        gap: 1rem;
        inline-size: min(100%, 32rem);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-keyboard-demo h2, .split-button-keyboard-demo p) { margin: 0; }
      :where(.split-button-keyboard-demo__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      :where(.split-button-keyboard-demo__row) {
        display: grid;
        gap: 0.5rem;
        justify-items: start;
        inline-size: min(100%, 20rem);
      }
      :where(.split-button-keyboard-demo output) { overflow-wrap: anywhere; }
    """


preview = SplitButtonFocusAndKeyboard()

preview  # noqa: B018
````


Once open, the collection uses CMenu arrow navigation, Home, End, typeahead,
submenus, Escape, and Tab behavior without trapping focus.

## Compose with clipping and Dialogs

The Menu uses the native top layer and the shared anchored-layer coordinator.
It escapes ordinary overflow while placement and width still follow the full
SplitButton root. A sibling Dialog opened by either action owns modal focus.


### Clipped layers, ShadowRoot, and sibling Dialog

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/layers-and-dialog/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonLayersAndDialog(Component):
    template = """
      <section
        class="split-button-layer-demo"
        x-data="{dialogOpen:false,last:'No layer action yet'}"
        @click="if ($event.target.closest('[data-open-provenance]')) dialogOpen=true"
        x-init="$nextTick(() => {
          const host = $refs.shadowHost;
          const fixture = $refs.shadowFixture;
          if (!host.shadowRoot && fixture) host.attachShadow({mode:'open'}).append(fixture);
        })"
      >
        <h2>Clipped specimen tray</h2>
        <div class="split-button-layer-demo__clip" dir="rtl">
          <c-CSplitButton
            label="Clipped specimen actions"
            menu_label="More clipped specimen actions"
            placement="bottom-end"
            c-primary_attrs="{'data-open-provenance':'','@click':'last=`Primary requested provenance`'}"
            $c-props="{onAction:(value)=>{
              last=value;
              if (value === 'open-provenance') dialogOpen=true;
            }}"
          >
            <c-fill name="default">Record provenance</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="open-provenance">Open provenance Dialog</c-CMenuItem>
              <c-CMenuSubmenu value="archive">
                <c-fill name="label">Archive destination</c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="alpine-archive">Alpine archive</c-CMenuItem>
                  <c-CMenuItem value="coastal-archive">Coastal archive</c-CMenuItem>
                </c-fill>
              </c-CMenuSubmenu>
            </c-fill>
          </c-CSplitButton>
        </div>

        <div x-ref="shadowHost" class="split-button-layer-demo__shadow-host">
          <div x-ref="shadowFixture">
            <c-CSplitButton
              label="Shadow specimen actions"
              menu_label="More Shadow specimen actions"
            >
              <c-fill name="default">Save Shadow specimen</c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="shadow-export">Export from ShadowRoot</c-CMenuItem>
              </c-fill>
            </c-CSplitButton>
          </div>
        </div>

        <output aria-live="polite" x-text="last">No layer action yet</output>
        <c-CDialog
          size="sm"
          $c-props="{
            open:dialogOpen,
            onOpenChange:(next)=>dialogOpen=next,
          }"
        >
          <c-fill name="title">Specimen provenance</c-fill>
          <c-fill name="default">Collected above the tree line during the August survey.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Close provenance</c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.split-button-layer-demo) {
        display: grid;
        gap: 1rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-layer-demo h2) { margin: 0; }
      :where(.split-button-layer-demo__clip) {
        overflow: hidden;
        inline-size: min(100%, 24rem);
        block-size: 7rem;
        padding: 2rem;
        border: 1px solid color-mix(in srgb, CanvasText 30%, transparent);
        border-radius: 0.75rem;
      }
      :where(.split-button-layer-demo__shadow-host) {
        display: block;
        padding: 0.75rem;
        border: 1px dashed GrayText;
      }
    """


preview = SplitButtonLayersAndDialog()

preview  # noqa: B018
````


Render Dialog and other peer overlays as siblings. Menu declaration content
still follows CMenu's noninteractive item-content boundary.

## Customize the joined control and Menu

Both Buttons consume the public `--cui-button-*` variables, and the Menu keeps
the public `--cui-menu-*` contract. SplitButton adds variables for its divider,
Menu Button width, and joined radius. Stable part selectors target each half
and its content without changing semantic ownership.


### Brand and environment customization

[Open the rendered preview](/v/0.4.6/ui-library/components/split-button/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonCustomization(Component):
    template = """
      <section class="split-button-brand-demo">
        <article class="split-button-brand-demo__card split-button-brand-demo__card--orchard">
          <p>Orchard field guide</p>
          <c-CSplitButton
            class_="split-button-brand-demo__subject"
            label="Orchard specimen publishing actions"
            menu_label="More Orchard specimen publishing actions"
            open
          >
            <c-fill name="default">Publish alpine gentian observation</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="orchard-draft">Save Orchard draft</c-CMenuItem>
              <c-CMenuItem value="orchard-export">Export Orchard record</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </article>

        <article
          class="split-button-brand-demo__card split-button-brand-demo__card--harbor"
          dir="rtl"
        >
          <p>دليل ميناء للأبحاث الميدانية</p>
          <c-CSplitButton
            class_="split-button-brand-demo__subject"
            label="إجراءات نشر ملاحظة العينة الساحلية"
            menu_label="المزيد من إجراءات نشر ملاحظة العينة الساحلية"
            variant="outline"
            open
          >
            <c-fill name="default">نشر ملاحظة العينة الساحلية الطويلة</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="harbor-draft">حفظ المسودة الساحلية</c-CMenuItem>
              <c-CMenuItem value="harbor-export">تصدير السجل الساحلي</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </article>
      </section>
    """

    css = """
      :where(.split-button-brand-demo) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-brand-demo__card) {
        min-block-size: 18rem;
        padding: 1.25rem;
        border-radius: 1rem;
      }
      :where(.split-button-brand-demo__card > p) { margin-block: 0 1rem; font-weight: 700; }
      :where(.split-button-brand-demo__subject) { max-inline-size: 20rem; }

      :where(.split-button-brand-demo__card--orchard) {
        color-scheme: light;
        background: #f5f0df;
        --cui-button-background: #315f37;
        --cui-button-foreground: #fffdf5;
        --cui-button-hover-background: #244c2a;
        --cui-menu-background: #fffdf5;
        --cui-menu-foreground: #203422;
        --cui-menu-focus-background: #d9e9cf;
        --cui-menu-focus-foreground: #17351c;
        --cui-split-button-divider-color: #c5d7bb;
        --cui-split-button-divider-width: 2px;
        --cui-split-button-radius: 0.75rem;
      }

      :where(.split-button-brand-demo__card--harbor) {
        color-scheme: dark;
        background: #102b38;
        --cui-button-background: #c6ecff;
        --cui-button-foreground: #082633;
        --cui-button-border-color: #79bfdc;
        --cui-button-hover-background: #a7ddf5;
        --cui-menu-background: #173c4c;
        --cui-menu-foreground: #eefaff;
        --cui-menu-focus-background: #95d9f4;
        --cui-menu-focus-foreground: #062531;
        --cui-split-button-divider-color: #29586b;
        --cui-split-button-divider-width: 1px;
        --cui-split-button-radius: 0.375rem;
      }

      :where(.split-button-brand-demo [data-citry-ui-part="split-button-primary"]) {
        min-inline-size: 0;
      }
      :where(.split-button-brand-demo [data-citry-ui-part="split-button-primary-content"]) {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      @media (prefers-reduced-motion: reduce) {
        :where(.split-button-brand-demo) {
          --cui-menu-duration: 0ms;
        }
      }
      @media (forced-colors: active) {
        :where(.split-button-brand-demo__card) {
          border: 1px solid CanvasText;
          forced-color-adjust: auto;
        }
      }
      @media print {
        :where(.split-button-brand-demo__card) {
          break-inside: avoid;
          border: 1px solid currentColor;
          background: transparent;
          color: black;
        }
      }
    """


preview = SplitButtonCustomization()

preview  # noqa: B018
````


The horizontal compound keeps the primary at logical start in RTL, preserves
the Menu Button target width at narrow sizes, removes motion under reduced
motion, and retains visible focus and divider boundaries in forced colors.

## Choose explicit composition for a different policy

Compose `CButtonGroup` and `CMenu` when the primary must be a link, actions are
equal peers, the layout must be vertical, or the two surfaces need separate
state owners. SplitButton intentionally keeps one dominant command, one Menu
owner, one horizontal anatomy, and no imperative methods or custom DOM events.

## Trust the four attribute destinations deliberately

`attrs`, `primary_attrs`, `trigger_attrs`, and `menu_attrs` are copied and
validated for their documented roots. They accept ordinary styling, language,
permitted ARIA, and `data-*` except `data-citry-*`, `data-cev*`, `data-cid*`,
and owned reflections. `@event` and `x-on:event` Alpine listeners are allowed;
raw `on*` browser-expression attributes are rejected. The primary also accepts
the documented native Form attributes, but URL-like action destinations remain
consumer-owned and are not sanitized or trusted by Citry. Component-owned
identity, semantics, state, focus order, popover targeting, Citry runtime
fields, and structural Alpine ownership are rejected.

Primary content accepts text and decorative noninteractive content. The final
Button needs a nonempty accessible name from visible text, `aria-label`, or
`aria-labelledby`. Menu declarations retain CMenu's exact trust boundary.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CSplitButton server inputs

Server inputs are passed in a template through `<c-CSplitButton ... />` or in Python through
`CSplitButton(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="split-button-input-csplit-button-server-inputs-id"></span>`id` | `str | None` | generated | Sets the literal root ID base and the primary, Menu Button, and Menu surface ID family. |
| <span id="split-button-input-csplit-button-server-inputs-label"></span>`label` | `non-whitespace str` | required | Names the related two-Button group. |
| <span id="split-button-input-csplit-button-server-inputs-menu-label"></span>`menu_label` | `non-whitespace str` | required | Names the secondary Menu Button with its specific purpose. |
| <span id="split-button-input-csplit-button-server-inputs-type"></span>`type` | `"button" | "submit" | "reset"` ([`CButtonType`](#split-button-interface-button-type)) | `"button"` | Selects the primary native Button activation and Form behavior. |
| <span id="split-button-input-csplit-button-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables both Buttons and force-closes the Menu. |
| <span id="split-button-input-csplit-button-server-inputs-primary-disabled"></span>`primary_disabled` | `bool` | `False` | Disables only the primary Button. |
| <span id="split-button-input-csplit-button-server-inputs-menu-disabled"></span>`menu_disabled` | `bool` | `False` | Disables only the Menu Button and force-closes the Menu. |
| <span id="split-button-input-csplit-button-server-inputs-loading"></span>`loading` | `bool` | `False` | Marks only the primary pending, retains its focus, and blocks new primary activation. |
| <span id="split-button-input-csplit-button-server-inputs-variant"></span>`variant` | `"solid" | "outline" | "ghost"` ([`CButtonVariant`](#split-button-interface-button-variant)) | `"solid"` | Sets both Buttons' presentation strength. |
| <span id="split-button-input-csplit-button-server-inputs-intent"></span>`intent` | `"primary" | "neutral" | "success" | "warn" | "danger"` ([`CButtonIntent`](#split-button-interface-button-intent)) | `"primary"` | Sets both Buttons' semantic color role. |
| <span id="split-button-input-csplit-button-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CButtonSize`](#split-button-interface-button-size)) | `"md"` | Sets both Buttons and Menu item geometry. |
| <span id="split-button-input-csplit-button-server-inputs-block"></span>`block` | `bool` | `False` | Fills the containing inline size while the primary takes remaining space. |
| <span id="split-button-input-csplit-button-server-inputs-loading-pos"></span>`loading_pos` | `"start" | "center" | "end"` ([`CButtonLoadingPos`](#split-button-interface-button-loading-pos)) | `"center"` | Places the primary loading indicator. |
| <span id="split-button-input-csplit-button-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial Menu visibility and the uncontrolled fallback. |
| <span id="split-button-input-csplit-button-server-inputs-loop"></span>`loop` | `bool` | `True` | Wraps Menu arrow navigation and typeahead. |
| <span id="split-button-input-csplit-button-server-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CMenuPlacement`](#split-button-interface-menu-placement)) | `"bottom-end"` | Sets the preferred logical placement relative to the full group. |
| <span id="split-button-input-csplit-button-server-inputs-match-width"></span>`match_width` | `bool` | `False` | Matches the full group width up to the Menu viewport-safe maximum. |
| <span id="split-button-input-csplit-button-server-inputs-close-on-select"></span>`close_on_select` | `bool` | `True` | Sets the root Menu default close policy. |
| <span id="split-button-input-csplit-button-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#split-button-interface-class-value)) | `None` | Adds root classes and merges them with attrs. |
| <span id="split-button-input-csplit-button-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#split-button-interface-style-value)) | `None` | Adds root styles; generated anchor ownership merges last. |
| <span id="split-button-input-csplit-button-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes to the labelled group root. |
| <span id="split-button-input-csplit-button-server-inputs-primary-attrs"></span>`primary_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed ARIA, Form, data, style, and native listener attributes to the primary Button. |
| <span id="split-button-input-csplit-button-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed descriptive, data, style, and native listener attributes to the Menu Button. |
| <span id="split-button-input-csplit-button-server-inputs-menu-attrs"></span>`menu_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed descriptive, language, data, style, and native listener attributes to the root Menu surface. |

</div>

#### CSplitButton client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSplitButton />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 15rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="split-button-input-csplit-button-client-inputs-open"></span>`open` | `boolean | null` | Releases control from the latest committed state. null has the same effect. | Controls Menu visibility while supplied as a Boolean. |
| <span id="split-button-input-csplit-button-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls common disabledness; native fieldset disabledness remains authoritative. |
| <span id="split-button-input-csplit-button-client-inputs-primary-disabled"></span>`primaryDisabled` | `boolean` | Uses the server input. | Controls primary-only disabledness. |
| <span id="split-button-input-csplit-button-client-inputs-menu-disabled"></span>`menuDisabled` | `boolean` | Uses the server input. | Controls Menu-only disabledness and forced close. |
| <span id="split-button-input-csplit-button-client-inputs-loading"></span>`loading` | `boolean` | Uses the server input. | Controls the focus-retaining primary pending guard. |
| <span id="split-button-input-csplit-button-client-inputs-variant"></span>`variant` | `"solid" | "outline" | "ghost"` ([`CButtonVariant`](#split-button-interface-button-variant)) | Uses the server input. | Controls both Buttons' presentation strength. |
| <span id="split-button-input-csplit-button-client-inputs-intent"></span>`intent` | `"primary" | "neutral" | "success" | "warn" | "danger"` ([`CButtonIntent`](#split-button-interface-button-intent)) | Uses the server input. | Controls both Buttons' semantic color role. |
| <span id="split-button-input-csplit-button-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CButtonSize`](#split-button-interface-button-size)) | Uses the server input. | Controls Button and Menu geometry. |
| <span id="split-button-input-csplit-button-client-inputs-block"></span>`block` | `boolean` | Uses the server input. | Controls full-inline group layout. |
| <span id="split-button-input-csplit-button-client-inputs-loading-position"></span>`loadingPosition` | `"start" | "center" | "end"` ([`CButtonLoadingPos`](#split-button-interface-button-loading-pos)) | Uses the server input. | Controls primary loading-indicator placement. |
| <span id="split-button-input-csplit-button-client-inputs-loop"></span>`loop` | `boolean` | Uses the server input. | Controls Menu navigation wrapping. |
| <span id="split-button-input-csplit-button-client-inputs-placement"></span>`placement` | `six logical placement strings` ([`CMenuPlacement`](#split-button-interface-menu-placement)) | Uses the server input. | Controls requested full-root Menu placement. |
| <span id="split-button-input-csplit-button-client-inputs-match-width"></span>`matchWidth` | `boolean` | Uses the server input. | Controls clamped full-group width matching. |
| <span id="split-button-input-csplit-button-client-inputs-close-on-select"></span>`closeOnSelect` | `boolean` | Uses the server input. | Controls the root Menu default close policy. |
| <span id="split-button-input-csplit-button-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Omission or null selects no visibility callback. | Receives Menu requests, forced closes, and deferred primary action-close notices. |
| <span id="split-button-input-csplit-button-client-inputs-on-action"></span>`onAction` | `function` | Omission or null selects no Menu action callback. | Receives valued Menu command and choice activations. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CSplitButton slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="split-button-slot-csplit-button-slots-default"></span>`default` | yes | `{}` ([`CSplitButtonDefaultSlotData`](#split-button-interface-csplit-button-default-slot-data)) | None. Must be structurally nonempty and help provide the final primary accessible name. |
| <span id="split-button-slot-csplit-button-slots-start"></span>`start` | no | `{}` ([`CSplitButtonStartSlotData`](#split-button-interface-csplit-button-start-slot-data)) | Omitted. |
| <span id="split-button-slot-csplit-button-slots-end"></span>`end` | no | `{}` ([`CSplitButtonEndSlotData`](#split-button-interface-csplit-button-end-slot-data)) | Omitted. |
| <span id="split-button-slot-csplit-button-slots-loading"></span>`loading` | no | `{}` ([`CSplitButtonLoadingSlotData`](#split-button-interface-csplit-button-loading-slot-data)) | CSS spinner hidden from accessibility. |
| <span id="split-button-slot-csplit-button-slots-menu"></span>`menu` | yes | `{}` ([`CSplitButtonMenuSlotData`](#split-button-interface-csplit-button-menu-slot-data)) | None. Requires a nonempty collection of existing CMenu declarations. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CSplitButton events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="split-button-event-csplit-button-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CMenuOpenChangeDetail) => void` ([`CMenuOpenChangeDetail`](#split-button-interface-csplit-button-open-change-detail)) | A root Menu visibility request, forced close, or accepted primary action close occurs. | `{reason, controlled, forced, source}` ([`CMenuOpenChangeDetail`](#split-button-interface-csplit-button-open-change-detail)) | Menu gestures use CMenu timing. A primary action notice runs in a cancelable zero-delay task after native activation; uncontrolled state already closed and controlled state waits. |
| <span id="split-button-event-csplit-button-events-on-action"></span>`onAction` | `(value: string, detail: CMenuActionDetail) => void` ([`CMenuActionDetail`](#split-button-interface-csplit-button-action-detail)) | An enabled valued Menu command, checkbox, or radio activates. | `{kind, item, event, path}` ([`CMenuActionDetail`](#split-button-interface-csplit-button-action-detail)) | Uses CMenu callback order and fires once. The primary action, links, and anonymous commands do not fire it. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSplitButton CSS variables

Apply these variables to `CSplitButton` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="split-button-css-csplit-button-css-variables-cui-split-button-divider-color"></span>`--cui-split-button-divider-color` | `color` | Boundary between the two native Buttons. | `color-mix(in srgb, currentColor 32%, transparent)` |
| <span id="split-button-css-csplit-button-css-variables-cui-split-button-divider-width"></span>`--cui-split-button-divider-width` | `length` | Joined divider width and overlap. | `1px` |
| <span id="split-button-css-csplit-button-css-variables-cui-split-button-menu-inline-size"></span>`--cui-split-button-menu-inline-size` | `length` | Menu Button inline target size. | `Effective Button height.` |
| <span id="split-button-css-csplit-button-css-variables-cui-split-button-radius"></span>`--cui-split-button-radius` | `length` | Joined outer corners. | `var(--cui-button-radius, 0.5rem)` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-background"></span>`--cui-button-background` | `color` | Both Button resting surfaces. | `Variant- and intent-derived color.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-foreground"></span>`--cui-button-foreground` | `color` | Both Button foregrounds. | `Derived contrast color.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-border-color"></span>`--cui-button-border-color` | `color` | Both Button borders. | `Variant- and intent-derived color.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-hover-background"></span>`--cui-button-hover-background` | `color` | Enabled hover surfaces. | `Derived color mix.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-active-background"></span>`--cui-button-active-background` | `color` | Enabled active surfaces. | `Derived stronger color mix.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-focus-color"></span>`--cui-button-focus-color` | `color` | Both focus-visible outlines. | `Highlight` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-radius"></span>`--cui-button-radius` | `length` | Source Button radius used by the joined fallback. | `0.5rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-font-weight"></span>`--cui-button-font-weight` | `font-weight` | Both Button labels. | `600` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-gap"></span>`--cui-button-gap` | `length` | Primary content-region gaps. | `0.5rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-disabled-opacity"></span>`--cui-button-disabled-opacity` | `number` | Disabled Button content opacity. | `0.48` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-height"></span>`--cui-button-height` | `length` | Both Button minimum block size. | `Size-derived length.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-inline-padding"></span>`--cui-button-inline-padding` | `length` | Primary inline padding. | `Size-derived length.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-block-padding"></span>`--cui-button-block-padding` | `length` | Both Button block padding. | `Size-derived length.` |
| <span id="split-button-css-csplit-button-css-variables-cui-button-font-size"></span>`--cui-button-font-size` | `length` | Both Button font size. | `Size-derived length.` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-background"></span>`--cui-menu-background` | `color` | Root and submenu surfaces. | `Canvas` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-foreground"></span>`--cui-menu-foreground` | `color` | Menu item text. | `CanvasText` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-muted-color"></span>`--cui-menu-muted-color` | `color` | Menu descriptions, labels, and shortcuts. | `color-mix(in srgb, current foreground 72%, transparent)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-border-color"></span>`--cui-menu-border-color` | `color` | Menu surface and separator boundaries. | `color-mix(in srgb, CanvasText 18%, transparent)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-border-width"></span>`--cui-menu-border-width` | `length` | Menu surface boundary width. | `1px` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-radius"></span>`--cui-menu-radius` | `length` | Menu surface corners. | `0.75rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-shadow"></span>`--cui-menu-shadow` | `shadow` | Root Menu elevation. | `0 0.75rem 2rem rgb(15 23 42 / 18%)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-submenu-shadow"></span>`--cui-menu-submenu-shadow` | `shadow` | Nested Menu elevation. | `0 1rem 2.5rem rgb(15 23 42 / 22%)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-inline-size"></span>`--cui-menu-inline-size` | `length` | Preferred Menu width. | `14rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-min-inline-size"></span>`--cui-menu-min-inline-size` | `length` | Minimum useful submenu corridor. | `10rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-max-inline-size"></span>`--cui-menu-max-inline-size` | `length` | Viewport-safe Menu width. | `calc(100dvi - 1rem)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-max-block-size"></span>`--cui-menu-max-block-size` | `length` | Menu scroll limit. | `min(24rem, calc(100dvb - 1rem))` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-padding"></span>`--cui-menu-padding` | `length` | Menu surface edge spacing. | `0.375rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-item-block-size"></span>`--cui-menu-item-block-size` | `length` | Menu item minimum height. | `Size-derived.` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-item-padding-inline"></span>`--cui-menu-item-padding-inline` | `length` | Menu item inline spacing. | `Size-derived.` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-item-gap"></span>`--cui-menu-item-gap` | `length` | Menu item-region gap. | `0.625rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-item-radius"></span>`--cui-menu-item-radius` | `length` | Menu item corners. | `0.5rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-hover-background"></span>`--cui-menu-hover-background` | `color` | Menu pointer-hover fill. | `color-mix(in srgb, CanvasText 8%, transparent)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-focus-background"></span>`--cui-menu-focus-background` | `color` | Focused Menu item fill. | `light-dark(#175cd3, #84adff)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-focus-foreground"></span>`--cui-menu-focus-foreground` | `color` | Focused Menu item content. | `light-dark(#ffffff, #101828)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-focus-outline-color"></span>`--cui-menu-focus-outline-color` | `color` | Menu item focus-visible outline. | `light-dark(#175cd3, #84adff)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-danger-color"></span>`--cui-menu-danger-color` | `color` | Destructive Menu item content. | `light-dark(#b42318, #fda29b)` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-disabled-opacity"></span>`--cui-menu-disabled-opacity` | `number` | Disabled Menu content opacity. | `0.5` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-offset"></span>`--cui-menu-offset` | `length` | Root Menu anchor gap. | `0.375rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-submenu-offset"></span>`--cui-menu-submenu-offset` | `length` | Nested Menu anchor gap. | `0.25rem` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-duration"></span>`--cui-menu-duration` | `time` | Menu entry and exit duration. | `120ms` |
| <span id="split-button-css-csplit-button-css-variables-cui-menu-easing"></span>`--cui-menu-easing` | `easing` | Menu entry and exit curve. | `cubic-bezier(0.2, 0.8, 0.2, 1)` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSplitButton attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="split-button-attribute-csplit-button-root-attributes-role"></span>`role` | Root | `"group"` | Groups the dominant action and its related Menu Button. |
| <span id="split-button-attribute-csplit-button-root-attributes-aria-label"></span>`aria-label` | Root | `non-whitespace string` | Uses the required group label. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-variant"></span>`data-variant` | Root | `"solid" | "outline" | "ghost"` ([`CButtonVariant`](#split-button-interface-button-variant)) | Mirrors effective common presentation. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-intent"></span>`data-intent` | Root | `five CButton intents` ([`CButtonIntent`](#split-button-interface-button-intent)) | Mirrors effective common semantic color. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` ([`CButtonSize`](#split-button-interface-button-size)) | Mirrors effective Button and Menu geometry. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-block"></span>`data-block` | Root | `present | absent` | Present when the group fills available inline size. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Mirrors the common disabled override. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-primary-disabled"></span>`data-primary-disabled` | Root | `present | absent` | Mirrors browser-effective primary disabledness. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-menu-disabled"></span>`data-menu-disabled` | Root | `present | absent` | Mirrors browser-effective Menu Button disabledness. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-loading"></span>`data-loading` | Root | `present | absent` | Mirrors effective primary pending state. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-loading-position"></span>`data-loading-position` | Root | `"start" | "center" | "end"` ([`CButtonLoadingPos`](#split-button-interface-button-loading-pos)) | Mirrors primary loading placement. |
| <span id="split-button-attribute-csplit-button-root-attributes-data-open"></span>`data-open` | Root | `present | absent` | Mirrors committed root Menu visibility. |

</div>

#### CSplitButton attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="split-button-attribute-csplit-button-primary-attributes-id"></span>`id` | Primary Button | `root ID plus -primary` | Uses the exact owned primary identity. |
| <span id="split-button-attribute-csplit-button-primary-attributes-type"></span>`type` | Primary Button | `"button" | "submit" | "reset"` ([`CButtonType`](#split-button-interface-button-type)) | Preserves the authored native action. |
| <span id="split-button-attribute-csplit-button-primary-attributes-disabled"></span>`disabled` | Primary Button | `present | absent` | Represents effective native disabledness and the no-JavaScript loading fallback. |
| <span id="split-button-attribute-csplit-button-primary-attributes-aria-busy"></span>`aria-busy` | Primary Button | `"true" | absent` | Present only while primary work is pending. |
| <span id="split-button-attribute-csplit-button-primary-attributes-aria-disabled"></span>`aria-disabled` | Primary Button | `"true" | absent` | Present while disabled or loading. |
| <span id="split-button-attribute-csplit-button-primary-attributes-data-disabled"></span>`data-disabled` | Primary Button | `present | absent` | Mirrors effective disabledness. |
| <span id="split-button-attribute-csplit-button-primary-attributes-data-loading"></span>`data-loading` | Primary Button | `present | absent` | Mirrors effective pending state. |
| <span id="split-button-attribute-csplit-button-primary-attributes-data-variant"></span>`data-variant` | Primary Button | `three CButton variants` ([`CButtonVariant`](#split-button-interface-button-variant)) | Mirrors presentation strength. |
| <span id="split-button-attribute-csplit-button-primary-attributes-data-intent"></span>`data-intent` | Primary Button | `five CButton intents` ([`CButtonIntent`](#split-button-interface-button-intent)) | Mirrors semantic color. |
| <span id="split-button-attribute-csplit-button-primary-attributes-data-size"></span>`data-size` | Primary Button | `three CButton sizes` ([`CButtonSize`](#split-button-interface-button-size)) | Mirrors geometry. |
| <span id="split-button-attribute-csplit-button-primary-attributes-data-loading-position"></span>`data-loading-position` | Primary Button | `three positions` ([`CButtonLoadingPos`](#split-button-interface-button-loading-pos)) | Mirrors pending-indicator placement. |

</div>

#### CSplitButton attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-id"></span>`id` | Menu Button | `root ID plus -menu-trigger` | Uses the exact owned Menu Button identity. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-type"></span>`type` | Menu Button | `"button"` | Prevents Form submission in every state. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-aria-label"></span>`aria-label` | Menu Button | `non-whitespace string` | Uses menu_label as the explicit secondary action name. |
| <span id="split-button-attribute-csplit-button-menu-attributes-aria-haspopup"></span>`aria-haspopup` | Menu Button | `"menu"` | Announces the popup kind. |
| <span id="split-button-attribute-csplit-button-menu-attributes-aria-controls"></span>`aria-controls` | Menu Button | `Menu surface IDREF` | References the owned root Menu surface. |
| <span id="split-button-attribute-csplit-button-menu-attributes-aria-expanded"></span>`aria-expanded` | Menu Button | `"true" | "false"` | Mirrors logical root Menu state. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-disabled"></span>`disabled` | Menu Button | `present | absent` | Mirrors effective native Menu disabledness. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-data-disabled"></span>`data-disabled` | Menu Button | `present | absent` | Styles effective Menu disabledness. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-data-variant"></span>`data-variant` | Menu Button | `three CButton variants` ([`CButtonVariant`](#split-button-interface-button-variant)) | Mirrors presentation strength. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-data-intent"></span>`data-intent` | Menu Button | `five CButton intents` ([`CButtonIntent`](#split-button-interface-button-intent)) | Mirrors semantic color. |
| <span id="split-button-attribute-csplit-button-menu-attributes-trigger-data-size"></span>`data-size` | Menu Button | `three CButton sizes` ([`CButtonSize`](#split-button-interface-button-size)) | Mirrors geometry. |
| <span id="split-button-attribute-csplit-button-menu-attributes-surface-id"></span>`id` | Root Menu surface | `root ID plus -menu` | Uses the exact owned Menu surface identity. |
| <span id="split-button-attribute-csplit-button-menu-attributes-popover"></span>`popover` | Root and submenu Menu surfaces | `"manual"` | Uses native top-layer presence with Citry dismissal. |
| <span id="split-button-attribute-csplit-button-menu-attributes-menu-role"></span>`role` | Root and submenu Menu surfaces | `"menu"` | Exposes application Menu semantics. |
| <span id="split-button-attribute-csplit-button-menu-attributes-menu-aria-labelledby"></span>`aria-labelledby` | Root Menu surface | `Menu Button IDREF` | Names the root Menu from its trigger. |
| <span id="split-button-attribute-csplit-button-menu-attributes-menu-data-open"></span>`data-open` | Root and submenu Menu surfaces | `present | absent` | Mirrors logical Menu visibility. |
| <span id="split-button-attribute-csplit-button-menu-attributes-data-placement"></span>`data-placement` | Root Menu surface | `six logical placement strings` ([`CMenuPlacement`](#split-button-interface-menu-placement)) | Mirrors the requested root placement. |
| <span id="split-button-attribute-csplit-button-menu-attributes-data-match-width"></span>`data-match-width` | Root Menu surface | `present | absent` | Indicates clamped full-root width matching. |
| <span id="split-button-attribute-csplit-button-menu-attributes-menu-data-size"></span>`data-size` | Root Menu surface | `three sizes` ([`CButtonSize`](#split-button-interface-button-size)) | Mirrors effective Menu item geometry. |

</div>

#### CSplitButton attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="split-button-attribute-csplit-button-reused-menu-item-attributes-aria-describedby"></span>`aria-describedby` | Menu item root | `description IDREF | absent` | Uses CMenu's optional separate item description. |
| <span id="split-button-attribute-csplit-button-reused-menu-item-attributes-aria-checked"></span>`aria-checked` | Checkbox or radio item Button | `"false" | "true" | "mixed"` | Uses the effective CMenu choice state; radio items never use mixed. |
| <span id="split-button-attribute-csplit-button-reused-menu-item-attributes-data-checked"></span>`data-checked` | Checkbox or radio item Button | `"false" | "true" | "mixed"` | Mirrors the effective CMenu choice state for styling. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSplitButton selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="split-button-selector-csplit-button-selectors-split-button"></span>`[data-citry-ui-part="split-button"]` | Root div | Labelled group and class, style, and attrs destination. |
| <span id="split-button-selector-csplit-button-selectors-split-button-primary"></span>`[data-citry-ui-part="split-button-primary"]` | Primary native Button | Dominant action and primary_attrs destination. |
| <span id="split-button-selector-csplit-button-selectors-split-button-primary-start"></span>`[data-citry-ui-part="split-button-primary-start"]` | Optional decorative wrapper | Primary logical-start content. |
| <span id="split-button-selector-csplit-button-selectors-split-button-primary-content"></span>`[data-citry-ui-part="split-button-primary-content"]` | Required content wrapper | Visible dominant action content. |
| <span id="split-button-selector-csplit-button-selectors-split-button-primary-end"></span>`[data-citry-ui-part="split-button-primary-end"]` | Optional decorative wrapper | Primary logical-end content. |
| <span id="split-button-selector-csplit-button-selectors-split-button-primary-loading-indicator"></span>`[data-citry-ui-part="split-button-primary-loading-indicator"]` | Stable decorative wrapper | Primary pending indicator. |
| <span id="split-button-selector-csplit-button-selectors-split-button-menu-trigger"></span>`[data-citry-ui-part="split-button-menu-trigger"]` | Secondary native Button | Menu activation and trigger_attrs destination. |
| <span id="split-button-selector-csplit-button-selectors-split-button-menu-indicator"></span>`[data-citry-ui-part="split-button-menu-indicator"]` | Decorative span | Logical-down Menu indicator. |
| <span id="split-button-selector-csplit-button-selectors-menu"></span>`[data-citry-ui-part="menu"]` | Root or submenu Menu surface | Popover presence and collection focus. |
| <span id="split-button-selector-csplit-button-selectors-menu-item"></span>`[data-citry-ui-part="menu-item"]` | Command, link, checkbox, or radio root | Menu item styling. |
| <span id="split-button-selector-csplit-button-selectors-menu-item-start"></span>`[data-citry-ui-part="menu-item-start"]` | Decorative item wrapper | Item logical-start content. |
| <span id="split-button-selector-csplit-button-selectors-menu-item-label"></span>`[data-citry-ui-part="menu-item-label"]` | Visible item label | Layout and exact owned label target. |
| <span id="split-button-selector-csplit-button-selectors-menu-item-description"></span>`[data-citry-ui-part="menu-item-description"]` | Optional description | Supporting text and accessible description. |
| <span id="split-button-selector-csplit-button-selectors-menu-item-end"></span>`[data-citry-ui-part="menu-item-end"]` | Decorative item wrapper | Shortcut or logical-end content. |
| <span id="split-button-selector-csplit-button-selectors-menu-choice-indicator"></span>`[data-citry-ui-part="menu-choice-indicator"]` | Decorative choice marker | Checkbox and radio state. |
| <span id="split-button-selector-csplit-button-selectors-menu-group"></span>`[data-citry-ui-part="menu-group"]` | Labelled group root | Generic command grouping. |
| <span id="split-button-selector-csplit-button-selectors-menu-group-label"></span>`[data-citry-ui-part="menu-group-label"]` | Visible group label | Exact group name and layout. |
| <span id="split-button-selector-csplit-button-selectors-menu-radio-group"></span>`[data-citry-ui-part="menu-radio-group"]` | Radio group root | Exclusive choice grouping. |
| <span id="split-button-selector-csplit-button-selectors-menu-separator"></span>`[data-citry-ui-part="menu-separator"]` | Horizontal separator | Collection division. |
| <span id="split-button-selector-csplit-button-selectors-menu-submenu"></span>`[data-citry-ui-part="menu-submenu"]` | Neutral submenu wrapper | Child trigger and surface ownership. |
| <span id="split-button-selector-csplit-button-selectors-menu-submenu-trigger"></span>`[data-citry-ui-part="menu-submenu-trigger"]` | Nested Menu Button | Submenu activation and placement anchor. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="split-button-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="split-button-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="split-button-interface-button-type"></span>`CButtonType` | `Literal["button", "submit", "reset"]` |
| <span id="split-button-interface-button-variant"></span>`CButtonVariant` | `Literal["solid", "outline", "ghost"]` |
| <span id="split-button-interface-button-intent"></span>`CButtonIntent` | `Literal["primary", "neutral", "success", "warn", "danger"]` |
| <span id="split-button-interface-button-size"></span>`CButtonSize` | `Literal["sm", "md", "lg"]` |
| <span id="split-button-interface-button-loading-pos"></span>`CButtonLoadingPos` | `Literal["start", "center", "end"]` |
| <span id="split-button-interface-menu-placement"></span>`CMenuPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |

</div>

<span id="split-button-interface-csplit-button-default-slot-data"></span>

#### `CSplitButtonDefaultSlotData`

Empty dataclass: `{}`.

<span id="split-button-interface-csplit-button-start-slot-data"></span>

#### `CSplitButtonStartSlotData`

Empty dataclass: `{}`.

<span id="split-button-interface-csplit-button-end-slot-data"></span>

#### `CSplitButtonEndSlotData`

Empty dataclass: `{}`.

<span id="split-button-interface-csplit-button-loading-slot-data"></span>

#### `CSplitButtonLoadingSlotData`

Empty dataclass: `{}`.

<span id="split-button-interface-csplit-button-menu-slot-data"></span>

#### `CSplitButtonMenuSlotData`

Empty dataclass: `{}`.

<span id="split-button-interface-csplit-button-open-change-detail"></span>

#### `CMenuOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="split-button-interface-csplit-button-open-change-detail-reason"></span>`reason` | `"trigger" | "escape" | "outside" | "focus-outside" | "tab" | "action" | "native" | "disabled" | "ancestor"` | - | Cause of the requested or forced visibility change. |
| <span id="split-button-interface-csplit-button-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client Boolean owns desired Menu state. |
| <span id="split-button-interface-csplit-button-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether native or structural safety overrides owner refusal. |
| <span id="split-button-interface-csplit-button-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Browser source associated with the change. |

</div>

<span id="split-button-interface-csplit-button-action-detail"></span>

#### `CMenuActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="split-button-interface-csplit-button-action-detail-kind"></span>`kind` | `"command" | "checkbox" | "radio"` | - | Activated semantic Menu item kind. |
| <span id="split-button-interface-csplit-button-action-detail-item"></span>`item` | `Element` | - | Activated Menu item root. |
| <span id="split-button-interface-csplit-button-action-detail-event"></span>`event` | `Event` | - | Native Menu activation event. |
| <span id="split-button-interface-csplit-button-action-detail-path"></span>`path` | `list[str]` | - | Canonical ancestor-submenu path from the SplitButton root Menu. |

</div>

### Translation keys

-