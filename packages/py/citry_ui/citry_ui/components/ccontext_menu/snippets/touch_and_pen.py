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
