---
title: ScrollArea
url: https://citry.dev/v/0.4.1/ui-library/components/scroll-area/
description: "Keep bounded content reachable through native scrolling."
---
# ScrollArea

Use `CScrollArea` when bounded content needs a consistent focus stop, optional
region name, logical-axis policy, normalized scroll callback, or retained-root
lifecycle behavior. The component renders one native scrolling `div`. The
browser still owns its scrollbar, wheel, touch, trackpad, and keyboard behavior.

Use ordinary CSS when `overflow: auto` is enough. ScrollArea does not replace
native scrollbars or add track, thumb, corner, edge-shadow, or scroll-button
elements.

## Start with one native viewport

The default slot is transparent. It adds no content wrapper and does not change
the semantics, focus order, or layout of its children.


```citry-html
<c-CScrollArea aria_label="Recent activity">
  <ol>
    <li>Import completed</li>
    <li>Review requested</li>
    <li>Release approved</li>
  </ol>
</c-CScrollArea>
```


When `aria_label` or `aria_labelledby` is supplied, the viewport becomes a
named region. Omit both for a generic focusable viewport. The two inputs are
mutually exclusive.


### Block, inline, and two-axis native scrolling

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/at-a-glance/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CScrollArea

citry.register_library(citry_ui)


class ScrollAreaAtAGlance(Component):
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
            "python_activity": CScrollArea(
                style={"--cui-scroll-area-max-block-size": "7rem"},
                slots={
                    "default": (
                        "Python composition keeps the same native viewport. ",
                        "Its content remains ordinary escaped slot content. ",
                        "The scrollbar belongs to the browser.",
                    ),
                },
            ),
        }

    template = """
      <section class="scroll-area-glance">
        <article>
          <h3>Recent activity</h3>
          <c-CScrollArea
            aria_label="Recent activity"
            style="--cui-scroll-area-max-block-size: 9rem"
          >
            <ol class="scroll-area-glance__activity">
              <li>Import completed</li>
              <li>Review requested</li>
              <li>Access approved</li>
              <li>Build started</li>
              <li>Checks completed</li>
              <li>Release published</li>
              <li>Audit archived</li>
            </ol>
          </c-CScrollArea>
        </article>

        <article>
          <h3>Applied filters</h3>
          <c-CScrollArea
            axis="inline"
            aria_label="Applied filters"
          >
            <div class="scroll-area-glance__rail">
              <span>Region: Central Europe</span>
              <span>Status: Needs review</span>
              <span>Owner: Operations</span>
              <span>Window: Last 90 days</span>
            </div>
          </c-CScrollArea>
        </article>

        <article>
          <h3>Result matrix</h3>
          <c-CScrollArea
            axis="both"
            aria_label="Result matrix"
            style="--cui-scroll-area-max-block-size: 9rem"
          >
            <div class="scroll-area-glance__matrix">
              <strong>Service</strong><strong>Owner</strong><strong>Region</strong>
              <span>Accounts</span><span>Identity</span><span>Prague</span>
              <span>Ledger</span><span>Finance</span><span>Berlin</span>
              <span>Search</span><span>Discovery</span><span>Vienna</span>
              <span>Archive</span><span>Records</span><span>Warsaw</span>
            </div>
          </c-CScrollArea>
        </article>

        <article>
          <h3>Python composition</h3>
          {{ python_activity }}
        </article>
      </section>
    """

    css = """
      :where(.scroll-area-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-glance article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-inline-size: 0;
      }

      :where(.scroll-area-glance h3) {
        margin: 0;
      }

      :where(.scroll-area-glance__activity) {
        display: grid;
        gap: 0.5rem;
        margin: 0;
        padding: 1rem 1rem 1rem 2rem;
      }

      :where(.scroll-area-glance__rail) {
        display: flex;
        inline-size: max-content;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-glance__rail span) {
        padding: 0.375rem 0.625rem;
        border-radius: 999px;
        background: color-mix(in srgb, Highlight 14%, Canvas);
      }

      :where(.scroll-area-glance__matrix) {
        display: grid;
        grid-template-columns: repeat(3, minmax(9rem, 1fr));
        gap: 1px;
        inline-size: max-content;
        min-inline-size: 30rem;
        background: color-mix(in srgb, CanvasText 18%, transparent);
      }

      :where(.scroll-area-glance__matrix > *) {
        padding: 0.625rem;
        background: Canvas;
      }
    """


preview = ScrollAreaAtAGlance()

preview  # noqa: B018
````


## Enter the viewport with the keyboard

The viewport always has `tabindex="0"` and a visible focus ring. Native Page,
Home, End, Space, arrow, wheel, and touch behavior stays with the browser, so
exact keys and pixel increments can differ by platform. Focusable children keep
their ordinary Tab order. ScrollArea never traps or moves focus.


### Viewport and descendant focus

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/activity-and-focus/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaActivityAndFocus(Component):
    template = """
      <section
        class="scroll-area-focus"
        x-data="{last:'Focus the viewport, a link, or an action'}"
        @activity-focus="last=$event.detail"
        @activity-blur="last=$event.detail"
      >
        <p>
          Tab enters the viewport before its descendants. Native scrolling
          keys keep focus on the viewport.
        </p>
        <c-CScrollArea
          aria_label="Deployment activity"
          style="--cui-scroll-area-max-block-size: 15rem"
          c-attrs="{
            '@focus':'$dispatch(`activity-focus`, `Focused ${$event.target.id}`)',
            '@blur':'$dispatch(`activity-blur`, `Left ${$event.target.id}`)',
          }"
          $c-props="{
            onScrollChange:(detail)=>
              last=`Block offset ${Math.round(detail.blockOffset)}`,
          }"
          id="deployment-activity"
        >
          <ol class="scroll-area-focus__timeline">
            <li>
              <strong>09:10</strong>
              <span>Build completed.</span>
              <a href="#build-details">View build details</a>
            </li>
            <li>
              <strong>09:18</strong>
              <span>Security review requested.</span>
              <c-CButton size="sm" variant="outline">Open review</c-CButton>
            </li>
            <li>
              <strong>09:26</strong>
              <span>Staging deployment completed.</span>
              <a href="#staging-log">Read staging log</a>
            </li>
            <li>
              <strong>09:42</strong>
              <span>Production approval received.</span>
              <c-CButton size="sm">Publish release</c-CButton>
            </li>
            <li>
              <strong>09:51</strong>
              <span>Release notes archived.</span>
              <a href="#release-notes">Open release notes</a>
            </li>
          </ol>
        </c-CScrollArea>
        <output x-text="last">Focus the viewport, a link, or an action</output>
      </section>
    """

    css = """
      :where(.scroll-area-focus) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-focus p, .scroll-area-focus output) {
        margin: 0;
      }

      :where(.scroll-area-focus__timeline) {
        display: grid;
        gap: 1rem;
        margin: 0;
        padding: 1rem 1rem 1rem 2.5rem;
      }

      :where(.scroll-area-focus__timeline li) {
        display: grid;
        grid-template-columns: 4rem 1fr;
        gap: 0.375rem 0.75rem;
        align-items: center;
      }

      :where(.scroll-area-focus__timeline li > :not(strong)) {
        grid-column: 2;
      }
    """


