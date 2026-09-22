from citry import Component


class CalendarForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section >
        <form @submit.prevent="submitted=JSON.stringify(Object.fromEntries(new window.FormData($event.target)))">
          <c-CField control_id="trip-date" required>
            <c-fill name="label">Trip date</c-fill>
            <c-fill name="description">The native Form value remains YYYY-MM-DD.</c-fill>
            <c-fill name="default"><c-CCalendar id="trip-date" name="trip_date" value="2026-08-19" /></c-fill>
            <c-fill name="error">Choose a trip date.</c-fill>
          </c-CField>
          <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        </form>
        <output v-text="submitted">Submit to inspect FormData</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            submitted:'Submit to inspect FormData'
          };
        },
      });
    """
    css = ":where(form,section){display:grid;justify-items:start;gap:.75rem}"


preview = CalendarForm()
preview  # noqa: B018
