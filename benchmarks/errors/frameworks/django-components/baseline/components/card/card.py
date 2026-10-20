from django_components import Component, SlotInput, register
from pydantic import BaseModel


@register('card')
class Card(Component):
    template_file = 'card.html'

    class Kwargs(BaseModel):
        title: str
        count: int

    class Slots(BaseModel):
        footer: SlotInput

    class TemplateData(BaseModel):
        title: str
        count: int

    def get_template_data(self, args, kwargs: Kwargs, slots: Slots, context):
        return {'title': kwargs.title, 'count': kwargs.count}
