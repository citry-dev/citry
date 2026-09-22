import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollErrorRetry(Component):
    template = """
      <section >
        <c-CInfiniteScroll
          aria_label="Orders"
          c-auto="False"
          :loading="loading" :error="error" :hasMore="hasMore" :onLoadMore="retryPage"
        >
          <ul>
            <li>Order #1042</li>
            <li>Order #1041</li>
            <template v-for="order in recoveredOrders" :key="order.id">
              <li v-text="order.label"></li>
            </template>
          </ul>
        </c-CInfiniteScroll>
        <output aria-live="polite" v-text="recovered ? 'Orders recovered' : 'Last request failed'">
          Last request failed
        </output>
      </section>
    """

    js = """
      $component({
        data() {
          return {
            recoveredOrders: [], loading: false, error: true, hasMore: true, recovered: false,
          };
        },
        methods: {
          retryPage() {
            if (this.loading || !this.hasMore) return;
            this.error = false;
            this.loading = true;
            return new Promise(resolve => setTimeout(() => {
              this.recoveredOrders.push(
                { id: 1040, label: 'Order #1040' },
                { id: 1039, label: 'Order #1039' },
              );
              this.recovered = true;
              this.hasMore = false;
              this.loading = false;
              resolve();
            }, 260));
          },
        },
      });
    """


preview = InfiniteScrollErrorRetry()
preview  # noqa: B018
