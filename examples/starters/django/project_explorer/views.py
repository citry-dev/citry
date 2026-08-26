from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from .components import ProjectPage
from .data import find_projects


@ensure_csrf_cookie
def home(_request) -> HttpResponse:
    return HttpResponse(str(ProjectPage(projects=find_projects())))
