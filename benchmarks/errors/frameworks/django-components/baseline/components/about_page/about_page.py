from django_components import Component, register


@register('about_page')
class AboutPage(Component):
    template_file = 'about_page.html'

    # Written as django-components' docs write it; see BoardPage.View.
    class View:  # pyright: ignore[reportIncompatibleVariableOverride]
        def get(self, request):
            return AboutPage.render_to_response(request=request)
