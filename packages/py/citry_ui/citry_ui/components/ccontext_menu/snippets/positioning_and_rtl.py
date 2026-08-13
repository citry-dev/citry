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
