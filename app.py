"""
Local demo of Citry's server and browser translation, plus one Citry Event, also an editor fixture.

Run ``python app.py`` to serve the page on http://127.0.0.1:8000/, where the
Like button calls Python, or ``python app.py --html`` to print the page.
Set ``CITRY_SECRET`` to keep signed State valid across restarts.
"""

import os
import secrets
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Annotated, Any
from wsgiref.simple_server import make_server

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
    SlotInput,
)
from citry.contrib.wsgi import wsgi_app
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
    # ProductCard's State travels through the browser in a signed token.
    # This local demo falls back to a fresh secret per process, so a page
    # left open across a restart needs a reload before Like works again.
    secret=os.environ.get("CITRY_SECRET") or secrets.token_urlsafe(32),
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


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    tags: tuple[str, ...]


# The product catalog stands in for a database: the page and the Like
# handler both read the product from here.
AURORA_LAMP_ID = 7
PRODUCTS = {
    AURORA_LAMP_ID: Product(AURORA_LAMP_ID, "Aurora Lamp", ("new", "sale")),
}


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
        return {
            "accountName": kwargs.name,
            "balanceText": str(kwargs.balance),
            "lazyMessage": "demo-account-lazy-detail",
            "localizedAmount": kwargs.localized_amount,
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
                v-text="$i18n.tr(
                  'demo-account-live-status',
                  { name: accountName },
                )"
              ></p>
              <output
                v-text="$i18n.format.currency(
                  balanceText,
                  'USD',
                  { format: 'account-balance' },
                )"
              ></output>
              <label>
                <span>{{ tr("demo-account-number-input-label") }}</span>
                <input type="text" v-model="localizedAmount"/>
              </label>
              <p
                v-text="$i18n.parse.number(
                  localizedAmount,
                  { format: 'editable-number' },
                ).state"
              ></p>
              <button type="button" @click="lazyText = $i18n.tr(lazyMessage)">
                <span v-text="$i18n.tr('demo-account-load-detail')"></span>
              </button>
              <p v-text="lazyText"></p>
            </section>
          </section>
        </div>
      </c-i18n>
    """

    js = """
      $component({
        data() {
          // Browser-only text; the js_data() keys are already reactive
          // members, so the template reads them without copying.
          return { lazyText: "" };
        },
        onServerRender({ component }) {
          // component.$i18n is the nearest client provider above this
          // component, which DemoPage supplies. The <c-i18n client> in this
          // template serves only the Vue expressions inside it.
          const i18n = component.$i18n;
          if (!i18n) return;
          // Citry stops effects created during the callback before each
          // rerun and on unmount, so this one re-translates on locale
          // changes without piling up.
          Citry.vue.watchEffect(() => {
            component.$el.dataset.browserStatus = i18n.tr(
              "demo-account-js-status",
            );
          });
        },
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


class Tag(Component):
    """Show one product tag; the parent decides whether it is highlighted."""

    citry = app

    class Kwargs:
        label: str

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002 - Citry supplies both declared schemas.
    ) -> dict[str, object]:
        return {"label": kwargs.label}

    template = """
      <span class="tag" :class="{ 'tag--active': highlight }">
        {{ label }}
      </span>
    """

    js = """
      $component({
        props: {
          highlight: Boolean,
        },
      });
    """


# ProductCard is also the VS Code formatting fixture: its template, JS, and
# CSS are deliberately untidy so the editor test can prove they get formatted.
class ProductCard(Component):
    citry = app

    class Kwargs:
        product_id: int
        tags: list[str]
        likes: int = 0
        accent: str = "#175cd3"

    class Slots:
        body: SlotInput
        footer: SlotInput | None = None

    class State(Kwargs):
        pass

    class Events:
        def like(self, state: "ProductCard.State") -> "ProductCard":
            # The event render is a fresh tree without the caller's slot
            # fill, so reload the product and pass the body again.
            product = PRODUCTS[state.product_id]
            return ProductCard(
                product_id=product.id,
                tags=state.tags,
                likes=state.likes + 1,
                accent=state.accent,
                slots={"body": product.name},
            )

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {
            "likes": kwargs.likes,
            "tags": kwargs.tags,
        }

    def js_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"likes": kwargs.likes}

    def css_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"accent": kwargs.accent}

    template = """
      <article class="card" :class="{ 'card--open': open }">
      <c-slot name="body" />
      <c-for each="tag in tags"> <c-Tag #c-key="tag" c-label="tag" :highlight="open" @click="open = !open" /> </c-for>
      <c-empty> <p>{{ tr("product-card-no-tags") }}</p> </c-empty>
      <button type="button" @c-click="like"> Like <span>{{ likes }}</span> </button>
      <c-slot name="footer">No footer yet</c-slot>
      </article>
    """

    js = """
      $component({ data() { return { open: false }; },
        onServerRender({ component }) {component.$el.dataset.likes = String(component.likes); } });
    """

    css = """
      .card { border-left: 3px solid var(--accent);}
      .tag--active {color: var(--accent);}
    """

    messages = """
      product-card-no-tags = No tags yet.
    """


