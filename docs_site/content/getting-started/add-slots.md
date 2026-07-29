---
title: Add flexible content
description: Give a Citry component a main content area, a named area, and fallback content that appears when nothing is supplied.
---

# Add flexible content

The reading lists on your page accept Python options. Sometimes the person
using a component should be able to add whole pieces of HTML instead.

You will build a panel with one area for its main content and another for an
optional action. If no action is supplied, the panel shows a useful fallback.

## Create the panel

Save this as `reading_panel.py`:

<c-live-code
  path="docs_site/live_snippets/reading_panel.py"
  title="Named slots and fallback content"
/>

Run it:

```sh
python reading_panel.py
```

The first panel ends with “No action needed.” The second ends with a “Start
reading” button.

## Mark the places that can change

Inside `ReadingPanel`, each `<c-slot>` marks a place where another template may
put content.

Here is how what's on the outside gets inserted on the inside:

```html
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

```html
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

## Describe the content the panel accepts

`Slots` gives those two places names in Python:

```python
class Slots:
    default: SlotInput
    footer: SlotInput | None = None
```

The default slot is required because it has no default value. The footer is
optional, so the component can use the fallback from its template.

[`SlotInput`][citry.SlotInput] means the fill may contain rendered HTML, text,
another component, or a function that produces content. You do not need to
choose one of those forms when you declare the slot.

## Fill one area or several areas

When you only fill the default slot, put the content directly inside the
component tag:

```html
<c-ReadingPanel title="Finished">
  <p>Kindred</p>
</c-ReadingPanel>
```

When you use a named fill, name every area explicitly, including `default`:

```html
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

## What to try next

You can now pass Python values through `Kwargs` and pass whole pieces of content
through slots. The [Slots guide](/concepts/slots/) goes further into required,
scoped, dynamic, and Python-supplied fills.

Next, [add behavior that runs immediately in the
browser](/getting-started/browser-interactivity/).
