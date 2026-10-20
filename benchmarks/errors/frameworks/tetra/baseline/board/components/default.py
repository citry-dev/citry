from dataclasses import dataclass
from typing import Literal

from django.conf import settings
from sourcetypes import css, django_html
from tetra import Component, public

# Tetra finds this module because it is board/components/default.py: every
# component class here belongs to the app's `default` library, the group of
# components whose scripts and styles Tetra builds into one JavaScript file
# and one CSS file. Templates use each one as a tag named after its class,
# such as {% Card %}.
#
# A public attribute is part of the component's Alpine data in the browser.
# Its type annotation lets Tetra check the value whenever it saves the
# component's state, and lets pyright check the code that assigns it. pyright
# sees `public(...)` itself as a `Public` object, not as the annotated type,
# so each of those lines silences that one check.
#
# Tetra's docs mark each inline template, stylesheet and script with a type
# from sourcetypes, which tells VS Code's Python Inline Source extension how
# to highlight it. `script` goes without one: Component declares it as
# `str | None`, so pyright rejects `script: javascript`, a form the docs use.


# The page's cards, typed so a type checker sees their fields.
@dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool


PROJECTS = [('Alpha', 3, True), ('Beta', 5, False), ('Gamma', 8, False)]


class ApiLine(Component):
    # Public, so the browser receives it and Alpine's x-text can show it.
    api_base: str = public('')  # pyright: ignore[reportAssignmentType]

    def load(self, *args, **kwargs) -> None:
        self.api_base = settings.API_BASE

    template: django_html = """
    <p>API: <span x-text="api_base"></span></p>
    """


class Card(Component):
    # Public, so the Hide button can send the title with its event.
    title: str = public('')  # pyright: ignore[reportAssignmentType]
    # No browser code reads these, so they stay on the server.
    count: int = 0
    tone: Literal['plain', 'accent'] = 'plain'

    # The {% Card %} tag's arguments arrive here. Tetra keeps them and calls
    # load() again whenever a public method call rebuilds the card from the
    # state saved in the page.
    def load(self, title: str, count: int, tone: Literal['plain', 'accent'], *args, **kwargs) -> None:
        self.title = title
        self.count = count
        self.tone = tone

    # The footer slot is filled by the card list. Tetra renders a slot's
    # content with the card's own variables, so the fill reads `title` and
    # `count` from the card.
    template: django_html = """
    <div class="card card--{{ tone }}">
      <h2>{{ title }}: {{ count }} tasks</h2>
      <button type="button" @click="$dispatch('hide', title)">Hide</button>
      <div class="card-footer">{% slot footer %}{% endslot %}</div>
    </div>
    """

    style: css = """
    .card--accent {
      border: 2px solid rgb(0, 0, 255);
    }
    """


class ProjectList(Component):
    # The titles of the cards the user hid. Tetra keeps public attributes in
    # the page and sends them back with every call.
    hidden: list[str] = public([])  # pyright: ignore[reportAssignmentType]

    # Tetra runs load() again on every call and does not save what it sets,
    # so the cards are rebuilt from server data each time.
    def load(self, *args, **kwargs) -> None:
        self.cards = [Project(title=title, count=count, featured=featured) for title, count, featured in PROJECTS]

    # A card's Hide button dispatches the browser event `hide` with its title.
    # The event bubbles up to this list, and `listen` makes Tetra call this
    # method with the event's value; it then renders the list again.
    @public.listen('hide')
    def hide(self, title: str) -> None:
        self.hidden = [*self.hidden, title]

    # Each card is keyed by its title, so Tetra matches it with its saved
    # state when the list renders again.
    template: django_html = """
    <div>
      {% for card in cards %}
        {% if card.title not in hidden %}
          {% Card title=card.title count=card.count tone=card.featured|yesno:"accent,plain" key=card.title %}
            {% slot footer %}<a href="#{{ title|lower }}">Open {{ title }} ({{ count }})</a>{% endslot %}
          {% /Card %}
        {% endif %}
      {% endfor %}
    </div>
    """


class Counter(Component):
    # The saved total. Tetra keeps it in the page, so a reload starts again at 0.
    count: int = public(0)  # pyright: ignore[reportAssignmentType]

    # Add calls this on the server with the amount. Tetra then renders the
    # counter again, so the new total shows.
    @public
    def save(self, amount: int) -> None:
        self.count = self.count + amount

    template: django_html = """
    <p>
      <span>Saved: {{ count }}</span>
      <button type="button" @click="save(1)">Add</button>
    </p>
    """


class Details(Component):
    # Whether the details show. The Details button changes it in the browser
    # only; opening them needs nothing from the server.
    open: bool = public(False)  # pyright: ignore[reportAssignmentType]

    # The status line's Close button dispatches `close`, which bubbles up to
    # this root element.
    template: django_html = """
    <div @close="close()">
      <button type="button" :aria-expanded="open" @click="toggle()">Details</button>
      <p x-show="open">Details are visible</p>
      {% Status / %}
    </div>
    """

    script = """
    export default {
      toggle() {
        this.open = !this.open;
      },
      close() {
        this.open = false;
      },
    }
    """


class Status(Component):
    # The status line sits inside the details, and `open` changes only in the
    # browser, after the server has rendered both. So the status line takes
    # no input: its Alpine component is nested inside the details' one, and
    # its markup reads the details' `open` through the scope Alpine shares
    # with it. Its Close button leaves `open` to the details and asks them to
    # close with an event.
    template: django_html = """
    <p>
      <span x-text="open ? 'Status: open' : 'Status: closed'"></span>
      <button type="button" @click="close()">Close</button>
    </p>
    """

    script = """
    export default {
      close() {
        this.$dispatch('close');
      },
    }
    """


class Search(Component):
    # What is typed in the search field. x-model keeps it in step with the
    # field, in the browser only.
    query: str = public('')  # pyright: ignore[reportAssignmentType]

    # The form submits to the page with GET, so the field's name decides what
    # the page's view reads.
    template: django_html = """
    <form role="search">
      <input type="search" name="q" x-model="query">
      <button type="submit">Search</button>
      <p>Searching for: <span x-text="query"></span></p>
    </form>
    """
