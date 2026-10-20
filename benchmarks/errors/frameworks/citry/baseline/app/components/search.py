from app.citry_app import citry_app
from citry import Component


class SearchIn:
    q: str


class Search(Component):
    citry = citry_app

    class Kwargs:
        searched: str = ""

    class Slots:
        pass

    class Events:
        def search(self, data: SearchIn):
            # The form's named controls arrive as SearchIn; the form renders
            # again and shows what was searched.
            return Search(searched=data.q)

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"searched": kwargs.searched}

    def js_data(self, kwargs: Kwargs, slots: Slots):
        # The text typed so far, which the line under the form repeats.
        return {"query": ""}

    template = """
      <section class="search">
        <form role="search" @c-submit.prevent="search">
          <input type="search" name="q" v-model="query" />
          <button type="submit">Search</button>
        </form>
        <p>Searching for: <span v-text="query"></span></p>
        <p c-if="searched">Searched: {{ searched }}</p>
      </section>
    """
