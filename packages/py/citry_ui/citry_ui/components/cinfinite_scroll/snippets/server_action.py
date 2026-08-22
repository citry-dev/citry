import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollServerAction(Component):
    template = """
      <form x-data @submit.prevent="loadServerPage($event)">
        <label>Search query <input name="query" required /></label>
        <c-CInfiniteScroll
          aria_label="Server search results"
          action_name="result_action"
          action_value="next:2"
          c-auto="False"
          $c-props="{loading, hasMore}"
        >
          <ol>
            <li>Camera body comparison</li>
            <li>Lens mount guide</li>
            <template x-for="result in moreResults" :key="result.id">
              <li x-text="result.label"></li>
            </template>
          </ol>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="acceptedAction">Waiting for a named action</output>
      </form>
    """

    js = """
      $component(({ scope }) => {
        scope.moreResults = [];
        scope.loading = false;
        scope.hasMore = true;
        scope.acceptedAction = 'Waiting for a named action';
        scope.loadServerPage = event => {
          const submitter = event.submitter;
          if (!submitter || scope.loading || !scope.hasMore) return;
          scope.acceptedAction = `${submitter.name}=${submitter.value}`;
          scope.loading = true;
          setTimeout(() => {
            scope.moreResults.push(
              { id: 3, label: 'Mirrorless travel kit' },
              { id: 4, label: 'Low-light autofocus test' },
            );
            scope.hasMore = false;
            scope.loading = false;
          }, 240);
        };
      });
    """


preview = InfiniteScrollServerAction()
preview  # noqa: B018
