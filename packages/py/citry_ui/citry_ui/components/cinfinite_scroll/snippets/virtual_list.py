import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollVirtualList(Component):
    template = """
      <section >
        <c-CInfiniteScroll
          aria_label="Audit log"
          c-auto="False"
          :loading="loading" :hasMore="hasMore" :onLoadMore="loadSnapshot"
        >
          <div :hidden="expanded">
            <c-CVirtualList aria_label="Loaded audit records" c-viewport_size="180">
              <c-CVirtualListItem item_key="event-1">Signed in</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-2">Changed billing contact</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-3">Exported report</c-CVirtualListItem>
            </c-CVirtualList>
          </div>
          <div hidden :hidden="!expanded">
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
        <output aria-live="polite" v-text="expanded ? 'Showing 6 audit records' : 'Showing 3 audit records'">
          Showing 3 audit records
        </output>
      </section>
    """

    js = """
      $component({
        data() {
          return { expanded: false, loading: false, hasMore: true };
        },
        methods: {
          loadSnapshot() {
            if (this.loading || !this.hasMore) return;
            this.loading = true;
            return new Promise(resolve => setTimeout(() => {
              this.expanded = true;
              this.hasMore = false;
              this.loading = false;
              resolve();
            }, 220));
          },
        },
      });
    """


preview = InfiniteScrollVirtualList()
preview  # noqa: B018
