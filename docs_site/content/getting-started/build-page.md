---
title: Build a page from components
description: Import your Citry components, use them as tags inside a page, pass Python values to them, and check the rendered result.
---

# Build a page from components

Real pages are made of many smaller components. In this step you put two
reading lists inside one complete HTML page, pass each one different data,
and add a quick check that the page renders what you expect.

Keep `reading_list.py` from [Use data in
components](/getting-started/data-in-components/) in the same folder.

## Create the page

Save this as `page.py`:

```citry
from citry import Component

from reading_list import ReadingList

class ReadingPage(Component):
    class Kwargs:
        current_books: list[str]
        next_books: list[str]

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>My reading shelf</title>
        </head>
        <body>
          <main>
            <h1>My reading shelf</h1>
            <c-ReadingList
              heading="Reading now"
              c-books="current_books"
            />
            <c-ReadingList
              heading="Up next"
              empty_message="Choose your next book."
              c-books="next_books"
            />
          </main>
        </body>
      </html>
    """


if __name__ == "__main__":
    page = ReadingPage(
        current_books=["A Wizard of Earthsea", "Kindred"],
        next_books=[],
    )
    print(page)
```

Run it:

```sh
python page.py
```

The page contains one list with two books and another with the message
“Choose your next book.”

## Import the components a page uses

This line matters even though the Python code below it never mentions
`ReadingList`:

```python
from reading_list import ReadingList
```

Importing the module defines the component class, and that tells Citry the
`<c-ReadingList>` tag exists. Without the import, Citry cannot find the tag
when it renders the page.

## Pass fixed text or Python values

The first list receives two options:

```citry-html
<c-ReadingList
  heading="Reading now"
  c-books="current_books"
/>
```

`heading="Reading now"` passes those exact words. The `c-` prefix on
`c-books` tells Citry to evaluate `current_books`, the page's own input,
as a Python expression and pass the resulting list. Use a plain attribute for fixed text and the
`c-` form for Python values.

The child receives only the values you pass. It cannot read other variables
from the page around it, so it behaves the same wherever you use it.

## Check the rendered page

A quick check can confirm the page shows the right text, without matching
the extra attributes Citry generates. Save this as `check_page.py`:

```python
from page import ReadingPage

html = str(
    ReadingPage(
        current_books=["Kindred"],
        next_books=[],
    )
)

assert "My reading shelf" in html
assert "Kindred" in html
assert "Choose your next book." in html

print("The page looks right.")
```

Run it:

```sh
python check_page.py
```

The check looks only for text a reader would see, so it keeps passing when a
generated attribute changes. It needs no extra package.

[Testing components](/advanced/testing/) shows how to turn checks like this
into pytest tests and add browser or framework coverage for larger projects.

!!! note "Find components without importing each one"

    Larger projects can import component modules automatically. Read
    [Registration](/concepts/registration/) for how tag names map to
    classes, then [Component discovery](/advanced/component-discovery/)
    for automatic imports.

## Next steps

You now have a complete page made from smaller pieces, and you have checked what
it shows. Next, [add flexible content with named areas and useful
fallbacks](/getting-started/add-slots/).
