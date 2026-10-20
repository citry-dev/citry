from typing import Literal, TypedDict

from django_components import Component, SlotInput, register
from pydantic import BaseModel


# What the card hands to the page's footer fill.
class FooterData(TypedDict):
    title: str
    count: int


@register('card')
class Card(Component):
    template_file = 'card.html'
    css_file = 'card.css'

    class Kwargs(BaseModel):
        title: str
        count: int
        tone: Literal['plain', 'accent']

    class Slots(BaseModel):
        footer: SlotInput[FooterData]

    class TemplateData(BaseModel):
        title: str
        count: int
        tone: Literal['plain', 'accent']

    def get_template_data(self, args, kwargs: Kwargs, slots: Slots, context):
        return {'title': kwargs.title, 'count': kwargs.count, 'tone': kwargs.tone}
