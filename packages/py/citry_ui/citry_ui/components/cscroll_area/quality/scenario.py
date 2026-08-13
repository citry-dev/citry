"""Shared ScrollArea scenario used by repository quality tools."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component


def scroll_area_states_component(app: Citry) -> type[Component]:
    """Create the reusable ScrollArea state and environment scenario."""

    class CitryUiScrollAreaStates(Component):
        citry = app

        class Kwargs:
            morph_step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def refresh(self, state: Any) -> CitryUiScrollAreaStates:
                state.morph_step += 1
                component_type: Any = CitryUiScrollAreaStates
                return component_type(morph_step=state.morph_step)

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            if kwargs.morph_step < 2:
                lifecycle_key = "scroll-area-quality-retained"
            elif kwargs.morph_step == 2:
                lifecycle_key = "scroll-area-quality-replacement"
            else:
                lifecycle_key = "scroll-area-quality-restored"
            return {
                "include_lifecycle": kwargs.morph_step != 3,
                "lifecycle_key": lifecycle_key,
                "lifecycle_states": (
                    "lifecycle retained-root replacement-root morph-target removal restore cleanup "
                    "owner-token writing-mode focus-preservation"
                ),
                "morph_step": kwargs.morph_step,
            }

        template = """
          <section
            class="citry-ui-quality-stack scroll-area-quality"
            aria-labelledby="scroll-area-states-title"
            @c-quality-morph="refresh"
            @quality-native-scroll="nativeScrolls += 1"
            @quality-native-settled="nativeSettles += 1"
            x-data="{
              axis:'both',
              width:'auto',
              gutter:'stable',
              overscroll:'auto',
              nativeScrolls:0,
              nativeSettles:0,
              callbackCount:0,
              lastInline:0,
              lastBlock:0,
              lifecycleCallbacks:0,
            }"
          >
            <h1 id="scroll-area-states-title">ScrollArea states</h1>
            <output hidden data-quality-morph-step>{{ morph_step }}</output>

            <div class="citry-ui-quality-grid">
              <article>
                <h2>Block activity</h2>
                <c-CScrollArea
                  id="quality-scroll-area-block"
                  aria_label="Quality activity"
                  style="--cui-scroll-area-max-block-size: 10rem"
                  c-attrs="{
                    'data-quality-states':
                      'block named-region focus keyboard native no-js long-content'
                  }"
                >
                  <ol class="scroll-area-quality__stacked-content">
                    <li>Import completed</li>
                    <li>Review requested</li>
                    <li>Policy approved</li>
                    <li>Build completed</li>
                    <li>Release published</li>
                    <li>Archive verified</li>
                  </ol>
                </c-CScrollArea>
              </article>

              <article>
                <h2>Generic viewport</h2>
                <c-CScrollArea
                  id="quality-scroll-area-generic"
                  style="--cui-scroll-area-max-block-size: 8rem"
                  c-attrs="{
                    'data-quality-states':
                      'generic unnamed empty-valid semantics shadow-root'
                  }"
                >
                  <p>
                    This viewport has no landmark role or accessible-name
                    attribute. It remains an explicit native focus stop.
                  </p>
                  <p>More generic content makes its block overflow visible.</p>
                </c-CScrollArea>
                <div id="quality-scroll-area-shadow-host"></div>
              </article>

              <article dir="ltr">
                <h2>LTR inline rail</h2>
                <c-CScrollArea
                  id="quality-scroll-area-ltr"
                  axis="inline"
                  aria_label="LTR quality stages"
                  c-attrs="{
                    'data-quality-states':
                      'inline ltr logical-offset long-unbroken'
                  }"
                >
                  <div class="scroll-area-quality__rail">
                    <span>Plan</span><span>Build</span><span>Review</span>
                    <span>Approve</span><span>Publish</span><span>Archive</span>
                  </div>
                </c-CScrollArea>
              </article>

              <article dir="rtl">
                <h2>RTL inline rail</h2>
                <c-CScrollArea
                  id="quality-scroll-area-rtl"
                  axis="inline"
                  aria_label="مراحل الجودة"
                  scrollbar_width="thin"
                  c-attrs="{
                    'data-quality-states':
                      'inline rtl negative-model thin direction-change'
                  }"
                >
                  <div class="scroll-area-quality__rail">
                    <span>تخطيط</span><span>بناء</span><span>مراجعة</span>
                    <span>موافقة</span><span>نشر</span><span>أرشفة</span>
                  </div>
                </c-CScrollArea>
              </article>
            </div>

            <article>
              <h2 id="quality-wide-table-title">Both-axis results</h2>
              <c-CScrollArea
                id="quality-scroll-area-both"
                axis="both"
                aria_labelledby="quality-wide-table-title"
                scrollbar_gutter="stable-both-edges"
                style="--cui-scroll-area-max-block-size: 12rem"
                c-attrs="{
                  'data-quality-states':
                    'both aria-labelledby table narrow zoom-400 print stable-both-edges'
                }"
              >
                <table class="scroll-area-quality__table">
                  <caption>Service results by quarter</caption>
                  <thead>
                    <tr>
                      <th scope="col">Service</th>
                      <th scope="col">Q1</th>
                      <th scope="col">Q2</th>
                      <th scope="col">Q3</th>
                      <th scope="col">Q4</th>
                      <th scope="col">Availability</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <th scope="row">Accounts</th>
                      <td>112 ms</td><td>104 ms</td><td>98 ms</td>
                      <td>91 ms</td><td>99.99%</td>
                    </tr>
                    <tr>
                      <th scope="row">Ledger</th>
                      <td>190 ms</td><td>172 ms</td><td>160 ms</td>
                      <td>151 ms</td><td>99.97%</td>
                    </tr>
                    <tr>
                      <th scope="row">Search</th>
                      <td>86 ms</td><td>81 ms</td><td>74 ms</td>
                      <td>69 ms</td><td>99.95%</td>
                    </tr>
                    <tr>
                      <th scope="row">Archive</th>
                      <td>244 ms</td><td>231 ms</td><td>218 ms</td>
                      <td>205 ms</td><td>99.90%</td>
                    </tr>
                  </tbody>
                </table>
              </c-CScrollArea>
            </article>

            <article class="scroll-area-quality__configuration">
              <h2>Reactive configuration</h2>
              <div class="scroll-area-quality__controls">
                <button type="button" @click="axis='block'">Block</button>
                <button type="button" @click="axis='inline'">Inline</button>
                <button type="button" @click="axis='both'">Both</button>
                <button type="button" @click="axis=null">Release axis</button>
                <button type="button" @click="axis='diagonal'">
                  Invalid axis
                </button>
                <button
                  type="button"
                  @click="width=width === 'auto' ? 'thin' : 'auto'"
                >Toggle width</button>
                <button
                  type="button"
                  @click="gutter=gutter === 'stable' ? 'auto' : 'stable'"
                >Toggle gutter</button>
                <button
                  type="button"
                  @click="overscroll=overscroll === 'auto' ? 'contain' : 'auto'"
                >Toggle overscroll</button>
              </div>
              <c-CScrollArea
                id="quality-scroll-area-configuration"
                axis="both"
                aria_label="Reactive configuration records"
                style="--cui-scroll-area-max-block-size: 10rem;scroll-behavior:smooth !important"
                c-attrs="{
                  'data-quality-states':
                    'configuration controlled release invalid repair smooth-owned disabled-axis reflections'
                }"
                $c-props="{
                  axis,
                  scrollbarWidth:width,
                  scrollbarGutter:gutter,
                  overscroll,
                }"
              >
                <div class="scroll-area-quality__large-content">
                  Reactive configuration subject
                </div>
              </c-CScrollArea>
            </article>

            <article>
              <h2>Native and component notifications</h2>
              <c-CScrollArea
                id="quality-scroll-area-callback"
                axis="both"
                aria_label="Callback records"
                style="max-inline-size:20rem;--cui-scroll-area-max-block-size:10rem"
                c-attrs="{
                  '@scroll':'$dispatch(`quality-native-scroll`)',
                  '@scrollend':'$dispatch(`quality-native-settled`)',
                  'data-quality-states':
                    'callback native-scroll native-scrollend coalesced absolute-content resize-content'
                }"
                $c-props="{
                  onScrollChange:(detail)=>{
                    callbackCount += 1;
                    lastInline = Math.round(detail.inlineOffset);
                    lastBlock = Math.round(detail.blockOffset);
                  },
                }"
              >
                <div class="scroll-area-quality__callback-content">
                  <p>Content changes do not synthesize a callback.</p>
                  <p>Only an actual native scroll creates a detail.</p>
                  <span class="scroll-area-quality__absolute">Absolute edge</span>
                </div>
              </c-CScrollArea>
              <output id="scroll-area-quality-log">
                Native:
                <span data-quality-native-scrolls x-text="nativeScrolls">0</span>;
                settled:
                <span data-quality-native-settles x-text="nativeSettles">0</span>;
                callbacks:
                <span data-quality-callbacks x-text="callbackCount">0</span>;
                inline:
                <span data-quality-inline-offset x-text="lastInline">0</span>;
                block:
                <span data-quality-block-offset x-text="lastBlock">0</span>
              </output>
            </article>

            <article>
              <h2>Nested native viewports</h2>
              <c-CScrollArea
                id="quality-scroll-area-outer"
                aria_label="Outer quality document"
                overscroll="auto"
                style="--cui-scroll-area-max-block-size: 14rem"
                c-attrs="{
                  'data-quality-states':
                    'nested outer auto touch wheel trackpad focus-order'
                }"
              >
                <div class="scroll-area-quality__nested-content">
                  <p>Outer content before the inspector.</p>
                  <c-CScrollArea
                    id="quality-scroll-area-inner"
                    aria_label="Inner quality inspector"
                    overscroll="contain"
                    style="--cui-scroll-area-max-block-size: 7rem"
                    c-attrs="{
                      'data-quality-states':
                        'nested inner contain independent-focus'
                    }"
                  >
                    <div class="scroll-area-quality__stacked-content">
                      Inner row one<br />Inner row two<br />Inner row three<br />
                      Inner row four<br />Inner row five<br />Inner row six
                    </div>
                  </c-CScrollArea>
                  <p>Outer content after the inspector.</p>
                  <p>Gesture delivery remains native.</p>
                </div>
              </c-CScrollArea>
            </article>

            <div class="scroll-area-quality__brand-grid">
              <article class="scroll-area-quality__orchard">
                <h2>Orchard theme</h2>
                <c-CScrollArea
                  class_="quality-scroll-area-brand"
                  aria_label="Orchard records"
                  scrollbar_width="thin"
                  scrollbar_gutter="stable"
                  c-attrs="{
                    'data-quality-states':
                      'brand-orchard light variables selector thin stable'
                  }"
                >
                  <div class="scroll-area-quality__stacked-content">
                    Orchard row one<br />Orchard row two<br />Orchard row three<br />
                    Orchard row four<br />Orchard row five
                  </div>
                </c-CScrollArea>
              </article>

              <article
                class="scroll-area-quality__harbor"
                style="color-scheme:dark"
              >
                <h2>Harbor theme</h2>
                <c-CScrollArea
                  class_="quality-scroll-area-brand"
                  aria_label="Harbor records"
                  c-attrs="{
                    'data-quality-states':
                      'brand-harbor dark variables selector forced-colors'
                  }"
                >
                  <div class="scroll-area-quality__stacked-content">
                    Harbor row one<br />Harbor row two<br />Harbor row three<br />
                    Harbor row four<br />Harbor row five
                  </div>
                </c-CScrollArea>
              </article>
            </div>

            <c-if cond="include_lifecycle">
              <div>
                <c-CScrollArea
                  #c-key="lifecycle_key"
                  id="quality-scroll-area-lifecycle"
                  axis="both"
                  aria_label="Lifecycle records"
                  style="max-inline-size:20rem;--cui-scroll-area-max-block-size:10rem"
                  c-attrs="{'data-quality-states':lifecycle_states}"
                  $c-props="{
                    onScrollChange:()=>lifecycleCallbacks += 1,
                  }"
                >
                  <div class="scroll-area-quality__large-content">
                    Lifecycle generation {{ morph_step }}
                  </div>
                </c-CScrollArea>
              </div>
            </c-if>
            <output id="scroll-area-quality-lifecycle-log">
              Lifecycle callbacks:
              <span data-quality-lifecycle-callbacks x-text="lifecycleCallbacks">0</span>
            </output>
          </section>
        """

        css = """
          :where(.scroll-area-quality article) {
            display: grid;
            gap: 0.75rem;
            min-inline-size: 0;
          }

          :where(.scroll-area-quality h2,
            .scroll-area-quality article > p) {
            margin: 0;
          }

          :where(.scroll-area-quality__stacked-content) {
            display: grid;
            gap: 0.75rem;
            min-block-size: 16rem;
            margin: 0;
            padding: 1rem;
          }

          :where(.scroll-area-quality__rail) {
            display: flex;
            inline-size: max-content;
            gap: 0.75rem;
            padding: 1rem;
          }

          :where(.scroll-area-quality__rail span) {
            min-inline-size: 7rem;
            padding: 0.625rem;
            border-radius: 0.5rem;
            background: color-mix(in srgb, Highlight 12%, Canvas);
            text-align: center;
          }

          :where(.scroll-area-quality__table) {
            inline-size: 52rem;
            border-collapse: collapse;
          }

          :where(.scroll-area-quality__table th,
            .scroll-area-quality__table td) {
            min-inline-size: 7rem;
            padding: 0.625rem;
            border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
            text-align: start;
          }

          :where(.scroll-area-quality__controls) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.625rem;
          }

          :where(.scroll-area-quality__large-content) {
            box-sizing: border-box;
            inline-size: 42rem;
            min-block-size: 24rem;
            padding: 1rem;
            background: linear-gradient(
              135deg,
              color-mix(in srgb, Highlight 12%, Canvas),
              Canvas
            );
          }

          :where(.scroll-area-quality__callback-content) {
            position: relative;
            inline-size: 36rem;
            min-block-size: 22rem;
            padding: 1rem;
          }

          :where(.scroll-area-quality__absolute) {
            position: absolute;
            inset-block-start: 18rem;
            inset-inline-start: 28rem;
          }

          :where(.scroll-area-quality__nested-content) {
            display: grid;
            gap: 1rem;
            min-block-size: 24rem;
            padding: 1rem;
          }

          :where(.scroll-area-quality__brand-grid) {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
            gap: 1rem;
          }

          :where(.scroll-area-quality__orchard,
            .scroll-area-quality__harbor) {
            padding: 1rem;
            border-radius: 1rem;
          }

          :where(.scroll-area-quality__orchard) {
            background: #f5f0df;
            color: #203422;
            --cui-scroll-area-max-block-size: 9rem;
            --cui-scroll-area-background: #fffdf5;
            --cui-scroll-area-foreground: #203422;
            --cui-scroll-area-border-color: #78916d;
            --cui-scroll-area-focus-color: #315f37;
          }

          :where(.scroll-area-quality__harbor) {
            background: #102b38;
            color: #eefaff;
            --cui-scroll-area-max-block-size: 9rem;
            --cui-scroll-area-background: #173c4c;
            --cui-scroll-area-foreground: #eefaff;
            --cui-scroll-area-border-color: #72b5ce;
            --cui-scroll-area-focus-color: #c6ecff;
            --cui-scroll-area-scrollbar-color: #9eddf4 #173c4c;
          }

          .scroll-area-quality
          .quality-scroll-area-brand[data-citry-ui-part="scroll-area"] {
            border-radius: 1rem;
          }

          @media (forced-colors: active) {
            :where(.scroll-area-quality__orchard,
              .scroll-area-quality__harbor) {
              border: 1px solid CanvasText;
            }
          }

          @media print {
            :where(.scroll-area-quality__table) {
              inline-size: 100%;
              table-layout: fixed;
              font-size: 8pt;
            }

            :where(.scroll-area-quality__table th,
              .scroll-area-quality__table td) {
              min-inline-size: 0;
              padding: 0.2rem;
              overflow-wrap: anywhere;
            }

            :where(.scroll-area-quality__orchard,
              .scroll-area-quality__harbor) {
              background: transparent;
              color: black;
            }
          }
        """

    return CitryUiScrollAreaStates
