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
