from citry import Component


class ControlledRating(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack" >
        <c-CRating
          label="Controlled conversation rating"
          value="3"
          allow_clear
          :value="score" :onValueChange="(next,detail)=>{score=next;last=`${detail.source}: ${next ?? 'unrated'}`}"
        />
        <output v-text="last">No request yet</output>
        <button type="button" @click="score='5'">Set five stars</button>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            score:'3',last:'No request yet'
          };
        },
      });
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledRating()
preview  # noqa: B018
