from app.citry_app import citry_app
from citry import Component


class Details(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"open": False}

    template = """
      <section class="details">
        <button
          type="button"
          :aria-expanded="open"
          @click="toggle()"
        >
          Details
        </button>
        <p v-if="open">Details are visible</p>
        <c-Status :open="open" @close="open = false" />
      </section>
    """

    js = """
      $component({
        methods: {
          toggle() {
            this.open = !this.open;
          },
        },
      });
    """
