# Django adds what this returns to the context of every template rendered
# with the request, including each component's own template. A django-unicorn
# component sees the page's context only on its first render, not when it
# renders again after Hide, so the board's name comes from here and every
# card reads it without taking it as an argument.
def board(request):
    return {'board_name': 'Projects'}
