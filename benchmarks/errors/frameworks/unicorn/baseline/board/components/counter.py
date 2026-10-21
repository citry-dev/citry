from django_unicorn.components import UnicornView


class CounterView(UnicornView):
    # The saved total. django-unicorn keeps it in the page and sends it back
    # with every action.
    count: int = 0

    def save(self, amount: int):
        self.count = self.count + amount
