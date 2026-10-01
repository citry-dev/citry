from citry import Component

# ruff: noqa: E501 - Vue expressions stay readable in the public source example


class ControlledCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section >
        <c-CCalendar
          label="Controlled calendar"
          value="2026-08-19"
          visible_date="2026-08-19"
          :value="selected" :visibleDate="visible" :onValueChange="(value,detail)=>{last=`selection: ${value}`;selected=value}" :onVisibleDateChange="(value,detail)=>{last=`month: ${value}`;visible=value}"
        />
        <output v-text="last">No request yet</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            selected:'2026-08-19',visible:'2026-08-19',last:'No request yet'
          };
        },
      });
    """
    css = ":where(section){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledCalendar()
preview  # noqa: B018
