from dataclasses import dataclass

from django.conf import settings
from django_components import Component, register
from pydantic import BaseModel


@dataclass
class Owner:
    name: str


# The page's cards, typed like the owner, so a type checker sees their fields.
@dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool


PROJECTS = [('Alpha', 3, True), ('Beta', 5, False), ('Gamma', 8, False)]


@register('board_page')
class BoardPage(Component):
    template_file = 'board_page.html'
    js_file = 'board_page.js'
    css_file = 'board_page.css'

    class Kwargs(BaseModel):
        # The saved total, which the View below reads from the session.
        count: int

    class TemplateData(BaseModel):
        owner: Owner
        cards: list[Project]
        count: int

    class JsData(BaseModel):
        api_base: str

    def get_template_data(self, args, kwargs: Kwargs, slots, context):
        cards = [Project(title=title, count=count, featured=featured) for title, count, featured in PROJECTS]
        return {
            'owner': Owner(name='Ada'),
            'cards': cards,
            'count': kwargs.count,
        }

    def get_js_data(self, args, kwargs, slots, context):
        # board_page.js receives this in its $onComponent callback.
        return {'api_base': settings.API_BASE}

    # Written as django-components' docs write it. The library turns this
    # plain class into a ComponentView subclass when it creates the
    # component, but pyright sees only the plain class, so its override
    # check is silenced on this line.
    class View:  # pyright: ignore[reportIncompatibleVariableOverride]
        def get(self, request, *args, **kwargs):
            return BoardPage.render_to_response(
                request=request,
                kwargs={'count': request.session.get('count', 0)},
            )
