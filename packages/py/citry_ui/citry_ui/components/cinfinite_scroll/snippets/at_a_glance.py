import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAtAGlance(Component):
    template = """
      <section >
        <form @submit.prevent>
          <c-CInfiniteScroll
            aria_label="Activity feed"
            action_name="feed_action"
            c-auto="False"
            :loading="loading" :hasMore="hasMore" :onLoadMore="loadNextPage"
          >
            <ol>
              <li>Created the project</li>
              <li>Invited the design team</li>
              <li>Published the brief</li>
              <template v-for="activity in moreActivities" :key="activity.id">
                <li v-text="activity.label"></li>
              </template>
            </ol>
          </c-CInfiniteScroll>
        </form>
        <output aria-live="polite" v-text="`Loaded ${3 + moreActivities.length} activities`">
          Loaded 3 activities
        </output>
      </section>
    """

    js = """
      $component({
        data() {
          return { moreActivities: [], loading: false, hasMore: true, page: 0 };
        },
        methods: {
          loadNextPage(detail) {
            // This static preview handles the named action locally. A server page
            // lets the submit continue and returns the next keyed result page.
            detail.sourceEvent?.preventDefault();
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
            if (this.loading || !this.hasMore) return;
            this.loading = true;
            return new Promise(resolve => setTimeout(() => {
              this.moreActivities.push(...pages[this.page]);
              this.page += 1;
              this.hasMore = this.page < pages.length;
              this.loading = false;
              resolve();
            }, 220));
          },
        },
      });
    """


preview = InfiniteScrollAtAGlance()
preview  # noqa: B018
