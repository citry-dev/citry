"""Shared ContextMenu scenario used by repository quality tools."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component


def context_menu_states_component(app: Citry) -> type[Component]:
    """Create the reusable ContextMenu interaction and lifecycle scenario."""

    class CitryUiContextMenuLifecycle(Component):
        citry = app

        class Kwargs:
            morph_step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def refresh(self, state: Any) -> CitryUiContextMenuLifecycle:
                state.morph_step += 1
                component_type: Any = CitryUiContextMenuLifecycle
                return component_type(morph_step=state.morph_step)

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            if kwargs.morph_step < 2:
                lifecycle_key = "context-menu-quality-retained"
            elif kwargs.morph_step == 2:
                lifecycle_key = "context-menu-quality-replacement"
            elif kwargs.morph_step == 4:
                lifecycle_key = "context-menu-quality-restored-one"
            else:
                lifecycle_key = "context-menu-quality-restored-two"
            return {
                "include_lifecycle": kwargs.morph_step not in {3, 5},
                "lifecycle_key": lifecycle_key,
                "lifecycle_states": (
                    "lifecycle morph-target retained-root replacement-root removal restore cleanup "
                    "owner-token target-point-surface focus invocation"
                ),
                "morph_step": kwargs.morph_step,
            }

        template = """
          <section
            class="context-menu-quality__lifecycle"
            @c-quality-morph="refresh"
            x-data="{lifecycleNotices:0}"
          >
            <output hidden data-quality-morph-step>{{ morph_step }}</output>
            <c-if cond="include_lifecycle">
              <div>
                <c-CContextMenu
                  #c-key="lifecycle_key"
                  id="quality-context-menu-lifecycle"
                  aria_label="Lifecycle target actions"
                  c-attrs="{'data-quality-states':lifecycle_states}"
                  $c-props="{
                    onOpenChange:()=>lifecycleNotices += 1,
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div
                      class="context-menu-quality__target"
                      tabindex="0"
                      c-bind="target_attrs"
                    >Lifecycle generation {{ morph_step }}</div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="retain">Retained action</c-CMenuItem>
                    <c-CMenuItem value="replace">Replacement action</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </div>
            </c-if>
            <output aria-live="polite">
              Lifecycle callbacks:
              <span data-quality-lifecycle-notices x-text="lifecycleNotices">0</span>
            </output>
          </section>
        """

    class CitryUiContextMenuStates(Component):
        citry = app

        template = """
          <section
            class="citry-ui-quality-stack context-menu-quality"
            aria-labelledby="context-menu-states-title"
            x-data="{
              lastAction:'none',
              lastReason:'none',
              lastPoint:'none',
              controlled:true,
              controlledOpen:false,
              acceptClaim:true,
              targetClicks:0,
              submits:0,
            }"
          >
            <h1 id="context-menu-states-title">ContextMenu states</h1>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Application commands</h2>
                <c-CContextMenu
                  id="quality-context-menu-basic"
                  aria_label="Quality document actions"
                  c-attrs="{
                    'data-quality-states':
                      'closed open pointer keyboard command checkbox radio group '
                      'separator submenu danger typeahead md'
                  }"
                  $c-props="{
                    onOpenChange:(next,detail)=>{
                      lastReason=detail.reason;
                      lastPoint=`${Math.round(detail.clientX)},${Math.round(detail.clientY)}`;
                    },
                    onAction:(value,detail)=>
                      lastAction=`${detail.path.join('/') || 'root'}:${value}`,
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div
                      class="context-menu-quality__target"
                      tabindex="0"
                      c-bind="target_attrs"
                    >
                      <strong>Quarterly report.pdf</strong>
                      <span>Right click, Context Menu, or Shift+F10</span>
                    </div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="rename">Rename</c-CMenuItem>
                    <c-CMenuCheckboxItem
                      value="featured"
                      checked="mixed"
                    >
                      Featured
                    </c-CMenuCheckboxItem>
                    <c-CMenuRadioGroup
                      value="updated"
                    >
                      <c-fill name="label">Sort records</c-fill>
                      <c-fill name="default">
                        <c-CMenuRadioItem value="updated">Updated</c-CMenuRadioItem>
                        <c-CMenuRadioItem value="name">Name</c-CMenuRadioItem>
                      </c-fill>
                    </c-CMenuRadioGroup>
                    <c-CMenuSeparator />
                    <c-CMenuGroup>
                      <c-fill name="label">Export</c-fill>
                      <c-fill name="default">
                        <c-CMenuSubmenu value="formats">
                          <c-fill name="label">Format</c-fill>
                          <c-fill name="default">
                            <c-CMenuItem value="pdf">PDF</c-CMenuItem>
                            <c-CMenuSubmenu value="image">
                              <c-fill name="label">Image</c-fill>
                              <c-fill name="default">
                                <c-CMenuItem value="png">PNG</c-CMenuItem>
                              </c-fill>
                            </c-CMenuSubmenu>
                          </c-fill>
                        </c-CMenuSubmenu>
                      </c-fill>
                    </c-CMenuGroup>
                    <c-CMenuItem value="delete" intent="danger">Delete</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </article>

              <article>
                <h2>Controlled native-default claim</h2>
                <c-CContextMenu
                  id="quality-context-menu-controlled"
                  aria_label="Controlled diagram actions"
                  c-attrs="{
                    'data-quality-states':
                      'controlled claim accept refuse release external same-open no-flash'
                  }"
                  $c-props="{
                    open:controlled ? controlledOpen : null,
                    onOpenChange:(next,detail)=>{
                      lastReason=detail.reason;
                      lastPoint=`${Math.round(detail.clientX)},${Math.round(detail.clientY)}`;
                      if (!next) {
                        controlledOpen=false;
                        return;
                      }
                      if (!acceptClaim) return false;
                      controlledOpen=true;
                      return true;
                    },
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div
                      class="context-menu-quality__target"
                      tabindex="0"
                      c-bind="target_attrs"
                    >Controlled diagram</div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="inspect">Inspect layers</c-CMenuItem>
                    <c-CMenuItem value="duplicate">Duplicate diagram</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
                <div class="context-menu-quality__controls">
                  <button
                    type="button"
                    @click="acceptClaim=!acceptClaim"
                  >Toggle claim acceptance</button>
                  <button
                    type="button"
                    @click="controlledOpen=true"
                  >External open</button>
                  <button
                    type="button"
                    @click="controlledOpen=false"
                  >External close</button>
                  <button
                    type="button"
                    @click="controlled=false"
                  >Release control</button>
                </div>
              </article>
            </div>

            <fieldset disabled>
              <legend>Disabled enhancement fallback</legend>
              <c-CContextMenu
                id="quality-context-menu-disabled"
                aria_label="Disabled target actions"
                c-open="True"
                size="sm"
                c-attrs="{
                  'data-quality-states':
                    'disabled fieldset-disabled sm no-js server-open-fallback'
                }"
              >
                <c-fill name="target" data="{ target_attrs }">
                  <button
                    class="context-menu-quality__target"
                    type="button"
                    c-bind="target_attrs"
                  >Disabled target</button>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="disabled-action">Unavailable action</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>
            </fieldset>

            <article>
              <h2>Protected native paths</h2>
              <c-CContextMenu
                id="quality-context-menu-native"
                aria_label="Native boundary actions"
                  c-attrs="{
                    'data-quality-states':
                      'native selection input editable link image media '
                      'custom-element closed-shadow-marker open-shadow iframe shift-secondary'
                }"
              >
                <c-fill name="target" data="{ target_attrs }">
                  <div
                    class="context-menu-quality__native-target"
                    tabindex="0"
                    c-bind="target_attrs"
                  >
                    <p data-quality-selection>
                      Select these words to preserve the browser copy path.
                    </p>
                    <input aria-label="Native title" value="Editable title" />
                    <div contenteditable="true">Editable note</div>
                    <a href="#context-menu-quality-destination">Native link</a>
                    <img
                      alt="Native image path"
                      width="64"
                      height="42"
                      src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
                    />
                    <video controls aria-label="Native media path"></video>
                    <context-menu-quality-host>Custom element</context-menu-quality-host>
                    <div
                      data-citry-context-menu-native
                      x-init="const root=$el.attachShadow({mode:'closed'});root.textContent='Closed shadow content'"
                    >Marked opaque host</div>
                    <div
                      data-quality-open-shadow
                      x-init="const root=$el.attachShadow({mode:'open'});root.textContent='Open shadow selection text'"
                    >Open shadow host</div>
                    <iframe
                      title="Separate quality document"
                      srcdoc="<p>Child document browser menu.</p>"
                    ></iframe>
                    <div data-quality-eligible tabindex="0">Eligible file row</div>
                  </div>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="archive">Archive file row</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>
            </article>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Touch and pen hold</h2>
                <form @submit.prevent="submits += 1">
                  <c-CContextMenu
                    id="quality-context-menu-touch"
                    aria_label="Touch submit actions"
                    c-attrs="{
                      'data-quality-states':
                        'touch pen long-press 700ms 10px scroll cancel derived-click submit reset token'
                    }"
                  >
                    <c-fill name="target" data="{ target_attrs }">
                      <button
                        class="context-menu-quality__target"
                        type="submit"
                        @click="targetClicks += 1"
                        c-bind="target_attrs"
                      >Hold submit target</button>
                    </c-fill>
                    <c-fill name="menu">
                      <c-CMenuItem value="preview">Preview submission</c-CMenuItem>
                    </c-fill>
                  </c-CContextMenu>
                </form>
                <output>
                  clicks <span data-quality-target-clicks x-text="targetClicks">0</span>;
                  submits <span data-quality-submits x-text="submits">0</span>
                </output>
              </article>

              <article>
                <h2>Deepest nested target</h2>
                <c-CContextMenu
                  id="quality-context-menu-outer"
                  aria_label="Outer record actions"
                  c-attrs="{'data-quality-states':'nested outer logical-layer'}"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div
                      class="context-menu-quality__target"
                      tabindex="0"
                      c-bind="target_attrs"
                    >
                      Outer target
                      <c-CContextMenu
                        id="quality-context-menu-inner"
                        aria_label="Inner badge actions"
                        c-attrs="{
                          'data-quality-states':
                            'nested inner deepest-boundary shadow-root modal ancestor'
                        }"
                      >
                        <c-fill name="target" data="{ target_attrs as inner_target_attrs }">
                          <span
                            class="context-menu-quality__badge"
                            tabindex="0"
                            c-bind="inner_target_attrs"
                          >Inner target</span>
                        </c-fill>
                        <c-fill name="menu">
                          <c-CMenuItem value="inner">Inspect inner target</c-CMenuItem>
                        </c-fill>
                      </c-CContextMenu>
                    </div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="outer">Inspect outer target</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </article>
            </div>

            <article
              class="context-menu-quality__positioning"
              dir="rtl"
            >
              <h2>Point positioning and styling</h2>
              <div class="context-menu-quality__transform">
                <c-CContextMenu
                  id="quality-context-menu-positioning"
                  class_="quality-context-menu-brand"
                  aria_label="Positioning target actions"
                  size="lg"
                  c-style="{
                    '--cui-menu-background':'#173c4c',
                    '--cui-menu-foreground':'#eefaff',
                    '--cui-menu-border-color':'#72b5ce',
                  }"
                  c-attrs="{
                    'data-quality-states':
                      'point corners transform filter contain visual-viewport rtl ltr '
                      'zoom-400 narrow variables selector forced-colors reduced-motion print lg brand'
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div
                      class="context-menu-quality__target"
                      dir="ltr"
                      tabindex="0"
                      c-bind="target_attrs"
                    >Transformed target with opposite local direction</div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="inspect">Inspect point</c-CMenuItem>
                    <c-CMenuItem value="long">
                      A deliberately long viewport-collision command
                    </c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </div>
            </article>

            <c-CitryUiContextMenuLifecycle
              #c-key="'context-menu-quality-lifecycle-owner'"
            />

            <output id="context-menu-quality-log" aria-live="polite">
              action <span data-quality-action x-text="lastAction">none</span>;
              reason <span data-quality-reason x-text="lastReason">none</span>;
              point <span data-quality-point x-text="lastPoint">none</span>
            </output>
            <span id="context-menu-quality-destination">Native link destination</span>
          </section>
        """

        css = """
          :where(.context-menu-quality article) {
            display: grid;
            gap: 0.75rem;
            align-content: start;
            min-inline-size: 0;
          }

          :where(.context-menu-quality h2,
            .context-menu-quality p) {
            margin: 0;
          }

          :where(.context-menu-quality__target) {
            display: grid;
            gap: 0.25rem;
            padding: 1rem;
            border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
            border-radius: 0.75rem;
            background: Canvas;
            color: CanvasText;
            text-align: start;
          }

          :where(.context-menu-quality__target:focus-visible,
            .context-menu-quality__badge:focus-visible,
            .context-menu-quality__native-target:focus-visible) {
            outline: 2px solid Highlight;
            outline-offset: 2px;
          }

          :where(.context-menu-quality__controls) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.625rem;
          }

          :where(.context-menu-quality__native-target) {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
            gap: 0.625rem;
            padding: 1rem;
            border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
            border-radius: 1rem;
          }

          :where(.context-menu-quality__native-target > *) {
            min-inline-size: 0;
            padding: 0.5rem;
            background: color-mix(in srgb, Highlight 7%, Canvas);
          }

          :where(.context-menu-quality__native-target iframe) {
            inline-size: 100%;
            min-block-size: 5rem;
          }

          :where(.context-menu-quality__badge) {
            display: inline-block;
            inline-size: fit-content;
            margin-block-start: 0.5rem;
            padding: 0.375rem 0.625rem;
            border-radius: 999px;
            background: color-mix(in srgb, Highlight 15%, Canvas);
          }

          :where(.context-menu-quality__positioning) {
            min-block-size: 18rem;
            padding: 1rem;
            overflow: hidden;
            color-scheme: dark;
            background: #102b38;
            color: #eefaff;
          }

          :where(.context-menu-quality__transform) {
            inline-size: fit-content;
            margin-block-start: 1rem;
            padding: 1rem;
            filter: saturate(0.9);
            transform: translateX(1rem);
            contain: paint;
          }

          .context-menu-quality
          .quality-context-menu-brand[data-citry-ui-part="context-menu"]
          [data-citry-ui-part="menu"] {
            border-width: 2px;
          }

          @media (forced-colors: active) {
            :where(.context-menu-quality__positioning) {
              border: 1px solid CanvasText;
              background: Canvas;
              color: CanvasText;
            }
          }

          @media print {
            :where(.context-menu-quality__positioning) {
              background: transparent;
              color: black;
            }
          }
        """

    return CitryUiContextMenuStates
