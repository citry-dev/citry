# Django adds what this returns to the context of every template rendered
# with the request, including each component's own template, which does not
# see the page's context. So every card reads the board's name without
# taking it as an argument.
def board(request):
    return {'board_name': 'Projects'}
