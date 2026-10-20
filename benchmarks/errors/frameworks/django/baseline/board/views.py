from dataclasses import dataclass

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_POST


@dataclass
class Owner:
    name: str


# The page's cards, typed like the owner, so a type checker sees their fields.
@dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool


PROJECTS = [('Alpha', 3, True), ('Beta', 5, False), ('Gamma', 8, False)]


def page(request):
    cards = [Project(title=title, count=count, featured=featured) for title, count, featured in PROJECTS]
    return render(request, 'board/page.html', {
        'owner': Owner(name='Ada'),
        'cards': cards,
        # The template hands this to Alpine through the json_script filter.
        'api_base': settings.API_BASE,
        'count': request.session.get('count', 0),
    })


@require_POST
def save(request):
    # HTMX sends hx-vals as ordinary form fields.
    amount = int(request.POST['amount'])
    count = request.session.get('count', 0) + amount
    request.session['count'] = count
    # Render only the `saved` partial; HTMX swaps it in for #saved.
    return render(request, 'board/page.html#saved', {'count': count})
