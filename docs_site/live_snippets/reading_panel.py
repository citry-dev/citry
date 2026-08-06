from citry import Component, SlotInput


class ReadingPanel(Component):
    class Kwargs:
        title: str

    class Slots:
        default: SlotInput
        footer: SlotInput | None = None

    template = """
      <section class="reading-panel">
        <h2>{{ title }}</h2>
        <div class="reading-panel__body">
          <c-slot />
        </div>
        <footer class="reading-panel__footer">
          <c-slot name="footer">
            No action needed.
          </c-slot>
        </footer>
      </section>
    """


class PanelPage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <main>
        <c-ReadingPanel title="Finished">
          <p>Kindred</p>
        </c-ReadingPanel>

        <c-ReadingPanel title="Up next">
          <c-fill name="default">
            <p>A Wizard of Earthsea</p>
          </c-fill>
          <c-fill name="footer">
            <button type="button">Start reading</button>
          </c-fill>
        </c-ReadingPanel>
      </main>
    """


page = PanelPage()

if __name__ == "__main__":
    print(page)

page
