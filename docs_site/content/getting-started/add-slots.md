---
title: Add flexible content
description: Give a Citry component a main content area, a named area, and fallback content that appears when nothing is supplied.
---

# Add flexible content

Options like `heading` work well for short values. When the person using a
component should be able to pass whole pieces of HTML, such as a paragraph
or a button, use **slots**: places in the template where outside content
goes.

In this step you build a panel with one slot for its main content and
another for an optional action. If no action is passed in, the panel shows
fallback text.

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

## Mark where outside content goes

Inside `ReadingPanel`, each [`<c-slot>`](/reference/builtins/#c-slot)
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

## Declare which slots are required

[`Slots`][citry.Component.Slots] gives those two places names in Python:

```python
class Slots:
    default: SlotInput
    footer: SlotInput | None = None
```

`default` has no `= ...` value after its type, so it is required. The footer
defaults to `None`, so it is optional and the template's fallback text shows
when it is empty.

[`SlotInput`][citry.SlotInput] accepts any kind of slot content: HTML, text,
another component, or a function that produces content.

## Fill one slot or several

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
through slots. The [Slots guide](/concepts/slots/) covers more, such as
slots that pass data back to their content and filling slots from Python.

Next, [add behavior that runs immediately in the
browser](/getting-started/browser-interactivity/).
