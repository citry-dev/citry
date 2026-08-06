from citry import Component, types


class CounterCard(Component):
    title: str
    count: int = 0

    template: types.html = """
    <article class="counter-card">
      <h2>{{ self.title }}</h2>
      <p c-if="self.count == 0">Try the button.</p>
      <button c-on:click="self.count += 1">
        Count: {{ self.count }}
      </button>
      <script>console.log("HTML script", document.title)</script>
      <style>.counter-card strong { color: rebeccapurple; }</style>
    </article>
    """

    js = """
    const label = `count-${this.count}`;
    console.log(label);
    """

    css = """
    .counter-card {
      display: grid;
      gap: 0.75rem;
      padding: 1.25rem;
    }
    """


CounterCard(title="Hello from Citry")
