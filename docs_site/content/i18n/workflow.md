---
title: Translation workflow and tooling
description: Check message contracts, inspect project catalogs, hand source to translators, and compile package artifacts.
---

# Translation workflow and tooling

As an application changes, messages, translations, and the code that
calls them drift apart: a variable is renamed, a message is deleted, a
new message is never translated. Citry can check all of them together,
so these problems show up in CI instead of on a user's screen.

A typical workflow:

```text
Write source messages
→ check message IDs, variables, and calls
→ translate into each locale
→ check coverage of each locale
→ compile catalog packages
→ build and deploy
```

This page covers each step and the commands that support it.

## Write source messages

The message in the source language defines the message: its ID, its
text and attributes, and the type of each variable. Write it in the
component's `messages` block or in a catalog package:

```fluent
# @param {str} $name - User name.
my-app-account-greeting = Welcome, { $name }.
```

Translators then write the same message in their locale's file, using
the same variables, without the `@param` comments:

```fluent
my-app-account-greeting = Ahoj, { $name }.
```

See [Write messages](/i18n/messages/) and
[Organize catalogs](/i18n/catalogs/).

## Check messages

Run the project checker with your application:

```bash
citry --app myproject.engine:app check
```

With `--app`, the checker sees every component's messages and every
configured catalog package at once. It reports problems such as:

- a call to an unknown message or attribute;
- two sources that define the same message;
- a missing, unknown, or wrongly typed variable;
- a broken, duplicate, unsupported, or unused `@param` comment;
- an unknown ID in `Component.I18n.client_messages`, the list of
  messages a component's browser code loads by runtime ID;
- a `<c-trans>` rich message that has no translation in some locale,
  because rendering it there fails;
- a `tr()` call or `I18n.client_messages` entry that would show text
  from a fallback language, as a warning you can change; and
- a variable without a type, at the severity you configure.

`citry check --static` checks syntax only and cannot see the whole
catalog. Use the `--app` form in CI.

## Find untranslated text { #find-missing-translations }

`coverage` lists, for each message and each Fluent attribute, whether
the locale has its own translation, falls back to another configured
locale, or falls back to the source language it was written in:

```bash
citry --app myproject.engine:app \
  ext run i18n coverage --locale cs-CZ
```

Repeat `--locale` for several locales. Add `--json` for output that
scripts can read. Add `--fail-on-missing` to exit with an error when any
message in the requested locales falls back to its source language; a
fallback to another configured locale does not count:

```bash
citry --app myproject.engine:app \
  ext run i18n coverage \
  --locale cs-CZ \
  --locale ar-EG \
  --json \
  --fail-on-missing
```

`coverage` also works when the engine has no i18n settings.

## Help translators

Translators see the comments above a message. Say where the text
appears, how much space it has, its tone, and whether it is an
accessible label. The description after each `@param` type explains the
variable:

```fluent
# Label above the list of account owners.
# @param {str} $name - Display name of the primary owner.
my-app-account-owner = Owner: { $name }
```

Leave implementation details out of these comments.

Use IDs with application and feature prefixes, such as
`my-app-account-owner`. A translator, or an error message, can then
trace the text back to its feature.

## Check in CI

At minimum, have CI:

1. run `citry --app ... check`;
2. run `citry --app ... ext run i18n check`;
3. run `citry --app ... ext run i18n coverage --fail-on-missing` for the
   locales that must be complete;
4. compile the catalog packages again;
5. fail if compiling changed the committed files; and
6. build the wheel, install it, and check that the descriptor, locale
   files, and compiled files are all present.

In your application tests, include at least one right-to-left locale
and a test locale with noticeably longer text. Check visible text,
accessible names, `lang`, `dir`, focus, and form input, not only
screenshots.

## Use the i18n commands

The i18n extension adds five commands under `citry ext run i18n`.
`coverage` is described above.

### Build the full catalog

```bash
citry --app myproject.engine:app \
  ext run i18n check
```

Loads every component's messages and every configured package, builds
the complete catalog, and prints the catalog and formatter versions. It
does not render any component.

### List sources

```bash
citry --app myproject.engine:app \
  ext run i18n extract
```

Prints JSON listing the package, locale, and path of every message
source Citry found, always in the same order. Use it to confirm that
Citry finds your files, or as input to other tools. It does not change
any `.ftl` file.

### Inspect the catalog

```bash
citry --app myproject.engine:app \
  ext run i18n inspect --out build/i18n-project.json
```

Writes the complete built catalog as JSON, or prints it when you leave
out `--out`. Use it to see which locale and file supplied a message, the
variables Citry found, and the versions that identify the result.

### Compile packages

```bash
citry --app myproject.engine:app \
  ext run i18n compile my_app_i18n
```

Writes the `_compiled` files into each named package, then loads them
the way production would to verify them. Without package names, it
compiles every package in the `catalogs` setting. The packages must be
writable source folders. Run it before building the wheel; see
[Production and deployment](/i18n/production/).

## Change type warnings { #make-a-missing-type-an-error-or-ignore-it }

A variable without an `@param` comment is a warning by default, whether
the server or the browser translates it. Change this for the whole
application with [`LintSettings`][citry.LintSettings]:

```python
from citry import Citry, LintSettings

app = Citry(
    lint=LintSettings(
        rule_i18n_missing_param_type="error",
    ),
)
```

Or for one component:

```citry
class LegacyNotice(Component):
    class Lint:
        rule_i18n_missing_param_type = "ignore"
```

The severities are `ignore`, `warning`, and `error`. Variables used in
selectors or formatting functions, and variables filled as a `Slot`,
always need a type, whatever the setting.

## Change fallback warnings { #change-fallback-warnings }

A locale may stay partly translated: a message without a translation
shows text from a fallback language. `citry check` warns about each
`tr()` call, `self.i18n.tr()` call, and `I18n.client_messages` entry that
would do so, because a screen reader reads that text as the page's
language
([why this matters](/i18n/direction-and-bidi/#mark-fallback-text-with-its-language)).
Calls in browser code, such as `$i18n.tr()`, are not checked for
fallback.

To fail the check until every locale is complete, make it an error:

```python
from citry import Citry, LintSettings

app = Citry(
    lint=LintSettings(
        rule_i18n_cross_language_fallback="error",
    ),
)
```

To hide the warning for a component that is translated later, use its
`Lint` class:

```citry
class BetaBanner(Component):
    class Lint:
        rule_i18n_cross_language_fallback = "ignore"
```

A `<c-trans>` rich message without a translation is always an error,
because rendering it in that locale fails. To fail CI only when a
message falls back to its source language, keep the warning and use
`coverage --fail-on-missing`, described in
[Find untranslated text](#find-missing-translations).

## Navigate in VS Code

When the [VS Code extension](/ide/vscode/) knows your application (the
`citry.app` setting), it uses the same catalog as the checker. It
completes message IDs and format profile names, shows variable types on
hover, and jumps to a message's definition from:

- template `tr()` and `<c-trans message="...">`;
- Python `self.i18n.tr()` and `Component.I18n.client_messages`;
- Vue `$i18n.tr()` inside a client provider;
- `$c-tr` bindings;
- component JavaScript calls on `component.$i18n` or `this.$i18n`,
  including `bind()` with an object literal; and
- message references inside Fluent.

It also highlights inline `messages` blocks and `.ftl` files.
