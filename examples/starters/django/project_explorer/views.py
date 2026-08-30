from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from project_explorer.components.project_page import ProjectPage
from project_explorer.data import find_projects


@ensure_csrf_cookie
def home(_request) -> HttpResponse:
    html = str(ProjectPage(projects=find_projects()))
    return HttpResponse(html)
