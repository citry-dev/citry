from dataclasses import dataclass

from django.conf import settings
from django.shortcuts import render


@dataclass
class Owner:
    name: str


def page(request):
    return render(request, 'board/page.html', {
        'owner': Owner(name='Ada'),
        # The template hands this to board.js through the json_script filter.
        'api_base': settings.API_BASE,
        'accent': settings.ACCENT,
        # The search form submits back to this page with its text in `q`.
        'searched': request.GET.get('q', ''),
    })


def about(request):
    return render(request, 'board/about.html')


def project(request, project_id):
    return render(request, 'board/project.html', {'project_id': project_id})
