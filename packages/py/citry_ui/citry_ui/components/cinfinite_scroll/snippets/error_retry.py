import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollErrorRetry(Component):
    template = """
      <section x-data>
        <c-CInfiniteScroll
          aria_label="Orders"
          c-auto="False"
          $c-props="{loading, error, hasMore, onLoadMore: retryPage}"
        >
          <ul>
            <li>Order #1042</li>
            <li>Order #1041</li>
            <template x-for="order in recoveredOrders" :key="order.id">
              <li x-text="order.label"></li>
            </template>
          </ul>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="recovered ? 'Orders recovered' : 'Last request failed'">
          Last request failed
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.recoveredOrders = [];
        scope.loading = false;
        scope.error = true;
        scope.hasMore = true;
        scope.recovered = false;
        scope.retryPage = () => {
          if (scope.loading || !scope.hasMore) return;
          scope.error = false;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            scope.recoveredOrders.push(
              { id: 1040, label: 'Order #1040' },
              { id: 1039, label: 'Order #1039' },
            );
            scope.recovered = true;
            scope.hasMore = false;
            scope.loading = false;
            resolve();
          }, 260));
        };
      });
    """


preview = InfiniteScrollErrorRetry()
preview  # noqa: B018
