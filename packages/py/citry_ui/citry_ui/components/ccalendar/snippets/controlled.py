from citry import Component

# ruff: noqa: E501 - Alpine expressions stay readable in the public source example


class ControlledCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section x-data="{selected:'2026-08-19',visible:'2026-08-19',last:'No request yet'}">
        <c-CCalendar
          label="Controlled calendar"
          value="2026-08-19"
          visible_date="2026-08-19"
          $c-props="{value:selected,visibleDate:visible,onValueChange:(value,detail)=>{last=`selection: ${value}`;selected=value},onVisibleDateChange:(value,detail)=>{last=`month: ${value}`;visible=value}}"
        />
        <output x-text="last">No request yet</output>
      </section>
    """
    css = ":where(section){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledCalendar()
preview  # noqa: B018
