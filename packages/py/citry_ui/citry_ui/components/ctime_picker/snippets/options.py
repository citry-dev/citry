from datetime import time
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTimePicker

citry.register_library(citry_ui)


class TimePickerOptions(Component):
    def template_data(self, kwargs, slots) -> dict[str, Any]:  # noqa: ANN001, ARG002
        return {
            "picker": CTimePicker(
                name="departure", value=time(23, 5, 9), options=(time(23, 5, 9), "00:00:10", "12:30:45")
            )
        }

    template = """
      <section>
        <h3>Irregular second-precision departures</h3>
        {{ picker }}
      </section>
    """


preview = TimePickerOptions()
preview  # noqa: B018
