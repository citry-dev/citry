---
title: Template linting
url: https://citry.dev/v/0.4.2/ide/template-linting/
description: "Configure unknown template, Alpine, and component JavaScript variables consistently across Citry tools."
---
# Template linting

Citry reports a free template root that is not available from the component's
template data, a lexical `c-for` or `c-fill` binding, or a known global. The
rule code is `citry.template.unknown-variable`, and its default severity is an
error.

Citry applies the same strict default to browser code that it can prove belongs
to a component:

- `citry.alpine.unknown-variable` checks free roots in Alpine expressions.
- `citry.component-js.unknown-variable` checks free names inside a
  `$component` callback or configuration object's `init` function.

The component JavaScript rule catches a missing context binding such as using
`scope` after destructuring only `data`:


```javascript
$component(({ data }) => {
  scope.ready = data.ready;
});
```


Destructure `scope` to use it, or declare a real project global through the
lint settings when another script supplies that name.

See the diagnostic reference entries for
[template variables](/v/0.4.2/ide/diagnostics/#citry.template.unknown-variable),
[Alpine variables](/v/0.4.2/ide/diagnostics/#citry.alpine.unknown-variable), and
[component JavaScript variables](/v/0.4.2/ide/diagnostics/#citry.component-js.unknown-variable)
for their stable messages and reporting surfaces.

The application owns this policy. `citry check` and the language server use
the same settings, so there is no separate VS Code lint preference.

## Configure the application

Pass one [`LintSettings`](/v/0.4.2/reference/citry/#citry-lintsettings) object to [`Citry`](/v/0.4.2/reference/citry/#citry-citry):


```python
from collections.abc import Callable
from typing import Annotated

from citry import Citry, LintSettings

app = Citry(
    template_globals={
        "site_name": "Citry",
    },
    lint=LintSettings(
        rule_unknown_template_variable="error",
        template_variables={
            "request": Annotated[
                "django.http.HttpRequest",
                "The current framework request.",
            ],
            "url_for": Callable[[str], str],
        },
        rule_unknown_alpine_variable="error",
        alpine_variables={
            "$analytics": Annotated[
                "myapp.browser.Analytics",
                "Analytics available as a custom Alpine magic.",
            ],
        },
        rule_unknown_component_js_variable="error",
        component_js_globals={
            "featureFlags": Annotated[
                "myapp.browser.FeatureFlags",
                "Flags installed by the host page.",
            ],
        },
    ),
)
```


Each `rule_unknown_*` field accepts `"ignore"`, `"warning"`, or `"error"`.

Every key already present in `Citry.template_globals` is known automatically.
Citry conservatively infers ordinary scalar, homogeneous-container, and
importable object types from their runtime values. You do not repeat those
keys in the lint settings merely to suppress a diagnostic.

`template_variables` is analysis metadata. It does not inject a runtime value.
Use it for request-scoped or framework-provided names that enter the render by
another integration. A plain annotation supplies a type. `Annotated[T,
"description"]` also supplies hover documentation. Qualified string
annotations are resolved by the language server in the selected project
environment.

`alpine_variables` and `component_js_globals` follow the same annotation
convention and also supply analysis metadata only. Use `alpine_variables` for
custom Alpine magics or values supplied to an Alpine scope outside Citry. Use
`component_js_globals` for project scripts that make a real global available
inside `$component`. Context values such as `data`, `scope`, `props`, and
`sendEvent` must still be destructured from the `$component` argument; listing
one as a global would hide a real initializer bug.

## Override one component

Use a nested `Lint` declaration when one component has a different contract:


```citry
from typing import Annotated

from citry import Component


class AccountCard(Component):
    class Lint:
        rule_unknown_template_variable = "warning"
        rule_unknown_component_js_variable = "warning"
        template_variables = {
            "account_context": Annotated[
                "myapp.accounts.AccountContext",
                "Context added by the account page integration.",
            ],
        }
        component_js_globals = {
            "accountClient": Annotated[
                "myapp.browser.AccountClient",
                "Client installed by the account page.",
            ],
        }
```


Nested `Lint` declarations compose through component inheritance. The nearest
rule wins, variable mappings merge by name, and `Lint = None` clears inherited
component overrides and returns to the application policy.

`Lint` is a nested component configuration class, not a Citry extension. It
does not install hooks or commands. Citry captures it while defining the
component and combines it with inherited lint declarations.

Go to Definition and Go to Declaration link a lint-only variable to its exact
authored dictionary key when the selected application uses a direct `Citry`
assignment or simple settings aliases. Component variables link to the nested
`Lint` class that supplied the effective value, including inherited and
library-component declarations. Computed mappings and factory-built settings
remain valid at runtime but have no guessed navigation target.

## Understand open schemas

Citry tracks known fields separately from whether they exhaust the normalized
runtime mapping:

| Namespace | Configured `error` | Configured `warning` | Configured `ignore` |
| --- | --- | --- | --- |
| Closed schema | error | warning | no finding |
| Pydantic `extra="allow"` | warning | warning | no finding |
| Unknown or absent schema | error | warning | no finding |

A Pydantic schema that explicitly allows extras can accept an undeclared name
at runtime, so Citry does not call it a definite error. It remains a warning
because relying on arbitrary undeclared keys makes a template contract harder
to understand. Unknown and absent schemas stay strict by default. Declare a
real variable or choose a component override when dynamic data is intentional.

Plain schema classes, dataclasses, NamedTuples, and Pydantic models that ignore
or forbid extras are closed.

## Run the batch check

Unknown-variable linting requires a complete component registry:


```console
citry --app myproject.app:app check
```


Warnings are printed and included in JSON output but do not make the command
fail. Any error exits with status 1. `citry check --static` cannot prove which
component owns a template or browser asset, so it intentionally performs
syntax checks without these namespace rules.

Extensions that add template data can publish detached namespace metadata with
[`TemplateNamespaceContribution`](/v/0.4.2/reference/extensions/#citry-templatenamespacecontribution). An
extension can enumerate variables or report that it preserves unenumerated
extras, but it cannot weaken the application's selected rule severity.