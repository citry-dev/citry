---
title: Add flexible content
url: https://citry.dev/v/0.4.6/getting-started/add-slots/
description: "Give a Citry component a main content area, a named area, and fallback content that appears when nothing is supplied."
---
# Add flexible content

The reading lists on your page accept Python options. Sometimes the person
using a component should be able to add whole pieces of HTML instead.

You will build a panel with one area for its main content and another for an
optional action. If no action is supplied, the panel shows a useful fallback.

## Create the panel

Save this as `reading_panel.py`:



### Named slots and fallback content

````citry
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
````



Run it:


```sh
python reading_panel.py
```


The first panel ends with “No action needed.” The second ends with a “Start
reading” button.

## Mark slots

Inside `ReadingPanel`, each [`<c-slot>`](/v/0.4.6/reference/builtins/#c-slot) marks a place where another template may
put content.

Here is how what's on the outside gets inserted on the inside:


```citry-html
<!-- Inside ReadingPanel (inside) -->
<div class="reading-panel__body">
  <c-slot />    ≪≪≪≪≪≪≪≪≪≪≪≪≪≪≪≪≪≪
</div>                               |
                                     |
<!-- Inside PanelPage (outside) -->  |
<c-ReadingPanel title="Finished">    |
  <p>Kindred</p>  ≫≫≫≫≫≫≫≫≫≫≫≫≫≫≫≫≫
</c-ReadingPanel>
```


The `<p>` is plain content inside `<c-ReadingPanel>`. Citry inserts it where
`<c-slot />` appears. Because that slot has no name, it is the **default slot**.

The footer uses a name to connect its two sides:


```citry-html
<!-- Inside ReadingPanel (inside) -->
<footer class="reading-panel__footer">
  <c-slot name="footer">   ≪≪≪≪≪≪≪≪≪≪≪
    No action needed.                   |
  </c-slot>                             |
</footer>                               |
                                        |
<!-- Inside PanelPage (outside) -->     |
<c-ReadingPanel title="Up next">        |
  <c-fill name="default">               |
    <p>A Wizard of Earthsea</p>         |
  </c-fill>                             |
  <c-fill name="footer">   ≫≫≫≫≫≫≫≫≫≫≫
    <button type="button">
      Start reading
    </button>
  </c-fill>
</c-ReadingPanel>
```


The matching `name="footer"` values tell Citry where the button belongs. The
button replaces “No action needed.” If there is no `footer` fill, that text
stays as the fallback.

## Declare accepted slots

[`Slots`](/v/0.4.6/reference/component/#citry-component-slots) gives those two places names in Python:


```python
class Slots:
    default: SlotInput
    footer: SlotInput | None = None
```


The default slot is required because it has no default value. The footer is
optional, so the component can use the fallback from its template.

[`SlotInput`](/v/0.4.6/reference/slots/#citry-slotinput) means the fill may contain rendered HTML, text,
another component, or a function that produces content. You do not need to
choose one of those forms when you declare the slot.

## Fill the slots

When you only fill the default slot, put the content directly inside the
component tag:


```citry-html
<c-ReadingPanel title="Finished">
  <p>Kindred</p>
</c-ReadingPanel>
```


When you use a named fill, name every area explicitly, including `default`:


```citry-html
<c-ReadingPanel title="Up next">
  <c-fill name="default">
    <p>A Wizard of Earthsea</p>
  </c-fill>
  <c-fill name="footer">
    <button type="button">Start reading</button>
  </c-fill>
</c-ReadingPanel>
```


Keeping the fills explicit makes it clear which content belongs in each area.
Citry reports an error if named fills and loose body content are mixed inside
the same component tag.

## Next steps

You can now pass Python values through `Kwargs` and pass whole pieces of content
through slots. The [Slots guide](/v/0.4.6/concepts/slots/) goes further into required,
scoped, dynamic, and Python-supplied fills.

Next, [add behavior that runs immediately in the
browser](/getting-started/browser-interactivity/).