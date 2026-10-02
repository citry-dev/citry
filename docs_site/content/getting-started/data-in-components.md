---
title: Use data in components
description: Give a Citry component typed Python options, show them in its HTML, and turn a list into repeated content.
---

# Use data in components

Most components show data that comes from Python: a title, a list of
records, a count. In this step you build a reading list whose heading, books,
and book count all come from Python, and you learn how to show, repeat, and
hide parts of the HTML based on that data.

If you have not built a component yet, start with
[Your first component](/getting-started/your-first-component/).

## Build the reading list

Save this as `reading_list.py`:

<c-live-code
  path="docs_site/live_snippets/reading_list.py"
  title="Reading list with Python data"
/>

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

Citry adds some attributes of its own, so the complete HTML is a little
longer.

The file's last line, a bare `reading_list`, is what the **Try live** button
shows. Python ignores it when you run the file.

## Declare the options

`Kwargs` lists the named options people can give your component:

```python
class Kwargs:
    books: list[str]
    heading: str = "Reading list"
    empty_message: str = "Your list is empty."
    show_count: bool = True
```

`books` has no default, so it is required. The other options have defaults,
so this works:

```python
ReadingList(books=["The Dispossessed"])
```

It uses “Reading list” as the heading and shows the count. Pass
`show_count=False` to hide the count:

```python
ReadingList(
    books=["The Dispossessed"],
    show_count=False,
)
```

## Compute new values

By default, the template can use each `Kwargs` field by its own name. That is
how `{{ heading }}` inserts the heading.

When the template needs a value that Python must compute, define
[`template_data()`][citry.Component.template_data]. Here it adds `total`, the
number of books:

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

Once you define `template_data()`, the template sees only the names it
returns. That is why it returns the `Kwargs` fields too.

## Show data in the HTML

The template uses four small tools:

- `c-if="show_count and total > 0"` leaves the count out when you hide it or
  when the list is empty. The value can be any Python expression.
- `{{ "book" if total == 1 else "books" }}` chooses the singular or plural
  word with a Python expression inside `{{ }}`.
- `c-for="book in books"` makes one `<li>` for every title.
- `c-data-count="total"` evaluates `total` and writes an ordinary
  `data-count` HTML attribute.

If `books` is empty, the `c-empty` item appears instead:

```html
<li>Your list is empty.</li>
```

[Conditions and loops](/syntax/control-flow/) and
[Attributes](/syntax/dynamic-attributes/) cover the other forms when you
need them.

## Catch wrong options

If you leave out `books`, Citry reports the missing option when the component
renders:

```python
reading_list = ReadingList()
print(reading_list)
# TypeError: ReadingList.Kwargs.__init__() missing ... 'books'
```

A misspelled option is also rejected:

```python
reading_list = ReadingList(books=[], heding="Typo")
print(reading_list)
# TypeError: ReadingList.Kwargs.__init__() got an unexpected
# keyword argument 'heding'. Did you mean 'heading'?
```

!!! note "Type annotations do not check values at runtime"

    The type annotations help your editor and type checker, but Citry does
    not check value types while the program runs. Validate values from
    forms, APIs, or other sources you do not control before you pass them
    in. [Inputs and validation](/concepts/inputs-and-validation/) explains
    the choices.

## Next steps

You now have a component that turns Python data into HTML. Next,
[build a complete page from components](/getting-started/build-page/)
and add a small render check.
