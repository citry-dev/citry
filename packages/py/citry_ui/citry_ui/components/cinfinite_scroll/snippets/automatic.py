# ruff: noqa: E501 - embedded Citry template attributes remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAutomatic(Component):
    template = """
      <section x-data>
        <p>Scroll to the end of the clipped result feed.</p>
        <c-CInfiniteScroll
          aria_label="Search results"
          c-style="{'max-block-size': '12rem', 'overflow': 'auto', 'overflow-anchor': 'none', 'padding-inline-end': '0.25rem'}"
          $c-props="{loading, hasMore, onLoadMore: loadNextPage}"
        >
          <ol>
            <li>Search result 1</li><li>Search result 2</li><li>Search result 3</li><li>Search result 4</li>
            <li>Search result 5</li><li>Search result 6</li><li>Search result 7</li><li>Search result 8</li>
            <template x-for="result in moreResults" :key="result.id">
              <li x-text="result.label"></li>
            </template>
          </ol>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="`Loaded ${8 + moreResults.length} results`">
          Loaded 8 results
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.moreResults = [];
        scope.loading = false;
        scope.hasMore = true;
        let nextResult = 9;
        scope.loadNextPage = () => {
          if (scope.loading) return;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            const page = Array.from({ length: 4 }, () => {
              const id = nextResult++;
              return { id, label: `Search result ${id}` };
            });
            scope.moreResults.push(...page);
            scope.loading = false;
            resolve();
          }, 260));
        };
      });
    """


preview = InfiniteScrollAutomatic()
preview  # noqa: B018
