from typing import Literal, TypedDict

from django_components import Component, SlotInput, register
from pydantic import BaseModel, ConfigDict


# What the card hands to the page's footer fill.
class FooterData(TypedDict):
    title: str
    count: int


@register('card')
class Card(Component):
    template_file = 'card.html'
    css_file = 'card.css'

    class Kwargs(BaseModel):
        # Reject names the model does not declare, as django-components'
        # default named tuples do; Pydantic's default ignores them.
        model_config = ConfigDict(extra='forbid')

        title: str
        count: int
        tone: Literal['plain', 'accent']

    class Slots(BaseModel):
        model_config = ConfigDict(extra='forbid')

        footer: SlotInput[FooterData]

    class TemplateData(BaseModel):
        model_config = ConfigDict(extra='forbid')

        title: str
        count: int
        tone: Literal['plain', 'accent']
        board_name: str

    def get_template_data(self, args, kwargs: Kwargs, slots: Slots, context):
        # The page provides the board's name to every card, so no card takes it as an input.
        board = self.inject('board')
        return {'title': kwargs.title, 'count': kwargs.count, 'tone': kwargs.tone, 'board_name': board.title}
