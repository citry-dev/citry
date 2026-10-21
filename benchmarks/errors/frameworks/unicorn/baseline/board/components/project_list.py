from dataclasses import dataclass

from django_unicorn.components import UnicornView


# The page's cards, typed so a type checker sees their fields.
@dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool


PROJECTS = [('Alpha', 3, True), ('Beta', 5, False), ('Gamma', 8, False)]


class ProjectListView(UnicornView):
    # The cards come from server data. The template reads them, but the
    # browser does not need them, so Meta below keeps them out of the page.
    cards: list[Project]
    # The titles of the cards the user hid. django-unicorn keeps this in the
    # page and sends it back with every action.
    hidden: list[str]

    class Meta:
        javascript_exclude = ('cards',)

    # django-unicorn calls mount() once when it creates the component. Starting
    # the lists here gives each page its own lists instead of shared class values.
    def mount(self):
        self.cards = [Project(title=title, count=count, featured=featured) for title, count, featured in PROJECTS]
        self.hidden = []

    # Each card calls this from its own hide(); this list renders the cards,
    # so it is their parent.
    def hide(self, title: str):
        self.hidden = [*self.hidden, title]
