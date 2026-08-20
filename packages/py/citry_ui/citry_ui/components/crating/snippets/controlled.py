from citry import Component

# ruff: noqa: E501 - Alpine expression stays readable in the public source example


class ControlledRating(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack" x-data="{score:'3',last:'No request yet'}">
        <c-CRating
          label="Controlled conversation rating"
          value="3"
          allow_clear
          $c-props="{value:score,onValueChange:(next,detail)=>{score=next;last=`${detail.source}: ${next ?? 'unrated'}`}}"
        />
        <output x-text="last">No request yet</output>
        <button type="button" @click="score='5'">Set five stars</button>
      </section>
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledRating()
preview  # noqa: B018
