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
