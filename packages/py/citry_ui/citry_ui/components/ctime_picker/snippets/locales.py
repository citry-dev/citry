import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LocalizedTimePicker(Component):
    template = """
      <c-i18n tag="section" client>
        <div style="display:flex;gap:.5rem;margin-block-end:1rem">
          <c-CButton type="button" @click="$i18n.switchLocale('en-US')">English</c-CButton>
          <c-CButton type="button" @click="$i18n.switchLocale('cs-CZ')">Čeština</c-CButton>
        </div>
        <c-CTimePicker value="14:30" min="13:00" max="16:00" />
      </c-i18n>
    """


preview = LocalizedTimePicker()
preview  # noqa: B018
