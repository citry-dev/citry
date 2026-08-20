---
title: Translation workflow and tooling
url: https://citry.dev/v/0.4.1/i18n/workflow/
description: "Check message contracts, inspect project catalogs, hand source to translators, and compile package artifacts."
---
# Translation workflow and tooling

Citry treats a message as checked application data. The source message defines
its stable ID and parameter interface. Translations may change grammar and
ordering, but they must still satisfy that interface.

A normal workflow is:


```text
Write source messages
→ check message IDs, variables, and call sites
→ translate locale catalogs
→ check the complete locale graph
→ compile standalone packages
→ build and deploy the application
```


## Write the defining source first

Put component-owned source text in `messages` or `messages_file`, or put shared
source text in a standalone catalog package:


```fluent
# @param {str} $name - User name.
my-app-account-greeting = Welcome, { $name }.
```


The defining source owns:

- the public message ID;
- the value and attributes;
- the allowed variables and `@param` types;
- public message references and private terms; and
- the package source locale.

Translators edit the corresponding locale file without copying the `@param`
declarations:


```fluent
my-app-account-greeting = Ahoj, { $name }.
```


## Run the project checker

Run Citry's normal registry-backed checker against the engine:


```bash
citry --app myproject.engine:app check
```


The project index lets i18n checks see component messages and configured
catalog packages together. It can report problems such as:

- an unknown literal message or attribute;
- two source units defining the same public ID;
- a missing, unknown, or statically incompatible argument;
- malformed, duplicate, unsupported, or unused `@param` metadata;
- an unknown `Component.I18n.client_messages` ID;
- unsafe cross-language fallback at a call site that cannot carry `lang`; and
- a missing parameter type according to the configured lint severity.

An application-backed check knows the complete registry. Syntax-only
`citry check --static` cannot prove the same project-wide catalog facts, so use
the explicit app form in CI.

## Choose the missing-type lint severity

A simple server-only scalar without `@param` metadata is a warning by default.
Set the application policy with [`LintSettings`](/v/0.4.1/reference/citry/#citry-lintsettings):


```citry
from citry import Citry, LintSettings

app = Citry(
    lint=LintSettings(
        rule_i18n_missing_param_type="error",
    ),
)
```


One component may override that lint rule:


```citry
class LegacyNotice(Component):
    class Lint:
        rule_i18n_missing_param_type = "ignore"
```


The accepted severities are `ignore`, `warning`, and `error`. Selectors,
formatters, browser values, and rich `Slot` parameters still need a concrete
type because their runtime behavior cannot be checked without it.

## Use the i18n extension commands

The built-in extension adds five commands below `citry ext run i18n`.

### Report locale coverage


```bash
citry --app myproject.engine:app \
  ext run i18n coverage --locale cs-CZ
```


`coverage` reports every checked message value and Fluent attribute as an
exact translation, an owner-source fallback, or another configured fallback.
It also works in zero-configuration source mode.

Repeat `--locale` to select several locales, use `--json` for stable machine
output, and use `--fail-on-missing` in CI to exit unsuccessfully when any
requested output falls back to the source text:


```bash
citry --app myproject.engine:app \
  ext run i18n coverage \
  --locale cs-CZ \
  --locale ar-EG \
  --json \
  --fail-on-missing
```


### Check the compiled catalog


```bash
citry --app myproject.engine:app \
  ext run i18n check
```


This loads every registered component source and configured package, compiles
the complete catalog, and prints the catalog and formatter revisions. It does
not render a component.

### List source units


```bash
citry --app myproject.engine:app \
  ext run i18n extract
```


`extract` prints a deterministic JSON index of the package, locale, and path of
each source unit used by the compiler. It is useful for verifying discovery and
for feeding project tooling. It does not rewrite the `.ftl` files.

### Inspect the checked artifact


```bash
citry --app myproject.engine:app \
  ext run i18n inspect --out build/i18n-project.json
```


`inspect` writes the complete checked project artifact. Use it to see which
locale and source path won for a public output, which interfaces were
extracted, and which revisions identify the result.

Without `--out`, the command prints JSON to standard output.

### Compile catalog packages


```bash
citry --app myproject.engine:app \
  ext run i18n compile my_app_i18n
```


Omit package names to compile every package listed in the engine's `catalogs`
setting. The command writes `_compiled/manifest.json`, `server.json`, and
`link.json` into each writable source package, then verifies the result as a
production loader would.

Run this command before the wheel build. See
[Production and deployment](/v/0.4.1/i18n/production/) for the package requirements.

## Navigate messages in VS Code

With `citry.app` configured, the Citry language server reads the same checked
catalog index as the project checker. It completes literal message IDs and
named formatter or parser profiles, shows each message's typed parameters on
hover, and navigates to definitions from:

- template `tr()` and `<c-trans message="...">` calls;
- Python `self.i18n.tr()` and `Component.I18n.client_messages`;
- Alpine `$i18n.tr()` inside a client-enabled provider;
- checked `$c-tr` bindings in component templates;
- component JavaScript calls and bounded `i18n.bind()` registrations through
  the injected `i18n` service; and
- public message references inside Fluent.

The extension also colors inline `messages` blocks and standalone `.ftl`
files. The docs playground uses Citry's small CodeMirror Fluent highlighter.
Coloring does not replace the Rust compiler: catalog validation, interfaces,
references, and source locations still come from the checked project index.

See [VS Code](/v/0.4.1/ide/vscode/) for project setup and the boundary between
registry-backed features and syntax-only mode.

## Give translators useful context

The optional text after an `@param` type belongs to the translator:


```fluent
# Label above the list of account owners.
# @param {str} $name - Display name of the primary owner.
my-app-account-owner = Owner: { $name }
```


Use ordinary Fluent comments to explain where the message appears, its space
constraints, tone, and whether an attribute is an accessible name. Keep
implementation details out of those comments.

Use stable IDs with application and feature prefixes. That gives a translator
and a diagnostic a direct path back to the owning feature.

## Check translations before release

At minimum, CI should:

1. run `citry --app ... check`;
2. run `citry --app ... ext run i18n check`;
3. run `citry --app ... ext run i18n coverage --fail-on-missing` for the
   locales that must be complete;
4. regenerate standalone package artifacts;
5. fail if regeneration changes committed artifacts; and
6. build and inspect the installed wheel so the descriptor, locale files, and
   compiled files are all present.

Exercise at least one right-to-left locale and a visibly expanded test locale
in application-level tests. Check visible text, accessible names, `lang`,
`dir`, focus behavior, and input state rather than only taking screenshots.