import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InlineSpinner(Component):
    template = """
      <section class="spinner-inline">
        <c-CRow gap="sm">
          <c-CSpinner label="Indexing nebula spectra" size="sm" />
          <span>Indexing nebula spectra</span>
        </c-CRow>
        <p>The rest of the observing log remains readable while the index catches up.</p>
      </section>
    """
    css = """
      :where(.spinner-inline) {
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-inline p) {
        margin-block-end: 0;
        color: light-dark(#57566f, #c8c6df);
        font-size: 0.8rem;
      }
    """


preview = InlineSpinner()

preview  # noqa: B018
