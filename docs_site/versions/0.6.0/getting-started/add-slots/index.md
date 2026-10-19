---
title: Add slots
url: https://citry.dev/v/0.6.0/getting-started/add-slots/
description: "Give a Citry component a main content area, a named area, and fallback content that appears when nothing is supplied."
---
# Add slots

Options like `heading` work well for short values. When the person using a
component should be able to pass whole pieces of HTML, such as a paragraph
or a button, use **slots**: places in the template where outside content
goes.

In this step you build a panel with one slot for its main content and
another for an optional action. If no action is passed in, the panel shows
fallback text.

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

## Place the slots

Inside `ReadingPanel`, each [`<c-slot>`](/v/0.6.0/reference/builtins/#c-slot)
marks a place where content from outside goes. The arrows show where the
content from `PanelPage` ends up:


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

The footer slot has a name, and the outside content uses the same name:


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


Each `<c-fill>` passes content to the slot with the same name. The button
replaces “No action needed.” When nothing fills the `footer` slot, that text
stays as the fallback.

## Declare the slots

[`Slots`](/v/0.6.0/reference/component/#citry-component-slots) gives those two places names in Python:


```python
class Slots:
    default: SlotInput
    footer: SlotInput | None = None
```


`default` has no `= ...` value after its type, so it is required. The footer
defaults to `None`, so it is optional and the template's fallback text shows
when it is empty.

[`SlotInput`](/v/0.6.0/reference/slots/#citry-slotinput) accepts any kind of slot content: HTML, text,
another component, or a function that produces content.

## Fill the slots

When you only fill the default slot, put the content directly inside the
component tag:


```citry-html
<c-ReadingPanel title="Finished">
  <p>Kindred</p>
</c-ReadingPanel>
```


When you fill a named slot, wrap every piece of content in a `<c-fill>`,
including the one for `default`:


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


Citry reports an error if you mix `<c-fill>` tags and loose content inside
the same component tag.

## Next steps

You can now pass Python values through `Kwargs` and whole pieces of content
through slots. The [Slots guide](/v/0.6.0/concepts/slots/) covers more, such as
slots that pass data back to their content and filling slots from Python.

Next, [add behavior that runs immediately in the
browser](/getting-started/browser-interactivity/).