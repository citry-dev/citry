# Functions passed to other functions in the expression sandbox (GHSA-c42m)

- **Advisory:**
  [GHSA-c42m-36vw-xvm3](https://github.com/citry-dev/citry/security/advisories/GHSA-c42m-36vw-xvm3),
  published 2026-11-19, severity medium (CVSS 3.1 score 5.0)
- **Affected and fixed versions:** `citry-core < 2.1.2`, fixed in 2.1.2;
  `citry < 1.0.3`, fixed in 1.0.3, which requires `citry-core` 2.1.2
- **Fix:** [#797](https://github.com/citry-dev/citry/pull/797), merged
  2026-11-19 (`523173cd5`). The sandbox now refuses reading or calling
  `format` and `format_map` on every string type, and refuses a call when
  one of its arguments is a function the sandbox would not call itself.
  A `validate_callable` hook also receives the functions passed as
  arguments. Both raise `SecurityError`. The fix refuses expressions that
  `citry-core` 2.1.1 ran, and the changelog says to use an f-string in
  place of `format`.
- **Reviewer:** two separate reviewing agents at high effort, the second
  on the commits made after the first review
- **Code:** in `packages/py/citry_core/citry_core/safe_eval/`,
  `sandbox.py` (`is_safe_callable`, `find_unsafe_callable_argument` and
  the format-method checks) and `eval.py` (`call`, and the
  `validate_callable` wrapper in `safe_eval`); tests in
  `test_safe_eval_callable_arguments.py`,
  `test_safe_eval_string_formatting.py` and `test_safe_eval.py` (all
  under `packages/py/citry_core/tests/`)

## Who controls the input

Citry evaluates the expressions in a template, such as the values in
`{{ }}` and in `c-*` attributes, inside a sandbox. The sandbox is on by
default (the `sandbox_expressions` setting). The sandbox checks each
name, attribute, item and call that the expression text writes. It
refuses private attributes, unsafe built-ins, and methods marked
`@unsafe` or, in Django, `alters_data`.

The input is the expression text, which the template author writes.
Values that reach a template as data never become expression text, so an
app whose templates are written only by its developers is not affected in
practice. An app that builds template text from request or stored data,
or lets its users write templates, is affected. The security docs tell
apps never to do that; the sandbox is a second layer of protection for
when it happens anyway.

Before the fix, the sandbox checked the function an expression calls,
but not the functions passed to it as arguments. A built-in method that
calls a function it is given, such as `list.sort` with `key=`, then
called a refused function without any check. The advisory names two
results:

- **Running a refused method.** A method marked `@unsafe` or
  `alters_data`, such as `delete` on a Django model in the template
  context, could run. That can change data.
- **Reading private attributes.** Reading `format` on a string was
  allowed and only calling it was refused. Passed to another function,
  `str.format` follows the attribute paths written in the format string,
  including private ones.

The `format` route is the same kind of flaw as the `format` part of
[GHSA-x37g-r286-r75v](https://github.com/citry-dev/citry/security/advisories/GHSA-x37g-r286-r75v),
through a route its fix in `citry-core` 1.9.0 does not cover. djc-core,
which shares this sandbox's design, fixed the same routes in 1.4.0
([GHSA-m62w-jpm9-jr5h](https://github.com/django-components/djc-core/security/advisories/GHSA-m62w-jpm9-jr5h)).

The expression text cannot run arbitrary Python code by this route. Of
the places where a value reaches the browser, listed in Mechanism 7 of
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches none. It changes what template text may do
on the server while Citry renders the page.

## How it was checked

- **A sweep of built-in methods.** A sweep of every public method on the
  types an expression can build from literals, on Python 3.10 and 3.14,
  found that only `list.sort` calls a function it is given. It was run
  for djc-core, which shares this sandbox's design, and the fix relies
  on it.
- **Kinds of function passed as arguments.** Methods marked `@unsafe`
  and `alters_data`, unsafe built-ins, the format methods of `str`,
  `str` subclasses, `UserString` and Django lazy strings (the values
  `gettext_lazy` and similar functions return), those methods read from
  the class, `functools.partial` objects wrapping any of them, and
  functions that a `validate_callable` hook refuses. The tests pass a
  refused function by position, by keyword, and through `*` and `**`
  unpacking.
- **Routes tried from template text alone.** Two separate reviews looked
  for a way past the fix using only the expression text, and found none.
  The first reviewer ran its probes on Python 3.11 to 3.15 with the same
  results.
- **Tests.** 30 new or updated tests fail on the code before the fix,
  most of them in the new file `test_safe_eval_callable_arguments.py`. They cover the
  `alters_data` and `@unsafe` routes, the format methods, partials, and
  the hook.
- **Python versions.** The `safe_eval` tests passed on CPython 3.11,
  3.12, 3.13, 3.14 and 3.15. On free-threaded CPython 3.14, all new tests
  passed. Seven cases of an older t-string test failed there,
  and they fail the same way without the fix, because they depend on the
  CPython patch release. `cargo test -p python_safe_eval` passed (344
  tests); the fix changes no Rust code.
- **The rest of Citry.** The `citry` and `citry_ui` test suites had no new
  failures with the fix. After the release, a clean
  install of `citry` 1.0.3 from PyPI refused the `format` read and a
  sort key that is `str.format`, an `alters_data` method or an `@unsafe`
  method, while a lambda sort key and f-strings still worked.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked two kinds: sandbox escapes, which include a
  Jinja advisory for the same kind of bug, and template injection. The
  fix introduces neither.

## Ruled out

- **A refused function reaching a call through an argument.** Every
  direct argument of a call goes through the same check as the called
  function, after `*` and `**` unpacking, so a function the sandbox
  refuses to call is also refused as an argument.
- **Format methods by another path.** Reading `format` or `format_map`
  is refused, not only calling it, on `str`, its subclasses,
  `UserString` and Django lazy strings. Django gives every method of a
  lazy string the same name, `__wrapper__`, so the check compares the
  method with the `format` function on the class instead of reading its
  name.
- **Partials.** A `functools.partial` is as safe as the function it
  wraps, so one that wraps a refused function is refused.
- **A hook that sees only the called function.** A `validate_callable`
  hook now also receives every function and class passed as an argument.
  A hook that allows only named functions must also allow, for example,
  a lambda sort key. The changelog says so.
- **Refusing too much.** A lambda sort key and f-strings still work.

## Fixed during the review

- **Lazy strings.** The first version of the fix did not refuse `format`
  on Django lazy strings, either when read or when called. Both are
  refused now.
- **Keeping the cause of a failed check.** When checking an argument
  raised an error, the first version let that error escape instead of
  refusing the call. The call is now refused with a `SecurityError` that
  names the error and keeps it as its cause.
- **The changelog.** The first draft of the changelog entry quoted a
  working attack expression. The entry now says what is refused and what
  to use instead.
- Wording in the docs.

## Not tested

- Free-threaded CPython 3.15 and PyPy.
- Functions nested inside a list, tuple or dict argument. The check
  looks only at direct arguments, a deliberate limit that matches
  djc-core. The `safe_eval` docs (the `python_safe_eval` crate README)
  say that a function inside a container is not checked.
- `sorted` and `map` given a refused function. They are not names the
  sandbox provides, so template text cannot reach them; an app could
  pass them into the context. The crate README lists them among the
  functions that call other functions without these checks.

## Follow-ups

None.
