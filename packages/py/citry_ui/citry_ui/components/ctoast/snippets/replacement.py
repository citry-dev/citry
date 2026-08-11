import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastReplacement(Component):
    template = """
      <section class="toast-example" x-data="{progress: 20}">
        <c-CButton @click="progress = Math.min(100, progress + 20)">Advance upload</c-CButton>
        <c-CToastRegion c-duration_ms="0" $c-props="{items: [{
          id: 'upload', title: `Upload ${progress}% complete`, description: 'Aurora Ridge photos'
        }]}" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastReplacement()
preview  # noqa: B018
