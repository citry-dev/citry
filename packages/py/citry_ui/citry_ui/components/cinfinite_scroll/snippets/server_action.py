import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollServerAction(Component):
    template = """
      <form @submit.prevent="loadServerPage($event)">
        <label>Search query <input name="query" required /></label>
        <c-CInfiniteScroll
          aria_label="Server search results"
          action_name="result_action"
          action_value="next:2"
          c-auto="False"
          :loading="loading" :hasMore="hasMore"
        >
          <ol>
            <li>Camera body comparison</li>
            <li>Lens mount guide</li>
            <template v-for="result in moreResults" :key="result.id">
              <li v-text="result.label"></li>
            </template>
          </ol>
        </c-CInfiniteScroll>
        <output aria-live="polite" v-text="acceptedAction">Waiting for a named action</output>
      </form>
    """

    js = """
      $component({
        data() {
          return {
            moreResults: [], loading: false, hasMore: true,
            acceptedAction: 'Waiting for a named action',
          };
        },
        methods: {
          loadServerPage(event) {
            const submitter = event.submitter;
            if (!submitter || this.loading || !this.hasMore) return;
            this.acceptedAction = `${submitter.name}=${submitter.value}`;
            this.loading = true;
            setTimeout(() => {
              this.moreResults.push(
                { id: 3, label: 'Mirrorless travel kit' },
                { id: 4, label: 'Low-light autofocus test' },
              );
              this.hasMore = false;
              this.loading = false;
            }, 240);
          },
        },
      });
    """


preview = InfiniteScrollServerAction()
preview  # noqa: B018
