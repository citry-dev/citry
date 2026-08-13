"""Shared CommandPalette scenario used by repository quality tools."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component
from citry_ui.components.ccommand_palette import (
    CCommandPaletteCommand,
    CCommandPaletteGroup,
    CCommandPaletteSeparator,
)


def _baseline_entries() -> tuple[object, ...]:
    """Build the immutable baseline collection used by lifecycle checks."""
    return (
        CCommandPaletteGroup(
            label="Workspace",
            commands=(
                CCommandPaletteCommand(
                    value="open-settings",
                    label="Open settings",
                    keywords=("preferences", "configuration"),
                    shortcut="Ctrl ,",
                ),
                CCommandPaletteCommand(value="create-project", label="Create project"),
                CCommandPaletteCommand(
                    value="invite-teammate",
                    label="Invite teammate",
                    description="Send a workspace invitation",
                ),
            ),
        ),
        CCommandPaletteSeparator(),
        CCommandPaletteGroup(
            label="Draft",
            commands=(
                CCommandPaletteCommand(
                    value="copy-id",
                    label="Copy draft ID",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(
                    value="managed-command",
                    label="Managed command",
                    disabled=True,
                    shortcut="Ctrl M",
                ),
                CCommandPaletteCommand(
                    value="delete-draft",
                    label="Delete draft",
                    intent="danger",
                ),
            ),
        ),
    )


def _changed_entries() -> tuple[object, ...]:
    """Change records while preserving stable identities needed for handoff."""
    return (
        CCommandPaletteGroup(
            label="Workspace tools",
            commands=(
                CCommandPaletteCommand(value="create-project", label="Create a new project"),
                CCommandPaletteCommand(
                    value="open-settings",
                    label="Open workspace settings",
                    keywords=("preferences", "appearance"),
                    shortcut="Ctrl ,",
                ),
                CCommandPaletteCommand(
                    value="archive-project",
                    label="Archive project",
                    intent="danger",
                ),
            ),
        ),
        CCommandPaletteSeparator(),
        CCommandPaletteCommand(value="copy-id", label="Copy project ID", close_on_action=False),
    )


def command_palette_states_component(app: Citry) -> type[Component]:
    """Create the reusable interaction, Form, layer, and lifecycle scenario."""

    class CitryUiCommandPaletteLifecycle(Component):
        citry = app

        class Kwargs:
            morph_step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def refresh(self, state: Any) -> CitryUiCommandPaletteLifecycle:
                state.morph_step += 1
                component_type: Any = CitryUiCommandPaletteLifecycle
                return component_type(morph_step=state.morph_step)

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            lifecycle_key = (
                "command-palette-quality-retained"
                if kwargs.morph_step < 3
                else f"command-palette-quality-replacement-{kwargs.morph_step}"
            )
            return {
                "include_lifecycle": kwargs.morph_step not in {4, 6},
                "lifecycle_entries": _baseline_entries() if kwargs.morph_step < 2 else _changed_entries(),
                "lifecycle_key": lifecycle_key,
                "morph_step": kwargs.morph_step,
            }

        template = """
          <section
            class="command-palette-quality__lifecycle"
            @c-quality-morph="refresh"
            x-data="{
              lifecycleOpen:false,
              lifecycleQuery:'open',
              lifecycleActions:0,
              lifecycleQueries:0,
              lifecycleOpens:0,
            }"
          >
            <output hidden data-quality-morph-step>{{ morph_step }}</output>
            <h2>Signed lifecycle</h2>
            <button type="button" @click="lifecycleOpen=true">Open lifecycle palette</button>
            <button type="button" @c-click="refresh">Advance signed palette lifecycle</button>
            <c-if cond="include_lifecycle">
              <c-CCommandPalette
                #c-key="lifecycle_key"
                id="quality-command-palette-lifecycle"
                label="Lifecycle commands"
                c-entries="lifecycle_entries"
                c-attrs="{
                  'data-quality-states':
                    'lifecycle retained-equal changed-records replacement-root removal restore owner-token',
                }"
                $c-props="{
                  open:lifecycleOpen,
                  query:lifecycleQuery,
                  onOpenChange:(value)=>{
                    lifecycleOpens++;
                    lifecycleOpen=value;
                  },
                  onQueryChange:(value)=>{
                    lifecycleQueries++;
                    lifecycleQuery=value;
                  },
                  onAction:()=>lifecycleActions++,
                }"
              />
            </c-if>
            <output id="quality-command-palette-lifecycle-output">
              <span x-text="lifecycleOpen ? 'open' : 'closed'">closed</span>|
              <span x-text="lifecycleQuery || 'empty'">open</span>|
              <span x-text="lifecycleActions">0</span>|
              <span x-text="lifecycleQueries">0</span>|
              <span x-text="lifecycleOpens">0</span>
            </output>
          </section>
        """

    class CitryUiCommandPaletteStates(Component):
        citry = app

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:  # noqa: ARG002
            return {
                "baseline_entries": _baseline_entries(),
                "changed_entries": _changed_entries(),
            }

        template = """
          <section
            class="citry-ui-quality-stack command-palette-quality"
            aria-labelledby="command-palette-quality-title"
            x-data="{
              basicOpen:false,
              basicQuery:'',
              basicAction:'none',
              controlledOpen:false,
              controlledQuery:'open',
              acceptClose:false,
              acceptQuery:false,
              actionOpen:false,
              actionLog:[],
              submits:0,
              shortcutOpens:0,
            }"
            x-init="$nextTick(() => {
              const host=$refs.shadowHost;
              const fixture=$refs.shadowFixture;
              if (!host.shadowRoot && fixture) {
                Alpine.destroyTree(fixture);
                host.attachShadow({mode:'open'}).append(fixture);
                Alpine.initTree(fixture);
              }
            })"
            @keydown.window="
              ($event.metaKey || $event.ctrlKey)
              && $event.key.toLowerCase()==='k'
              && !$event.isComposing
              && !['INPUT','TEXTAREA','SELECT'].includes($event.target.tagName)
              && !$event.target.isContentEditable
              && ($event.preventDefault(), shortcutOpens++, basicOpen=true)
            "
          >
            <h1 id="command-palette-quality-title">CommandPalette states</h1>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Basic grouped commands</h2>
                <c-CCommandPalette
                  id="quality-command-palette-basic"
                  label="Workspace commands"
                  c-entries="baseline_entries"
                  c-attrs="{
                    'data-quality-states':
                      'closed open dialog searchbox combobox listbox group option separator '
                      + 'active-descendant filter keywords empty disabled default danger shortcut-hint '
                      + 'start-adornment end-adornment accepted-close app-shortcut '
                      + 'sm md lg rtl narrow zoom-200 zoom-400 reduced-motion forced-colors print',
                  }"
                  $c-props="{
                    open:basicOpen,
                    query:basicQuery,
                    onOpenChange:(value)=>basicOpen=value,
                    onQueryChange:(value)=>basicQuery=value,
                    onAction:(value)=>basicAction=value,
                  }"
                >
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton
                      c-disabled="activator_disabled"
                      c-attrs="activator_attrs"
                    >Open workspace commands</c-CButton>
                  </c-fill>
                  <c-fill
                    name="item_start"
                    data="{ value, label, description, keywords, shortcut, disabled, close_on_action, intent }"
                  >
                    <span class="command-palette-quality__icon">◆</span>
                  </c-fill>
                  <c-fill
                    name="item_end"
                    data="{ value, label, description, keywords, shortcut, disabled, close_on_action, intent }"
                  >
                    <span class="command-palette-quality__badge">Beta</span>
                  </c-fill>
                  <c-fill name="empty">No workspace commands match</c-fill>
                </c-CCommandPalette>
                <output id="quality-command-palette-basic-output">
                  <span x-text="basicOpen ? 'open' : 'closed'">closed</span>|
                  <span x-text="basicQuery || 'empty'">empty</span>|
                  <span x-text="basicAction">none</span>|
                  <span x-text="shortcutOpens">0</span>
                </output>
              </article>

              <article x-data="{controlledOpen:false,controlledQuery:'open',acceptClose:false,acceptQuery:false}">
                <h2>Controlled ownership</h2>
                <label><input type="checkbox" x-model="acceptClose" /> Accept close</label>
                <label><input type="checkbox" x-model="acceptQuery" /> Accept query</label>
                <button type="button" @click="controlledOpen=true">Restore controlled open</button>
                <c-CCommandPalette
                  id="quality-command-palette-controlled"
                  label="Controlled workspace commands"
                  c-entries="baseline_entries"
                  c-attrs="{
                    'data-quality-states':
                      'controlled-open controlled-query declined-close accepted-close null-release',
                  }"
                  $c-props="{
                    open:controlledOpen,
                    query:controlledQuery,
                    onOpenChange:(value)=>{
                      if (value || acceptClose) controlledOpen=value;
                    },
                    onQueryChange:(value,detail)=>{
                      if (acceptQuery || detail.reason==='close') controlledQuery=value;
                    },
                  }"
                />
                <output id="quality-command-palette-controlled-output">
                  <span x-text="controlledOpen ? 'open' : 'closed'">closed</span>|
                  <span x-text="controlledQuery">open</span>
                </output>
              </article>

              <article>
                <h2>Action and close policy</h2>
                <button id="quality-command-palette-owner-focus" type="button">Owner focus target</button>
                <c-CCommandPalette
                  id="quality-command-palette-actions"
                  label="Action transaction commands"
                  c-entries="baseline_entries"
                  c-attrs="{
                    'data-quality-states':
                      'action-once stay-open focus-winner',
                  }"
                  $c-props="{
                    open:actionOpen,
                    onOpenChange:(value,detail)=>{
                      actionLog.push(`open:${value}:${detail.reason}`);
                      actionOpen=value;
                    },
                    onAction:(value,detail)=>{
                      actionLog.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);
                      if (value==='copy-id') {
                        document.getElementById('quality-command-palette-owner-focus').focus();
                      }
                    },
                  }"
                />
                <button type="button" @click="actionOpen=true">Restore action palette</button>
                <output id="quality-command-palette-action-output" x-text="actionLog.slice(-4).join('|')">
                  No action
                </output>
              </article>
            </div>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Native Form and IME safety</h2>
                <form id="quality-command-palette-form" @submit.prevent="submits++">
                  <label>Profile name <input name="profile_name" value="Ada" /></label>
                  <c-CCommandPalette
                    id="quality-command-palette-form-palette"
                    label="Profile commands"
                    c-entries="changed_entries"
                    c-attrs="{
                      'data-quality-states':
                        'form implicit-submit ime composition',
                    }"
                    $c-props="{
                      onAction:(value)=>{
                        if (value==='copy-id') {
                          document.getElementById('quality-command-palette-form').requestSubmit();
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
                  <button type="submit" name="intent" value="publish">Publish profile</button>
                </form>
                <output id="quality-command-palette-submit-output" x-text="submits">0</output>
              </article>

              <article>
                <h2>Dialog and anchored layers</h2>
                <c-CDialog>
                  <c-fill name="activator" data="{ activator_attrs }">
                    <c-CButton c-attrs="activator_attrs">Open parent Dialog</c-CButton>
                  </c-fill>
                  <c-fill name="title">Parent workflow</c-fill>
                  <c-fill name="default">
                    <c-CCommandPalette
                      id="quality-command-palette-layers"
                      label="Nested workflow commands"
                      c-entries="changed_entries"
                      c-attrs="{
                        'data-quality-states':
                          'nested-dialog anchored-layer resource-cleanup',
                      }"
                    >
                      <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                        <c-CButton
                          c-disabled="activator_disabled"
                          c-attrs="activator_attrs"
                        >Open nested palette</c-CButton>
                      </c-fill>
                    </c-CCommandPalette>
                    <c-CPopover>
                      <c-fill name="activator" data="{ activator_attrs }">
                        <c-CButton variant="outline" c-attrs="activator_attrs">Popover anchor</c-CButton>
                      </c-fill>
                      <c-fill name="title">Owned anchored detail</c-fill>
                      <c-fill name="default">Owned anchored detail</c-fill>
                    </c-CPopover>
                  </c-fill>
                </c-CDialog>
                <div
                  id="quality-command-palette-shadow-host"
                  x-ref="shadowHost"
                >
                  <div x-ref="shadowFixture">
                    <c-CCommandPalette
                      label="Open ShadowRoot commands"
                      c-entries="changed_entries"
                      c-attrs="{'data-quality-states':'open-shadow-root'}"
                    />
                  </div>
                </div>
              </article>
            </div>

            <c-CitryUiCommandPaletteLifecycle #c-key="'command-palette-quality-lifecycle-owner'" />
          </section>
        """

        css = """
          :where(.command-palette-quality) {
            color: CanvasText;
            font-family: ui-sans-serif, system-ui, sans-serif;
          }
          :where(.command-palette-quality article) {
            display: grid;
            gap: 0.75rem;
            align-content: start;
          }
          :where(.command-palette-quality h1, .command-palette-quality h2) { margin: 0; }
          :where(.command-palette-quality form) {
            display: grid;
            gap: 0.625rem;
            justify-items: start;
          }
          :where(.command-palette-quality__icon) { color: light-dark(#175cd3, #84adff); }
          :where(.command-palette-quality__badge) {
            padding: 0.125rem 0.375rem;
            border: 1px solid currentColor;
            border-radius: 999px;
            font-size: 0.6875rem;
          }
          @media (forced-colors: active) {
            :where(.command-palette-quality output) { border: 1px solid CanvasText; }
          }
          @media print {
            :where(.command-palette-quality button, .command-palette-quality output) { display: none; }
          }
        """

    return CitryUiCommandPaletteStates
