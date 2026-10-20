from dataclasses import dataclass

from django.conf import settings
from django.shortcuts import render
from django.utils.html import json_script
from django.utils.translation import gettext
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
        # The pinned Rusty parser has no {% translate %} tag, so the heading
        # is translated here, with the English text as the message id.
        'heading': gettext('Projects'),
        # It has no json_script filter either, so the view calls the function
        # behind that filter, and the page writes the tag that board.js reads.
        'api_base_script': json_script(settings.API_BASE, 'api-base'),
        'count': request.session.get('count', 0),
    })


@require_POST
def save(request):
    # HTMX sends hx-vals as ordinary form fields.
    amount = int(request.POST['amount'])
    count = request.session.get('count', 0) + amount
    request.session['count'] = count
    # Render only the counter's own template, which the page also includes;
    # HTMX swaps it in for #saved.
    return render(request, 'board/saved.html', {'count': count})
