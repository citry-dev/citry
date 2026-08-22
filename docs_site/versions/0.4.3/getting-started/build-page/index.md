---
title: Build a page from components
url: https://citry.dev/v/0.4.3/getting-started/build-page/
description: "Import your Citry components, use them as tags inside a page, pass Python values to them, and check the rendered result."
---
# Build a page from components

Small components become much more useful when you put them together. In this
step, you will use two reading lists inside one complete HTML page.

Keep `reading_list.py` from [Use data in a
component](/getting-started/data-in-components/) in the same folder.

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

## Import components

This line matters even though `ReadingList` is not mentioned in the Python
code below it:


```python
from reading_list import ReadingList
```


Importing the module creates the component class and tells Citry that the
`<c-ReadingList>` tag exists. If you remove the import, Citry cannot find that
tag when it renders the page.

Larger projects can discover component modules automatically. For now, an
ordinary import keeps the setup visible. Read
[Registration](/v/0.4.3/concepts/registration/) for tag names and engine ownership,
then
[Component discovery](/v/0.4.3/advanced/component-discovery/) for automatic imports
and startup.

## Pass component inputs

The first list receives two kinds of options:


```citry-html
<c-ReadingList
  heading="Reading now"
  c-books="current_books"
/>
```


`heading="Reading now"` passes those exact words. The `c-` prefix on
`c-books` tells Citry to evaluate `current_books` from the page's Python data
and pass the resulting list.

Use a plain option for fixed text. Use the `c-` form when the value is a Python
expression:


```citry-html
<c-ReadingList heading="Fixed words" c-books="books_from_python" />
```


The child receives only the values you pass. It cannot silently read other
variables from the page around it, which makes the component safe to reuse.

## Add a render check

You can test the useful result without matching Citry's generated attributes.
Save this as `check_page.py`:


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


This check describes what a reader should see, and it does not need another
package. It will keep working when an unimportant generated attribute changes.

[Testing components](/v/0.4.3/advanced/testing/) shows how to turn checks like this
into pytest tests and add browser or framework coverage for larger projects.

## Next steps

You now have a complete page made from smaller pieces, and you have checked its
meaningful output. Next, [add flexible content with named areas and useful
fallbacks](/getting-started/add-slots/).