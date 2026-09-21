from citry import Component


class NumberInputForms(Component):
    template = """
      <form

        @submit.prevent="submitted=new FormData($event.target).get('amount')"
        class="number-input-example-stack"
      >
        <c-CField required>
          <c-fill name="label">Amount</c-fill>
          <c-fill name="default"><c-CNumberInput name="amount" value="1.25" step="0.25" /></c-fill>
        </c-CField>
        <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        <output v-text="submitted">Not submitted</output>
      </form>
    """
    js = """
      $component({
        data() {
          return {
            submitted:'Not submitted'
          };
        },
      });
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = NumberInputForms()
preview  # noqa: B018
