import sys
from datetime import date
from decimal import Decimal
from typing import Annotated

from i18n_demo_messages import i18n_demo_library

from citry import (
    Citry,
    Component,
    CurrencyFormat,
    DateFormat,
    FormatRegistry,
    LintSettings,
    NumberFormat,
    PercentFormat,
    PercentInput,
)
from citry.ext.i18n import make_context
from citry_ui import __citry_library__

formats = FormatRegistry(
    number={
        "whole-number": NumberFormat(),
        "editable-number": NumberFormat(),
    },
    percent={
        "account-progress": PercentFormat(
            input=PercentInput(affix="required"),
        ),
    },
    currency={
        "account-balance": CurrencyFormat(),
    },
    date={
        "account-date": DateFormat(length="long"),
    },
)

app = Citry(
    autodiscover=False,
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "formats": formats,
        },
    },
    template_globals={
        "site_name": "Citry",
    },
    lint=LintSettings(
        rule_i18n_missing_param_type="error",
        rule_unknown_template_variable="error",
        template_variables={
            "request_label": Annotated[
                str,
                "The current request label.",
            ],
        },
    ),
)
app.register_library(__citry_library__)
app.register_library(i18n_demo_library)


class AccountSameFileMessages(Component):
    """Own a message used by AccountDashboard from this Python file."""

    citry = app

    template = """
      <template></template>
    """

    messages = """
      demo-account-same-file-note =
          This message is owned by another component in app.py.
    """


