"""Shared Editable scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def editable_states_component(app: Citry) -> type[Component]:
    class CitryUiEditableStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-editable-ready>
            <h1>Editable states</h1>
            <form data-quality-editable-form>
              <c-CField required>
                <c-fill name="label">Project title</c-fill>
                <c-fill name="description">Rename the project without leaving context.</c-fill>
                <c-fill name="default">
                  <c-CEditable value="Aurora atlas" name="title" />
                </c-fill>
              </c-CField>
            </form>
            <c-CEditable value="Inside actions" editing c-input_attrs="{'aria-label':'Inside actions'}" />
            <c-CEditable
              value="Outside actions" editing action_position="outside" variant="filled"
              c-input_attrs="{'aria-label':'Outside actions'}"
            />
            <c-CEditable value="Read only" readonly c-input_attrs="{'aria-label':'Read only'}" />
            <c-CEditable value="Disabled" disabled c-input_attrs="{'aria-label':'Disabled'}" />
            <div dir="rtl" style="inline-size:16rem">
              <c-CEditable value="عنوان المشروع" editing c-input_attrs="{'aria-label':'عنوان المشروع'}" />
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CEditable value="Night title" variant="plain" size="lg" />
            </div>
          </section>
        """

    return CitryUiEditableStates
