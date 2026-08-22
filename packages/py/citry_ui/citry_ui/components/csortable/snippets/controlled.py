# ruff: noqa: E501 - Alpine expression remains readable in the public example

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableControlled(Component):
    template = """
      <section x-data="{order:['draft','review','ship'],last:'No request'}">
        <c-CSortable $c-props="{
          order,
          onOrderChange:(next,detail)=>{order=next;last=`${detail.value}: ${detail.fromIndex + 1} → ${detail.toIndex + 1}`},
        }">
          <c-CSortableItem value="draft" label="Draft" />
          <c-CSortableItem value="review" label="Review" />
          <c-CSortableItem value="ship" label="Ship" />
        </c-CSortable>
        <output x-text="last">No request</output>
      </section>
    """


preview = SortableControlled()
preview  # noqa: B018
