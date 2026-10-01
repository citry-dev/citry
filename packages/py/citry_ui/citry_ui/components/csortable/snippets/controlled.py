# ruff: noqa: E501 - Vue expression remains readable in the public example

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableControlled(Component):
    template = """
      <section >
        <c-CSortable :order="order" :onOrderChange="(next,detail)=>{order=next;last=`${detail.value}: ${detail.fromIndex + 1} → ${detail.toIndex + 1}`}">
          <c-CSortableItem value="draft" label="Draft" />
          <c-CSortableItem value="review" label="Review" />
          <c-CSortableItem value="ship" label="Ship" />
        </c-CSortable>
        <output v-text="last">No request</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            order:['draft','review','ship'],last:'No request'
          };
        },
      });
    """


preview = SortableControlled()
preview  # noqa: B018
