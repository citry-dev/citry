---
title: CommandPalette
url: https://citry.dev/v/0.4.4/ui-library/components/command-palette/
description: "Search and run grouped application commands in a modal dialog."
---
# CommandPalette

Use `CCommandPalette` for a finite collection of application commands that
people can search and run without leaving their current task. It combines a
native modal Dialog, one editable combobox, and grouped listbox options. The
application still owns command registration, authorization, routing, and side
effects.

## Open and run a command

Pass immutable records through `entries`, give the Dialog a visible `label`,
and handle values with `onAction`. The activator slot receives
`activator_attrs` and `activator_disabled`. Spread the complete attribute map
on one ordinary native activator. For `CButton`, also pass
`c-disabled="activator_disabled"` because Button owns its disabled state.


### Open and run a command

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/basic-command-palette/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class BasicCommandPalette(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="open-settings",
                    label="Open settings",
                    keywords=("preferences",),
                    shortcut="Ctrl ,",
                ),
                CCommandPaletteCommand(value="create-project", label="Create project"),
                CCommandPaletteCommand(value="invite-teammate", label="Invite teammate"),
            )
        }

    template = """
      <section
        class="command-palette-basic"
        x-data="{lastAction:'none',lastQuery:'',lastOpen:'closed'}"
      >
        <h2>Workspace commands</h2>
        <p>Search a small set of actions without leaving the current task.</p>
        <c-CCommandPalette
          label="Workspace commands"
          c-entries="commands"
          $c-props="{
            onAction:(value)=>lastAction=value,
            onQueryChange:(value)=>lastQuery=value,
            onOpenChange:(value)=>lastOpen=value ? 'open' : 'closed',
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton
              variant="solid"
              c-disabled="activator_disabled"
              c-attrs="activator_attrs"
            >
              Open command palette
            </c-CButton>
          </c-fill>
        </c-CCommandPalette>
        <output aria-live="polite">
          State: <span x-text="lastOpen">closed</span>;
          query: <span x-text="lastQuery || 'empty'">empty</span>;
          action: <span x-text="lastAction">none</span>
        </output>
      </section>
    """

    css = """
      :where(.command-palette-basic) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-basic h2, .command-palette-basic p) { margin: 0; }
    """


preview = BasicCommandPalette()

preview  # noqa: B018
````


Commands are callback-only options. They are not links, selected form values,
or Menu items. Use a native navigation list or Menu when people need link
semantics, modifier keys, a browser context menu, or copyable destinations.

## Build records in Python

`CCommandPaletteCommand`, `CCommandPaletteGroup`, and
`CCommandPaletteSeparator` are frozen value records. They do not render alone.
Command values stay globally unique across top-level entries and groups.
Separators are visual boundaries between top-level regions.


### Build command records in Python

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/python-command-records/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import (
    CCommandPalette,
    CCommandPaletteCommand,
    CCommandPaletteGroup,
    CCommandPaletteSeparator,
)

citry.register_library(citry_ui)


class PythonCommandRecords(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        entries = (
            CCommandPaletteGroup(
                label="Project navigation",
                commands=(
                    CCommandPaletteCommand(value="project-overview", label="Open project overview"),
                    CCommandPaletteCommand(value="project-files", label="Browse project files"),
                ),
            ),
            CCommandPaletteSeparator(),
            CCommandPaletteGroup(
                label="Draft actions",
                commands=(
                    CCommandPaletteCommand(value="save-draft", label="Save draft", shortcut="Ctrl S"),
                    CCommandPaletteCommand(
                        value="delete-draft",
                        label="Delete draft",
                        description="Moves this draft to Trash",
                        intent="danger",
                    ),
                ),
            ),
        )
        return {
            "python_palette": CCommandPalette(
                label="Project commands",
                entries=entries,
                open=True,
            )
        }

    template = """
      <section class="command-palette-records">
        <h2>Frozen Python records</h2>
        <p>The rendered palette preserves group, separator, and command order.</p>
        {{ python_palette }}
      </section>
    """

    css = """
      :where(.command-palette-records) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-records h2, .command-palette-records p) { margin: 0; }
    """


preview = PythonCommandRecords()

preview  # noqa: B018
````


## Search labels and aliases

Filtering normalizes labels, keywords, and the exact query with NFKC, collapses
Unicode whitespace, trims, and applies locale-neutral lowercase. A command
matches when the whole normalized query appears in its label or one keyword.
Descriptions, shortcut hints, values, and slot content are not searched.
Matches keep their server order and are never fuzzy-ranked.


### Search aliases and empty results

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/search-and-empty/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class SearchAndEmpty(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="theme",
                    label="Choose theme",
                    keywords=("appearance", "color mode"),
                ),
                CCommandPaletteCommand(
                    value="light-mode",
                    label="Use light appearance",
                    keywords=("theme", "color mode"),
                ),
                CCommandPaletteCommand(
                    value="dark-mode",
                    label="Use dark appearance",
                    keywords=("theme", "color mode"),
                ),
                CCommandPaletteCommand(
                    value="managed-theme",
                    label="Use managed appearance",
                    keywords=("theme",),
                    disabled=True,
                ),
            )
        }

    template = """
      <section
        class="command-palette-search"
        x-data="{open:true,query:'theme'}"
      >
        <h2>Exact substring search</h2>
        <div role="group" aria-label="Search examples">
          <button type="button" @click="query='appearance'">Search appearance</button>
          <button type="button" @click="query='zz'">Show no match</button>
          <button type="button" @click="query='managed'">Show a disabled match</button>
          <button type="button" @click="query=''">Clear search</button>
        </div>
        <c-CCommandPalette
          label="Appearance commands"
          c-entries="commands"
          empty_label="No appearance commands match"
          $c-props="{
            open,
            query,
            onOpenChange:(value)=>open=value,
            onQueryChange:(value)=>query=value,
          }"
        />
        <output>Owner query: <span x-text="query || 'empty'">theme</span></output>
      </section>
    """

    css = """
      :where(.command-palette-search) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-search h2) { margin: 0; }
      :where(.command-palette-search [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
    """


preview = SearchAndEmpty()

preview  # noqa: B018
````


## Show disabled commands and shortcut hints

Disabled commands remain visible and searchable, expose disabled option state,
and are skipped by active navigation. `shortcut` is presentational text only.
The component never registers that key combination.


