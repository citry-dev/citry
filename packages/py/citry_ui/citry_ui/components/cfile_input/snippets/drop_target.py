import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FileDropTarget(Component):
    template = """
      <div >
        <c-CDropTarget
          label="Supporting documents"
          name="documents"
          multiple
          @change="names = [...$event.target.files].map(file => file.name)"
        >
          PDF or image files
        </c-CDropTarget>
        <p v-text="names.join(', ')"></p>
      </div>
    """
    js = """
      $component({
        data() {
          return {
            names: []
          };
        },
      });
    """


preview = FileDropTarget()

preview  # noqa: B018
