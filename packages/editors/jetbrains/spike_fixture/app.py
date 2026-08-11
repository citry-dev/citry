from citry import Citry, CitryRender, Component

app = Citry(autodiscover=False)


class SaveIn:
    title: str


class Frame(Component):
    citry = app

    class Kwargs:
        body: CitryRender

    template = "<article>{{ body }}</article>"


class InlineCard(Component):
    citry = app

    class Kwargs:
        title: str
        count: int = 0

    class JsData:
        active: bool
        colors: list[str]

    class CssData:
        accent: str

    class Slots:
        pass

    class Events:
        def save(self, data: SaveIn) -> None:
            pass

    template = """
      <section
        c-class="'is-active' if count > 0 else ''"
        :aria-busy="active"
      >
        <h2>{{ title.upper() }}</h2>
        <button @c-click="save">Save</button>
        <template x-for="color in colors">
          <span x-text="color.toUpperCase()"></span>
        </template>
        <c-Frame
          c-body="<><span c-title='title'>Nested {{ title }}</span></>"
        />
        <c-element is="form" c-action="title.lower()"></c-element>
      </section>
    """

    js = """
      $component({
        init: ({ data, scope }) => {
          scope.active = data.active;
        },
      });
    """

    css = """
      :scope {
        border-color: var(--accent);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"title": kwargs.title, "count": kwargs.count}

    def js_data(self, kwargs: Kwargs, slots: Slots) -> JsData:  # noqa: ARG002
        return self.JsData(active=kwargs.count > 0, colors=["red", "blue"])

    def css_data(self, kwargs: Kwargs, slots: Slots) -> CssData:  # noqa: ARG002
        return self.CssData(accent="tomato")


class ExternalCard(Component):
    citry = app
    template_file = "external_card.citry-html"

    class Kwargs:
        title: str
        items: list[str]

    class JsData:
        expanded: bool

    class Slots:
        pass

    class Events:
        def toggle(self) -> None:
            pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"title": kwargs.title, "items": kwargs.items}

    def js_data(self, kwargs: Kwargs, slots: Slots) -> JsData:  # noqa: ARG002
        return self.JsData(expanded=False)
