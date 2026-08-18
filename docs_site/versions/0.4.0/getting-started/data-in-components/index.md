---
title: Use data in components
url: https://citry.dev/v/0.4.0/getting-started/data-in-components/
description: "Give a Citry component typed Python options, show them in its HTML, and turn a list into repeated content."
---
# Use data in components

Your first Card accepted one color and a place for content. Now you will build
a reading list whose heading, books, and item count all come from Python.

If you have not built a component yet, start with
[Your first component](/v/0.4.0/getting-started/your-first-component/).

## Build the reading list

Save this as `reading_list.py`:



### Reading list with Python data

````citry
from citry import Component


class ReadingList(Component):
    class Kwargs:
        books: list[str]
        heading: str = "Reading list"
        empty_message: str = "Your list is empty."
        show_count: bool = True

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "books": kwargs.books,
            "heading": kwargs.heading,
            "empty_message": kwargs.empty_message,
            "show_count": kwargs.show_count,
            "total": len(kwargs.books),
        }

    template = """
      <section>
        <h2>{{ heading }}</h2>
        <p c-if="show_count and total > 0">
          {{ total }} {{ "book" if total == 1 else "books" }}
        </p>
        <ul c-data-count="total">
          <li c-for="book in books">{{ book }}</li>
          <li c-empty>{{ empty_message }}</li>
        </ul>
      </section>
    """


reading_list = ReadingList(
    heading="Books for the weekend",
    books=["A Wizard of Earthsea", "Kindred", "Piranesi"],
)

if __name__ == "__main__":
    print(reading_list)

reading_list
````



The final `reading_list` line gives **Try live** the value to preview. Python
ignores that bare expression when you run the file normally; the `__main__`
block prints the same component in your terminal.

Run it:


```sh
python reading_list.py
```


The result contains this list:


```html
<h2>Books for the weekend</h2>
<p>3 books</p>
<ul data-count="3">
  <li>A Wizard of Earthsea</li>
  <li>Kindred</li>
  <li>Piranesi</li>
</ul>
```


Citry adds some attributes of its own, so the complete HTML will be a little
longer.

## Component inputs

`Kwargs` lists the named options people can give your component:


```python
class Kwargs:
    books: list[str]
    heading: str = "Reading list"
    empty_message: str = "Your list is empty."
    show_count: bool = True
```


`books` has no default, so it is required. The other options already have
useful values. This works without mentioning them:


```python
ReadingList(books=["The Dispossessed"])
```


It uses “Reading list” as the heading and shows the count. Pass
`show_count=False` when you do not want the count:


```python
ReadingList(
    books=["The Dispossessed"],
    show_count=False,
)
```


## Template variables

A `Kwargs` field is available to the template under the same name. That is why
`{{ heading }}` inserts the heading and `books` is ready for the loop.

Use [`template_data()`](/v/0.4.0/reference/component/#citry-component-template-data) when the template needs
a new value that Python must work out. Here it adds `total`:


```python
def template_data(
    self,
    kwargs: Kwargs,
    slots: Slots,
) -> dict[str, object]:
    return {
        "books": kwargs.books,
        "heading": kwargs.heading,
        "empty_message": kwargs.empty_message,
        "show_count": kwargs.show_count,
        "total": len(kwargs.books),
    }
```


The method returns every name this template uses.

!!! note

    For a component that only needs its `Kwargs` fields, leave the `template_data()` out and Citry supplies those fields automatically. Like we did in [Your first component](/v/0.4.0/getting-started/your-first-component#create-the-card).

## Template syntax

The template uses four small tools:

- `c-if="show_count and total > 0"` leaves the count out when you hide it or
  when the list is empty. The value can be any Python expression, not only one
  name.
- `{{ "book" if total == 1 else "books" }}` chooses the singular or plural
  word with a Python expression inside `{{ }}`.
- `c-for="book in books"` makes one `<li>` for every title.
- `c-data-count="total"` evaluates `total` and writes an ordinary
  `data-count` HTML attribute.

If `books` is empty, the `c-empty` item appears instead:


```html
<li>Your list is empty.</li>
```


The [Control flow](/v/0.4.0/syntax/control-flow/) and [Dynamic
attributes](/syntax/dynamic-attributes/) pages cover the other forms once you
need them.

## Input validation

If you leave out `books`, Citry tells you that the required option is missing
when the component renders:


```python
print(ReadingList())
# TypeError: ReadingList.Kwargs.__init__() missing ... 'books'
```


A misspelled option is also rejected:


```python
print(ReadingList(books=[], heding="Typo"))
# TypeError: ReadingList.Kwargs got unexpected keyword 'heding'
```


The annotations help your editor and type checker, but they do not check the
value's type while the program runs. Validate values from forms, APIs, or other
untrusted sources before passing them to the component. [Typing and
validation](/concepts/inputs-and-validation/) explains the available choices.

## Next steps

You now have a component that turns Python data into useful HTML. Next,
[build a complete page from components](/v/0.4.0/getting-started/build-page/)
and add a small render test.