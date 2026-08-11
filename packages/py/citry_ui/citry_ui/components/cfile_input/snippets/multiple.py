import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultipleFiles(Component):
    template = """
      <form @submit.prevent="window.__selectedFiles = [...new FormData($event.target).getAll('evidence')]">
        <c-CDropTarget label="Research evidence" name="evidence" multiple variant="soft">
          Select or drop several files
        </c-CDropTarget>
        <c-CButton type="submit">Inspect FormData</c-CButton>
      </form>
    """


preview = MultipleFiles()

preview  # noqa: B018