### Show disabled commands and shortcut hints

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/disabled-and-shortcuts/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class DisabledAndShortcuts(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="deploy-production",
                    label="Deploy production",
                    description="Unavailable until checks pass",
                    shortcut="Ctrl D",
                    disabled=True,
                ),
                CCommandPaletteCommand(value="view-logs", label="View logs", shortcut="Ctrl L"),
                CCommandPaletteCommand(
                    value="delete-environment",
                    label="Delete environment",
                    shortcut="Shift Delete",
                    intent="danger",
                ),
            )
        }

    template = """
      <section
        class="command-palette-disabled"
        dir="rtl"
        x-data="{open:true,disabled:false,loop:true,last:'none'}"
      >
        <h2>Deployment commands</h2>
        <div role="group" aria-label="Palette settings">
          <label><input type="checkbox" x-model="disabled" /> Disable palette</label>
          <label><input type="checkbox" x-model="loop" /> Loop navigation</label>
        </div>
        <c-CCommandPalette
          label="Deployment commands"
          c-entries="commands"
          size="lg"
          $c-props="{
            open,
            disabled,
            loop,
            onOpenChange:(value)=>open=value,
            onAction:(value)=>last=value,
          }"
        />
        <output aria-live="polite">Action: <span x-text="last">none</span></output>
      </section>
    """

    css = """
      :where(.command-palette-disabled) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-disabled h2) { margin: 0; }
      :where(.command-palette-disabled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      @media (forced-colors: active) {
        :where(.command-palette-disabled output) { border: 1px solid CanvasText; }
      }
    """


preview = DisabledAndShortcuts()

preview  # noqa: B018
````


Use `intent="danger"` to give a destructive command visual emphasis. It does
not authorize the action or bypass disabled state.

## Add safe visual adornments

The `item_start` and `item_end` slots receive immutable
`CCommandPaletteItemSlotData`. Their output is decorative, inert, and hidden
from the accessibility tree. Keep the owned label and description as the
command's complete semantic content. Interactive controls, links, meaningful
images, form controls, and custom elements are rejected.


### Add safe visual adornments

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/command-adornments/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class CommandAdornments(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="create-release",
                    label="Create release",
                    description="Prepare notes and artifacts",
                    keywords=("publish",),
                ),
                CCommandPaletteCommand(
                    value="open-preview",
                    label="Open preview",
                    description="Inspect the latest deployment",
                    keywords=("beta",),
                ),
            )
        }

    template = """
      <section class="command-palette-adornments" x-data="{open:true,last:'none'}">
        <h2>Release commands with decoration</h2>
        <c-CCommandPalette
          label="Release commands"
          c-entries="commands"
          $c-props="{
            open,
            onOpenChange:(value)=>open=value,
            onAction:(value)=>last=value,
          }"
        >
          <c-fill
            name="item_start"
            data="{ value, label, description, keywords, shortcut, disabled, close_on_action, intent }"
          >
            <span class="command-palette-adornments__icon">◆</span>
          </c-fill>
          <c-fill
            name="item_end"
            data="{ value, label, description, keywords, shortcut, disabled, close_on_action, intent }"
          >
            <span class="command-palette-adornments__badge">Beta</span>
          </c-fill>
        </c-CCommandPalette>
        <output aria-live="polite">Action: <span x-text="last">none</span></output>
      </section>
    """

    css = """
      :where(.command-palette-adornments) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-adornments h2) { margin: 0; }
      :where(.command-palette-adornments__badge) {
        padding: 0.125rem 0.375rem;
        border: 1px solid currentColor;
        border-radius: 999px;
        font-size: 0.6875rem;
      }
      :where(.command-palette-adornments__icon) { color: light-dark(#175cd3, #84adff); }
    """


preview = CommandAdornments()

preview  # noqa: B018
````


## Control open state and query text

Client `open` and `query` values own independent axes while supplied. User
edits and dismissals are requests through `onQueryChange` and `onOpenChange`.
If the owner retains its old value, the input, results, active command, focus,
and Dialog remain on that accepted state.


### Control open state and query text

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/controlled-command-palette/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class ControlledCommandPalette(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(value="workspace-alpha", label="Switch to Alpha workspace"),
                CCommandPaletteCommand(value="workspace-bravo", label="Switch to Bravo workspace"),
                CCommandPaletteCommand(value="workspace-charlie", label="Switch to Charlie workspace"),
            )
        }

    template = """
      <section
        class="command-palette-controlled"
        x-data="{
          open:true,
          query:'work',
          controlOpen:true,
          controlQuery:true,
          acceptClose:false,
          acceptQuery:false,
          requests:[],
        }"
      >
        <h2>Switch workspace</h2>
        <div role="group" aria-label="Controlled palette settings">
          <label><input type="checkbox" x-model="acceptClose" /> Accept close</label>
          <label><input type="checkbox" x-model="acceptQuery" /> Accept query edits</label>
          <button type="button" @click="controlOpen=false">Release open control</button>
          <button type="button" @click="controlQuery=false">Release query control</button>
          <button type="button" @click="controlOpen=true;open=true">Open from owner</button>
        </div>
        <c-CCommandPalette
          label="Switch workspace"
          c-entries="commands"
          $c-props="{
            open:controlOpen ? open : null,
            query:controlQuery ? query : null,
            onOpenChange:(value,detail)=>{
              requests.push(`open:${value}:${detail.reason}`);
              if (!controlOpen || value || acceptClose) open=value;
            },
            onQueryChange:(value,detail)=>{
              requests.push(`query:${value}:${detail.reason}`);
              if (!controlQuery || acceptQuery || detail.reason==='close') query=value;
            },
          }"
        />
        <output aria-live="polite">
          Owner: <span x-text="open ? 'open' : 'closed'">open</span>;
          query: <span x-text="query || 'empty'">work</span>;
          requests: <span x-text="requests.slice(-3).join(' | ') || 'none'">none</span>
        </output>
      </section>
    """

    css = """
      :where(.command-palette-controlled) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-controlled h2) { margin: 0; }
      :where(.command-palette-controlled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        align-items: center;
      }
    """


preview = ControlledCommandPalette()

preview  # noqa: B018
````


A completed close clears the uncontrolled query exactly once. A declined
controlled close preserves it. Releasing a controlled value with `null` or by
omitting it continues from the last accepted fallback, never rejected browser
text or the original server seed.

