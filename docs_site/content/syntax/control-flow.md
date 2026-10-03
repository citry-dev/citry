---
title: Conditions and loops
description: Show, skip, and repeat template content with Citry's if, elif, else, for, and empty forms.
---

# Conditions and loops

A template often shows a part only in some cases, such as admin tools for an
admin, or repeats a part for every item, such as one row per book. Citry
decides both in Python while it renders the page.

Each has two forms:

- An attribute, such as `c-if` or `c-for`, on the one tag it controls.
- A tag, such as `<c-if>` or `<c-for>`, around a larger block.

## `c-if`, `c-elif`, `c-else` { #add-a-condition }

Put `c-if` on the element:

```citry-html
<p c-if="account.is_active">Your account is active.</p>
```

The value is a Python expression. When it is true, the whole `<p>` renders.
When it is false, nothing from it renders. Conditions follow Python's rules,
so an empty list counts as false.

For several cases, add `c-elif` and `c-else` on the elements right after it:

```citry-html
<p c-if="role == 'admin'">Administrator tools</p>
<p c-elif="role == 'editor'">Editor tools</p>
<p c-else>Reader account</p>
```

Citry renders the first branch whose condition is true and skips the rest.
`c-else` takes no value.

## `<c-if>` blocks { #wrap-several-elements }

When a branch holds several elements, use the tag form. Write the condition
in `cond`, without `{{ }}`:

```citry-html
<c-if cond="account.is_active">
  <h2>Welcome back</h2>
  <p>Your account is ready.</p>
</c-if>
<c-else>
  <c-ActivationHelp />
</c-else>
```

`<c-elif>` also takes `cond`. `<c-else>` takes nothing.

## `c-for` and `c-empty` { #repeat-an-element }

Put `c-for` on the element to repeat. Add a `c-empty` element right after it
for the case when there are no items:

```citry-html
<ul>
  <li c-for="book in books">{{ book.title }}</li>
  <li c-empty>No books yet.</li>
</ul>
```

`c-empty` takes no value.

The loop name works anywhere on the repeated element, including its other
attributes:

```citry-html
<li
  c-for="book in books"
  c-class="{'featured': book.is_featured}"
>
  {{ book.title }}
</li>
```

## `<c-for>` blocks { #repeat-a-larger-block }

When each item needs several elements, use `<c-for>` and write the loop in
`each`, without `{{ }}`:

```citry-html
<c-for each="book in books">
  <h2>{{ book.title }}</h2>
  <p>{{ book.summary }}</p>
</c-for>
<c-empty>
  <p>No books yet.</p>
</c-empty>
```

## `<c-for>` unpack and filter { #unpack-and-filter-values }

The loop is written like the `for` part of a Python list comprehension. You
can unpack each item:

```citry-html
<c-for each="name, score in scores.items()">
  <p>{{ name }}: {{ score }}</p>
</c-for>
```

Skip items with `if`:

```citry-html
<c-for each="book in books if book.is_available">
  <p>{{ book.title }}</p>
</c-for>
```

Loop over nested lists with several `for` parts:

```citry-html
<c-for
  each="shelf in shelves for book in shelf.books"
>
  <p>{{ shelf.name }}: {{ book.title }}</p>
</c-for>
```

`c-empty` renders when no items are left, including when `if` skipped all of
them.

## `<c-for>` indices

There is no `loop.index` or `loop.first`. Pair items with numbers in Python,
then unpack them in the loop:

```citry-html
<!-- indexed_books = list(enumerate(books, start=1)) -->
<p c-for="number, book in indexed_books">
  {{ number }}. {{ book.title }}
</p>
```

## Combine `c-if` and `c-for`

`c-if` and `c-for` can share an element:

```citry-html
<p c-if="show_books" c-for="book in books">
  {{ book.title }}
</p>
```

The condition wraps the loop. Citry checks `show_books` once, before the
loop, so the condition cannot read `book`. To skip single items, filter in
the loop with `if`.

A `c-empty` cannot follow this combined element. When you need a condition,
a loop, and an empty message, nest the tags:

```citry-html
<c-if cond="show_books">
  <c-for each="book in books">
    <p>{{ book.title }}</p>
  </c-for>
  <c-empty>No books yet.</c-empty>
</c-if>
```

## `c-elif`/`c-else` order { #keep-branches-next-to-each-other }

Each `elif`, `else`, or `empty` branch must come right after the branch
before it. Whitespace and [template comments](/syntax/comments/) between
them are fine, because they render nothing:

```citry-html
<p c-if="ready">Ready</p>
{# Explain why the fallback exists. #}
<p c-else>Still working</p>
```

Anything that renders breaks the chain and is an error: text, an HTML
comment, an expression, or another element.

## Less common rules

- The names a loop creates exist only inside the loop.
- A loop name must not reuse a name the template already has. If the
  template has a `book` variable, name the loop variable something else.
  Citry rejects the clash even when the list is empty.
- Each name in one loop must be different, so `x, x in pairs` is an error.
- Async comprehensions are not supported.
- The tag form treats a bare `cond` or `cond=""` as `True`, for
  compatibility. Write an explicit expression instead. The `c-if` and
  `c-elif` attributes always need a value.

Read [Expressions](/syntax/expressions/) for the Python you can use in a
condition or loop, and [Attributes](/syntax/attributes/) for the
other attributes you can put on a repeated element.
