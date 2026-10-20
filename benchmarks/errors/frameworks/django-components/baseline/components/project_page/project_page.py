from django_components import Component, register
from pydantic import BaseModel


@register('project_page')
class ProjectPage(Component):
    template_file = 'project_page.html'

    class Kwargs(BaseModel):
        project_id: int

    class TemplateData(BaseModel):
        project_id: int

    def get_template_data(self, args, kwargs: Kwargs, slots, context):
        return {'project_id': kwargs.project_id}

    # Written as django-components' docs write it; see BoardPage.View.
    class View:  # pyright: ignore[reportIncompatibleVariableOverride]
        def get(self, request, project_id):
            return ProjectPage.render_to_response(request=request, kwargs={'project_id': project_id})
