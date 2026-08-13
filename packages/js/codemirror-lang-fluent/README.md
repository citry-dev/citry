# @citry/codemirror-lang-fluent

A small CodeMirror 6 syntax highlighter for [Project Fluent](https://projectfluent.org/).
Citry uses it for `Component.messages` blocks in the browser playground.

```js
import { fluent } from "@citry/codemirror-lang-fluent";

const extensions = [fluent()];
```

This package colors messages, attributes, terms, variables, selectors,
functions, strings, numbers, and comments. It does not provide a complete
Fluent syntax tree, validation, formatting, completion, or navigation. Citry's
Rust Fluent compiler remains authoritative for those features.

The package is private while Citry coordinates with the CodeMirror and Fluent
projects about an official package backed by a complete Lezer grammar.
