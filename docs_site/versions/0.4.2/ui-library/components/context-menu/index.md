---
title: ContextMenu
url: https://citry.dev/v/0.4.2/ui-library/components/context-menu/
description: "Offer target-relative application commands while preserving browser context actions."
---
# ContextMenu

Use `CContextMenu` for application commands that belong to one target region.
It opens the existing Citry Menu at a trusted pointer point or at a visible
point derived from the focused target. It does not create a second Menu model.

Keep the browser's native context menu when copy, spelling, editing, links,
images, media, or embedded content are the primary job. The
[`contextmenu` event](https://w3c.github.io/uievents/#event-type-contextmenu),
the [browser event guide](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event),
and the [APG Menu pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
describe the platform contracts that ContextMenu joins. The safest native
browser path is to render no ContextMenu for content that mainly needs browser
commands.

## Start with a contextual action

Bind every value from the required `target` slot to exactly one direct native
Element. Make that target, or a useful descendant, focusable so keyboard users
can press the Context Menu key or Shift+F10.


```citry-html
<c-CContextMenu aria_label="Document actions">
  <c-fill name="target" data="{ target_attrs }">
    <div c-bind="target_attrs" tabindex="0">
      Quarterly report.pdf
    </div>
  </c-fill>
  <c-fill name="menu">
    <c-CMenuItem value="rename">Rename</c-CMenuItem>
    <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
  </c-fill>
</c-CContextMenu>
```


The target keeps its native semantics. ContextMenu does not add `role=button`,
`aria-expanded`, or Menu Button keys. A native focusable descendant is better
than adding an extra wrapper Tab stop when the content already has one.


### Start with a contextual action

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/basic-context-menu/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CButton, CContextMenu, CMenuItem, CMenuSeparator

citry.register_library(citry_ui)


class BasicContextMenu(Component):
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
            "python_menu": CContextMenu(
                aria_label="Invoice actions",
                slots={
                    "target": lambda data: CButton(
                        variant="outline",
                        attrs=data.target_attrs,
                        slots={"default": "Invoices"},
                    ),
                    "menu": (
                        CMenuItem(value="rename", slots={"default": "Rename"}),
                        CMenuItem(value="duplicate", slots={"default": "Duplicate"}),
                        CMenuSeparator(),
                        CMenuItem(
                            value="delete",
                            intent="danger",
                            slots={"default": "Delete"},
                        ),
                    ),
                },
            ),
        }

    template = """
      <section
        class="context-menu-basic"
        x-data
      >
        <article>
          <h3>Template file</h3>
          <c-CContextMenu
            aria_label="Document actions"
            $c-props="{onAction: onAction}"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-basic__file"
                tabindex="0"
                c-bind="target_attrs"
              >
                <strong>Quarterly report.pdf</strong>
                <span>2.4 MB · Updated today</span>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="rename">Rename</c-CMenuItem>
              <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
              <c-CMenuSeparator />
              <c-CMenuItem value="delete" intent="danger">Delete</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </article>

        <article>
          <h3>Python composition</h3>
          {{ python_menu }}
        </article>

        <output aria-live="polite" x-text="lastActionLabel">
          Last action: No action yet
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.lastActionLabel = "Last action: No action yet";
        scope.onAction = (value) => {
          scope.lastActionLabel = `Last action: ${value}`;
        };
      });
    """

    css = """
      :where(.context-menu-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 1rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-basic article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
      }

      :where(.context-menu-basic h3) {
        margin: 0;
      }

      :where(.context-menu-basic__file) {
        display: grid;
        gap: 0.25rem;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.context-menu-basic__file:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-basic output) {
        grid-column: 1 / -1;
      }
    """


preview = BasicContextMenu()

preview  # noqa: B018
````


## Keep one Menu model

The `menu` slot accepts the existing `CMenuItem`, `CMenuCheckboxItem`,
`CMenuRadioGroup`, `CMenuRadioItem`, `CMenuGroup`, `CMenuSeparator`, and
`CMenuSubmenu` declarations. Their values, choices, action ordering, item
callbacks, typeahead, submenu keys, links, disabled state, and validation are
the [Menu contract](/v/0.4.2/ui-library/components/menu/).

ContextMenu adds no item-model array or duplicate declaration API. Import Menu
declarations and `CMenuActionDetail` from their existing `citry_ui` exports.


### Keep one Menu model

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/choices-and-submenus/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuChoicesAndSubmenus(Component):
    template = """
      <section
        class="context-menu-choices"
        dir="rtl"
        x-init="Alpine.store('contextMenuChoices', {showGrid:true, sort:'updated'})"
        x-data="{
          last:'No Menu action yet',
        }"
      >
        <h3>Canvas card</h3>
        <c-CContextMenu
          aria_label="Canvas card actions"
          c-close_on_select="False"
          $c-props="{
            onAction:(value,detail)=>
              last=`${detail.path.join(' / ') || 'root'}: ${value}`,
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <article
              class="context-menu-choices__card"
              dir="ltr"
              tabindex="0"
              c-bind="target_attrs"
            >
              <strong>Release canvas</strong>
              <span>Four records · Updated today</span>
            </article>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuCheckboxItem
              value="show-grid"
              c-checked="True"
              $c-props="{
                checked:$store.contextMenuChoices.showGrid,
                onCheckedChange:(next)=>$store.contextMenuChoices.showGrid=next,
              }"
            >
              Show grid
            </c-CMenuCheckboxItem>
            <c-CMenuSeparator />
            <c-CMenuRadioGroup
              value="updated"
              $c-props="{
                value:$store.contextMenuChoices.sort,
                onValueChange:(next)=>$store.contextMenuChoices.sort=next,
              }"
            >
              <c-fill name="label">Sort cards</c-fill>
              <c-fill name="default">
                <c-CMenuRadioItem value="updated">Recently updated</c-CMenuRadioItem>
                <c-CMenuRadioItem value="name">Name</c-CMenuRadioItem>
              </c-fill>
            </c-CMenuRadioGroup>
            <c-CMenuSeparator />
            <c-CMenuSubmenu value="export">
              <c-fill name="label">Export</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="export-png">PNG image</c-CMenuItem>
                <c-CMenuSubmenu value="document">
                  <c-fill name="label">Document</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="export-pdf">PDF</c-CMenuItem>
                    <c-CMenuItem value="export-svg">SVG</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenuSubmenu>
          </c-fill>
        </c-CContextMenu>
        <div class="context-menu-choices__peer" dir="ltr">
          <c-CContextMenu
            aria_label="Canvas peer actions"
            $c-props="{
              onAction:(value,detail)=>
                last=`LTR ${detail.path.join(' / ') || 'root'}: ${value}`,
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <button type="button" c-bind="target_attrs">LTR peer card</button>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect-peer">Inspect peer</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </div>
        <output
          aria-live="polite"
          x-text="`${last}; grid ${$store.contextMenuChoices.showGrid}; sort ${$store.contextMenuChoices.sort}`"
        >No Menu action yet; grid true; sort updated</output>
      </section>
    """

    css = """
      :where(.context-menu-choices) {
        display: grid;
        gap: 0.875rem;
        justify-items: start;
        min-block-size: 24rem;
        max-inline-size: 22rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-choices h3) {
        margin: 0;
      }

      :where(.context-menu-choices__card) {
        display: grid;
        gap: 0.25rem;
        inline-size: min(18rem, 100%);
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
        border-radius: 0.75rem;
        background: color-mix(in srgb, Highlight 8%, Canvas);
      }

      :where(.context-menu-choices__card:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-choices__peer) {
        padding: 0.75rem;
        border: 1px dashed color-mix(in srgb, CanvasText 24%, transparent);
      }
    """


preview = ContextMenuChoicesAndSubmenus()

preview  # noqa: B018
````


## Own visibility without stealing native fallback

Supply client `open` and `onOpenChange` together when application state owns
visibility. A trusted closed-to-open request has to decide whether to suppress
the browser menu before its event listener returns. The callback therefore
uses a narrow claim protocol:

1. Set the owner's `open` state to `true` synchronously.
2. Return the literal Boolean `true` in the same callback turn.

Every other return, including a Promise or another truthy value, refuses that
opening. The candidate coordinates remain available in the detail, but the
component does not commit them or prevent the native default. Returning
`true` without supplying `open=true` on the next settled props turn is a broken
claim: the component stays closed and reports one diagnostic.

Return values are ignored for uncontrolled opening and for every close.
`open=null` or prop removal releases control from the currently committed
visibility, using the same handoff as CMenu.


### Own visibility without stealing native fallback

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/controlled-open/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledContextMenu(Component):
    template = """
      <section
        class="context-menu-controlled"
        x-data="{
          open:false,
          controlled:true,
          accept:true,
          breakClaim:false,
          lastReason:'none',
          candidate:'none',
        }"
      >
        <c-CContextMenu
          aria_label="Diagram actions"
          $c-props="{
            open:controlled ? open : null,
            onOpenChange:(nextOpen,detail)=>{
              lastReason=detail.reason;
              candidate=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
              if (!controlled) return;
              if (!nextOpen) {
                open=false;
                return;
              }
              if (!accept) return false;
              if (!breakClaim) open=true;
              return true;
            },
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <div
              class="context-menu-controlled__target"
              tabindex="0"
              c-bind="target_attrs"
            >
              <strong>Controlled diagram</strong>
              <span>Right click or press Shift+F10</span>
            </div>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="inspect">Inspect layers</c-CMenuItem>
            <c-CMenuItem value="duplicate">Duplicate diagram</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>

        <div role="group" aria-label="Controlled visibility settings">
          <label><input type="checkbox" x-model="accept" /> Claim requests</label>
          <label><input type="checkbox" x-model="breakClaim" /> Break the claim</label>
          <button type="button" @click="controlled=true;open=true">
            Open from owner
          </button>
          <button type="button" @click="controlled=true;open=false">
            Close from owner
          </button>
          <button type="button" @click="controlled=false">
            Release control
          </button>
        </div>

        <output>
          State:
          <span x-text="controlled ? (open ? 'controlled open' : 'controlled closed') : 'uncontrolled'">
            controlled closed
          </span>;
          request: <span x-text="lastReason">none</span>;
          candidate: <span x-text="candidate">none</span>
        </output>
      </section>
    """

    css = """
      :where(.context-menu-controlled) {
        display: grid;
        gap: 1rem;
        min-block-size: 22rem;
        padding: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-controlled__target) {
        display: grid;
        gap: 0.25rem;
        padding: 1.25rem;
        border-radius: 1rem;
        background: light-dark(#eef4ff, #182230);
      }

      :where(.context-menu-controlled__target:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-controlled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        align-items: center;
      }

      :where(.context-menu-controlled label) {
        display: inline-flex;
        gap: 0.375rem;
        align-items: center;
      }
    """


preview = ControlledContextMenu()

preview  # noqa: B018
````


## Keep browser commands

ContextMenu preserves native behavior for:

- input, textarea, select, option, and editable content;
- links with `href`, images, audio, video, object, embed, and iframe Elements;
- custom Elements and detectable open-shadow hosts;
- a noncollapsed Selection that intersects the target; and
- any composed event path containing `data-citry-context-menu-native`.

Put `data-citry-context-menu-native` on a standard host when outside code
cannot inspect a closed shadow. Shift plus secondary click is always a native
escape. Firefox may not dispatch `contextmenu` for that gesture, so
ContextMenu also recognizes the pointer sequence and never suppresses it.

If a custom Menu is already open, a protected native request closes it once
and leaves the platform default untouched. Citry never clears selected text.


### Keep browser commands

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/native-content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuNativeContent(Component):
    template = """
      <section
        class="context-menu-native"
        x-data="{last:'No custom request yet'}"
      >
        <p>
          Select text or use the editing, link, image, media, embedded, and
          marked regions below. Their browser context menus stay available.
        </p>
        <c-CContextMenu
          aria_label="Document region actions"
          $c-props="{
            onOpenChange:(next,detail)=>
              last=`${next ? 'Open' : 'Close'}: ${detail.reason}`,
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <div
              class="context-menu-native__target"
              tabindex="0"
              c-bind="target_attrs"
            >
              <p class="context-menu-native__selection">
                Select part of this paragraph before opening its browser menu.
              </p>
              <label>
                Editable title
                <input value="Quarterly report" />
              </label>
              <div contenteditable="true">Editable note</div>
              <a href="#native-content-destination">Open linked record</a>
              <img
                alt="Blue document thumbnail"
                width="72"
                height="48"
                src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
              />
              <video controls aria-label="Media preview"></video>
              <context-menu-native-card>Custom element host</context-menu-native-card>
              <div
                data-citry-context-menu-native
                x-init="const root=$el.attachShadow({mode:'closed'});root.textContent='Closed shadow fixture'"
              >
                Marked closed-shadow host
              </div>
              <div
                x-init="const root=$el.attachShadow({mode:'open'});root.textContent='Select open-shadow text'"
              >
                Open-shadow selection fixture
              </div>
              <iframe
                title="Embedded document boundary"
                srcdoc="<p>Child document keeps its own browser menu.</p>"
              ></iframe>
              <div class="context-menu-native__eligible" tabindex="0">
                Plain file row · Custom commands available here
              </div>
            </div>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="rename">Rename file row</c-CMenuItem>
            <c-CMenuItem value="archive">Archive file row</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>
        <output aria-live="polite" x-text="last">No custom request yet</output>
        <span id="native-content-destination">Linked record destination</span>
      </section>
    """

    css = """
      :where(.context-menu-native) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-native > p) {
        max-inline-size: 62ch;
        margin: 0;
      }

      :where(.context-menu-native__target) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 1rem;
      }

      :where(.context-menu-native__target > *) {
        min-inline-size: 0;
        padding: 0.625rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, Highlight 7%, Canvas);
      }

      :where(.context-menu-native__selection) {
        user-select: text;
      }

      :where(.context-menu-native__eligible:focus-visible,
        .context-menu-native__target:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-native iframe) {
        inline-size: 100%;
        min-block-size: 5rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
      }
    """


preview = ContextMenuNativeContent()

preview  # noqa: B018
````


## Bound touch and pen fallback

An eligible primary touch or pen press can request the Menu after 700 ms. The
hold cancels for movement beyond 10 CSS pixels, scrolling, selection, another
pointer, pointer end or cancellation, blur, visibility loss, disabledness, or
structural change. Citry does not cancel pointerdown, capture the pointer,
change `touch-action`, disable selection, or apply callout-suppression CSS.

An accepted synthetic hold suppresses only its matching trusted derived click,
through pointerup plus 1,500 ms and never beyond the 10-second absolute
deadline. This prevents one hold from also navigating, submitting, resetting,
or running a target click. Other clicks keep their native behavior.

Desktop emulation cannot prove an operating system's callout timing. If a
platform shows a native callout without a cancelable `contextmenu`, Citry does
not claim to suppress it. Test real touch and pen devices before release.


### Bound long press

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/touch-and-pen/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuTouchAndPen(Component):
    template = """
      <section
        class="context-menu-touch"
        x-init="Alpine.store('contextMenuTouchDemo', {
          phase:'idle',
          log:[],
          targetClicks:0,
        })"
        x-data="{
          simulate(kind) {
            const state=Alpine.store('contextMenuTouchDemo');
            state.phase='armed: synthetic probe';
            state.log.unshift(`armed synthetic ${kind}`);
            const target=document.querySelector(
              kind === 'scroll'
                ? '[data-context-menu-scroll-target]'
                : '[data-context-menu-touch-target]'
            );
            const fire=(type,id,x,y,buttons=1)=>target.dispatchEvent(
              new PointerEvent(type, {
                bubbles:true,
                pointerType:'touch',
                pointerId:id,
                clientX:x,
                clientY:y,
                buttons,
              })
            );
            fire('pointerdown',81,12,12);
            if (kind === 'hold') {
              state.log.unshift('synthetic hold: pointerup after 700 ms');
              setTimeout(()=>{
                fire('pointerup',81,12,12,0);
                state.phase='synthetic hold complete: use a trusted device';
              },725);
            } else if (kind === 'move') {
              fire('pointermove',81,28,12);
              fire('pointerup',81,28,12,0);
              state.phase='canceled: movement';
              state.log.unshift('canceled movement');
            } else if (kind === 'scroll') {
              const scroller=document.querySelector('.context-menu-touch__scroller');
              scroller.scrollTop += 24;
              scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
              fire('pointerup',81,12,12,0);
            } else if (kind === 'lost-up') {
              state.phase='armed: lost-up deadline pending';
              state.log.unshift('synthetic lost-up: absolute 10 s guard');
            } else {
              fire('pointerdown',82,14,14);
              fire('pointercancel',81,12,12,0);
              fire('pointercancel',82,14,14,0);
              state.phase='canceled: second pointer';
              state.log.unshift('canceled second pointer');
            }
          },
        }"
      >
        <div class="context-menu-touch__policy">
          <strong>Bound fallback</strong>
          <span>Hold 700 ms · move at most 10 CSS px</span>
          <span>Matching click guard: pointerup + 1,500 ms</span>
          <span>Absolute guard deadline: 10 seconds</span>
        </div>

        <c-CContextMenu
          aria_label="Touch card actions"
          $c-props="{
            onOpenChange:(next,detail)=>{
              const state=$store.contextMenuTouchDemo;
              state.phase=next ? 'accepted' : 'idle';
              state.log.unshift(`${next ? 'accepted' : 'closed'} ${detail.reason}`);
            },
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <button
              class="context-menu-touch__card"
              type="button"
              data-context-menu-touch-target
              @click="$store.contextMenuTouchDemo.targetClicks += 1"
              c-bind="target_attrs"
            >
              <strong>Touch card</strong>
              <span>Press and hold for contextual commands</span>
            </button>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="pin">Pin card</c-CMenuItem>
            <c-CMenuItem value="share">Share card</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>

        <div
          class="context-menu-touch__scroller"
          @scroll="
            $store.contextMenuTouchDemo.phase='canceled: scroll';
            $store.contextMenuTouchDemo.log.unshift('canceled scroll')
          "
        >
          <c-CContextMenu
            aria_label="Scrollable card actions"
            $c-props="{
              open:false,
              onOpenChange:(next,detail)=>{
                $store.contextMenuTouchDemo.phase='controlled refused';
                $store.contextMenuTouchDemo.log.unshift(`refused ${detail.reason}`);
                return false;
              },
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-touch__card"
                tabindex="0"
                data-context-menu-scroll-target
                c-bind="target_attrs"
              >
                <strong>Scrollable card</strong>
                <span>Scrolling, movement, and another pointer cancel the hold.</span>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect">Inspect card</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
          <div class="context-menu-touch__spacer">Scroll boundary</div>
        </div>

        <div class="context-menu-touch__controls">
          <button type="button" @click="simulate('hold')">Test 700 ms hold</button>
          <button type="button" @click="simulate('move')">Test movement cancel</button>
          <button type="button" @click="simulate('scroll')">Test scroll cancel</button>
          <button type="button" @click="simulate('lost-up')">Test lost pointerup</button>
          <button type="button" @click="simulate('second')">Test second pointer</button>
          <button
            type="button"
            @click="$store.contextMenuTouchDemo.log=[];$store.contextMenuTouchDemo.phase='idle'"
          >Clear ledger</button>
          <output
            aria-live="polite"
            x-text="`State: ${$store.contextMenuTouchDemo.phase};
              primary clicks: ${$store.contextMenuTouchDemo.targetClicks}`"
          >State: idle; primary clicks: 0</output>
        </div>
        <ol aria-live="polite">
          <template x-for="entry in $store.contextMenuTouchDemo.log.slice(0,5)">
            <li x-text="entry"></li>
          </template>
        </ol>
        <p>
          Desktop emulation cannot prove an operating system's callout timing.
          Citry does not disable selection, touch scrolling, or platform callouts.
        </p>
      </section>
    """

    css = """
      :where(.context-menu-touch) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-touch__policy) {
        display: grid;
        gap: 0.25rem;
        padding: 0.875rem;
        border-inline-start: 0.25rem solid Highlight;
        background: color-mix(in srgb, Highlight 8%, Canvas);
      }

      :where(.context-menu-touch__card) {
        display: grid;
        gap: 0.25rem;
        inline-size: min(100%, 26rem);
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        text-align: start;
      }

      :where(.context-menu-touch__scroller) {
        max-block-size: 8rem;
        overflow: auto;
        border: 1px solid color-mix(in srgb, CanvasText 16%, transparent);
      }

      :where(.context-menu-touch__spacer) {
        min-block-size: 12rem;
        padding: 1rem;
      }

      :where(.context-menu-touch__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.context-menu-touch p,
        .context-menu-touch ol) {
        margin: 0;
      }
    """


preview = ContextMenuTouchAndPen()

preview  # noqa: B018
````


## Return focus deliberately

After an accepted request, focus moves to the first enabled Menu item. Escape
and a non-link command try the original deep focus snapshot, then the invoking
Element, then the focusable target. If those are unavailable, focus moves to
the nearest open modal Dialog or to the document body. A link action keeps
native navigation and skips focus return.

Outside pointer, focus outside, Tab, Shift+Tab, ancestor closure, and owner
focus movement do not restore focus. Owner-moved focus always wins.


### Return focus deliberately

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/focus-and-keyboard/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuFocusAndKeyboard(Component):
    template = """
      <section
        class="context-menu-focus"
        x-data="{disableInvoker:false,last:'No close yet'}"
      >
        <p>
          Focus the row or nested Button, then press the Context Menu key or
          Shift+F10. A linked path keeps the browser's native context menu.
        </p>
        <c-CContextMenu
          aria_label="Focusable row actions"
          $c-props="{
            onOpenChange:(next,detail)=>last=
              `${next ? 'opened' : 'closed'} by ${detail.reason}`,
            onAction:(value)=>{
              if (value === 'disable-invoker') disableInvoker=true;
              if (value === 'remove-invoker') {
                document.querySelector('[data-context-menu-return-target]')?.remove();
              }
            },
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <div
              class="context-menu-focus__row"
              tabindex="0"
              c-bind="target_attrs"
            >
              <span>
                <strong>Focusable report row</strong>
                <small>The row is the stable fallback target.</small>
              </span>
              <c-CButton
                size="sm"
                variant="outline"
                c-attrs="{'data-context-menu-return-target':''}"
                $c-props="{disabled:disableInvoker}"
              >Nested action</c-CButton>
              <a href="#focus-linked-record">Linked record</a>
            </div>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="rename">Rename</c-CMenuItem>
            <c-CMenuItem value="disable-invoker">
              Disable nested return target
            </c-CMenuItem>
            <c-CMenuItem value="remove-invoker">
              Remove nested return target
            </c-CMenuItem>
            <c-CMenuItem href="#focus-linked-record">Open linked record</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>

        <div class="context-menu-focus__fallbacks">
          <button type="button" @click="location.reload()">Reload nested Button</button>
          <button type="button" disabled>Disabled fallback</button>
          <span tabindex="-1">Programmatic fallback</span>
        </div>

        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Open composed modal fixture
            </c-CButton>
          </c-fill>
          <c-fill name="title">Modal focus ancestry</c-fill>
          <c-fill name="default">
            <p>
              This target and its private point stay inside the current modal.
            </p>
            <c-CContextMenu
              aria_label="Modal row actions"
              $c-props="{
                onOpenChange:(next,detail)=>last=
                  `modal ${next ? 'opened' : 'closed'} by ${detail.reason}`,
              }"
            >
              <c-fill name="target" data="{ target_attrs }">
                <button
                  class="context-menu-focus__modal-target"
                  type="button"
                  c-bind="target_attrs"
                >Modal report row</button>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="review-modal-row">Review modal row</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </c-fill>
        </c-CDialog>
        <output aria-live="polite" x-text="last">No close yet</output>
        <span id="focus-linked-record">Linked destination</span>
      </section>
    """

    css = """
      :where(.context-menu-focus) {
        display: grid;
        gap: 1rem;
        min-block-size: 22rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-focus > p) {
        max-inline-size: 62ch;
        margin: 0;
      }

      :where(.context-menu-focus__row) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.75rem;
      }

      :where(.context-menu-focus__row > span:first-child) {
        display: grid;
        gap: 0.25rem;
      }

      :where(.context-menu-focus__row:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-focus__fallbacks) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.context-menu-focus__modal-target) {
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
      }
    """


preview = ContextMenuFocusAndKeyboard()

preview  # noqa: B018
````


## Share the layer coordinator

Nested ContextMenus use the deepest bound target. A ContextMenu inside a
Popover, Tooltip, or Dialog keeps that logical ancestry. A coexisting ordinary
Menu shares the same coordinator; right-clicking inside its open surface stays
native and does not reinvoke the ContextMenu. A later modal outside the ancestry
force-closes it. Point and Menu surfaces remain inline in the same Document or
open ShadowRoot, then use native Popover for the top layer.

Events do not cross iframe Document boundaries. A child document needs its own
Citry installation and coordinator. An iframe Element inside the parent target
keeps its native context menu.


### Share the layer coordinator

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/layers-and-roots/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuLayersAndRoots(Component):
    template = """
      <section
        class="context-menu-layers"
        x-data="{
          last:'No layer request yet',
          counterTick:0,
        }"
      >
        <article>
          <h3>Deepest target wins</h3>
          <c-CContextMenu
            aria_label="Outer card actions"
            $c-props="{
              onOpenChange:(next,detail)=>last=
                `outer ${next ? 'open' : 'close'} ${detail.reason}`,
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-layers__outer"
                tabindex="0"
                c-bind="target_attrs"
              >
                Outer card
                <c-CContextMenu
                  aria_label="Inner badge actions"
                  $c-props="{
                    onOpenChange:(next,detail)=>last=
                      `inner ${next ? 'open' : 'close'} ${detail.reason}`,
                  }"
                >
                  <c-fill name="target" data="{ target_attrs as inner_target_attrs }">
                    <span
                      class="context-menu-layers__inner"
                      tabindex="0"
                      c-bind="inner_target_attrs"
                    >Inner badge</span>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="inspect-badge">Inspect badge</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect-card">Inspect card</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </article>

        <article>
          <h3>Inside another anchored layer</h3>
          <c-CPopover>
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton c-attrs="activator_attrs">Open inspector</c-CButton>
            </c-fill>
            <c-fill name="title">Record inspector</c-fill>
            <c-fill name="default">
              <c-CContextMenu
                aria_label="Inspector row actions"
                c-attrs="{'data-context-menu-removable':''}"
              >
                <c-fill name="target" data="{ target_attrs }">
                  <div
                    class="context-menu-layers__popover-target"
                    tabindex="0"
                    c-bind="target_attrs"
                  >Row inside Popover</div>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="open-row">Open row</c-CMenuItem>
                  <c-CMenuItem value="archive-row">Archive row</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>
            </c-fill>
          </c-CPopover>
          <button
            type="button"
            @click="
              document.querySelector('[data-context-menu-removable]')?.remove();
              last='nested ContextMenu removed'
            "
          >Remove nested ContextMenu</button>
          <button type="button" @click="location.reload()">
            Restore the fixture, then repeat the cycle
          </button>

          <c-CContextMenu aria_label="Tooltip target actions">
            <c-fill name="target" data="{ target_attrs }">
              <div class="context-menu-layers__popover-target" c-bind="target_attrs">
                <c-CTooltip text="This descendant shares Tooltip layer ancestry">
                  <c-fill name="activator" data="{ activator_attrs }">
                    <c-CButton
                      size="sm"
                      variant="outline"
                      c-attrs="activator_attrs"
                    >Tooltip-bound target</c-CButton>
                  </c-fill>
                </c-CTooltip>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect-tooltip-target">
                Inspect Tooltip target
              </c-CMenuItem>
            </c-fill>
          </c-CContextMenu>

          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">
                Open sibling Menu
              </c-CButton>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="ordinary-menu-command">
                Ordinary Menu command
              </c-CMenuItem>
              <c-CMenuItem href="#context-menu-menu-native-link">
                Native link in Menu
              </c-CMenuItem>
            </c-fill>
          </c-CMenu>
          <p id="context-menu-menu-native-link">
            Right click inside the open Menu to keep the browser path rather
            than reinvoking ContextMenu.
          </p>
        </article>

        <article
          x-data
          x-init="$nextTick(()=>{
            const shadow=$refs.shadowHost.attachShadow({mode:'open'});
            document.querySelectorAll('style').forEach(
              (style)=>shadow.append(style.cloneNode(true))
            );
            shadow.append($refs.shadowFixture);
          })"
        >
          <h3>Open ShadowRoot scope</h3>
          <div x-ref="shadowFixture">
            <c-CContextMenu aria_label="Shadow record actions">
              <c-fill name="target" data="{ target_attrs }">
                <button
                  class="context-menu-layers__shadow-target"
                  type="button"
                  c-bind="target_attrs"
                >ShadowRoot target</button>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="inspect-shadow">Inspect shadow record</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </div>
          <div x-ref="shadowHost" data-context-menu-shadow-host></div>
        </article>

        <article>
          <h3>Later modal owns the top layer</h3>
          <c-CDialog>
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton variant="outline" c-attrs="activator_attrs">
                Open sibling Dialog
              </c-CButton>
            </c-fill>
            <c-fill name="title">Layer review</c-fill>
            <c-fill name="default">
              A later modal outside a ContextMenu ancestry force-closes it.
            </c-fill>
            <c-fill name="actions" data="{ close_attrs }">
              <c-CButton c-attrs="close_attrs">Close review</c-CButton>
            </c-fill>
          </c-CDialog>
          <iframe
            title="Separate document context boundary"
            srcdoc="<p>A child document needs its own Citry instance.</p>"
          ></iframe>
        </article>

        <div class="context-menu-layers__diagnostics">
          <button type="button" @click="counterTick += 1">
            Refresh layer counters
          </button>
          <output
            aria-live="polite"
            x-text="`${last}; layers ${counterTick >= 0
              ? (globalThis[Symbol.for('citry-ui:anchored-layer-runtime')]?.layers.length ?? 0)
              : 0}; registrations ${globalThis[Symbol.for('citry-ui:anchored-layer-runtime')]
                ?.stats?.activeCoordinators ?? 0}`"
          >No layer request yet; layers 0; registrations 0</output>
        </div>
      </section>
    """

    css = """
      :where(.context-menu-layers) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        min-block-size: 28rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-layers article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-inline-size: 0;
      }

      :where(.context-menu-layers h3) {
        margin: 0;
      }

      :where(.context-menu-layers__outer,
        .context-menu-layers__popover-target) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.75rem;
      }

      :where(.context-menu-layers__inner) {
        display: inline-block;
        inline-size: fit-content;
        padding: 0.375rem 0.625rem;
        border-radius: 999px;
        background: color-mix(in srgb, Highlight 14%, Canvas);
      }

      :where(.context-menu-layers__shadow-target) {
        padding: 0.75rem;
        border: 1px solid currentColor;
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.context-menu-layers iframe) {
        inline-size: 100%;
        min-block-size: 6rem;
      }

      :where(.context-menu-layers__diagnostics) {
        grid-column: 1 / -1;
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
    """


preview = ContextMenuLayersAndRoots()

preview  # noqa: B018
````


## Anchor to the accepted point

Pointer requests use the trusted event's viewport point. Keyboard and external
owner-open requests derive a visible logical start and block-end point from the
focused descendant or target. The Menu reads its own computed direction and
uses logical `bottom-start`, native CSS Anchor Positioning, and collision
fallbacks.

There is no public coordinate, target selector, Element reference, placement,
offset, or positioning-strategy input. A request whose target-derived rect is
fully outside the visual viewport is rejected rather than anchored to a stale
or arbitrary point.


### Anchor to the accepted point

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/positioning-and-rtl/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuPositioningAndRtl(Component):
    template = """
      <section
        class="context-menu-positioning"
        style="--cui-menu-inline-size:18rem"
        x-data="{
          surfaceDir:'ltr',
          targetDir:'rtl',
          externalOpen:false,
          lastPoint:'none',
          lastInvocation:'none',
        }"
        :dir="surfaceDir"
      >
        <div class="context-menu-positioning__controls">
          <button
            type="button"
            @click="surfaceDir=surfaceDir === 'ltr' ? 'rtl' : 'ltr'"
          >Toggle surface direction</button>
          <button
            type="button"
            @click="targetDir=targetDir === 'ltr' ? 'rtl' : 'ltr'"
          >Toggle target-only direction</button>
          <button
            type="button"
            @click="
              externalOpen=true;
              lastInvocation='external';
              $nextTick(()=>setTimeout(()=>{
                const point=document.querySelector('#context-position-external-point');
                const box=point?.getBoundingClientRect();
                if (box) lastPoint=`${Math.round(box.x)}, ${Math.round(box.y)}`;
              }))
            "
          >Open from owner state</button>
          <button type="button" @click="$refs.repairScroller.scrollTop += 32">
            Scroll repair fixture
          </button>
          <button type="button" @click="window.dispatchEvent(new Event('resize'))">
            Resize repair fixture
          </button>
          <button
            type="button"
            @click="
              const target=document.querySelector('[data-context-menu-offscreen-target]');
              target.focus();
              target.dispatchEvent(new KeyboardEvent('keydown', {
                bubbles:true,
                key:'F10',
                shiftKey:true,
              }))
            "
          >Test fully offscreen rejection</button>
          <output x-text="`Accepted point: ${lastPoint}; invocation: ${lastInvocation}`">
            Accepted point: none; invocation: none
          </output>
          <output
            x-text="`Visual viewport: ${Math.round(visualViewport?.width ?? innerWidth)} x
              ${Math.round(visualViewport?.height ?? innerHeight)} CSS px`"
          >Visual viewport diagnostic</output>
        </div>

        <div class="context-menu-positioning__board">
          <c-CContextMenu
            aria_label="Top start actions"
            $c-props="{
              onOpenChange:(next,detail)=>{
                if (next) {
                  lastPoint=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
                  lastInvocation=detail.reason === 'contextmenu' ? 'pointer' : detail.reason;
                }
              },
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-positioning__target is-top-start"
                tabindex="0"
                :dir="targetDir"
                c-bind="target_attrs"
              >Top start</div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect">Inspect corner</c-CMenuItem>
              <c-CMenuItem value="duplicate">Duplicate record</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>

          <c-CContextMenu aria_label="Top end actions">
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-positioning__target is-top-end"
                tabindex="0"
                c-bind="target_attrs"
              >Top end</div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect">Inspect corner</c-CMenuItem>
              <c-CMenuItem value="duplicate">Duplicate record</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>

          <c-CContextMenu aria_label="Bottom start actions">
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-positioning__target is-bottom-start"
                tabindex="0"
                c-bind="target_attrs"
              >Bottom start</div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect">Inspect corner</c-CMenuItem>
              <c-CMenuItem value="duplicate">Duplicate record</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>

          <c-CContextMenu
            id="context-position-external"
            aria_label="Bottom end actions"
            $c-props="{
              open:externalOpen,
              onOpenChange:(next,detail)=>{
                externalOpen=next;
                if (next) {
                  lastPoint=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
                  lastInvocation=detail.reason === 'contextmenu' ? 'pointer' : detail.reason;
                  return true;
                }
              },
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-positioning__target is-bottom-end"
                tabindex="0"
                c-bind="target_attrs"
              >Bottom end</div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect">Inspect corner</c-CMenuItem>
              <c-CMenuItem value="duplicate">Duplicate record</c-CMenuItem>
              <c-CMenuItem value="history">Open a deliberately longer command label</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>

          <c-CContextMenu aria_label="Fully offscreen target actions">
            <c-fill name="target" data="{ target_attrs }">
              <button
                class="context-menu-positioning__target is-offscreen"
                type="button"
                data-context-menu-offscreen-target
                c-bind="target_attrs"
              >Fully offscreen target</button>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="unreachable">Rejected while fully offscreen</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </div>

        <div
          class="context-menu-positioning__repair-scroller"
          x-ref="repairScroller"
        >
          <div class="context-menu-positioning__repair-spacer">Scrollable repair boundary</div>
          <div class="context-menu-positioning__transformed">
            <c-CContextMenu aria_label="Transformed card actions">
              <c-fill name="target" data="{ target_attrs }">
                <div
                  class="context-menu-positioning__target"
                  tabindex="0"
                  c-bind="target_attrs"
                >Target inside transform, filter, and containment</div>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="inspect">Inspect transformed card</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </div>
        </div>
        <p>
          Pointer requests use the accepted browser event point. Keyboard and
          owner-open requests derive a visible point from the focused target.
          The component has no coordinate or placement input. Zoom to 400% to
          verify the same collision-safe 18 rem surface.
        </p>
      </section>
    """

    css = """
      :where(.context-menu-positioning) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-positioning__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        align-items: center;
      }

      :where(.context-menu-positioning__board) {
        position: relative;
        min-block-size: 20rem;
        overflow: hidden;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 1rem;
        background: linear-gradient(
          135deg,
          color-mix(in srgb, Highlight 10%, Canvas),
          Canvas
        );
      }

      :where(.context-menu-positioning__target) {
        padding: 0.625rem;
        border: 1px solid color-mix(in srgb, CanvasText 28%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
      }

      :where(.context-menu-positioning__board .context-menu-positioning__target) {
        position: absolute;
      }

      :where(.context-menu-positioning__target:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-positioning__target.is-top-start) {
        inset-block-start: -0.25rem;
        inset-inline-start: -0.25rem;
      }

      :where(.context-menu-positioning__target.is-top-end) {
        inset-block-start: 0.5rem;
        inset-inline-end: 0.5rem;
      }

      :where(.context-menu-positioning__target.is-bottom-start) {
        inset-block-end: 0.5rem;
        inset-inline-start: 0.5rem;
      }

      :where(.context-menu-positioning__target.is-bottom-end) {
        inset-block-end: -0.25rem;
        inset-inline-end: -0.25rem;
      }

      :where(.context-menu-positioning__target.is-offscreen) {
        inset-block-start: -20rem;
        inset-inline-start: -20rem;
      }

      :where(.context-menu-positioning__repair-scroller) {
        max-block-size: 9rem;
        overflow: auto;
        border: 1px dashed color-mix(in srgb, CanvasText 24%, transparent);
      }

      :where(.context-menu-positioning__repair-spacer) {
        min-block-size: 8rem;
        padding: 0.5rem;
      }

      :where(.context-menu-positioning__transformed) {
        inline-size: fit-content;
        padding: 1rem;
        filter: saturate(0.9);
        transform: translateX(1rem);
        contain: paint;
      }

      :where(.context-menu-positioning p) {
        max-inline-size: 68ch;
        margin: 0;
      }
    """


preview = ContextMenuPositioningAndRtl()

preview  # noqa: B018
````


## Use Menu styling and native fallback

`class_`, `style`, and `attrs` target the ContextMenu host. The host renders no
visual box, so set target presentation on the Element that binds
`target_attrs`. Existing `--cui-menu-*` variables inherit from the host or an
ancestor to the inline Menu surface. Existing Menu part selectors customize
its surface and items. ContextMenu adds no theme or coordinate variables.


### Use Menu styling and native fallback

[Open the rendered preview](/v/0.4.2/ui-library/components/context-menu/_previews/customization-and-fallback/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuCustomizationAndFallback(Component):
    template = """
      <section
        class="context-menu-customization"
        x-data="{orchardEnhanced:false,harborEnhanced:true}"
      >
        <div class="context-menu-customization__controls">
          <button type="button" @click="orchardEnhanced=!orchardEnhanced">
            Toggle server-disabled Orchard enhancement
          </button>
          <button type="button" @click="harborEnhanced=!harborEnhanced">
            Disable or restore ready Harbor enhancement
          </button>
          <output
            aria-live="polite"
            x-text="`Orchard ${orchardEnhanced ? 'enhanced' : 'native'};
              Harbor ${harborEnhanced ? 'enhanced' : 'native'}`"
          >Orchard native; Harbor enhanced</output>
        </div>

        <div class="context-menu-customization__brands">
          <article class="context-menu-customization__orchard">
            <h3>Orchard</h3>
            <c-CContextMenu
              class_="brand-context-menu"
              aria_label="Orchard file actions"
              c-open="True"
              c-disabled="True"
              c-style="{
                '--cui-menu-radius':'1rem',
                '--cui-menu-focus-background':'#315f37',
              }"
              c-attrs="{'data-quality-brand':'orchard'}"
              $c-props="{disabled:!orchardEnhanced}"
            >
              <c-fill name="target" data="{ target_attrs }">
                <div
                  class="context-menu-customization__file"
                  tabindex="0"
                  c-bind="target_attrs"
                >
                  <strong>Harvest plan.pdf</strong>
                  <span>Server-open fallback</span>
                </div>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="open">Open file</c-CMenuItem>
                <c-CMenuItem value="archive">Archive file</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </article>

          <article
            class="context-menu-customization__harbor"
            style="color-scheme:dark"
          >
            <h3>Harbor</h3>
            <c-CContextMenu
              class_="brand-context-menu"
              aria_label="Harbor file actions"
              size="lg"
              c-style="{
                '--cui-menu-background':'#173c4c',
                '--cui-menu-foreground':'#eefaff',
                '--cui-menu-border-color':'#72b5ce',
              }"
              c-attrs="{'data-quality-brand':'harbor'}"
              $c-props="{disabled:!harborEnhanced}"
            >
              <c-fill name="target" data="{ target_attrs }">
                <div
                  class="context-menu-customization__file"
                  tabindex="0"
                  c-bind="target_attrs"
                >
                  <strong>Dock schedule.csv</strong>
                  <span>Server-closed fallback</span>
                </div>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="open">Open file</c-CMenuItem>
                <c-CMenuItem value="remove" intent="danger">Remove file</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </article>
        </div>

        <p>
          Without JavaScript, targets remain ordinary native content. A
          server-closed Menu stays hidden and a server-open Menu remains readable
          in document flow. The browser context menu remains available until a
          valid enhanced request is accepted.
        </p>
      </section>
    """

    css = """
      :where(.context-menu-customization) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-customization__brands) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }

      :where(.context-menu-customization__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.context-menu-customization article) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.context-menu-customization h3,
        .context-menu-customization p) {
        margin: 0;
      }

      :where(.context-menu-customization__orchard) {
        background: #f5f0df;
        color: #203422;
        --cui-menu-background: #fffdf5;
        --cui-menu-foreground: #203422;
        --cui-menu-border-color: #78916d;
      }

      :where(.context-menu-customization__harbor) {
        background: #102b38;
        color: #eefaff;
      }

      :where(.context-menu-customization__file) {
        display: grid;
        gap: 0.25rem;
        padding: 1rem;
        border: 1px solid currentColor;
        border-radius: 0.75rem;
      }

      :where(.context-menu-customization__file:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      .context-menu-customization
      .brand-context-menu[data-citry-ui-part="context-menu"]
      [data-citry-ui-part="menu"] {
        border-width: 2px;
      }

      @media (forced-colors: active) {
        :where(.context-menu-customization article) {
          border: 1px solid CanvasText;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        :where(.context-menu-customization) {
          scroll-behavior: auto;
        }
      }

      @media print {
        :where(.context-menu-customization article) {
          background: transparent;
          color: black;
        }
      }
    """


preview = ContextMenuCustomizationAndFallback()

preview  # noqa: B018
````


Without JavaScript, the target stays ordinary native content. A server-closed
Menu remains hidden through native Popover presence, while an initially open
Menu remains readable in document flow. Before successful initialization,
ContextMenu does not suppress native requests. Capability loss after
initialization closes the enhanced Menu before removing its point.

## Distinguish callbacks from native events

`onOpenChange` and `onAction` are component callbacks supplied through
`$c-props`. `onOpenChange` describes requests and forced closes;
`onAction` uses the existing `CMenuActionDetail`. ContextMenu dispatches no
custom DOM event.

Native events remain Alpine listeners in allowed `attrs` or target content.
The ContextMenu root has Citry's isolated expression scope, so an attrs listener
cannot read ancestor-local `x-data` identifiers directly. Use `$event`,
`$dispatch`, `$store`, or an explicit global bridge. Use component callbacks
for owner-local state.

The component owns `contextmenu`, ContextMenu/Shift+F10 keydown, and its
touch/pen pointer sequence. It does not stop propagation on those paths. Only
the exact trusted click derived from an accepted synthetic long press is
prevented and stopped immediately so the target's primary action cannot also
run.

## Keep target and host attributes separate

`target_attrs` is copied, validated, and included in the target slot data. It
may carry ordinary classes, styles, safe ARIA, semantic native attributes,
nonreserved data, and unrelated native listeners. It cannot author the target
ID, ContextMenu marker, owned invocation events, `role`, native `disabled`,
Popover/anchor state, or Menu Button ARIA.

Host `attrs` accepts ordinary descriptive attributes, `dir`, `lang`,
nonreserved data, and unrelated native listeners. It cannot replace owned
identity, roles, ARIA, parts, reflections, lifecycle, Popover/anchor state, or
Citry runtime namespaces. Mappings are copied once. ContextMenu trusts ordinary
slot content as application content; it is not an HTML or URL sanitizer.

CContextMenu is not Form-associated. It emits no name/value pair and does not
participate in reset or constraint validation. Target descendants keep their
native Form behavior. A target Button may submit or reset on primary
activation; only the exact derived click from an accepted synthetic long press
is suppressed.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CContextMenu server inputs

Server inputs are passed in a template through `<c-CContextMenu ... />` or in Python through
`CContextMenu(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 10rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="context-menu-input-ccontext-menu-server-inputs-id"></span>`id` | `str | None` | generated | Sets the correlated host, target, point, Menu surface, declaration, and submenu ID family. |
| <span id="context-menu-input-ccontext-menu-server-inputs-aria-label"></span>`aria_label` | `non-whitespace str` | required | Supplies the root Menu surface accessible name without relabelling the arbitrary target. |
| <span id="context-menu-input-ccontext-menu-server-inputs-open"></span>`open` | `bool` | `False` | Sets server and uncontrolled Menu visibility. |
| <span id="context-menu-input-ccontext-menu-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Blocks custom invocation and force-closes an open Menu while preserving native context behavior. |
| <span id="context-menu-input-ccontext-menu-server-inputs-loop"></span>`loop` | `bool` | `True` | Selects existing CMenu arrow and typeahead wrapping. |
| <span id="context-menu-input-ccontext-menu-server-inputs-close-on-select"></span>`close_on_select` | `bool` | `True` | Selects the existing root CMenu action-close policy. |
| <span id="context-menu-input-ccontext-menu-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CMenuSize`](#context-menu-interface-menu-size)) | `"md"` | Selects existing CMenu item geometry. |
| <span id="context-menu-input-ccontext-menu-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#context-menu-interface-class-value)) | `None` | Adds host classes and merges them with attrs. |
| <span id="context-menu-input-ccontext-menu-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#context-menu-interface-style-value)) | `None` | Adds host styles; inherited Menu variables reach the inline surface. |
| <span id="context-menu-input-ccontext-menu-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed host attributes and isolated-scope unrelated native listeners. |
| <span id="context-menu-input-ccontext-menu-server-inputs-target-attrs"></span>`target_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes to the exact bound target mapping without replacing owned identity or invocation behavior. |

</div>

#### CContextMenu client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CContextMenu />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 17rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="context-menu-input-ccontext-menu-client-inputs-open"></span>`open` | `boolean | null` | Releases control from the current committed visibility; null has the same effect. | Controls Menu visibility while supplied as a Boolean. |
| <span id="context-menu-input-ccontext-menu-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls custom invocation disabledness; native target and fieldset disabledness remain authoritative. |
| <span id="context-menu-input-ccontext-menu-client-inputs-loop"></span>`loop` | `boolean` | Uses the server input. | Controls existing CMenu navigation wrapping. |
| <span id="context-menu-input-ccontext-menu-client-inputs-close-on-select"></span>`closeOnSelect` | `boolean` | Uses the server input. | Controls the existing root CMenu action-close policy. |
| <span id="context-menu-input-ccontext-menu-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CMenuSize`](#context-menu-interface-menu-size)) | Uses the server input. | Controls existing CMenu item geometry. |
| <span id="context-menu-input-ccontext-menu-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Omission or null selects no visibility callback and refuses a controlled native-default claim. | Receives visibility requests and forced closes; only a synchronous literal-true return can claim a controlled closed-to-open native request. |
| <span id="context-menu-input-ccontext-menu-client-inputs-on-action"></span>`onAction` | `function` | Omission or null selects no root action callback. | Receives existing valued CMenu command and choice activations. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CContextMenu slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="context-menu-slot-ccontext-menu-slots-target"></span>`target` | yes | `{target_attrs}` ([`CContextMenuTargetSlotData`](#context-menu-interface-ccontext-menu-target-slot-data)) | None. Must settle to exactly one direct standard native Element with the complete target_attrs mapping bound. |
| <span id="context-menu-slot-ccontext-menu-slots-menu"></span>`menu` | yes | `{}` ([`CContextMenuMenuSlotData`](#context-menu-interface-ccontext-menu-menu-slot-data)) | None. Requires one or more direct existing CMenu declarations under the existing collection rules. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CContextMenu events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="context-menu-event-ccontext-menu-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CContextMenuOpenChangeDetail) => boolean | void` ([`CContextMenuOpenChangeDetail`](#context-menu-interface-ccontext-menu-open-change-detail)) | A trusted contextual request, Menu dismissal, or forced native, disabled, or ancestor close occurs. | `{reason, controlled, forced, source, clientX, clientY}` ([`CContextMenuOpenChangeDetail`](#context-menu-interface-ccontext-menu-open-change-detail)) | Candidate coordinates accompany refused controlled requests. A controlled closed-to-open request is claimed only when the callback synchronously sets owner open state and returns literal true; all other returns refuse without preventing the native default. |
| <span id="context-menu-event-ccontext-menu-events-on-action"></span>`onAction` | `(value: string, detail: CMenuActionDetail) => void` ([`CMenuActionDetail`](#context-menu-interface-ccontext-menu-action-detail)) | An enabled valued CMenu command, checkbox, or radio activates. | `{kind, item, event, path}` ([`CMenuActionDetail`](#context-menu-interface-ccontext-menu-action-detail)) | Uses exact CMenu callback order and action detail. ContextMenu adds no target or point fields to action detail. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CContextMenu CSS variables

Apply these variables to `CContextMenu` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-background"></span>`--cui-menu-background` | `color` | Root and submenu Menu surfaces. | `Canvas` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-foreground"></span>`--cui-menu-foreground` | `color` | Menu item text. | `CanvasText` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-muted-color"></span>`--cui-menu-muted-color` | `color` | Descriptions, labels, and shortcuts. | `color-mix(in srgb, current foreground 72%, transparent)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-border-color"></span>`--cui-menu-border-color` | `color` | Menu surface and separator boundaries. | `color-mix(in srgb, CanvasText 18%, transparent)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-border-width"></span>`--cui-menu-border-width` | `length` | Menu surface boundary width. | `1px` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-radius"></span>`--cui-menu-radius` | `length` | Menu surface corners. | `0.75rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-shadow"></span>`--cui-menu-shadow` | `shadow` | Root Menu elevation. | `0 0.75rem 2rem rgb(15 23 42 / 18%)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-submenu-shadow"></span>`--cui-menu-submenu-shadow` | `shadow` | Nested Menu elevation. | `0 1rem 2.5rem rgb(15 23 42 / 22%)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-inline-size"></span>`--cui-menu-inline-size` | `length` | Preferred Menu width. | `14rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-min-inline-size"></span>`--cui-menu-min-inline-size` | `length` | Minimum useful submenu corridor. | `10rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-max-inline-size"></span>`--cui-menu-max-inline-size` | `length` | Viewport-safe Menu width. | `calc(100dvi - 1rem)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-max-block-size"></span>`--cui-menu-max-block-size` | `length` | Menu scroll limit. | `min(24rem, calc(100dvb - 1rem))` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-padding"></span>`--cui-menu-padding` | `length` | Menu surface edge spacing. | `0.375rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-item-block-size"></span>`--cui-menu-item-block-size` | `length` | Menu item minimum height. | `Size-derived.` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-item-padding-inline"></span>`--cui-menu-item-padding-inline` | `length` | Menu item inline spacing. | `Size-derived.` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-item-gap"></span>`--cui-menu-item-gap` | `length` | Menu item-region gap. | `0.625rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-item-radius"></span>`--cui-menu-item-radius` | `length` | Menu item corners. | `0.5rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-hover-background"></span>`--cui-menu-hover-background` | `color` | Enabled pointer-hover fill. | `color-mix(in srgb, CanvasText 8%, transparent)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-focus-background"></span>`--cui-menu-focus-background` | `color` | Focused Menu item fill. | `light-dark(#175cd3, #84adff)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-focus-foreground"></span>`--cui-menu-focus-foreground` | `color` | Focused Menu item content. | `light-dark(#ffffff, #101828)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-focus-outline-color"></span>`--cui-menu-focus-outline-color` | `color` | Menu item focus-visible outline. | `light-dark(#175cd3, #84adff)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-danger-color"></span>`--cui-menu-danger-color` | `color` | Destructive Menu item content. | `light-dark(#b42318, #fda29b)` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-disabled-opacity"></span>`--cui-menu-disabled-opacity` | `number` | Disabled Menu content opacity. | `0.5` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-offset"></span>`--cui-menu-offset` | `length` | Context point to root Menu gap. | `0.375rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-submenu-offset"></span>`--cui-menu-submenu-offset` | `length` | Nested Menu anchor gap. | `0.25rem` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-duration"></span>`--cui-menu-duration` | `time` | Menu entry and exit duration. | `120ms` |
| <span id="context-menu-css-ccontext-menu-reused-menu-css-variables-cui-menu-easing"></span>`--cui-menu-easing` | `easing` | Menu entry and exit curve. | `cubic-bezier(0.2, 0.8, 0.2, 1)` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CContextMenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="context-menu-attribute-ccontext-menu-root-attributes-root-id"></span>`id` | ContextMenu host | `supplied or generated string` | Identifies the host and bases the correlated target, point, surface, and declaration IDs. |
| <span id="context-menu-attribute-ccontext-menu-root-attributes-data-open"></span>`data-open` | ContextMenu host | `present | absent` | Mirrors committed root Menu visibility. |
| <span id="context-menu-attribute-ccontext-menu-root-attributes-data-disabled"></span>`data-disabled` | ContextMenu host | `present | absent` | Mirrors effective component, native target, and fieldset disabledness. |
| <span id="context-menu-attribute-ccontext-menu-root-attributes-data-size"></span>`data-size` | ContextMenu host | `"sm" | "md" | "lg"` ([`CMenuSize`](#context-menu-interface-menu-size)) | Mirrors effective CMenu item geometry. |
| <span id="context-menu-attribute-ccontext-menu-root-attributes-data-invocation"></span>`data-invocation` | ContextMenu host | `"pointer" | "keyboard" | "long-press" | "external" | absent` | Identifies the latest accepted invocation only while the Menu is open. |

</div>

#### CContextMenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="context-menu-attribute-ccontext-menu-target-attributes-target-id"></span>`id` | Bound target Element | `root ID plus -target` | Uses the exact owned target identity from target_attrs. |
| <span id="context-menu-attribute-ccontext-menu-target-attributes-native-escape"></span>`data-citry-context-menu-native` | Target or descendant | `present | absent` | Preserves the browser context menu for a consumer-declared native path. |

</div>

#### CContextMenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-surface-id"></span>`id` | Root Menu surface | `root ID plus -menu` | Uses the exact owned root Menu identity. |
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-popover"></span>`popover` | Root and submenu Menu surfaces | `"manual"` | Uses native top-layer presence with Citry dismissal. |
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-role"></span>`role` | Root and submenu Menu surfaces | `"menu"` | Exposes application Menu semantics. |
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-aria-label"></span>`aria-label` | Root Menu surface | `non-whitespace string` | Uses required aria_label without naming the arbitrary target as a Menu Button. |
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-menu-data-open"></span>`data-open` | Root and submenu Menu surfaces | `present | absent` | Mirrors logical Menu visibility. |
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-data-placement"></span>`data-placement` | Root Menu surface | `"bottom-start"` | Mirrors the fixed requested logical point placement rather than collision result. |
| <span id="context-menu-attribute-ccontext-menu-surface-attributes-menu-data-size"></span>`data-size` | Root Menu surface | `"sm" | "md" | "lg"` ([`CMenuSize`](#context-menu-interface-menu-size)) | Mirrors effective Menu item geometry. |

</div>

#### CContextMenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-item-role"></span>`role` | Menu item, group, separator, submenu trigger, or submenu surface | `CMenu-owned role` | Uses existing CMenu command, choice, group, separator, and submenu semantics. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-labelledby"></span>`aria-labelledby` | Menu item or labelled group | `owned label IDREF | absent` | Uses existing CMenu exact visible labels. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-describedby"></span>`aria-describedby` | Menu item root | `description IDREF | absent` | Uses an optional separate CMenu item description. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-disabled"></span>`aria-disabled` | Menu item root | `"true" | absent` | Represents a focusable inactive CMenu item. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-data-item-disabled"></span>`data-disabled` | Menu item root | `present | absent` | Mirrors effective CMenu item disabledness. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-data-intent"></span>`data-intent` | Menu item root | `"default" | "danger"` | Mirrors existing CMenu item emphasis. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-checked"></span>`aria-checked` | Checkbox or radio item | `"false" | "true" | "mixed"` | Uses effective CMenu choice state; radio items never use mixed. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-data-checked"></span>`data-checked` | Checkbox or radio item | `"false" | "true" | "mixed"` | Mirrors effective CMenu choice state. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-haspopup"></span>`aria-haspopup` | Submenu trigger | `"menu"` | Announces an existing CMenu child surface. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-controls"></span>`aria-controls` | Submenu trigger | `child Menu IDREF` | References the existing child Menu surface. |
| <span id="context-menu-attribute-ccontext-menu-reused-item-attributes-aria-expanded"></span>`aria-expanded` | Submenu trigger | `"true" | "false"` | Mirrors existing child Menu visibility. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CContextMenu selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="context-menu-selector-ccontext-menu-selectors-context-menu"></span>`[data-citry-ui-part="context-menu"]` | Host div | Lifecycle owner and class_, style, and attrs destination; it has no visual box. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu"></span>`[data-citry-ui-part="menu"]` | Root or submenu Menu surface | Existing CMenu Popover presence and collection focus. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-item"></span>`[data-citry-ui-part="menu-item"]` | Command, link, checkbox, or radio root | Existing CMenu item styling. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-item-start"></span>`[data-citry-ui-part="menu-item-start"]` | Decorative item wrapper | Existing logical-start content. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-item-label"></span>`[data-citry-ui-part="menu-item-label"]` | Visible item label | Existing layout and exact accessible-name target. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-item-description"></span>`[data-citry-ui-part="menu-item-description"]` | Optional item description | Existing supporting text and accessible description. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-item-end"></span>`[data-citry-ui-part="menu-item-end"]` | Decorative item wrapper | Existing shortcut or logical-end content. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-choice-indicator"></span>`[data-citry-ui-part="menu-choice-indicator"]` | Decorative choice marker | Existing checkbox and radio state. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-group"></span>`[data-citry-ui-part="menu-group"]` | Labelled group root | Existing grouped-command layout. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-group-label"></span>`[data-citry-ui-part="menu-group-label"]` | Visible group label | Existing exact group name and layout. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-radio-group"></span>`[data-citry-ui-part="menu-radio-group"]` | Radio-group root | Existing exclusive choice grouping. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-separator"></span>`[data-citry-ui-part="menu-separator"]` | Horizontal separator | Existing collection division. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-submenu"></span>`[data-citry-ui-part="menu-submenu"]` | Neutral submenu wrapper | Existing child trigger and surface ownership. |
| <span id="context-menu-selector-ccontext-menu-selectors-menu-submenu-trigger"></span>`[data-citry-ui-part="menu-submenu-trigger"]` | Submenu Button | Existing child Menu activation and placement anchor. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="context-menu-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="context-menu-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="context-menu-interface-menu-size"></span>`CMenuSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="context-menu-interface-ccontext-menu-target-slot-data"></span>

#### `CContextMenuTargetSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="context-menu-interface-ccontext-menu-target-slot-data-target-attrs"></span>`target_attrs` | `dict[str, object]` | - | Generated target ID, private ownership marker, and the validated copied target_attrs mapping. |

</div>

<span id="context-menu-interface-ccontext-menu-menu-slot-data"></span>

#### `CContextMenuMenuSlotData`

Empty dataclass: `{}`.

<span id="context-menu-interface-ccontext-menu-open-change-detail"></span>

#### `CContextMenuOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="context-menu-interface-ccontext-menu-open-change-detail-reason"></span>`reason` | `"contextmenu" | "keyboard" | "long-press" | "escape" | "outside" | "focus-outside" | "tab" | "action" | "native" | "disabled" | "ancestor"` | - | Cause of the requested or forced visibility change. |
| <span id="context-menu-interface-ccontext-menu-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client Boolean owns desired Menu visibility. |
| <span id="context-menu-interface-ccontext-menu-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether native or structural safety overrides owner refusal. |
| <span id="context-menu-interface-ccontext-menu-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Responsible composed-path target, focused Element, item, surface, target, or ancestor when still connected. |
| <span id="context-menu-interface-ccontext-menu-open-change-detail-client-x"></span>`clientX` | `float` | - | Candidate or latest committed visual-viewport-clamped x coordinate. |
| <span id="context-menu-interface-ccontext-menu-open-change-detail-client-y"></span>`clientY` | `float` | - | Candidate or latest committed visual-viewport-clamped y coordinate. |

</div>

<span id="context-menu-interface-ccontext-menu-action-detail"></span>

#### `CMenuActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="context-menu-interface-ccontext-menu-action-detail-kind"></span>`kind` | `"command" | "checkbox" | "radio"` | - | Activated semantic CMenu item kind. |
| <span id="context-menu-interface-ccontext-menu-action-detail-item"></span>`item` | `Element` | - | Activated CMenu item root. |
| <span id="context-menu-interface-ccontext-menu-action-detail-event"></span>`event` | `Event` | - | Native CMenu activation event. |
| <span id="context-menu-interface-ccontext-menu-action-detail-path"></span>`path` | `list[str]` | - | Canonical ancestor-submenu path from the ContextMenu root Menu. |

</div>

### Translation keys

-