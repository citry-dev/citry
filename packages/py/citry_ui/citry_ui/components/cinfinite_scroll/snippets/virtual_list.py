import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollVirtualList(Component):
    template = """
      <section x-data>
        <c-CInfiniteScroll
          aria_label="Audit log"
          c-auto="False"
          $c-props="{loading, hasMore, onLoadMore: loadSnapshot}"
        >
          <div x-bind:hidden="expanded">
            <c-CVirtualList aria_label="Loaded audit records" c-viewport_size="180">
              <c-CVirtualListItem item_key="event-1">Signed in</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-2">Changed billing contact</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-3">Exported report</c-CVirtualListItem>
            </c-CVirtualList>
          </div>
          <div hidden x-bind:hidden="!expanded">
            <c-CVirtualList aria_label="Loaded audit records" c-viewport_size="180">
              <c-CVirtualListItem item_key="event-1">Signed in</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-2">Changed billing contact</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-3">Exported report</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-4">Created an API token</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-5">Updated tax details</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-6">Invited a reviewer</c-CVirtualListItem>
            </c-CVirtualList>
          </div>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="expanded ? 'Showing 6 audit records' : 'Showing 3 audit records'">
          Showing 3 audit records
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.expanded = false;
        scope.loading = false;
        scope.hasMore = true;
        scope.loadSnapshot = () => {
          if (scope.loading || !scope.hasMore) return;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            scope.expanded = true;
            scope.hasMore = false;
            scope.loading = false;
            resolve();
          }, 220));
        };
      });
    """


preview = InfiniteScrollVirtualList()
preview  # noqa: B018
