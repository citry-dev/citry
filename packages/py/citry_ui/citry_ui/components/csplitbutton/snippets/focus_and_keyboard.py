import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonFocusAndKeyboard(Component):
    template = """
      <section
        class="split-button-keyboard-demo"

      >
        <h2>Keyboard specimen workflow</h2>
        <p>
          Tab reaches the primary and Menu Button in DOM order. Enter or Space activates the
          focused Button. In the Menu, use arrows, Home, End, typeahead, and Escape.
        </p>
        <div class="split-button-keyboard-demo__controls">
          <label><input type="checkbox" v-model="loading" /> Primary loading</label>
          <label><input type="checkbox" v-model="primaryDisabled" /> Primary disabled</label>
          <label><input type="checkbox" v-model="menuDisabled" /> Menu disabled</label>
        </div>

        <div class="split-button-keyboard-demo__row" dir="ltr">
          <span>LTR</span>
          <c-CSplitButton
            ref="ltrSplit"
            label="Keyboard save actions"
            menu_label="More keyboard save actions"
            v-bind="{loading, primaryDisabled, menuDisabled}"
          >
            <c-fill name="default">Save field note</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="duplicate">Duplicate note</c-CMenuItem>
              <c-CMenuItem value="export">Export note</c-CMenuItem>
              <c-CMenuItem value="archive">Archive note</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>

        <div class="split-button-keyboard-demo__row" dir="rtl">
          <span>RTL</span>
          <c-CSplitButton
            ref="rtlSplit"
            label="إجراءات حفظ العينة"
            menu_label="المزيد من إجراءات حفظ العينة"
          >
            <c-fill name="default">حفظ ملاحظة العينة</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="duplicate-rtl">نسخ الملاحظة</c-CMenuItem>
              <c-CMenuItem value="export-rtl">تصدير الملاحظة</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </div>

        <output aria-live="polite" v-text="trace.length ? trace.join(' → ') : 'Focus trace is empty'">
          Focus trace is empty
        </output>
        <button type="button" @click="trace=[]">Clear focus trace</button>
      </section>
    """

    js = r"""
      $component({
        data(){return {trace:[], loading:false, primaryDisabled:false, menuDisabled:false};},
        onServerRender({component}) {
          const removers=[];
          for (const [name,label] of [['ltrSplit','LTR'],['rtlSplit','RTL']]) {
            const host=component.$refs[name].$el;
            for (const [selector,part] of [
              ['[data-citry-ui-part="split-button-primary"]','primary'],
              ['[data-citry-ui-part="split-button-menu-trigger"]','menu'],
            ]) {
              const element=host.querySelector(selector);
              const listener=()=>component.trace.push(`${label} ${part}`);
              element.addEventListener('focus',listener);
              removers.push(()=>element.removeEventListener('focus',listener));
            }
          }
          return ()=>removers.forEach((remove)=>remove());
        },
      });
    """

    css = """
      :where(.split-button-keyboard-demo) {
        display: grid;
        gap: 1rem;
        inline-size: min(100%, 32rem);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.split-button-keyboard-demo h2, .split-button-keyboard-demo p) { margin: 0; }
      :where(.split-button-keyboard-demo__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
      :where(.split-button-keyboard-demo__row) {
        display: grid;
        gap: 0.5rem;
        justify-items: start;
        inline-size: min(100%, 20rem);
      }
      :where(.split-button-keyboard-demo output) { overflow-wrap: anywhere; }
    """


preview = SplitButtonFocusAndKeyboard()

preview  # noqa: B018
