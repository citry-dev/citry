import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListForm(Component):
    template = """
      <form
        @submit.prevent="result=[...new window.FormData($el).getAll('reviewers')].join(' → ')"
      >
        <c-CTransferList name="reviewers" c-required="True" c-value="['ada']">
          <c-CTransferListItem value="ada" label="Ada" />
          <c-CTransferListItem value="grace" label="Grace" />
          <c-CTransferListItem value="katherine" label="Katherine" />
        </c-CTransferList>
        <p><button type="submit">Submit order</button> <button type="reset">Reset</button></p>
        <output v-text="result">Not submitted</output>
      </form>
    """
    js = """
      $component({
        data() {
          return {
            result:'Not submitted'
          };
        },
      });
    """


preview = TransferListForm()
preview  # noqa: B018
