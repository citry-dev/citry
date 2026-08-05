from citry import Component

class Card(Component):
    template = """
      <main>
        <section>{{ foo(1, bar=[1, 2]) }}</section>
      </main>
    """
