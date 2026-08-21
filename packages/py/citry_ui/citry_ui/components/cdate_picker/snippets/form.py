# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerForm(Component):
    template = """
      <section x-data="{submitted:'Submit to inspect FormData'}">
        <form @submit.prevent="submitted=JSON.stringify(Array.from(new FormData($event.target).entries()))">
          <c-CField control_id="trip-date" required>
            <c-fill name="label">Trip date</c-fill>
            <c-fill name="description">The submitted value stays canonical.</c-fill>
            <c-fill name="default"><c-CDatePicker id="trip-date" name="trip_date" value="2026-08-19" /></c-fill>
            <c-fill name="error">Choose a trip date.</c-fill>
          </c-CField>
          <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        </form>
        <output x-text="submitted">Submit to inspect FormData</output>
      </section>
    """
    css = ":where(form){display:grid;gap:.75rem;max-inline-size:28rem}:where(output){display:block;margin-block-start:.75rem;overflow-wrap:anywhere}"


preview = DatePickerForm()
preview  # noqa: B018
