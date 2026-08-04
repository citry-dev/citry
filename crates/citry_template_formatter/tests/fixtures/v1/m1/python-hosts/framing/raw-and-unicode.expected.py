from citry import Component

class RawCard(Component):
    template = r"""
      <main>
        <section></section>
      </main>
    """

class UnicodeCard(Component):
    template = u'''
      <main>
        <footer></footer>
      </main>
    '''
