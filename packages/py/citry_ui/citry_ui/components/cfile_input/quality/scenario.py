"""Shared FileInput scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def file_input_states_component(app: Citry) -> type[Component]:
    class CitryUiFileInputStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-file-input-ready>
            <h1>File input states</h1>
            <form>
              <c-CField required>
                <c-fill name="label">Required evidence</c-fill>
                <c-fill name="default"><c-CFileInput name="required_file" /></c-fill>
                <c-fill name="description">One document.</c-fill>
                <c-fill name="error">Choose a document.</c-fill>
              </c-CField>
              <c-CDropTarget label="Multiple evidence" name="evidence" multiple variant="soft">
                Drop files here or browse
              </c-CDropTarget>
              <button type="reset">Reset files</button>
            </form>
            <c-CRow>
              <c-CFileInput c-attrs="{'aria-label': 'Small file'}" size="sm" />
              <c-CFileInput c-attrs="{'aria-label': 'Large file'}" size="lg" variant="plain" />
            </c-CRow>
            <fieldset disabled>
              <legend>Disabled</legend>
              <c-CDropTarget label="Disabled drop" c-disabled="False" />
            </fieldset>
            <div dir="rtl">
              <c-CDropTarget label="مستندات طويلة" variant="outline">
                ملفملفملفملفملفملفملفملفملفملفملفملف
              </c-CDropTarget>
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CDropTarget label="Night evidence" variant="soft">Choose research notes</c-CDropTarget>
            </div>
          </section>
        """

    return CitryUiFileInputStates
