from citry import Component


class ClickCounter(Component):
    class Kwargs:
        name: str

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"name": kwargs.name}

    template = """
      <button class="counter" type="button" @click="count += 1">
        <span class="counter__name" x-text="name"></span>
        clicked
        <span class="counter__count" x-text="count"></span>
        times
      </button>
    """

    js = """
      $component(({ data, scope }) => {
        // Pass data from Python to Alpine
        scope.name = data.name;
        scope.count = 0;
      });
    """


class CounterPage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Component data</title>
        </head>
        <body>
          <c-ClickCounter name="Ada" />
          <c-ClickCounter name="Grace" />
        </body>
      </html>
    """


page = CounterPage()

if __name__ == "__main__":
    print(page)

page
