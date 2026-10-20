from django_components import Component, register
from pydantic import BaseModel


@register('counter')
class Counter(Component):
    template_file = 'counter.html'

    class Kwargs(BaseModel):
        count: int

    def get_template_data(self, args, kwargs: Kwargs, slots, context):
        return {'count': kwargs.count}

    # Written as django-components' docs write it. The library turns this
    # plain class into a ComponentView subclass when it creates the
    # component, but pyright sees only the plain class, so its override
    # check is silenced on this line.
    class View:  # pyright: ignore[reportIncompatibleVariableOverride]
        def post(self, request, *args, **kwargs):
            # HTMX sends hx-vals as ordinary form fields.
            amount = int(request.POST['amount'])
            count = request.session.get('count', 0) + amount
            request.session['count'] = count
            # Reply with only the counter; HTMX swaps it in for the old one.
            return Counter.render_to_response(
                request=request,
                kwargs={'count': count},
                deps_strategy='fragment',
            )
