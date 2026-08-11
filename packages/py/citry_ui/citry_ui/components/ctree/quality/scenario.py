"""Shared Tree scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def tree_states_component(app: Citry) -> type[Component]:
    class CitryUiTreeStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-tree-ready>
            <h1>Tree states</h1>
            <c-CTree label="Files" c-expanded="['src']" c-selected="['app']" variant="outline">
              <c-CTreeItem value="src" label="src">
                <c-CTreeItem value="app" label="app.py" />
                <c-CTreeItem value="style" label="style.css" />
              </c-CTreeItem>
              <c-CTreeItem value="tests" label="tests" />
              <c-CTreeItem value="readme" label="README" />
            </c-CTree>
            <c-CTree label="Multiple" selection_mode="multiple" c-selected="['one', 'three']" variant="soft" size="sm">
              <c-CTreeItem value="one" label="One" />
              <c-CTreeItem value="two" label="Two" disabled />
              <c-CTreeItem value="three" label="Three" />
            </c-CTree>
            <fieldset disabled>
              <legend>Locked Tree</legend>
              <c-CTree label="Locked">
                <c-CTreeItem value="locked-a" label="A" />
                <c-CTreeItem value="locked-b" label="B" />
              </c-CTree>
            </fieldset>
            <div dir="rtl">
              <c-CTree label="شجرة" variant="outline">
                <c-CTreeItem value="rtl-a" label="فرع طويل للغاية" />
                <c-CTreeItem value="rtl-b" label="عنصر طويل للغاية" />
              </c-CTree>
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CTree label="Night" c-selected="['night-b']" variant="soft" size="lg">
                <c-CTreeItem value="night-a" label="Night A" />
                <c-CTreeItem value="night-b" label="Night B" />
              </c-CTree>
            </div>
          </section>
        """

    return CitryUiTreeStates