class DemoPage(Component):
    """Serve the i18n dashboard and the product card as one document."""

    citry = app

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002 - Citry supplies both declared schemas.
        slots: Slots,  # noqa: ARG002 - Citry supplies both declared schemas.
    ) -> dict[str, object]:
        product = PRODUCTS[AURORA_LAMP_ID]
        return {
            "product_id": product.id,
            "product_name": product.name,
            "product_tags": list(product.tags),
        }

    # AccountDashboard's JavaScript reads the client provider above the
    # component, so this page wraps it in one. The dashboard's own provider
    # inherits this one's locale.
    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8"/>
          <title>{{ site_name }} demo</title>
          <c-css/>
        </head>
        <body>
          <c-i18n tag="div" client>
            <c-AccountDashboard/>
            <c-ProductCard c-product_id="product_id" c-tags="product_tags">
              <c-fill name="body">{{ product_name }}</c-fill>
            </c-ProductCard>
          </c-i18n>
          <c-js/>
        </body>
      </html>
    """


def render_demo(*, locale: str = "en-US") -> str:
    """Render the demo page with an explicit locale context at the root."""
    context = make_context(app, locale=locale)
    return (
        DemoPage()
        .render(
            provides={"citry_i18n": context},
        )
        .serialize()
    )


CITRY_PREFIX = "/citry"
citry_routes = wsgi_app(app)
app.set_mounted_prefix(CITRY_PREFIX)
# Initialize at import so a WSGI server that imports `application` gets a
# ready app too, not only `python app.py`.
app.initialize()


def application(
    environ: dict[str, Any],
    start_response: Callable[[str, list[tuple[str, str]]], object],
) -> Iterable[bytes]:
    """Serve the demo page at / and Citry's event routes under /citry."""
    path = environ.get("PATH_INFO", "")
    # Clicking Like posts to Citry's event route, so hand that prefix to
    # the Citry sub-application with the prefix moved into SCRIPT_NAME.
    if path == CITRY_PREFIX or path.startswith(CITRY_PREFIX + "/"):
        mounted = dict(environ)
        mounted["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + CITRY_PREFIX
        mounted["PATH_INFO"] = path[len(CITRY_PREFIX) :]
        return citry_routes(mounted, start_response)
    if path == "/":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [render_demo().encode()]
    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"Not Found"]


def main(argv: list[str]) -> None:
    """Print the page with --html, or serve it on http://127.0.0.1:8000/."""
    if "--html" in argv:
        sys.stdout.write(render_demo())
        sys.stdout.write("\n")
        return
    with make_server("127.0.0.1", 8000, application) as server:
        sys.stdout.write("Serving the demo on http://127.0.0.1:8000/\n")
        server.serve_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
