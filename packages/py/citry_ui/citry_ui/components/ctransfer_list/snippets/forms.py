import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListForm(Component):
    template = """
      <form x-data="{result:'Not submitted'}"
        @submit.prevent="result=[...new FormData($el).getAll('reviewers')].join(' → ')"
      >
        <c-CTransferList name="reviewers" c-required="True" c-value="['ada']">
          <c-CTransferListItem value="ada" label="Ada" />
          <c-CTransferListItem value="grace" label="Grace" />
          <c-CTransferListItem value="katherine" label="Katherine" />
        </c-CTransferList>
        <p><button type="submit">Submit order</button> <button type="reset">Reset</button></p>
        <output x-text="result">Not submitted</output>
      </form>
    """


preview = TransferListForm()
preview  # noqa: B018
