from citry import Component


class LocalizedNumberInput(Component):
    template = """
      <section class="number-input-example-stack">
        <p>
          Place the same component under a client-enabled
          <code>&lt;c-i18n&gt;</code> provider to switch locale in place.
        </p>
        <c-CNumberInput
          value="1234.5"
          step="0.1"
          c-input_attrs="{'aria-label':'Localized measurement'}"
        />
        <p>
          The editor and its ARIA value text use the provider locale; the
          enhanced Form value stays <code>1234.5</code>.
        </p>
      </section>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:32rem}"


preview = LocalizedNumberInput()
preview  # noqa: B018