## Choose action and close policy

`onAction(value, detail)` runs synchronously before an optional close request.
The root `close_on_action` default can be overridden by one command. Callback
return values are ignored. If the callback throws, the close step does not run.
If it deliberately moves focus, that connected focus destination wins over
Dialog return-focus behavior.


### Choose action and close policy

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/command-actions/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class CommandActions(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="copy-id",
                    label="Copy ID",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(
                    value="toggle-sidebar",
                    label="Toggle sidebar",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(
                    value="delete-draft",
                    label="Delete draft",
                    intent="danger",
                ),
            )
        }

    template = """
      <section
        class="command-palette-actions"
        x-data="{open:true,events:[],throwNext:false,moveFocus:false}"
      >
        <h2>Action transaction</h2>
        <div role="group" aria-label="Action behavior">
          <label><input type="checkbox" x-model="throwNext" /> Throw in next action</label>
          <label><input type="checkbox" x-model="moveFocus" /> Move owner focus</label>
        </div>
        <button id="command-action-focus-target" type="button">Owner focus target</button>
        <c-CCommandPalette
          label="Draft commands"
          c-entries="commands"
          $c-props="{
            open,
            onOpenChange:(value,detail)=>{
              events.push(`open:${value}:${detail.reason}`);
              open=value;
            },
            onQueryChange:(value,detail)=>events.push(`query:${value}:${detail.reason}`),
            onAction:(value,detail)=>{
              events.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);
              if (moveFocus) document.getElementById('command-action-focus-target').focus();
              if (throwNext) { throwNext=false; throw new Error('Application action failed'); }
            },
          }"
        />
        <output aria-live="polite" x-text="events.slice(-4).join(' | ') || 'No actions yet'">
          No actions yet
        </output>
      </section>
    """

    css = """
      :where(.command-palette-actions) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-actions h2) { margin: 0; }
      :where(.command-palette-actions [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = CommandActions()

preview  # noqa: B018
````


## Own global shortcuts in the application

CommandPalette installs no document or window shortcut listener. The
application decides how `Mod+K` behaves around editable controls, composition,
multiple palettes, operating-system reservations, and shortcut collisions,
then updates controlled `open`.


### Own a global shortcut in the application

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/application-shortcut/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class ApplicationShortcut(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "help_commands": (
                CCommandPaletteCommand(value="help-docs", label="Open documentation"),
                CCommandPaletteCommand(value="help-support", label="Contact support"),
            ),
            "workspace_commands": (
                CCommandPaletteCommand(value="workspace-settings", label="Open workspace settings"),
                CCommandPaletteCommand(value="workspace-members", label="Manage workspace members"),
            ),
        }

    template = """
      <section
        class="command-palette-shortcut"
        x-data="{workspaceOpen:false,helpOpen:false,enabled:true,target:'workspace',opens:0}"
        @keydown.window="
          enabled
          && ($event.metaKey || $event.ctrlKey)
          && $event.key.toLowerCase()==='k'
          && !$event.isComposing
          && !['INPUT','TEXTAREA','SELECT'].includes($event.target.tagName)
          && !$event.target.isContentEditable
          && (
            $event.preventDefault(),
            opens++,
            target==='workspace' ? workspaceOpen=true : helpOpen=true
          )
        "
      >
        <h2>Application-owned Mod+K</h2>
        <p>Focus the app shell and press Mod+K. Editable targets stay native.</p>
        <label><input type="checkbox" x-model="enabled" /> Enable app shortcut</label>
        <label>
          Shortcut target
          <select x-model="target">
            <option value="workspace">Workspace palette</option>
            <option value="help">Help palette</option>
          </select>
        </label>
        <label>Unrelated input <input type="text" value="Mod+K stays editable here" /></label>
        <div contenteditable="true" role="textbox" aria-label="Editable application note">
          Contenteditable shortcut exclusion
        </div>

        <c-CCommandPalette
          label="Workspace commands"
          c-entries="workspace_commands"
          $c-props="{
            open:workspaceOpen,
            onOpenChange:(value)=>workspaceOpen=value,
          }"
        />
        <c-CCommandPalette
          label="Help commands"
          c-entries="help_commands"
          $c-props="{
            open:helpOpen,
            onOpenChange:(value)=>helpOpen=value,
          }"
        />
        <output>Handled app shortcuts: <span x-text="opens">0</span></output>
      </section>
    """

    css = """
      :where(.command-palette-shortcut) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-shortcut h2, .command-palette-shortcut p) { margin: 0; }
      :where(.command-palette-shortcut [contenteditable]) {
        min-block-size: 2.75rem;
        padding: 0.625rem;
        border: 1px solid currentColor;
      }
    """


preview = ApplicationShortcut()

preview  # noqa: B018
````


Shortcut text inside a command is a hint, not a binding or authorization rule.

## Keep Forms and IME input safe

The search input has no name, value contribution, reset behavior, or validity.
Every noncomposing Enter is contained before an ancestor Form can submit,
including empty and all-disabled results. During composition, Arrow, Enter,
and Escape remain with the IME and cannot navigate, act, clear, or dismiss.
The final committed text produces at most one query request.


### Keep Forms and IME input safe

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/form-safe-palette/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class FormSafePalette(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(value="focus-name", label="Focus display name"),
                CCommandPaletteCommand(value="submit-profile", label="Submit profile explicitly"),
                CCommandPaletteCommand(value="managed-setting", label="Managed setting", disabled=True),
            )
        }

    template = """
      <form
        id="command-palette-profile-form"
        class="command-palette-form"
        x-data="{open:false,submits:0,actions:0,query:''}"
        @submit.prevent="submits++"
      >
        <h2>Profile Form</h2>
        <label>Display name <input id="command-profile-name" name="display_name" value="Ada" /></label>
        <c-CCommandPalette
          label="Profile commands"
          c-entries="commands"
          $c-props="{
            open,
            query,
            onOpenChange:(value)=>open=value,
            onQueryChange:(value)=>query=value,
            onAction:(value)=>{
              actions++;
              if (value==='focus-name') document.getElementById('command-profile-name').focus();
              if (value==='submit-profile') {
                document.getElementById('command-palette-profile-form').requestSubmit();
              }
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton
              type="button"
              c-disabled="activator_disabled"
              c-attrs="activator_attrs"
            >Open profile commands</c-CButton>
          </c-fill>
        </c-CCommandPalette>
        <button type="submit">Save profile</button>
        <output aria-live="polite">
          Native submits: <span x-text="submits">0</span>;
          palette actions: <span x-text="actions">0</span>
        </output>
        <p>
          IME fixture: composition Enter and Escape remain native; ordinary
          palette Enter never submits this Form unless the action callback asks.
        </p>
      </form>
    """

    css = """
      :where(.command-palette-form) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-form h2, .command-palette-form p) { margin: 0; }
      :where(.command-palette-form label) { display: grid; gap: 0.25rem; }
    """


preview = FormSafePalette()

preview  # noqa: B018
````


An action callback may explicitly submit application data. The palette itself
never calls `requestSubmit()` or changes FormData.

## Compose with modal and anchored layers

CommandPalette uses the same native Dialog controller as `CDialog`. A nested
Dialog becomes the topmost focus owner. Popovers opened from a command close
before the palette. Escape closes only the deepest owned layer, and ordinary
close restores the eligible deep-focus invoker.


### Compose with modal and anchored layers

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/palette-layers/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class PaletteLayers(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="show-details",
                    label="Show deployment details",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(value="close-workflow", label="Finish workflow"),
            )
        }

    template = """
      <section
        class="command-palette-layers"
        x-data="{removed:false}"
        x-init="
          Alpine.store('commandPaletteLayers', {paletteOpen:false,popoverOpen:false});
          $nextTick(() => {
          const host=$refs.shadowHost;
          const fixture=$refs.shadowFixture;
          if (!host.shadowRoot && fixture) {
            Alpine.destroyTree(fixture);
            host.attachShadow({mode:'open'}).append(fixture);
            Alpine.initTree(fixture);
          }
          })
        "
      >
        <h2>Modal and anchored layers</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open deployment workflow</c-CButton>
          </c-fill>
          <c-fill name="title">Deployment workflow</c-fill>
          <c-fill name="default">
            <div class="command-palette-layers__workflow">
              <div x-ref="paletteOwner">
                <c-CCommandPalette
                  label="Deployment workflow commands"
                c-entries="commands"
                $c-props="{
                  open:$store.commandPaletteLayers.paletteOpen,
                  onOpenChange:(value)=>$store.commandPaletteLayers.paletteOpen=value,
                  onAction:(value)=>{
                    if (value==='show-details') $store.commandPaletteLayers.popoverOpen=true;
                  },
                    }"
                >
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton
                      c-disabled="activator_disabled"
                      c-attrs="activator_attrs"
                    >Open workflow commands</c-CButton>
                  </c-fill>
                </c-CCommandPalette>
              </div>

              <c-CPopover
                $c-props="{
                  open:$store.commandPaletteLayers.popoverOpen,
                  onOpenChange:(value)=>$store.commandPaletteLayers.popoverOpen=value,
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">Details anchor</c-CButton>
                </c-fill>
                <c-fill name="title">Deployment details</c-fill>
                <c-fill name="default">The latest deployment passed its checks.</c-fill>
              </c-CPopover>
              <button
                type="button"
                @click="$refs.paletteOwner.remove(); removed=true"
                x-show="!removed"
              >Remove palette owner</button>
              <output x-text="removed ? 'Palette owner removed' : 'Palette owner present'">
                Palette owner present
              </output>
            </div>
          </c-fill>
        </c-CDialog>
        <div x-ref="shadowHost" class="command-palette-layers__shadow-host">
          <div x-ref="shadowFixture">
            <c-CCommandPalette label="ShadowRoot commands" c-entries="commands">
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton
                  c-disabled="activator_disabled"
                  c-attrs="activator_attrs"
                >Open ShadowRoot fixture</c-CButton>
              </c-fill>
            </c-CCommandPalette>
          </div>
        </div>
      </section>
    """

    css = """
      :where(.command-palette-layers) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-layers h2) { margin: 0; }
      :where(.command-palette-layers__workflow) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
      :where(.command-palette-layers__shadow-host) {
        display: block;
        padding: 0.75rem;
        border: 1px solid currentColor;
      }
    """


preview = PaletteLayers()

preview  # noqa: B018
````


The Dialog stays in its authored Document or open ShadowRoot. Closed
ShadowRoots, cross-document adoption, invalid anatomy, and hostile ownership
changes fail closed.

## Adapt size, direction, and environment

`size` coordinates surface width, input height, and row density. Public
variables and part selectors support application styling. Logical layout keeps
start/end decoration correct in RTL, while vertical command order remains
unchanged.


### Inspect responsive and environment behavior

[Open the rendered preview](/v/0.4.4/ui-library/components/command-palette/_previews/command-palette-environment/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand, CCommandPaletteGroup

citry.register_library(citry_ui)


class CommandPaletteEnvironment(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteGroup(
                    label="Localized workspace administration",
                    commands=(
                        CCommandPaletteCommand(
                            value="archive-workspace",
                            label="Archive this exceptionally long localized workspace name",
                            description="Keeps a recoverable copy for organization administrators",
                        ),
                        CCommandPaletteCommand(
                            value="delete-workspace",
                            label="Delete workspace permanently",
                            description="This command cannot be undone",
                            intent="danger",
                        ),
                        CCommandPaletteCommand(
                            value="managed-workspace",
                            label="Transfer managed workspace",
                            disabled=True,
                        ),
                    ),
                ),
            )
        }

    template = """
      <section
        class="command-palette-environment"
        x-data="{open:true,size:'md',dark:false,rtl:false}"
        :class="dark ? 'command-palette-environment--dark' : ''"
        :dir="rtl ? 'rtl' : 'ltr'"
      >
        <h2>Responsive command environment</h2>
        <div role="group" aria-label="Environment controls">
          <label>
            Size
            <select x-model="size">
              <option value="sm">Small</option>
              <option value="md">Medium</option>
              <option value="lg">Large</option>
            </select>
          </label>
          <label><input type="checkbox" x-model="dark" /> Dark scheme</label>
          <label><input type="checkbox" x-model="rtl" /> RTL</label>
        </div>
        <c-CCommandPalette
          label="Localized workspace commands"
          c-entries="commands"
          c-style="{
            '--cui-command-palette-inline-size':'min(42rem, calc(100dvi - 1rem))',
            '--cui-command-palette-row-min-block-size':'3rem',
          }"
          $c-props="{
            open,
            size,
            onOpenChange:(value)=>open=value,
          }"
        />
        <p>
          Inspect sm, md, and lg at 200% and 400% zoom, narrow and wide widths,
          coarse pointer, virtual keyboard, reduced motion, forced colors, and print.
        </p>
      </section>
    """

    css = """
      :where(.command-palette-environment) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        color-scheme: light;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-environment--dark) {
        color-scheme: dark;
        background: Canvas;
      }
      :where(.command-palette-environment h2, .command-palette-environment p) { margin: 0; }
      :where(.command-palette-environment [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      @media (forced-colors: active) {
        :where(.command-palette-environment) { border: 1px solid CanvasText; }
      }
      @media print {
        :where(.command-palette-environment [role="group"]) { display: none; }
      }
    """


preview = CommandPaletteEnvironment()

preview  # noqa: B018
````


The active option stays visible at narrow widths, 200% and 400% zoom, with a
virtual keyboard, coarse pointer, text spacing, reduced motion, and forced
colors. The modal palette is hidden in print.

Without JavaScript, a server-closed palette stays closed. A server-open native
Dialog remains readable in document flow without claiming modality. Its search
input remains disabled and commands do not run, so it cannot submit an
ancestor Form or promise unavailable interaction.

## Distinguish callbacks from native events

`onOpenChange`, `onQueryChange`, and `onAction` are component callbacks passed
through `$c-props`. Native input, composition, keyboard, pointer, click,
Dialog cancel, and close events remain browser events. The family dispatches no
custom DOM event.

`attrs` target the native Dialog. `input_attrs` target the owned search input
and accept only attributes that cannot replace its identity, value, disabled
state, Form boundary, combobox relationships, or active descendant. Mappings
are copied once. Labels, descriptions, keywords, shortcut hints, and values are
escaped text, not HTML or authorized domain actions.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CCommandPalette server inputs

Server inputs are passed in a template through `<c-CCommandPalette ... />` or in Python
through `CCommandPalette(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 11rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="command-palette-input-ccommand-palette-server-inputs-entries"></span>`entries` | `Sequence[CCommandPaletteEntry]` ([`CCommandPaletteEntry`](#command-palette-interface-command-palette-entry)) | required | Snapshots and validates ordered command, group, and separator records. |
| <span id="command-palette-input-ccommand-palette-server-inputs-label"></span>`label` | `non-whitespace str` | required | Supplies the visible Dialog title and accessible name. |
| <span id="command-palette-input-ccommand-palette-server-inputs-id"></span>`id` | `str | None` | generated | Sets the Dialog identity and bases owned relationship IDs. |
| <span id="command-palette-input-ccommand-palette-server-inputs-open"></span>`open` | `bool` | `False` | Selects initial server and uncontrolled Dialog visibility. |
| <span id="command-palette-input-ccommand-palette-server-inputs-query"></span>`query` | `str` | `""` | Seeds the exact search text without server-side filtering. |
| <span id="command-palette-input-ccommand-palette-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables activation and force-closes an open palette. |
| <span id="command-palette-input-ccommand-palette-server-inputs-loop"></span>`loop` | `bool` | `True` | Wraps active Arrow navigation at the first and last eligible command. |
| <span id="command-palette-input-ccommand-palette-server-inputs-close-on-action"></span>`close_on_action` | `bool` | `True` | Sets the root action-close default that each command may override. |
| <span id="command-palette-input-ccommand-palette-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCommandPaletteSize`](#command-palette-interface-command-palette-size)) | `"md"` | Selects coordinated surface width and control density. |
| <span id="command-palette-input-ccommand-palette-server-inputs-placeholder"></span>`placeholder` | `str` | `"Search commands"` | Supplies visible search-input placeholder text. |
| <span id="command-palette-input-ccommand-palette-server-inputs-search-label"></span>`search_label` | `non-whitespace str` | `"Search commands"` | Supplies the visually hidden native label for the search input. |
| <span id="command-palette-input-ccommand-palette-server-inputs-empty-label"></span>`empty_label` | `non-whitespace str` | `"No commands found"` | Supplies the empty live-status fallback when the empty slot is omitted. |
| <span id="command-palette-input-ccommand-palette-server-inputs-close-label"></span>`close_label` | `non-whitespace str` | `"Close command palette"` | Supplies the built-in close Button accessible name. |
| <span id="command-palette-input-ccommand-palette-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#command-palette-interface-class-value)) | `None` | Adds classes to the native Dialog and merges them with attrs. |
| <span id="command-palette-input-ccommand-palette-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#command-palette-interface-style-value)) | `None` | Adds styles to the native Dialog and merges them with attrs. |
| <span id="command-palette-input-ccommand-palette-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed native Dialog attributes without replacing owned semantics or state. |
| <span id="command-palette-input-ccommand-palette-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed search-input attributes without replacing Form, value, focus, or ARIA ownership. |

</div>

#### CCommandPalette client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CCommandPalette />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="command-palette-input-ccommand-palette-client-inputs-open"></span>`open` | `boolean | null` | Releases control from committed visibility; null has the same effect. | Controls native Dialog visibility while supplied as a Boolean. |
| <span id="command-palette-input-ccommand-palette-client-inputs-query"></span>`query` | `string | null` | Releases control from the last accepted internal query fallback; null has the same effect. | Controls exact input text and filtering while supplied as a string. |
| <span id="command-palette-input-ccommand-palette-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the immutable server input. | Controls activation and forced closure. |
| <span id="command-palette-input-ccommand-palette-client-inputs-loop"></span>`loop` | `boolean` | Uses the immutable server input. | Controls Arrow navigation wrapping. |
| <span id="command-palette-input-ccommand-palette-client-inputs-close-on-action"></span>`closeOnAction` | `boolean` | Uses the immutable server input. | Controls the root action-close default. |
| <span id="command-palette-input-ccommand-palette-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCommandPaletteSize`](#command-palette-interface-command-palette-size)) | Uses the immutable server input. | Controls coordinated surface width and density. |
| <span id="command-palette-input-ccommand-palette-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Omission selects no visibility callback; null clears the last valid callback. | Receives user-authored and forced visibility requests. |
| <span id="command-palette-input-ccommand-palette-client-inputs-on-query-change"></span>`onQueryChange` | `function` | Omission selects no query callback; null clears the last valid callback. | Receives committed user input and accepted-close reset requests. |
| <span id="command-palette-input-ccommand-palette-client-inputs-on-action"></span>`onAction` | `function` | Omission selects no command callback; null clears the last valid callback. | Receives one eligible command activation before optional close. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCommandPalette slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="command-palette-slot-ccommand-palette-slots-activator"></span>`activator` | no | `{activator_attrs: dict[str, object], activator_disabled: bool}` | None. Bind the complete mapping to one ordinary native activator; for CButton also bind activator_disabled through disabled. |
| <span id="command-palette-slot-ccommand-palette-slots-item-start"></span>`item_start` | no | `CCommandPaletteItemSlotData` ([`CCommandPaletteItemSlotData`](#command-palette-interface-ccommand-palette-item-slot-data)) | None. Output is inert and accessibility-hidden visual decoration. |
| <span id="command-palette-slot-ccommand-palette-slots-item-end"></span>`item_end` | no | `CCommandPaletteItemSlotData` ([`CCommandPaletteItemSlotData`](#command-palette-interface-ccommand-palette-item-slot-data)) | Escaped shortcut text when supplied. Output is inert and accessibility-hidden. |
| <span id="command-palette-slot-ccommand-palette-slots-empty"></span>`empty` | no | `{}` | Escaped empty_label text. Output is inert and cannot contain interactive content. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CCommandPalette events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="command-palette-event-ccommand-palette-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CCommandPaletteOpenChangeDetail) => void` ([`CCommandPaletteOpenChangeDetail`](#command-palette-interface-ccommand-palette-open-change-detail)) | Activator, Escape, outside dismissal, close Button, action, native close, disabled transition, ancestor close, or owner request changes visibility. | `{reason, controlled, source}` ([`CCommandPaletteOpenChangeDetail`](#command-palette-interface-ccommand-palette-open-change-detail)) | Uncontrolled state commits before notification. Controlled state remains authoritative and may decline an ordinary close by retaining true. |
| <span id="command-palette-event-ccommand-palette-events-on-query-change"></span>`onQueryChange` | `(requestedQuery: string, detail: CCommandPaletteQueryChangeDetail) => void` ([`CCommandPaletteQueryChangeDetail`](#command-palette-interface-ccommand-palette-query-change-detail)) | A noncomposing user edit settles or an accepted close clears a nonempty query. | `{reason, closeReason, controlled, source}` ([`CCommandPaletteQueryChangeDetail`](#command-palette-interface-ccommand-palette-query-change-detail)) | Controlled input is request-only and restores every observable surface when the owner declines. Accepted close clears the internal fallback once. |
| <span id="command-palette-event-ccommand-palette-events-on-action"></span>`onAction` | `(value: string, detail: CCommandPaletteActionDetail) => void` ([`CCommandPaletteActionDetail`](#command-palette-interface-ccommand-palette-action-detail)) | An enabled visible active command receives unmodified Enter or an eligible option receives a plain click. | `{query, source, item, event, closeOnAction}` ([`CCommandPaletteActionDetail`](#command-palette-interface-ccommand-palette-action-detail)) | Runs synchronously before optional close; return values are ignored and an exception stops the close transaction. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCommandPalette CSS variables

Apply these variables to `CCommandPalette` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-backdrop"></span>`--cui-command-palette-backdrop` | `color` | Native modal backdrop. | `Theme overlay color.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-background"></span>`--cui-command-palette-background` | `color` | Dialog surface background. | `Theme surface color.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-foreground"></span>`--cui-command-palette-foreground` | `color` | Primary text. | `Theme foreground.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-muted"></span>`--cui-command-palette-muted` | `color` | Descriptions and shortcut hints. | `Theme muted foreground.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-border-color"></span>`--cui-command-palette-border-color` | `color` | Surface, input, and row boundaries. | `Theme border color.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-active-background"></span>`--cui-command-palette-active-background` | `color` | Active option background. | `Theme subtle accent.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-active-foreground"></span>`--cui-command-palette-active-foreground` | `color` | Active option text. | `Theme accent foreground.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-danger"></span>`--cui-command-palette-danger` | `color` | Danger command text. | `Theme danger color.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-radius"></span>`--cui-command-palette-radius` | `length` | Surface corner radius. | `0.875rem` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-shadow"></span>`--cui-command-palette-shadow` | `shadow` | Modal elevation. | `Theme overlay shadow.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-inline-size"></span>`--cui-command-palette-inline-size` | `length` | Preferred Dialog width. | `Size-derived.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-max-block-size"></span>`--cui-command-palette-max-block-size` | `length` | Viewport-constrained Dialog height. | `calc(100dvb - 2rem)` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-padding"></span>`--cui-command-palette-padding` | `length` | Outer surface spacing. | `0.75rem` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-gap"></span>`--cui-command-palette-gap` | `length` | Gap between surface regions. | `0.5rem` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-input-block-size"></span>`--cui-command-palette-input-block-size` | `length` | Search-control height. | `Size-derived.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-row-min-block-size"></span>`--cui-command-palette-row-min-block-size` | `length` | Command row minimum height. | `Size-derived; at least 2.75rem.` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-row-padding-inline"></span>`--cui-command-palette-row-padding-inline` | `length` | Command row horizontal inset. | `0.75rem` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-group-gap"></span>`--cui-command-palette-group-gap` | `length` | Spacing between command groups. | `0.5rem` |
| <span id="command-palette-css-ccommand-palette-css-variables-cui-command-palette-focus-ring"></span>`--cui-command-palette-focus-ring` | `color` | Visible keyboard focus ring. | `Theme focus color.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCommandPalette attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-id"></span>`id` | Native Dialog | `supplied or generated string` | Identifies the palette and bases all owned relationships. |
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-open"></span>`open` | Native Dialog | `present | absent` | Native Dialog visibility; enhanced open uses showModal. |
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-data-open"></span>`data-open` | Native Dialog | `present | absent` | Mirrors effective committed visibility. |
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-data-disabled"></span>`data-disabled` | Native Dialog | `present | absent` | Mirrors effective palette disabledness. |
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-data-size"></span>`data-size` | Native Dialog | `"sm" | "md" | "lg"` ([`CCommandPaletteSize`](#command-palette-interface-command-palette-size)) | Mirrors effective surface width and density. |
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-data-empty"></span>`data-empty` | Native Dialog | `present | absent` | Mirrors whether filtering exposes zero command results. |
| <span id="command-palette-attribute-ccommand-palette-dialog-attributes-aria-labelledby"></span>`aria-labelledby` | Native Dialog | `owned title IDREF` | Names the modal from its visible title. |

</div>

#### CCommandPalette attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="command-palette-attribute-ccommand-palette-input-attributes-type"></span>`type` | Search input | `"text"` | Avoids divergent native search Escape and clear behavior. |
| <span id="command-palette-attribute-ccommand-palette-input-attributes-role"></span>`role` | Search input | `"combobox"` | Exposes editable command filtering. |
| <span id="command-palette-attribute-ccommand-palette-input-attributes-aria-autocomplete"></span>`aria-autocomplete` | Search input | `"list"` | Announces list filtering without completing the input value. |
| <span id="command-palette-attribute-ccommand-palette-input-attributes-aria-controls"></span>`aria-controls` | Search input | `owned listbox IDREF` | References the result collection. |
| <span id="command-palette-attribute-ccommand-palette-input-attributes-aria-expanded"></span>`aria-expanded` | Search input | `"true" | "false"` | Mirrors effective result-surface visibility. |
| <span id="command-palette-attribute-ccommand-palette-input-attributes-aria-activedescendant"></span>`aria-activedescendant` | Search input | `eligible owned option IDREF | absent` | Exposes internal active navigation while DOM focus stays in the input. |
| <span id="command-palette-attribute-ccommand-palette-input-attributes-disabled"></span>`disabled` | Search input | `present | absent` | Keeps server fallback and effective disabled state natively safe. |

</div>

#### CCommandPalette attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="command-palette-attribute-ccommand-palette-command-attributes-option-role"></span>`role` | Command row | `"option"` | Exposes one callback-only command candidate. |
| <span id="command-palette-attribute-ccommand-palette-command-attributes-aria-selected"></span>`aria-selected` | Command row | `"true" | "false"` | Mirrors transient active-descendant state rather than an application value. |
| <span id="command-palette-attribute-ccommand-palette-command-attributes-aria-disabled"></span>`aria-disabled` | Command row | `"true" | absent` | Exposes an unavailable command. |
| <span id="command-palette-attribute-ccommand-palette-command-attributes-data-active"></span>`data-active` | Command row | `present | absent` | Mirrors internal active state. |
| <span id="command-palette-attribute-ccommand-palette-command-attributes-data-disabled"></span>`data-disabled` | Command row | `present | absent` | Mirrors immutable command disabledness. |
| <span id="command-palette-attribute-ccommand-palette-command-attributes-data-intent"></span>`data-intent` | Command row | `"default" | "danger"` ([`CCommandPaletteIntent`](#command-palette-interface-command-palette-intent)) | Mirrors immutable visual intent. |

</div>

#### CCommandPalette attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="command-palette-attribute-ccommand-palette-group-attributes-group-role"></span>`role` | Command group | `"group"` | Groups commands under one visible label. |
| <span id="command-palette-attribute-ccommand-palette-group-attributes-group-aria-labelledby"></span>`aria-labelledby` | Command group | `owned group-label IDREF` | Names the group from its visible label. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCommandPalette selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette"></span>`[data-citry-ui-part="command-palette"]` | Native Dialog | Modal owner and class_, style, and attrs destination. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-surface"></span>`[data-citry-ui-part="command-palette-surface"]` | Surface section | Contains every visual palette region. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-header"></span>`[data-citry-ui-part="command-palette-header"]` | Header | Lays out the title and close Button. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-title"></span>`[data-citry-ui-part="command-palette-title"]` | Heading | Provides visible Dialog name. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-close"></span>`[data-citry-ui-part="command-palette-close"]` | Button | Closes the current palette through shared Dialog policy. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-search"></span>`[data-citry-ui-part="command-palette-search"]` | Search landmark | Owns the native label and editable combobox. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-search-label"></span>`[data-citry-ui-part="command-palette-search-label"]` | Native label | Supplies the search input accessible name. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-input"></span>`[data-citry-ui-part="command-palette-input"]` | Text input | Owns query editing and active-descendant navigation. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-listbox"></span>`[data-citry-ui-part="command-palette-listbox"]` | Listbox | Owns visible command options and labelled groups. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-command"></span>`[data-citry-ui-part="command-palette-command"]` | Option row | Shows one callback-only command and its state. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-group"></span>`[data-citry-ui-part="command-palette-group"]` | Group section | Groups visible command options. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-group-label"></span>`[data-citry-ui-part="command-palette-group-label"]` | Group label | Names one visible group. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-separator"></span>`[data-citry-ui-part="command-palette-separator"]` | Accessibility-hidden hr | Separates visible top-level regions. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-empty"></span>`[data-citry-ui-part="command-palette-empty"]` | Live status | Announces and displays the empty result. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-item-start"></span>`[data-citry-ui-part="command-palette-item-start"]` | Inert leading wrapper | Displays accessibility-hidden visual decoration. |
| <span id="command-palette-selector-ccommand-palette-selectors-command-palette-item-end"></span>`[data-citry-ui-part="command-palette-item-end"]` | Inert trailing wrapper | Displays accessibility-hidden decoration or shortcut text. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="command-palette-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="command-palette-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="command-palette-interface-command-palette-entry"></span>`CCommandPaletteEntry` | `CCommandPaletteCommand | CCommandPaletteGroup | CCommandPaletteSeparator` |
| <span id="command-palette-interface-command-palette-intent"></span>`CCommandPaletteIntent` | `Literal["default", "danger"]` |
| <span id="command-palette-interface-command-palette-size"></span>`CCommandPaletteSize` | `Literal["sm", "md", "lg"]` |
| <span id="command-palette-interface-command-palette-action-source"></span>`CCommandPaletteActionSource` | `Literal["keyboard", "click"]` |
| <span id="command-palette-interface-command-palette-open-reason"></span>`CCommandPaletteOpenReason` | `Literal["trigger", "escape", "outside", "close-button", "action", "native", "disabled", "ancestor", "owner"]` |
| <span id="command-palette-interface-command-palette-query-reason"></span>`CCommandPaletteQueryReason` | `Literal["input", "close"]` |

</div>

<span id="command-palette-interface-ccommand-palette-command-record"></span>

#### `CCommandPaletteCommand`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="command-palette-interface-ccommand-palette-command-record-value"></span>`value` | `non-whitespace str` | - | Globally unique opaque application command identity. |
| <span id="command-palette-interface-ccommand-palette-command-record-label"></span>`label` | `non-whitespace str` | - | Visible owned command label and accessible name. |
| <span id="command-palette-interface-ccommand-palette-command-record-description"></span>`description` | `str | None` | - | Optional visible owned supporting description. |
| <span id="command-palette-interface-ccommand-palette-command-record-keywords"></span>`keywords` | `tuple[str, ...]` | - | Immutable search-only aliases; default is empty. |
| <span id="command-palette-interface-ccommand-palette-command-record-shortcut"></span>`shortcut` | `str | None` | - | Optional accessibility-hidden visual hint with no listener; default is null. |
| <span id="command-palette-interface-ccommand-palette-command-record-disabled"></span>`disabled` | `bool` | - | Immutable unavailable state; default is false. |
| <span id="command-palette-interface-ccommand-palette-command-record-close-on-action"></span>`close_on_action` | `bool | None` | - | Optional per-command close override; null uses the root policy. |
| <span id="command-palette-interface-ccommand-palette-command-record-intent"></span>`intent` | `CCommandPaletteIntent` ([`CCommandPaletteIntent`](#command-palette-interface-command-palette-intent)) | - | Visual default or danger emphasis; default is default. |

</div>

<span id="command-palette-interface-ccommand-palette-group-record"></span>

#### `CCommandPaletteGroup`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="command-palette-interface-ccommand-palette-group-record-label"></span>`label` | `non-whitespace str` | - | Visible accessible group label. |
| <span id="command-palette-interface-ccommand-palette-group-record-commands"></span>`commands` | `tuple[CCommandPaletteCommand, ...]` | - | Nonempty immutable command tuple; groups never nest. |

</div>

<span id="command-palette-interface-ccommand-palette-separator-record"></span>

#### `CCommandPaletteSeparator`

Empty dataclass: `{}`.

<span id="command-palette-interface-ccommand-palette-item-slot-data"></span>

#### `CCommandPaletteItemSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="command-palette-interface-ccommand-palette-item-slot-data-value"></span>`value` | `str` | - | Stable command identity. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-label"></span>`label` | `str` | - | Owned command label. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-description"></span>`description` | `str | None` | - | Optional owned description. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-keywords"></span>`keywords` | `tuple[str, ...]` | - | Immutable search aliases. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-shortcut"></span>`shortcut` | `str | None` | - | Optional visual shortcut hint. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-disabled"></span>`disabled` | `bool` | - | Immutable command disabledness. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-close-on-action"></span>`close_on_action` | `bool` | - | Effective command close policy after the root fallback. |
| <span id="command-palette-interface-ccommand-palette-item-slot-data-intent"></span>`intent` | `CCommandPaletteIntent` ([`CCommandPaletteIntent`](#command-palette-interface-command-palette-intent)) | - | Immutable visual intent. |

</div>

<span id="command-palette-interface-ccommand-palette-open-change-detail"></span>

#### `CCommandPaletteOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="command-palette-interface-ccommand-palette-open-change-detail-reason"></span>`reason` | `CCommandPaletteOpenReason` ([`CCommandPaletteOpenReason`](#command-palette-interface-command-palette-open-reason)) | - | Cause of the requested or committed visibility change. |
| <span id="command-palette-interface-ccommand-palette-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client Boolean owns desired visibility. |
| <span id="command-palette-interface-ccommand-palette-open-change-detail-source"></span>`source` | `object | null` | - | Connected owned origin when one remains available. |

</div>

<span id="command-palette-interface-ccommand-palette-query-change-detail"></span>

#### `CCommandPaletteQueryChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="command-palette-interface-ccommand-palette-query-change-detail-reason"></span>`reason` | `CCommandPaletteQueryReason` ([`CCommandPaletteQueryReason`](#command-palette-interface-command-palette-query-reason)) | - | User input or accepted-close reset. |
| <span id="command-palette-interface-ccommand-palette-query-change-detail-close-reason"></span>`closeReason` | `CCommandPaletteOpenReason | null` ([`CCommandPaletteOpenReason`](#command-palette-interface-command-palette-open-reason)) | - | Accepted close cause for reset; null for ordinary input. |
| <span id="command-palette-interface-ccommand-palette-query-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client string owns effective query text. |
| <span id="command-palette-interface-ccommand-palette-query-change-detail-source"></span>`source` | `object | null` | - | Owned input or accepted close origin when available. |

</div>

<span id="command-palette-interface-ccommand-palette-action-detail"></span>

#### `CCommandPaletteActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="command-palette-interface-ccommand-palette-action-detail-query"></span>`query` | `string` | - | Exact accepted effective query at activation time. |
| <span id="command-palette-interface-ccommand-palette-action-detail-source"></span>`source` | `CCommandPaletteActionSource` ([`CCommandPaletteActionSource`](#command-palette-interface-command-palette-action-source)) | - | Keyboard Enter or accepted click-handler path. |
| <span id="command-palette-interface-ccommand-palette-action-detail-item"></span>`item` | `object` | - | Exact owned option Element. |
| <span id="command-palette-interface-ccommand-palette-action-detail-event"></span>`event` | `object` | - | Triggering native browser event. |
| <span id="command-palette-interface-ccommand-palette-action-detail-close-on-action"></span>`closeOnAction` | `boolean` | - | Effective close policy for this action. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CCommandPalette translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="command-palette-translation-ccommand-palette-translations-placeholder"></span>`citry-ui-command-palette-placeholder` | Provides the search-field hint. | `None` | `placeholder` input | $c-tr updates `placeholder`. |
| <span id="command-palette-translation-ccommand-palette-translations-search-label"></span>`citry-ui-command-palette-search-label` | Labels the command search field. | `None` | `search_label` input | $c-tr updates text content. |
| <span id="command-palette-translation-ccommand-palette-translations-empty"></span>`citry-ui-command-palette-empty` | Reports that no commands match. | `None` | `empty_label` input or `empty` slot | $c-tr updates fallback text. |
| <span id="command-palette-translation-ccommand-palette-translations-close"></span>`citry-ui-command-palette-close` | Names the palette close control. | `None` | `close_label` input | $c-tr updates `aria-label`. |

</div>