preview = ScrollAreaActivityAndFocus()

preview  # noqa: B018
````


Do not attach a root key handler to reproduce native scrolling. It can consume
Home, End, or arrow keys intended for an input or another interactive child.

## Keep wide data semantic

Use `axis="both"` for a table or other surface whose meaning requires two
dimensions. The slotted Table keeps its own caption, headers, cells, and focus
behavior. ScrollArea only supplies the bounded native viewport.


### A semantic table at narrow width

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/wide-table/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaWideTable(Component):
    template = """
      <section class="scroll-area-wide-table" x-data="{direction:'ltr'}">
        <h2 id="quarterly-results-title">Quarterly service results</h2>
        <p>
          The Table keeps its caption and headers. ScrollArea only bounds the
          two-dimensional viewport.
        </p>
        <button
          type="button"
          @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
        >Flip table direction</button>
        <div :dir="direction">
          <c-CScrollArea
            axis="both"
            aria_labelledby="quarterly-results-title"
            style="--cui-scroll-area-max-block-size: 16rem"
          >
            <table class="scroll-area-wide-table__table">
            <caption>Latency and availability by quarter</caption>
            <thead>
              <tr>
                <th scope="col">Service</th>
                <th scope="col">Q1 latency</th>
                <th scope="col">Q2 latency</th>
                <th scope="col">Q3 latency</th>
                <th scope="col">Q4 latency</th>
                <th scope="col">Availability</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Accounts</a></th>
                <td>112 ms</td><td>104 ms</td><td>98 ms</td>
                <td>91 ms</td><td>99.99%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Ledger</a></th>
                <td>190 ms</td><td>172 ms</td><td>160 ms</td>
                <td>151 ms</td><td>99.97%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Search</a></th>
                <td>86 ms</td><td>81 ms</td><td>74 ms</td>
                <td>69 ms</td><td>99.95%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Archive</a></th>
                <td>244 ms</td><td>231 ms</td><td>218 ms</td>
                <td>205 ms</td><td>99.90%</td>
              </tr>
              <tr>
                <th scope="row"><a href="#quarterly-results-title">Reports</a></th>
                <td>155 ms</td><td>149 ms</td><td>141 ms</td>
                <td>134 ms</td><td>99.96%</td>
              </tr>
            </tbody>
            </table>
          </c-CScrollArea>
        </div>
        <p class="scroll-area-wide-table__print-note">
          This fixture supplies its own compact print table so the final
          column fits inside the physical page.
        </p>
      </section>
    """

    css = """
      :where(.scroll-area-wide-table) {
        display: grid;
        gap: 0.75rem;
        inline-size: min(100%, 42rem);
        min-inline-size: 0;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-wide-table h2, .scroll-area-wide-table p) {
        margin: 0;
      }

      :where(.scroll-area-wide-table > button) {
        justify-self: start;
      }

      :where(.scroll-area-wide-table__table) {
        inline-size: 52rem;
        border-collapse: collapse;
      }

      :where(.scroll-area-wide-table__table caption) {
        padding: 0.75rem;
        font-weight: 700;
        text-align: start;
      }

      :where(.scroll-area-wide-table__table th,
        .scroll-area-wide-table__table td) {
        min-inline-size: 7rem;
        padding: 0.625rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        text-align: start;
      }

      :where(.scroll-area-wide-table__table thead th) {
        background: color-mix(in srgb, Highlight 12%, Canvas);
      }

      @media print {
        :where(.scroll-area-wide-table) {
          inline-size: 100%;
        }

        :where(.scroll-area-wide-table__table) {
          inline-size: 100%;
          table-layout: fixed;
          font-size: 8pt;
        }

        :where(.scroll-area-wide-table__table th,
          .scroll-area-wide-table__table td) {
          min-inline-size: 0;
          padding: 0.2rem;
          overflow-wrap: anywhere;
        }
      }
    """


preview = ScrollAreaWideTable()

preview  # noqa: B018
````


At 400 percent zoom, prefer block flow unless two-dimensional content is
essential. In print, ScrollArea removes its own maximum size, border, and
overflow clipping. An application must still reflow, scale, rotate, or replace
content that is wider than the physical page.

## Change native overflow policy

`axis` accepts logical `block`, `inline`, or `both`. `scrollbar_width` accepts
`auto` or `thin`. `scrollbar_gutter` accepts `auto`, `stable`, or
`stable-both-edges`. Native scrollbar thickness, overlay behavior, and gutter
pixels remain browser and operating-system choices.

`overscroll="contain"` limits native scroll chaining on enabled axes, while
`none` also requests suppression of local boundary effects. These are CSS
policies, not promises that every browser, device, or synthetic event delivers
the same gesture behavior.

