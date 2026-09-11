---
title: v0.5.1 (2026-09-11)
url: https://citry.dev/v/0.5.1/releases/v0.5.1/
description: "What changed in citry v0.5.1 (2026-09-11)."
---
# v0.5.1 (2026-09-11)

- **Values passed to `template_data()` are no longer `Const()`.**

    When you define a literal value in a template, Citry knows it's a literal
    and wraps it in `Const(...)` to optimize the template rendering:

    `<c-MyCard text="Hello">` -> `<c-MyCard c-text="Const('Hello')">`

    `Const()` is a [wrapt](https://github.com/GrahamDumpleton/wrapt) proxy - it
    copies the methods and behavior of the underlying
    value, so you rarely notice the difference.

    When such value is passed to a component, component's `template_data()`
    may receive `Const()` instead of the underlying value.

    We discovered critical problems:
    - `is` keyword does NOT respect the proxying.
    - Python's `pathlib` does NOT accept a string wrapped in a proxy.
    - and more...

    Because of this, values passed to `template_data()` are now always unwrapped.
    So that you don't have to deal with flaky behavior.

    The tradeoff is ~10% slower render time.

    Fixes ([#107](https://github.com/citry-dev/citry/issues/107)).

- The linter (`citry check`) now reports error for State bindings (`:c-*` HTML attributes) when:
   - Placed on unsupported elements and or `<input>` with unsupported type.
   - Unknown State key or unknown event handler is set.

- `citry check` validates `$component` callback data members against declared
  or inferred JavaScript data schemas
  ([#113](https://github.com/citry-dev/citry/issues/113)).