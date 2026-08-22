"""Shared Infinite Scroll scenario used by repository quality tools."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from citry import Citry, Component


def infinite_scroll_states_component(app: Citry) -> type[Component]:
    class CitryUiInfiniteScrollStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-infinite-scroll-ready x-data="{loading:false,error:false,hasMore:true}">
            <h1>Infinite Scroll states</h1>
            <form>
              <c-CInfiniteScroll aria_label="Localized activity" action_name="activity_action"
                $c-props="{loading,error,hasMore,onLoadMore:()=>{loading=true}}" c-attrs="quality_attrs">
                <ol><li>A long server result that wraps at narrow widths without changing request behavior</li><li dir="rtl">نتيجة متاحة</li></ol>
              </c-CInfiniteScroll>
            </form>
            <c-CInfiniteScroll aria_label="Failed results" c-error="True" c-auto="False">
              <p>Last retained result</p>
            </c-CInfiniteScroll>
            <c-CInfiniteScroll aria_label="Disabled results" disabled c-auto="False">
              <p>Requests are temporarily unavailable</p>
            </c-CInfiniteScroll>
            <c-CInfiniteScroll aria_label="Completed results" c-has_more="False"><p>Final result</p></c-CInfiniteScroll>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "quality_attrs": {
                    "data-quality-states": "native auto loading error retry end disabled rtl localized cleanup"
                }
            }

    return CitryUiInfiniteScrollStates


__all__ = ["infinite_scroll_states_component"]
