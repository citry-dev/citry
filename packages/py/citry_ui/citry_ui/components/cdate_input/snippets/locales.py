from citry import Component

# ruff: noqa: E501 - localized template and CSS lines stay readable in the public source example


class DateInputLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="date-input-demo-grid">
        <div lang="en"><label for="date-en">English context</label><c-CDateInput id="date-en" value="2026-08-19" /></div>
        <div lang="ar" dir="rtl"><label for="date-ar">سياق عربي</label><c-CDateInput id="date-ar" value="2026-08-19" /></div>
        <p>The submitted value is 2026-08-19 in both controls; visible native formatting remains browser-owned.</p>
      </section>
    """
    css = ":where(.date-input-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1rem}:where(.date-input-demo-grid>div){display:grid;gap:.5rem}"


preview = DateInputLocales()
preview  # noqa: B018
