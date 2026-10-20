from django_components import Component, register


@register('status')
class Status(Component):
    template_file = 'status.html'
    js_file = 'status.js'
