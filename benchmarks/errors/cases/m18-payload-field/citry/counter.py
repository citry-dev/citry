from app.citry_app import citry_app
from citry import Component


class SaveIn:
    amount: int


class Counter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class Slots:
        pass

    class State:
        count: int = 0

    class Events:
        def save(self, data: SaveIn, state: "Counter.State"):
            # Returning nothing skips the re-render; the new count still
            # reaches the browser through $state.
            state.count += data.amount

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"count": kwargs.count}

    template = """
      <section class="counter">
        <p>Saved: <span v-text="$state.count">{{ count }}</span></p>
        <button type="button" @c-click="save({amont: 1})">Add</button>
      </section>
    """
