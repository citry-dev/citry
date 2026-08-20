"""Shared Rating scenario used by repository quality tools."""

# ruff: noqa: E501 - template expressions stay readable as authored HTML

from citry import Citry, Component


def rating_states_component(app: Citry) -> type[Component]:
    """Create the reusable Rating state and environment scenario."""

    class CitryUiRatingStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack rating-quality" aria-labelledby="rating-states-title" x-data="{score:'3',last:'No Rating action yet'}">
            <h1 id="rating-states-title">Rating states</h1>
            <form id="rating-quality-form" @submit.prevent="last=JSON.stringify(Array.from(new FormData($event.target).entries()))">
              <c-CField required>
                <c-fill name="label">Required product rating</c-fill>
                <c-fill name="description">Choose a half-star score.</c-fill>
                <c-fill name="default">
                  <c-CRating name="rating" value="2.5" precision="0.5" allow_clear c-attrs="{'data-quality-states':'required exact fractional form field description keyboard pointer hover clear reset localized'}" $c-props="{onValueChange:(next,detail)=>last=`${detail.source}: ${next ?? 'unrated'}`}" />
                </c-fill>
              </c-CField>
              <button type="submit">Submit rating</button><button type="reset">Reset rating</button>
            </form>
            <div class="citry-ui-quality-grid">
              <c-CRating label="Controlled rating" value="3" c-attrs="{'data-quality-states':'controlled callback refusal acceptance'}" $c-props="{value:score,onValueChange:(next)=>{score=next;last=`Accepted ${next}`}}" />
              <c-CRating label="Small subtle rating" value="2" size="sm" variant="subtle" c-attrs="{'data-quality-states':'subtle sm'}" />
              <c-CRating label="Large readonly rating" value="4.5" precision="0.5" size="lg" readonly name="readonly-rating" c-attrs="{'data-quality-states':'readonly submitted lg'}" />
              <c-CRating label="Disabled rating" value="1" disabled name="disabled-rating" c-attrs="{'data-quality-states':'disabled omitted md solid'}" />
              <div dir="rtl" style="color-scheme:dark"><c-CRating label="RTL localized rating" value="4" c-attrs="{'data-quality-states':'rtl dark localized touch long-content'}" /></div>
            </div>
            <output x-text="last">No Rating action yet</output>
          </section>
        """
        css = """
          :where(.rating-quality form){display:grid;justify-items:start;gap:.75rem}
          :where(.rating-quality [dir="rtl"]){padding:1rem;background:#172033;color:#f8fafc}
        """

    return CitryUiRatingStates


__all__ = ["rating_states_component"]
