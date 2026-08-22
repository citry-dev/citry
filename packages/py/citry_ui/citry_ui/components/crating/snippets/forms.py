from citry import Component

# ruff: noqa: E501 - template expressions stay readable in the public source example


class RatingForms(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="rating-demo-stack" x-data="{result:'Submit or reset the Form'}" @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))">
        <c-CField required>
          <c-fill name="label">Service rating</c-fill>
          <c-fill name="default"><c-CRating name="service" value="2" /></c-fill>
        </c-CField>
        <c-CRating name="published" label="Published rating" value="4.5" precision="0.5" readonly />
        <c-CRow><c-CButton type="submit">Submit</c-CButton><c-CButton type="reset" variant="outline">Reset</c-CButton></c-CRow>
        <output x-text="result">Submit or reset the Form</output>
      </form>
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = RatingForms()
preview  # noqa: B018