class AccountDashboard(Component):
    """Exercise Citry's server, browser, rich-message, and tooling i18n paths."""

    citry = app

    class Kwargs:
        name: str = "Ada Lovelace"
        balance: Decimal = Decimal("1234.50")
        completion: Decimal = Decimal("0.625")
        joined_on: date = date(2025, 5, 12)
        unread_count: int = 3
        localized_amount: str = "1,234.50"

    class Slots:
        pass

    class I18n:
        # This dynamic browser key cannot be discovered from a literal tr() call.
        client_messages = ("demo-account-lazy-detail",)

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002 - Citry supplies both declared schemas.
    ) -> dict[str, object]:
        return {
            "balance": kwargs.balance,
            "completion": kwargs.completion,
            "joined_on": kwargs.joined_on,
            "name": kwargs.name,
            "server_title": self.i18n.tr(
                "demo-account-title",
                name=kwargs.name,
            ),
            "unread_count": kwargs.unread_count,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002 - Citry supplies both declared schemas.
    ) -> dict[str, object]:
        parsed_amount = self.i18n.parse.number(
            kwargs.localized_amount,
            format="editable-number",
        )
        return {
            "accountName": kwargs.name,
            "balanceText": str(kwargs.balance),
            "completionText": str(kwargs.completion),
            "lazyMessage": "demo-account-lazy-detail",
            "localizedAmount": kwargs.localized_amount,
            "parseState": parsed_amount.state,
        }

    template = """
      <c-i18n tag="main" client>
        <div class="i18n-demo">
          <section
            class="i18n-demo__card"
            c-aria-label="tr(
              'demo-account-title',
              attr='aria-label',
              name=name,
            )"
            x-data="{
              'accountName': accountName,
              'balance': balanceText,
              'completion': completionText,
              'lazyMessage': lazyMessage,
              'lazyText': '',
              'localizedAmount': localizedAmount,
              'parseState': parseState,
            }"
          >
            <p class="i18n-demo__eyebrow">
              {{ tr("demo-account-kicker") }}
            </p>
            <h1>{{ server_title }}</h1>
            <p>{{ tr("demo-account-unread", count=unread_count) }}</p>
            <p>{{ tr("demo-account-summary") }}</p>
            <p>{{ tr("demo-account-same-file-note") }}</p>
            <p>{{ tr("demo-account-other-file-note") }}</p>
            <dl class="i18n-demo__facts">
              <div>
                <dt>{{ tr("demo-account-balance-label") }}</dt>
                <dd>
                  {{
                    fmt.currency(
                      balance,
                      "USD",
                      format="account-balance",
                    )
                  }}
                </dd>
              </div>
              <div>
                <dt>{{ tr("demo-account-progress-label") }}</dt>
                <dd>
                  {{
                    fmt.percent(
                      completion,
                      format="account-progress",
                    )
                  }}
                </dd>
              </div>
              <div>
                <dt>{{ tr("demo-account-joined-label") }}</dt>
                <dd>{{ fmt.date(joined_on, format="account-date") }}</dd>
              </div>
            </dl>
            <c-trans message="demo-account-settings-help" c-values="{'name': name}">
              <c-fill name="settings_link">
                <a href="/settings">{{ tr("demo-account-settings-link") }}</a>
              </c-fill>
            </c-trans>
            <section class="i18n-demo__browser">
              <h2>{{ tr("demo-account-browser-heading") }}</h2>
              <p
                x-text="$i18n.tr(
                  'demo-account-live-status',
                  { name: accountName },
                )"
              ></p>
              <output
                x-text="$i18n.format.currency(
                  balance,
                  'USD',
                  { format: 'account-balance' },
                )"
              ></output>
              <label>
                <span>{{ tr("demo-account-number-input-label") }}</span>
                <input
                  type="text"
                  x-model="localizedAmount"
                  @input="parseState = $i18n.parse.number(
                    localizedAmount,
                    { format: 'editable-number' },
                  ).state"
                />
              </label>
              <p x-text="parseState"></p>
              <button type="button" @click="lazyText = $i18n.tr(lazyMessage)">
                <span x-text="$i18n.tr('demo-account-load-detail')"></span>
              </button>
              <p x-text="lazyText"></p>
            </section>
          </section>
        </div>
      </c-i18n>
    """

    js = """
        $component(({ effect, els, i18n }) => {
          effect(() => {
            els[0].dataset.browserStatus = i18n.tr(
              "demo-account-js-status",
            );
          });
        });
    """

    css = """
        .i18n-demo {
          min-height: 100vh;
          padding: 3rem;
          background: #f2f5ef;
          color: #18332c;
          font-family: system-ui, sans-serif;
        }

        .i18n-demo__card {
          max-width: 48rem;
          margin: 0 auto;
          padding: 2rem;
          border: 1px solid #bfd0c8;
          border-radius: 1.25rem;
          background: white;
          box-shadow: 0 1.5rem 4rem rgb(24 51 44 / 12%);
        }

        .i18n-demo__eyebrow {
          color: #267a61;
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }

        .i18n-demo__facts {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
          gap: 1rem;
          margin-block: 2rem;
        }

        .i18n-demo__facts div,
        .i18n-demo__browser {
          padding: 1rem;
          border-radius: 0.75rem;
          background: #edf7f3;
        }

        .i18n-demo__facts dt {
          margin-block-end: 0.25rem;
          color: #4b625c;
          font-size: 0.8rem;
        }

        .i18n-demo__facts dd {
          margin: 0;
          font-size: 1.15rem;
          font-weight: 650;
        }

        .i18n-demo__browser {
          display: grid;
          gap: 0.75rem;
          margin-block-start: 2rem;
        }
    """

    messages = """
        -demo-product-name = Citry

        demo-account-kicker = { -demo-product-name } i18n editor fixture

        # Heading and accessible name for the account summary.
        # @param {str} $name - Account holder's display name.
        demo-account-title = Welcome back, { $name }
            .aria-label = Account overview for { $name }

        # @param {int} $count - Number of unread messages.
        demo-account-unread = { $count ->
            [one] { NUMBER($count, profile: "whole-number") } unread message
           *[other] { NUMBER($count, profile: "whole-number") } unread messages
        }

        demo-account-summary-label = Account status
        demo-account-summary = { demo-account-summary-label }: active

        demo-account-balance-label = Current balance
        demo-account-progress-label = Profile completion
        demo-account-joined-label = Member since

        # @param {str} $name - Account holder's display name.
        # @param {Slot} $settings_link - Application-owned settings link.
        demo-account-settings-help =
            { $name }, review { $settings_link }. You can return to { $settings_link } later.
        demo-account-settings-link = account settings

        demo-account-browser-heading = Browser-owned i18n

        # @param {str} $name - Account holder's display name.
        demo-account-live-status = Live controls are ready for { $name }.

        demo-account-number-input-label = Localized amount
        demo-account-load-detail = Load a dynamic browser message
        demo-account-lazy-detail =
            This key is declared through Component.I18n.client_messages.
        demo-account-js-status = Component JavaScript received the i18n service.
    """


def render_demo(*, locale: str = "en-US") -> str:
    """Render the fixture with an explicit locale context at the root."""
    context = make_context(app, locale=locale)
    return (
        AccountDashboard()
        .render(
            provides={"citry_i18n": context},
        )
        .serialize()
    )


if __name__ == "__main__":
    sys.stdout.write(render_demo())
    sys.stdout.write("\n")
