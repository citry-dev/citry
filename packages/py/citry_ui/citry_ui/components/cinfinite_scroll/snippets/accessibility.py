import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAccessibility(Component):
    template = """
      <c-CInfiniteScroll aria_label="Completed notifications" c-has_more="False">
        <ul><li>Backup completed</li><li>Invoice sent</li></ul>
      </c-CInfiniteScroll>
    """


preview = InfiniteScrollAccessibility()
preview  # noqa: B018
