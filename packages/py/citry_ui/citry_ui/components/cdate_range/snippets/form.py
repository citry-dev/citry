# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DateRangeForm(Component):
    template = """
      <form x-data="{result:'Submit the form to inspect its canonical values.'}" @submit.prevent="result=JSON.stringify(Object.fromEntries(new FormData($event.target)))">
        <fieldset><legend>Conference stay</legend><c-CDateRange start_name="check_in" end_name="check_out" start="2026-09-14" end="2026-09-18" required /></fieldset>
        <div><button type="submit">Submit dates</button> <button type="reset">Reset dates</button></div>
        <output x-text="result">Submit the form to inspect its canonical values.</output>
      </form>
    """
    css = ":where(form,fieldset){display:grid;gap:.75rem;max-inline-size:32rem}"


preview = DateRangeForm()
preview  # noqa: B018
