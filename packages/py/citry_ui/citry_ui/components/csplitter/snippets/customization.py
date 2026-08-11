import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedSplitter(Component):
    template = """
      <div class="brand-splitter">
        <style>
          .brand-splitter {
            --cui-splitter-radius: 1.25rem;
            --cui-splitter-handle-active-color: rebeccapurple;
            --cui-splitter-background: color-mix(in srgb, rebeccapurple 7%, Canvas);
          }
          .brand-splitter [data-citry-ui-part="panel"] { overflow-wrap: anywhere; }
        </style>
        <c-CSplitter c-sizes="[38, 62]" variant="outline" size="lg">
          <c-CSplitterPanel id="index" label="Index">Branded index</c-CSplitterPanel>
          <c-CSplitterPanel id="article" label="Article">Branded article</c-CSplitterPanel>
        </c-CSplitter>
      </div>
    """


preview = CustomizedSplitter()
preview  # noqa: B018