The policies follow [CSS Overflow](https://drafts.csswg.org/css-overflow/),
[CSS Scrollbars](https://drafts.csswg.org/css-scrollbars/), and
[CSS Overscroll Behavior](https://drafts.csswg.org/css-overscroll-1/).


### Reactive axis and scrollbar policy

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaConfiguration(Component):
    template = """
      <section
        class="scroll-area-configuration"
        x-data="{
          axis:'block',
          width:'auto',
          gutter:'auto',
          overscroll:'auto',
          show:(value)=>value ?? 'server fallback',
        }"
      >
        <div class="scroll-area-configuration__controls">
          <label>
            Axis
            <select x-model="axis">
              <option value="block">Block</option>
              <option value="inline">Inline</option>
              <option value="both">Both</option>
            </select>
          </label>
          <label>
            Scrollbar width
            <select x-model="width">
              <option value="auto">Auto</option>
              <option value="thin">Thin</option>
            </select>
          </label>
          <label>
            Scrollbar gutter
            <select x-model="gutter">
              <option value="auto">Auto</option>
              <option value="stable">Stable</option>
              <option value="stable-both-edges">Both edges</option>
            </select>
          </label>
          <label>
            Overscroll
            <select x-model="overscroll">
              <option value="auto">Auto</option>
              <option value="contain">Contain</option>
              <option value="none">None</option>
            </select>
          </label>
        </div>

        <c-CScrollArea
          id="scroll-area-configuration-target"
          axis="block"
          aria_label="Configurable audit records"
          style="--cui-scroll-area-max-block-size: 12rem"
          $c-props="{
            axis,
            scrollbarWidth:width,
            scrollbarGutter:gutter,
            overscroll,
          }"
        >
          <div class="scroll-area-configuration__content">
            <span>Record 01</span><span>Identity review</span><span>Approved</span>
            <span>Record 02</span><span>Ledger review</span><span>Pending</span>
            <span>Record 03</span><span>Archive review</span><span>Approved</span>
            <span>Record 04</span><span>Search review</span><span>Pending</span>
            <span>Record 05</span><span>Report review</span><span>Approved</span>
            <span>Record 06</span><span>Export review</span><span>Pending</span>
          </div>
        </c-CScrollArea>

        <div class="scroll-area-configuration__actions">
          <button
            type="button"
            @click="axis=null;width=null;gutter=null;overscroll=null"
          >Release every override</button>
          <button type="button" @click="axis='diagonal'">
            Try an invalid axis
          </button>
        </div>
        <output
          x-text="`Requested: ${show(axis)}, ${show(width)}, ${show(gutter)}, ${show(overscroll)}`"
        >Requested: block, auto, auto, auto</output>
      </section>
    """

    css = """
      :where(.scroll-area-configuration) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-configuration__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.scroll-area-configuration__controls label) {
        display: grid;
        gap: 0.25rem;
      }

      :where(.scroll-area-configuration__content) {
        display: grid;
        grid-template-columns: repeat(3, minmax(9rem, 1fr));
        gap: 1px;
        inline-size: 38rem;
        min-block-size: 18rem;
        background: color-mix(in srgb, CanvasText 18%, transparent);
      }

      :where(.scroll-area-configuration__content span) {
        padding: 0.75rem;
        background: Canvas;
      }

      :where(.scroll-area-configuration__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ScrollAreaConfiguration()

preview  # noqa: B018
````


Client `axis`, `scrollbarWidth`, `scrollbarGutter`, and `overscroll` values win
field by field. `null` or omission releases one field to its latest server
fallback. An invalid value keeps the last valid effective value and reports one
diagnostic for that invalid episode.

The root owns instantaneous `scroll-behavior: auto` for direction, disabled-axis,
and morph repair. An application can still request a smooth native movement in
an explicit `scrollTo()` call, but it cannot replace the root's computed CSS
policy.

## Read logical RTL offsets

`onScrollChange` receives logical distance from inline start and block distance
from the top. RTL callers do not need to interpret a negative browser
`scrollLeft`. The detail describes the callback instant only and does not claim
persistent edge or progress state.

Raw viewport geometry and native events follow
[CSSOM View](https://drafts.csswg.org/cssom-view/).


### LTR and RTL logical offsets

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/rtl-and-direction/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaRtlAndDirection(Component):
    template = """
      <section
        class="scroll-area-direction"
        x-data="{
          direction:'ltr',
          ltrOffset:0,
          rtlOffset:0,
          flipOffset:0,
        }"
      >
        <div class="scroll-area-direction__controls">
          <button
            type="button"
            @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
          >Flip the third rail</button>
          <output x-text="`Third rail direction: ${direction}`">
            Third rail direction: ltr
          </output>
        </div>

        <div class="scroll-area-direction__grid">
          <article dir="ltr">
            <h3>LTR</h3>
            <c-CScrollArea
              axis="inline"
              aria_label="LTR deployment stages"
              $c-props="{
                onScrollChange:(detail)=>
                  ltrOffset=Math.round(detail.inlineOffset),
              }"
            >
              <div class="scroll-area-direction__rail">
                <span>Plan</span><span>Build</span><span>Review</span>
                <span>Approve</span><span>Publish</span><span>Archive</span>
              </div>
            </c-CScrollArea>
            <output x-text="`Logical offset ${ltrOffset}`">
              Logical offset 0
            </output>
          </article>

          <article dir="rtl">
            <h3>RTL</h3>
            <c-CScrollArea
              axis="inline"
              aria_label="مراحل النشر"
              $c-props="{
                onScrollChange:(detail)=>
                  rtlOffset=Math.round(detail.inlineOffset),
              }"
            >
              <div class="scroll-area-direction__rail">
                <span>تخطيط</span><span>بناء</span><span>مراجعة</span>
                <span>موافقة</span><span>نشر</span><span>أرشفة</span>
              </div>
            </c-CScrollArea>
            <output x-text="`Logical offset ${rtlOffset}`">
              Logical offset 0
            </output>
          </article>

          <article :dir="direction">
            <h3>Direction change</h3>
            <c-CScrollArea
              axis="inline"
              aria_label="Direction-changing stages"
              $c-props="{
                onScrollChange:(detail)=>
                  flipOffset=Math.round(detail.inlineOffset),
              }"
            >
              <div class="scroll-area-direction__rail">
                <span>North</span><span>South</span><span>East</span>
                <span>West</span><span>Coast</span><span>Harbor</span>
              </div>
            </c-CScrollArea>
            <output x-text="`Logical offset ${flipOffset}`">
              Logical offset 0
            </output>
          </article>
        </div>
      </section>
    """

    css = """
      :where(.scroll-area-direction) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-direction__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.scroll-area-direction__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
      }

      :where(.scroll-area-direction article) {
        display: grid;
        gap: 0.5rem;
        min-inline-size: 0;
      }

      :where(.scroll-area-direction h3) {
        margin: 0;
      }

      :where(.scroll-area-direction__rail) {
        display: flex;
        inline-size: max-content;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-direction__rail span) {
        min-inline-size: 7rem;
        padding: 0.625rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, Highlight 12%, Canvas);
        text-align: center;
      }
    """


preview = ScrollAreaRtlAndDirection()

preview  # noqa: B018
````


A direction change preserves the last cached logical distance when the same
root remains connected. Stylesheet-only direction changes are reconciled at
the next native scroll, configuration update, or Citry morph settlement.
Vertical writing modes keep usable native overflow but suspend normalized
callbacks and lifecycle repair.

## Nest independent scrolling regions

Nested ScrollAreas remain ordinary nested native scroll containers. The
browser decides which area receives a gesture. Give nested named regions
distinct useful names, and leave incidental regions unnamed.


### Nested regions and overscroll policy

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/nested-areas/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaNestedAreas(Component):
    template = """
      <section class="scroll-area-nested" x-data="{direction:'ltr'}">
        <h2>Operations document</h2>
        <p>
          The outer document and inner inspector are separate native scroll
          containers. Tab order and gesture targeting stay with the browser.
        </p>
        <button
          type="button"
          @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
        >Flip document direction</button>
        <div :dir="direction">
          <c-CScrollArea
            overscroll="auto"
            style="--cui-scroll-area-max-block-size: 20rem"
          >
            <div class="scroll-area-nested__document">
            <p>
              The deployment plan contains enough content to scroll before
              and after the nested inspector.
            </p>
            <p>
              Review the service boundary, owner, and current policy before
              continuing to the approval section.
            </p>

              <c-CScrollArea
                aria_label="Service inspector"
                overscroll="contain"
                style="--cui-scroll-area-max-block-size: 10rem"
              >
                <dl class="scroll-area-nested__inspector">
                <dt>Service</dt><dd>Ledger export</dd>
                <dt>Owner</dt><dd>Finance platform</dd>
                <dt>Region</dt><dd>Central Europe</dd>
                <dt>Status</dt><dd>Needs approval</dd>
                <dt>Retention</dt><dd>Seven years</dd>
                <dt>Encryption</dt><dd>Customer managed</dd>
                <dt>Review</dt><dd>Quarterly</dd>
                </dl>
              </c-CScrollArea>

              <c-CScrollArea axis="inline" overscroll="none">
                <div class="scroll-area-nested__rail">
                  <span>Plan</span><span>Build</span><span>Review</span>
                  <span>Approve</span><span>Release</span>
                </div>
              </c-CScrollArea>

            <p>
              Continue through the remaining deployment notes after leaving
              the inspector.
            </p>
            <p>
              The outer viewport does not register the inner viewport as a
              widget or arbitrate its gestures.
            </p>
            <p>
              Real wheel, precision trackpad, and touch behavior remains a
              platform acceptance check.
            </p>
            </div>
          </c-CScrollArea>
        </div>
      </section>
    """

    css = """
      :where(.scroll-area-nested) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-nested h2, .scroll-area-nested p) {
        margin: 0;
      }

      :where(.scroll-area-nested > button) {
        justify-self: start;
      }

      :where(.scroll-area-nested__document) {
        display: grid;
        gap: 1.5rem;
        padding: 1rem;
      }

      :where(.scroll-area-nested__inspector) {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 0.625rem 1rem;
        margin: 0;
        padding: 1rem;
      }

      :where(.scroll-area-nested__inspector dt) {
        font-weight: 700;
      }

      :where(.scroll-area-nested__inspector dd) {
        margin: 0;
      }

      :where(.scroll-area-nested__rail) {
        display: flex;
        inline-size: max-content;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-nested__rail span) {
        min-inline-size: 7rem;
        padding: 0.5rem;
        background: color-mix(in srgb, Highlight 12%, Canvas);
      }
    """


preview = ScrollAreaNestedAreas()

preview  # noqa: B018
````


## Distinguish the component callback from native events

`onScrollChange` is a semantic component callback supplied through `$c-props`.
It runs at most once per animation frame after one or more actual native
`scroll` events. It receives the latest native event as `detail.source`.
Content resize, image load, configuration changes, and component-owned repairs
do not create this callback.


### Event-scoped logical scroll details

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/native-callback/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaNativeCallback(Component):
    template = """
      <section
        class="scroll-area-callback"
        x-data="{
          rows:6,
          sentinelTop:150,
          imageVisible:false,
          expanded:false,
          nativeCount:0,
          settled:0,
          callbackCount:0,
          lastInline:0,
          lastBlock:0,
        }"
        @scroll-area-native="nativeCount += 1"
        @scroll-area-settled="settled += 1"
        x-init="$nextTick(() => {
          const host = $refs.shadowHost;
          const fixture = $refs.shadowFixture;
          if (!host.shadowRoot && fixture) host.attachShadow({mode:'open'}).append(fixture);
        })"
      >
        <div class="scroll-area-callback__controls">
          <button type="button" @click="rows += 2">Add content</button>
          <button type="button" @click="rows = Math.max(1, rows - 2)">
            Remove content
          </button>
          <button type="button" @click="sentinelTop += 80">
            Move absolute marker
          </button>
          <button
            type="button"
            @click="setTimeout(()=>imageVisible=true,350)"
          >Load a delayed image</button>
          <button type="button" @click="expanded=!expanded">
            Toggle content stylesheet
          </button>
        </div>

        <c-CScrollArea
          axis="both"
          aria_label="Event-scoped audit log"
          style="--cui-scroll-area-max-block-size: 13rem"
          c-attrs="{
            '@scroll':'$dispatch(`scroll-area-native`)',
            '@scrollend':'$dispatch(`scroll-area-settled`)',
          }"
          $c-props="{
            onScrollChange:(detail)=>{
              callbackCount += 1;
              lastInline = Math.round(detail.inlineOffset);
              lastBlock = Math.round(detail.blockOffset);
            },
          }"
        >
          <div
            class="scroll-area-callback__content"
            :class="{'scroll-area-callback__content--expanded':expanded}"
          >
            <template x-for="row in rows" :key="row">
              <p x-text="`Audit row ${row}: current native content`"></p>
            </template>
            <span
              class="scroll-area-callback__sentinel"
              :style="`inset-block-start:${sentinelTop}px`"
            >Absolute marker</span>
            <template x-if="imageVisible">
              <img
                class="scroll-area-callback__image"
                alt="Delayed audit chart"
                src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
              />
            </template>
            <div x-ref="shadowHost" class="scroll-area-callback__shadow-host">
              <div x-ref="shadowFixture">
                <p style="inline-size:26rem;min-block-size:5rem;padding:0.5rem">
                  Open ShadowRoot content changes native layout without creating
                  a component callback.
                </p>
              </div>
            </div>
          </div>
        </c-CScrollArea>

        <dl class="scroll-area-callback__readout">
          <dt>Native scroll events</dt><dd x-text="nativeCount">0</dd>
          <dt>Native scrollend events</dt><dd x-text="settled">0</dd>
          <dt>Component callbacks</dt><dd x-text="callbackCount">0</dd>
          <dt>Logical inline offset</dt><dd x-text="lastInline">0</dd>
          <dt>Block offset</dt><dd x-text="lastBlock">0</dd>
        </dl>
      </section>
    """

    css = """
      :where(.scroll-area-callback) {
        display: grid;
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-callback__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.scroll-area-callback__content) {
        position: relative;
        inline-size: 44rem;
        min-block-size: 26rem;
        padding: 1rem;
      }

      :where(.scroll-area-callback__content--expanded) {
        min-block-size: 34rem;
      }

      :where(.scroll-area-callback__content p) {
        margin: 0 0 1rem;
      }

      :where(.scroll-area-callback__sentinel) {
        position: absolute;
        inset-inline-start: 28rem;
        padding: 0.375rem 0.625rem;
        border-radius: 0.375rem;
        background: color-mix(in srgb, Highlight 18%, Canvas);
      }

      :where(.scroll-area-callback__image) {
        display: block;
        inline-size: 30rem;
        block-size: 6rem;
        margin-block: 1rem;
        background: color-mix(in srgb, Highlight 14%, Canvas);
      }

      :where(.scroll-area-callback__shadow-host) {
        display: block;
        min-inline-size: 26rem;
        min-block-size: 5rem;
        border: 1px dashed GrayText;
      }

      :where(.scroll-area-callback__readout) {
        display: grid;
        grid-template-columns: max-content 1fr;
        gap: 0.375rem 1rem;
        margin: 0;
      }

      :where(.scroll-area-callback__readout dt) {
        font-weight: 700;
      }

      :where(.scroll-area-callback__readout dd) {
        margin: 0;
      }
    """


preview = ScrollAreaNativeCallback()

preview  # noqa: B018
````


Native root events remain Alpine listeners in `attrs`:


```citry-html
<section
  x-data="{nativeCount:0,settled:false,last:0}"
  @build-log-scroll="nativeCount += 1"
  @build-log-settled="settled = true"
>
  <c-CScrollArea
    aria_label="Build log"
    c-attrs="{
      '@scroll':'$dispatch(`build-log-scroll`)',
      '@scrollend':'$dispatch(`build-log-settled`)',
    }"
    $c-props="{onScrollChange:(detail)=>last=detail.blockOffset}"
  >
    ...
  </c-CScrollArea>
</section>
```


Native listeners observe every browser event, including an event produced by
component-owned coordinate repair. ScrollArea dispatches no custom DOM event
and exposes no public method. A listener on a component root has Citry's
isolated component scope, so it cannot read ancestor-local `x-data` identifiers
directly. Use `$event`, `$dispatch`, `$store`, or another explicit global bridge;
use `onScrollChange` for owner-local callback state. Application controls can
use an ordinary DOM ref and the native `scrollTo()` or `scrollBy()` method.

## Customize standards-based styling

Public variables control the viewport's size, colors, border, radius, padding,
focus ring, scroll padding, and complete standard `scrollbar-color` value. The
one stable selector targets the same native viewport.


### Public variables and the viewport selector

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaCustomization(Component):
    template = """
      <section class="scroll-area-customization">
        <article class="scroll-area-brand scroll-area-brand--orchard">
          <h3>Orchard notes</h3>
          <c-CScrollArea
            class_="brand-scroll"
            aria_label="Orchard notes"
            scrollbar_width="thin"
            scrollbar_gutter="stable"
          >
            <div class="scroll-area-customization__notes">
              <p>Pear block: pollinator rows checked.</p>
              <p>North field: irrigation pressure normal.</p>
              <p>West field: pruning review scheduled.</p>
              <p>Harvest window: seven days remaining.</p>
              <p>Cold store: capacity confirmed.</p>
            </div>
          </c-CScrollArea>
        </article>

        <article
          class="scroll-area-brand scroll-area-brand--harbor"
          style="color-scheme:dark"
        >
          <h3>Harbor notes</h3>
          <c-CScrollArea
            class_="brand-scroll"
            aria_label="Harbor notes"
            scrollbar_gutter="stable-both-edges"
          >
            <div class="scroll-area-customization__notes">
              <p>North berth: loading complete.</p>
              <p>East pier: tide window confirmed.</p>
              <p>Customs desk: manifest approved.</p>
              <p>Harbor pilot: departure booked.</p>
              <p>Weather station: visibility clear.</p>
            </div>
          </c-CScrollArea>
        </article>
      </section>
    """

    css = """
      :where(.scroll-area-customization) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-brand) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.scroll-area-brand h3) {
        margin: 0;
      }

      :where(.scroll-area-brand--orchard) {
        background: #f5f0df;
        color: #203422;
        --cui-scroll-area-max-block-size: 10rem;
        --cui-scroll-area-background: #fffdf5;
        --cui-scroll-area-foreground: #203422;
        --cui-scroll-area-border-color: #78916d;
        --cui-scroll-area-focus-color: #315f37;
        --cui-scroll-area-radius: 1rem;
      }

      :where(.scroll-area-brand--harbor) {
        background: #102b38;
        color: #eefaff;
        --cui-scroll-area-max-block-size: 10rem;
        --cui-scroll-area-background: #173c4c;
        --cui-scroll-area-foreground: #eefaff;
        --cui-scroll-area-border-color: #72b5ce;
        --cui-scroll-area-focus-color: #c6ecff;
        --cui-scroll-area-scrollbar-color: #9eddf4 #173c4c;
      }

      .scroll-area-brand
      .brand-scroll[data-citry-ui-part="scroll-area"] {
        border-width: 2px;
      }

      :where(.scroll-area-customization__notes) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-customization__notes p) {
        margin: 0;
      }

      @media (forced-colors: active) {
        :where(.scroll-area-brand) {
          border: 1px solid CanvasText;
        }
      }

      @media print {
        :where(.scroll-area-brand) {
          background: transparent;
          color: black;
        }
      }
    """


preview = ScrollAreaCustomization()

preview  # noqa: B018
````


Citry uses `scrollbar-width`, `scrollbar-color`, and `scrollbar-gutter`. Vendor
scrollbar pseudo-elements are not public API. Forced colors restore platform
scrollbar, border, and focus colors. Unlayered application rules override the
Citry UI theme layer whether loaded before or after the component stylesheet.
A named application layer must be ordered after `citry-ui.theme`.

## Respect the clipping boundary

Native overflow clips ordinary positioned descendants. A dropdown, tooltip,
or menu cannot escape merely because it appears in the default slot. Compose a
supported Citry overlay or native top-layer element whose own contract defines
its host, focus, and layering.


### Clipped content and an independently owned overlay

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/overlay-boundary/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaOverlayBoundary(Component):
    template = """
      <section class="scroll-area-overlay-boundary">
        <h2>Credential review</h2>
        <p>
          The red sample is ordinary positioned content and clips at the
          viewport. The Popover follows its own anchored-layer contract.
        </p>
        <c-CScrollArea
          aria_label="Credential review notes"
          style="--cui-scroll-area-max-block-size: 12rem"
        >
          <div class="scroll-area-overlay-boundary__content">
            <span class="scroll-area-overlay-boundary__clipped">
              Ordinary positioned note
            </span>
            <p>Confirm the token owner and intended service boundary.</p>
            <p>Review the current scopes before granting another permission.</p>
            <c-CPopover>
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton
                  size="sm"
                  variant="outline"
                  c-attrs="activator_attrs"
                >Open scope help</c-CButton>
              </c-fill>
              <c-fill name="title">Credential scope</c-fill>
              <c-fill name="default">
                Grant only the permissions this worker needs.
              </c-fill>
            </c-CPopover>
            <p>Record the approval before rotating the credential.</p>
            <p>Archive the previous key after the overlap window closes.</p>
          </div>
        </c-CScrollArea>
      </section>
    """

    css = """
      :where(.scroll-area-overlay-boundary) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-overlay-boundary h2,
        .scroll-area-overlay-boundary p) {
        margin: 0;
      }

      :where(.scroll-area-overlay-boundary__content) {
        position: relative;
        display: grid;
        gap: 1rem;
        min-block-size: 22rem;
        padding: 1rem;
      }

      :where(.scroll-area-overlay-boundary__clipped) {
        position: absolute;
        inset-block-start: 1rem;
        inset-inline-end: -5rem;
        inline-size: 8rem;
        padding: 0.5rem;
        border: 2px solid #b42318;
        background: Canvas;
        color: #b42318;
      }
    """


preview = ScrollAreaOverlayBoundary()

preview  # noqa: B018
````


ScrollArea does not register as an overlay owner, lock page scroll, make
siblings inert, or create a stacking context.

## Preserve only a retained root

A correlated Citry morph that retains the same root preserves valid client
configuration, cached logical position, and focus on that root. Incoming
server values become new fallbacks for fields without client ownership.


### Retained-root morph and replacement scope

[Open the rendered preview](/v/0.4.1/ui-library/components/scroll-area/_previews/lifecycle/)

````citry
from __future__ import annotations

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaLifecycle(Component):
    class Kwargs:
        step: int = 0
        replacement: int = 0

    class Slots:
        pass

    class Events:
        def refresh(self) -> ScrollAreaLifecycle:
            return ScrollAreaLifecycle(step=1, replacement=0)

        def replace(self) -> ScrollAreaLifecycle:
            return ScrollAreaLifecycle(step=2, replacement=1)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "root_key": f"scroll-area-lifecycle-{kwargs.replacement}",
            "step": kwargs.step,
        }

    template = """
      <section
        class="scroll-area-lifecycle"
        x-data="{mounted:true,lastOffset:0,direction:'ltr'}"
      >
        <div class="scroll-area-lifecycle__controls">
          <button type="button" @c-click="refresh">
            Retained-root server morph
          </button>
          <button type="button" @c-click="replace">
            Replace the root
          </button>
          <button type="button" @click="mounted=!mounted">
            Remove or restore locally
          </button>
          <button
            type="button"
            @click="direction=direction === 'ltr' ? 'rtl' : 'ltr'"
          >Flip direction</button>
          <button
            type="button"
            @click="
              const area=$root.querySelector('#scroll-area-lifecycle-target');
              if (area) {
                area.setAttribute('tabindex','-1');
                area.setAttribute('role','button');
                area.dataset.axis='invalid';
              }
            "
          >Damage then repair owned attributes</button>
          <button
            type="button"
            @click="
              const area=$root.querySelector('#scroll-area-lifecycle-target');
              if (area) area.style.writingMode =
                area.style.writingMode === 'vertical-rl'
                  ? 'horizontal-tb'
                  : 'vertical-rl';
            "
          >Toggle unsupported writing mode</button>
        </div>

        <p>Server step: <output>{{ step }}</output></p>

        <template x-if="mounted">
          <div :dir="direction">
            <c-CScrollArea
              #c-key="root_key"
              id="scroll-area-lifecycle-target"
              axis="both"
              aria_label="Lifecycle audit records"
              style="--cui-scroll-area-max-block-size: 12rem"
              $c-props="{
                onScrollChange:(detail)=>
                  lastOffset=Math.round(detail.blockOffset),
              }"
            >
              <div class="scroll-area-lifecycle__content">
                <p>Server generation {{ step }}</p>
                <p>Scroll before using a server action.</p>
                <p>A retained root preserves its logical position and focus.</p>
                <p>A replacement root starts with native browser position.</p>
                <p>Removal cancels pending callback and observer work.</p>
                <p>Restoration creates a fresh local instance.</p>
                <p>Nested content focus is never redirected.</p>
                <p>The viewport remains useful without JavaScript.</p>
              </div>
            </c-CScrollArea>
          </div>
        </template>

        <output x-text="`Last user scroll offset ${lastOffset}`">
          Last user scroll offset 0
        </output>
      </section>
    """

    css = """
      :where(.scroll-area-lifecycle) {
        display: grid;
        gap: 1rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-lifecycle__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.scroll-area-lifecycle p) {
        margin: 0;
      }

      :where(.scroll-area-lifecycle__content) {
        display: grid;
        grid-template-columns: repeat(2, minmax(16rem, 1fr));
        gap: 1rem;
        inline-size: 42rem;
        min-block-size: 24rem;
        padding: 1rem;
      }

      :where(.scroll-area-lifecycle__content p) {
        padding: 0.75rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, Highlight 10%, Canvas);
      }
    """


preview = ScrollAreaLifecycle()

preview  # noqa: B018
````


A replacement root, even with the same authored ID, starts with native browser
position. Removal cancels pending callbacks and lifecycle work. Restoring a new
root does not inherit the removed instance's offsets or focus.

## Keep the native fallback useful

Without JavaScript, server output is already one focusable native viewport
with its configured axis, standard scrollbar, gutter, overscroll, colors, and
slot content. A supplied name already emits the region and naming attribute.
Client enhancement only adds reactive configuration, normalized callbacks,
direction repair, and retained-root lifecycle behavior.

## Treat root attributes as trusted configuration

`class_`, `style`, and `attrs` all target the native viewport. `attrs` accepts
ordinary descriptive attributes, `dir`, language hints, nonreserved `data-*`,
and native Alpine event listeners that respect the isolated scope boundary. It
rejects values that replace the root ID, role, focusability, region name, part
marker, reflected state, lifecycle, or owned scrolling policy.

Slotted text and components follow Citry's normal trusted content boundary.
ScrollArea does not evaluate content as HTML, URLs, selectors, or Alpine
expressions.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CScrollArea server inputs

Server inputs are passed in a template through `<c-CScrollArea ... />` or in Python through
`CScrollArea(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 11rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="scroll-area-input-cscroll-area-server-inputs-id"></span>`id` | `str | None` | generated | Sets the native viewport ID. |
| <span id="scroll-area-input-cscroll-area-server-inputs-aria-label"></span>`aria_label` | `str | None` | `None` | Adds a nonempty direct region name and the region role; mutually exclusive with aria_labelledby. |
| <span id="scroll-area-input-cscroll-area-server-inputs-aria-labelledby"></span>`aria_labelledby` | `str | None` | `None` | Adds a validated IDREF-list region name and the region role; mutually exclusive with aria_label. |
| <span id="scroll-area-input-cscroll-area-server-inputs-axis"></span>`axis` | `"block" | "inline" | "both"` ([`CScrollAreaAxis`](#scroll-area-interface-axis)) | `"block"` | Selects logical native overflow axes. |
| <span id="scroll-area-input-cscroll-area-server-inputs-scrollbar-width"></span>`scrollbar_width` | `"auto" | "thin"` ([`CScrollAreaScrollbarWidth`](#scroll-area-interface-scrollbar-width)) | `"auto"` | Selects the standard native scrollbar width policy without hiding it. |
| <span id="scroll-area-input-cscroll-area-server-inputs-scrollbar-gutter"></span>`scrollbar_gutter` | `"auto" | "stable" | "stable-both-edges"` ([`CScrollAreaScrollbarGutter`](#scroll-area-interface-scrollbar-gutter)) | `"auto"` | Selects standard native scrollbar-space reservation. |
| <span id="scroll-area-input-cscroll-area-server-inputs-overscroll"></span>`overscroll` | `"auto" | "contain" | "none"` ([`CScrollAreaOverscroll`](#scroll-area-interface-overscroll)) | `"auto"` | Selects logical overscroll policy on enabled axes. |
| <span id="scroll-area-input-cscroll-area-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#scroll-area-interface-class-value)) | `None` | Adds native viewport classes and merges them with attrs. |
| <span id="scroll-area-input-cscroll-area-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#scroll-area-interface-style-value)) | `None` | Adds native viewport styles and merges them with attrs before the owned scrolling policy. |
| <span id="scroll-area-input-cscroll-area-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed descriptive attributes and isolated-scope native listeners that may use event magics, dispatch, stores, or globals. |

</div>

#### CScrollArea client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CScrollArea />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 15rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="scroll-area-input-cscroll-area-client-inputs-axis"></span>`axis` | `"block" | "inline" | "both"` ([`CScrollAreaAxis`](#scroll-area-interface-axis)) | Uses the latest server fallback; null has the same effect. | Controls logical overflow axes while valid. |
| <span id="scroll-area-input-cscroll-area-client-inputs-scrollbar-width"></span>`scrollbarWidth` | `"auto" | "thin"` ([`CScrollAreaScrollbarWidth`](#scroll-area-interface-scrollbar-width)) | Uses the latest server fallback; null has the same effect. | Controls standard native scrollbar width policy while valid. |
| <span id="scroll-area-input-cscroll-area-client-inputs-scrollbar-gutter"></span>`scrollbarGutter` | `"auto" | "stable" | "stable-both-edges"` ([`CScrollAreaScrollbarGutter`](#scroll-area-interface-scrollbar-gutter)) | Uses the latest server fallback; null has the same effect. | Controls standard native scrollbar-space reservation while valid. |
| <span id="scroll-area-input-cscroll-area-client-inputs-overscroll"></span>`overscroll` | `"auto" | "contain" | "none"` ([`CScrollAreaOverscroll`](#scroll-area-interface-overscroll)) | Uses the latest server fallback; null has the same effect. | Controls logical overscroll policy while valid. |
| <span id="scroll-area-input-cscroll-area-client-inputs-on-scroll-change"></span>`onScrollChange` | `function` | Omission or null selects no component callback. | Receives one event-scoped normalized snapshot for the latest native scroll event in a frame. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CScrollArea slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="scroll-area-slot-cscroll-area-slots-default"></span>`default` | no | `none` | Renders an empty focusable native viewport. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CScrollArea events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="scroll-area-event-cscroll-area-events-scroll-change"></span>`onScrollChange` | `(detail: CScrollAreaScrollDetail) => void` ([`CScrollAreaScrollDetail`](#scroll-area-interface-cscroll-area-scroll-detail)) | One or more actual native scroll events occur on the valid initialized viewport. | `{inlineOffset, blockOffset, source}` ([`CScrollAreaScrollDetail`](#scroll-area-interface-cscroll-area-scroll-detail)) | Runs at most once per animation frame with the latest event. Return values do not cancel native scrolling; controlled state does not exist. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CScrollArea CSS variables

Apply these variables to `CScrollArea` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="scroll-area-css-cscroll-area-css-variables-max-block-size"></span>`--cui-scroll-area-max-block-size` | `length or none` | Maximum block size for block and both-axis viewports. | `20rem` |
| <span id="scroll-area-css-cscroll-area-css-variables-background"></span>`--cui-scroll-area-background` | `color` | Native viewport background. | `Canvas` |
| <span id="scroll-area-css-cscroll-area-css-variables-foreground"></span>`--cui-scroll-area-foreground` | `color` | Inherited viewport foreground. | `CanvasText` |
| <span id="scroll-area-css-cscroll-area-css-variables-border-color"></span>`--cui-scroll-area-border-color` | `color` | Native viewport border. | `color-mix(in srgb, currentColor 24%, transparent)` |
| <span id="scroll-area-css-cscroll-area-css-variables-border-width"></span>`--cui-scroll-area-border-width` | `length` | Native viewport border width. | `1px` |
| <span id="scroll-area-css-cscroll-area-css-variables-radius"></span>`--cui-scroll-area-radius` | `length` | Native viewport corner radius. | `0.75rem` |
| <span id="scroll-area-css-cscroll-area-css-variables-padding"></span>`--cui-scroll-area-padding` | `length` | Content inset inside the native viewport. | `0px` |
| <span id="scroll-area-css-cscroll-area-css-variables-scrollbar-color"></span>`--cui-scroll-area-scrollbar-color` | `complete scrollbar-color value` | Standard native thumb and track colors as one property value. | `auto` |
| <span id="scroll-area-css-cscroll-area-css-variables-focus-color"></span>`--cui-scroll-area-focus-color` | `color` | Viewport focus-visible ring. | `#2563eb` |
| <span id="scroll-area-css-cscroll-area-css-variables-scroll-padding"></span>`--cui-scroll-area-scroll-padding` | `length` | Native focus and anchor scroll padding. | `0px` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CScrollArea attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="scroll-area-attribute-cscroll-area-attributes-root-id"></span>`id` | Native viewport div | `supplied or generated string` | Identifies the single component root and viewport. |
| <span id="scroll-area-attribute-cscroll-area-attributes-tabindex"></span>`tabindex` | Native viewport div | `"0"` | Places the viewport in sequential keyboard focus order. |
| <span id="scroll-area-attribute-cscroll-area-attributes-role"></span>`role` | Native viewport div | `absent | "region"` | Present only when exactly one naming input is supplied. |
| <span id="scroll-area-attribute-cscroll-area-attributes-aria-label"></span>`aria-label` | Native viewport div | `string | absent` | Supplies the direct region name only when aria_label is used. |
| <span id="scroll-area-attribute-cscroll-area-attributes-aria-labelledby"></span>`aria-labelledby` | Native viewport div | `IDREF list | absent` | Supplies the referenced region name only when aria_labelledby is used. |
| <span id="scroll-area-attribute-cscroll-area-attributes-data-axis"></span>`data-axis` | Native viewport div | `"block" | "inline" | "both"` ([`CScrollAreaAxis`](#scroll-area-interface-axis)) | Mirrors the effective logical axis policy. |
| <span id="scroll-area-attribute-cscroll-area-attributes-data-scrollbar-width"></span>`data-scrollbar-width` | Native viewport div | `"auto" | "thin"` ([`CScrollAreaScrollbarWidth`](#scroll-area-interface-scrollbar-width)) | Mirrors the effective standard scrollbar width policy. |
| <span id="scroll-area-attribute-cscroll-area-attributes-data-scrollbar-gutter"></span>`data-scrollbar-gutter` | Native viewport div | `"auto" | "stable" | "stable-both-edges"` ([`CScrollAreaScrollbarGutter`](#scroll-area-interface-scrollbar-gutter)) | Mirrors the effective standard gutter policy. |
| <span id="scroll-area-attribute-cscroll-area-attributes-data-overscroll"></span>`data-overscroll` | Native viewport div | `"auto" | "contain" | "none"` ([`CScrollAreaOverscroll`](#scroll-area-interface-overscroll)) | Mirrors the effective logical overscroll policy. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CScrollArea selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="scroll-area-selector-cscroll-area-selectors-scroll-area"></span>`[data-citry-ui-part="scroll-area"]` | Native viewport div | The focusable scroll viewport and class_, style, and attrs destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="scroll-area-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="scroll-area-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="scroll-area-interface-axis"></span>`CScrollAreaAxis` | `Literal["block", "inline", "both"]` |
| <span id="scroll-area-interface-scrollbar-width"></span>`CScrollAreaScrollbarWidth` | `Literal["auto", "thin"]` |
| <span id="scroll-area-interface-scrollbar-gutter"></span>`CScrollAreaScrollbarGutter` | `Literal["auto", "stable", "stable-both-edges"]` |
| <span id="scroll-area-interface-overscroll"></span>`CScrollAreaOverscroll` | `Literal["auto", "contain", "none"]` |

</div>

<span id="scroll-area-interface-cscroll-area-scroll-detail"></span>

#### `CScrollAreaScrollDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="scroll-area-interface-cscroll-area-scroll-detail-inline-offset"></span>`inlineOffset` | `float` | - | Logical horizontal distance from inline start, clamped to the current native range. |
| <span id="scroll-area-interface-cscroll-area-scroll-detail-block-offset"></span>`blockOffset` | `float` | - | Vertical distance from the top, clamped to the current native range. |
| <span id="scroll-area-interface-cscroll-area-scroll-detail-source"></span>`source` | `Event` | - | Latest native scroll event coalesced into this callback frame. |

</div>

### Translation keys

-