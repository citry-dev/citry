from citry import Component

# ruff: noqa: E501 - Vue expressions stay readable in the public source example


class ControlledDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="date-input-demo-stack" >
        <c-CDateInput c-attrs="{'aria-label':'Controlled arrival date'}" value="2026-08-19" :value="day" @input="last=$event.currentTarget.value" />
        <c-CRow><button type="button" @click="day='2026-08-22'">Set 22 August</button><button type="button" @click="day=null">Clear</button></c-CRow>
        <output v-text="last">No native input yet</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            day:'2026-08-19',last:'No native input yet'
          };
        },
      });
    """
    css = ":where(.date-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledDateInput()
preview  # noqa: B018
