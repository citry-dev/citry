# ruff: noqa: E501 - embedded Citry template attributes remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAutomatic(Component):
    template = """
      <section >
        <p>Scroll to the end of the clipped result feed.</p>
        <c-CInfiniteScroll
          aria_label="Search results"
          c-style="{'max-block-size': '12rem', 'overflow': 'auto', 'overflow-anchor': 'none', 'padding-inline-end': '0.25rem'}"
          :loading="loading" :hasMore="hasMore" :onLoadMore="loadNextPage"
        >
          <ol>
            <li>Search result 1</li><li>Search result 2</li><li>Search result 3</li><li>Search result 4</li>
            <li>Search result 5</li><li>Search result 6</li><li>Search result 7</li><li>Search result 8</li>
            <template v-for="result in moreResults" :key="result.id">
              <li v-text="result.label"></li>
            </template>
          </ol>
        </c-CInfiniteScroll>
        <output aria-live="polite" v-text="`Loaded ${8 + moreResults.length} results`">
          Loaded 8 results
        </output>
      </section>
    """

    js = """
      $component({
        data() {
          return { moreResults: [], loading: false, hasMore: true, nextResult: 9 };
        },
        methods: {
          loadNextPage() {
            if (this.loading) return;
            this.loading = true;
            return new Promise(resolve => setTimeout(() => {
              const page = Array.from({ length: 4 }, () => {
                const id = this.nextResult++;
                return { id, label: `Search result ${id}` };
              });
              this.moreResults.push(...page);
              this.loading = false;
              resolve();
            }, 260));
          },
        },
      });
    """


preview = InfiniteScrollAutomatic()
preview  # noqa: B018
