---
title: Conditions and loops
url: https://citry.dev/v/0.4.1/syntax/control-flow/
description: "Show, skip, and repeat template content with Citry's if, elif, else, for, and empty forms."
---
# Conditions and loops

Citry can show content when a Python expression is true and repeat content for
every item in an iterable. Each tool has two forms:

- Put a shorthand attribute on one HTML or component tag.
- Use a built-in tag around a larger piece of markup.

Choose the form that keeps the resulting HTML easiest to see.

## Show one element conditionally

Put `c-if` directly on the element you want to show:


```citry-html
<p c-if="account.is_active">Your account is active.</p>
```


Citry evaluates the value as a Python expression. When it is truthy, the
entire `<p>` renders. When it is falsy, nothing from that element renders.

Add adjacent `c-elif` and `c-else` elements when there are several possible
results:


```citry-html
<p c-if="role == 'admin'">Administrator tools</p>
<p c-elif="role == 'editor'">Editor tools</p>
<p c-else>Reader account</p>
```


Citry renders the first truthy branch and skips the rest. Conditions use
normal Python truthiness: a non-empty list is truthy and an empty list is
falsy. `c-else` is bare and must not have a value.

## Wrap several elements in a condition

Use the tag form when one branch contains several elements:


```citry-html
<c-if cond="account.is_active">
  <h2>Welcome back</h2>
  <p>Your account is ready.</p>
</c-if>
<c-else>
  <c-ActivationHelp />
</c-else>
```


The condition belongs in `cond="..."` without `{{ }}`. `<c-elif>` also takes
a `cond` attribute; `<c-else>` does not.

For compatibility, the tag form treats a bare `cond` or `cond=""` as `True`.
Prefer an explicit expression so the intent is visible. The shorthand `c-if`
and `c-elif` forms require a non-empty expression value.

Every `elif` and `else` branch must immediately follow the branch before it.
Formatting whitespace and template comments between branches are fine:


```citry-html
<p c-if="ready">Ready</p>
{# Explain why the fallback exists. #}
<p c-else>Still working</p>
```


Template comments do not render, so neither they nor the formatting whitespace
around them becomes part of a branch. Text, an HTML comment, an expression, or
another element between branches does produce content, so it breaks the chain
and is an error. The same rule applies between `for` and `empty` branches.

## Repeat one element

Put `c-for` on the element you want to repeat:


```citry-html
<ul>
  <li c-for="book in books">{{ book.title }}</li>
  <li c-empty>No books yet.</li>
</ul>
```


The first `<li>` renders once for each book. The adjacent `c-empty` element
renders only when the loop produces no rows. `c-empty` is bare and must not
have a value.

The loop name is available everywhere on the repeated element, including its
other attributes:


```citry-html
<li
  c-for="book in books"
  c-class="{'featured': book.is_featured}"
>
  {{ book.title }}
</li>
```


## Repeat a larger block

Use `<c-for>` when each item needs several sibling elements:


```citry-html
<c-for each="book in books">
  <h2>{{ book.title }}</h2>
  <p>{{ book.summary }}</p>
</c-for>
<c-empty>
  <p>No books yet.</p>
</c-empty>
```


Put the loop clause in `each="..."`, again without `{{ }}`.

## Unpack and filter values

The loop clause uses Python comprehension syntax. You can unpack each item:


```citry-html
<c-for each="name, score in scores.items()">
  <p>{{ name }}: {{ score }}</p>
</c-for>
```


You can also filter rows:


```citry-html
<c-for each="book in books if book.is_available">
  <p>{{ book.title }}</p>
</c-for>
```


Multiple `for` clauses work too:


```citry-html
<c-for
  each="shelf in shelves for book in shelf.books"
>
  <p>{{ shelf.name }}: {{ book.title }}</p>
</c-for>
```


`c-empty` renders when the complete comprehension produces no rows, including
when a filter removes every item.

The names you bind exist only inside the loop. Citry does not provide a
special `loop` object, so there is no `loop.index` or `loop.first`. Prepare an
index in Python, then unpack it in the template:


```citry-html
<!-- indexed_books = list(enumerate(books, start=1)) -->
<p c-for="number, book in indexed_books">
  {{ number }}. {{ book.title }}
</p>
```


Loop targets must be unique and may not replace a name that is already
visible. If the template already has a `book` variable, bind this loop to a
different name. This is rejected even when the iterable is empty.

Async comprehensions are not supported.

## Combine a condition and a loop carefully

You may put `c-if` and `c-for` on the same element:


```citry-html
<p c-if="show_books" c-for="book in books">
  {{ book.title }}
</p>
```


The condition is outside the loop. Citry checks `show_books` once, before it
starts iterating, so the condition cannot use `book`.

An adjacent `c-empty` cannot attach to this combined shorthand because the
outer condition separates it from the loop. When you need both a condition
and an empty state, make the order visible with nested tags:


```citry-html
<c-if cond="show_books">
  <c-for each="book in books">
    <p>{{ book.title }}</p>
  </c-for>
  <c-empty>No books yet.</c-empty>
</c-if>
```


Read [Expressions](/v/0.4.1/syntax/expressions/) for the Python you can use in a
condition or loop clause. Read [Attributes](/v/0.4.1/syntax/dynamic-attributes/) for
the other dynamic attributes you can put on a repeated element.