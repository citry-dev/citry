from citry import Component


class LocalizedSlider(Component):
    template = """
      <section class="slider-example-stack">
        <p>Inside a client-enabled <code>&lt;c-i18n&gt;</code>, labels and formatted values switch locale in place.</p>
        <c-CRangeSlider c-value="('1234.5', '5678.5')" min="0" max="10000" step="0.5" show_value="always" />
        <p>Canonical Form values remain <code>1234.5</code> and <code>5678.5</code>.</p>
      </section>
    """
    css = ":where(.slider-example-stack){display:grid;gap:1rem;max-inline-size:36rem}"


preview = LocalizedSlider()
preview  # noqa: B018
