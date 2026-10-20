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
    })
