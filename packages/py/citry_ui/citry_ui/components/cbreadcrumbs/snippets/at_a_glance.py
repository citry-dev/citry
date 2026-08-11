import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbsAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Library", "/library"),
                citry_ui.CBreadcrumbItem("Natural history", "/library/nature"),
                citry_ui.CBreadcrumbItem("The hidden life of trees"),
            )
        }

    template = """
      <section class="breadcrumb-shelf">
        <c-CBreadcrumbs c-items="items" label="Book location" />
        <h2>The hidden life of trees</h2>
        <p>Essays on forests, roots, and the communities beneath them.</p>
      </section>
    """
    css = """
      :where(.breadcrumb-shelf) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b8aa92, #655a49);
        border-radius: 0.9rem;
        color: CanvasText;
        font-family: ui-serif, Georgia, serif;
      }

      :where(.breadcrumb-shelf h2, .breadcrumb-shelf p) {
        margin: 0;
      }
    """


preview = BreadcrumbsAtAGlance()

preview  # noqa: B018
