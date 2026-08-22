import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAtAGlance(Component):
    template = """
      <section x-data>
        <form @submit.prevent>
          <c-CInfiniteScroll
            aria_label="Activity feed"
            action_name="feed_action"
            c-auto="False"
            $c-props="{loading, hasMore, onLoadMore: loadNextPage}"
          >
            <ol>
              <li>Created the project</li>
              <li>Invited the design team</li>
              <li>Published the brief</li>
              <template x-for="activity in moreActivities" :key="activity.id">
                <li x-text="activity.label"></li>
              </template>
            </ol>
          </c-CInfiniteScroll>
        </form>
        <output aria-live="polite" x-text="`Loaded ${3 + moreActivities.length} activities`">
          Loaded 3 activities
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        const pages = [
          [
            { id: 4, label: 'Received legal approval' },
            { id: 5, label: 'Scheduled the launch' },
          ],
          [
            { id: 6, label: 'Opened early access' },
            { id: 7, label: 'Collected the first responses' },
          ],
        ];
        scope.moreActivities = [];
        scope.loading = false;
        scope.hasMore = true;
        let page = 0;
        scope.loadNextPage = detail => {
          // This static preview handles the named action locally. A server page
          // lets the submit continue and returns the next keyed result page.
          detail.sourceEvent?.preventDefault();
          if (scope.loading || !scope.hasMore) return;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            scope.moreActivities.push(...pages[page]);
            page += 1;
            scope.hasMore = page < pages.length;
            scope.loading = false;
            resolve();
          }, 220));
        };
      });
    """


preview = InfiniteScrollAtAGlance()
preview  # noqa: B018
