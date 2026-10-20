from app.citry_app import citry_app
from citry import Component


class Status(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    # The status line only shows the details panel's state, so the panel owns
    # `open` and the status line asks it to close through an event.
    template = """
      <p class="status">
        Status: <span v-text="open ? 'open' : 'closed'"></span>
        <button type="button" @click="$emit('close')">Close</button>
      </p>
    """

    js = """
      $component({
        props: {
          open: { type: Boolean, required: true },
        },
        emits: ['close'],
      });
    """
