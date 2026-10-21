from django_unicorn.components import UnicornView


class SearchView(UnicornView):
    # What is typed in the search field. unicorn:model sends each change to
    # the server, which renders the `Searching for:` line again.
    query: str = ''
