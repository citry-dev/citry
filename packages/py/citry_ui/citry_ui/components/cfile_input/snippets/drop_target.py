import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileDropTarget(Component):
    template = """
      <div x-data="{names: []}">
        <c-CDropTarget
          label="Supporting documents"
          name="documents"
          multiple
          @change="names = [...$event.target.files].map(file => file.name)"
        >
          PDF or image files
        </c-CDropTarget>
        <p x-text="names.join(', ')"></p>
      </div>
    """


preview = FileDropTarget()

preview  # noqa: B018
