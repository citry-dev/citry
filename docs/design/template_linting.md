# Template linting

Status: implemented 2026-08-08.

This document defines the first shared Citry lint rule and the public settings
that control it. The same portable rule implementation serves `citry check`
and editor diagnostics. Editors do not own a parallel Citry preference.

## Scope

The first rule diagnoses a free template root that Citry cannot join to a
parser-proven lexical binding, component template data, or known global. It
does not diagnose members such as `user.name`; member and call intelligence
belongs to the Python analyzer.

The stable rule code is `citry.template.unknown-variable`. Syntax-only analysis
does not run the rule because it cannot associate a template with a component
namespace.

## Public application API

The application configures linting through one immutable object on `Citry`:

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
    ),
)
```

The public records are:

```python
LintSeverity = Literal["ignore", "warning", "error"]


@dataclass(frozen=True, slots=True)
class LintSettings:
    rule_unknown_template_variable: LintSeverity = "error"
    template_variables: Mapping[str, object] = field(default_factory=dict)
```

Rule settings use a `rule_` prefix so they remain visually distinct from
metadata inputs. Unknown settings and invalid severities fail at construction.
Mappings are defensively copied like the other `CitrySettings` mappings.

`LintSettings.template_variables` is analysis metadata only. It does not add a
runtime value. A plain annotation supplies a type. `Annotated[T,
"description"]` supplies the type and one exact string description. A string
annotation is a forward reference resolved in the selected project
environment. Unsupported or ambiguous metadata keeps the name known but drops
the unproven type or description.

## Runtime globals

Every key in the live `Citry.template_globals` mapping is automatically known
to the linter. Its value receives a conservative portable type when Citry can
prove one, including ordinary scalar values and safely importable object
classes. `None`, empty or heterogeneous containers, lazy proxies, and unsafe
objects may retain an unknown type, but the key remains known.

The lint-only `template_variables` mapping is primarily for values supplied by
frameworks, extensions, or per-render integrations outside
`Citry.template_globals`. It may also enrich a runtime global with an explicit
annotation or description. Authors do not duplicate ordinary runtime globals
merely to suppress this rule.

## Component overrides

Components configure lint policy through a nested declaration:

```python
class Card(Component):
    class Lint:
        rule_unknown_template_variable = "warning"
        template_variables = {
            "plugin_value": Annotated[
                str,
                "Added by the card data provider.",
            ],
        }
```

`Component.Lint` composes through component C3. Rule fields use the nearest
declaration. `template_variables` mappings merge with the nearest declaration
winning by name. `Lint = None` clears inherited component overrides and returns
to application policy. A component with a deliberately unbounded namespace can
set the rule to `ignore`, though declaring known dynamic variables is preferred.

`Lint` is component configuration, not an [`Extension`][citry.Extension]. It
does not register hooks, commands, or an independently installed runtime
object. Citry's component metaclass captures the authored nested class and
combines it with inherited component lint declarations.

Application metadata wins over extension metadata for the same global name;
component metadata wins for the same component name. Conflicting lower-priority
types keep the name known but contribute no guessed type. Extensions may add
portable known variables or declare that they intentionally preserve extras,
but they cannot weaken application or component rule severity.

## Namespace policy

Portable schema metadata records known fields separately from whether those
fields exhaust the normalized runtime mapping:

```python
NamespacePolicy = Literal["closed", "allow-extra", "unknown"]
```

- `closed` means normalized runtime output contains only declared fields.
  Plain Citry schema classes, dataclasses, NamedTuples, and Pydantic models with
  `extra="ignore"` or `extra="forbid"` are closed.
- `allow-extra` means the schema explicitly preserves undeclared fields.
  Pydantic v1 or v2 `extra="allow"` has this policy.
- `unknown` means Citry cannot prove either contract. Opaque schemas, an absent
  schema, and unsupported source shapes retain this fact.

The lint rule deliberately treats `unknown` and absent schemas strictly.
Authors who depend on dynamic values declare them or override the rule. The
underlying portable metadata still says `unknown`; it is not falsified to
`closed`, because future tooling may need the distinction.

A Pydantic model that allows extras proves that an undeclared value can be
valid at runtime, but allowing arbitrary keys is an authoring antipattern. Its
diagnostic is therefore capped at warning instead of disappearing.

## Severity

The effective severity is:

| Namespace policy | `ignore` | `warning` | `error` |
| --- | --- | --- | --- |
| `closed` | none | warning | error |
| `allow-extra` | none | warning | warning |
| `unknown` or absent | none | warning | error |

The application default is `error`. A component override applies after the
application setting. For a shared physical template, known component names are
intersected across every proven consumer. The most conservative namespace
policy participates in the diagnostic message, while explicitly
`allow-extra` consumers cap only their own contribution at warning. One
consumer that produces an error makes the shared finding an error.

Closed findings say that a variable is not available in the template. Open
findings say that it is undeclared but may be supplied dynamically. Unknown
findings say that Citry could not determine whether it is supplied dynamically.
The rule enforces declarations; it does not claim that every advisory warning
must fail at render time.

## Resolution order

For each parser-reported free root, analysis accounts for:

1. `c-for` and `c-fill` lexical bindings;
2. declared `TemplateData` fields;
3. conservative `template_data()` roots and inherited `Kwargs` roots;
4. live runtime `Citry.template_globals` keys;
5. application lint-only variables;
6. component lint-only variables;
7. installed extension contributions.

Python-local lambda, comprehension, and assignment-expression bindings remain
inside the Python expression analyzer and are not mistaken for template roots.
Unicode identifier identity follows the parser's Python identifier contract.

## Portable records

`SchemaInfo` and its JSON/catalog form gain `namespace_policy`. Field lists do
not imply closure. The application analysis snapshot carries the effective
rule setting and detached global-variable records. Component catalog records
carry detached component overrides and effective extension contributions.

Each portable variable record contains only strict copied data:

- normalized name;
- optional type display and fidelity;
- optional description;
- contribution source suitable for diagnostics and hover.

No project object or runtime value crosses from the isolated discovery worker
into the long-lived LSP process. The client protocol remains version 1 because
the editor receives standard LSP diagnostics. The unreleased catalog and
analysis formats remain version 1 while their first published shape is still
being completed.

Direct string keys in application or component `template_variables` mappings
carry private authored-source provenance into the LSP worker result. Go to
Definition and Go to Declaration reparse synchronized Python text and link to
the exact mapping key. Application provenance supports a direct selected
`Citry` assignment, with simple earlier aliases for `LintSettings` and its
mapping. Component provenance follows the exact nested `Lint` class that won
C3 composition, including component-library definitions. Factory calls,
computed mappings, duplicate keys, invalid source, and removed or ambiguous
bindings produce no navigation target. They do not fall back to a nearby
setting or stale worker range.

## Checker and editor behavior

The portable rule implementation returns source ranges, rule code, severity,
and message. `citry check --app` and the LSP call that same implementation with
the same joined namespace. `citry check --static` does not guess component
ownership and therefore does not run the rule.

The text and JSON checker outputs include warning/error severity. Warnings are
reported but do not make the command fail. Errors and existing parser or
component-contract findings produce exit status 1. App/discovery degradation
retains exit status 2. A project that wants strict CI selects `error` on its
`Citry` instance instead of configuring an editor-only or command-only rule.

The LSP maps warning and error directly to standard diagnostic severities. It
recomputes findings from synchronized template text while using the same
registry generation and stale-consumer guards as completion and navigation.
No diagnostic is published for syntax-only files, an invalid current parse,
or a template whose ownership cannot be proven.

Citry-owned codes, message templates, default severities, surfaces, and public
documentation links live in
`packages/protocol/diagnostics/v1/catalog.json`. Generated Python, Rust, and
TypeScript bindings keep implementations on that catalog, and repository
validation rejects uncataloged codes or stale generated files. The LSP keeps
`citry` as its diagnostic source and attaches the catalog help URL through the
standard `Diagnostic.codeDescription` field. Analyzer-derived
`citry.python.*` suffixes and messages remain owned by the pinned analyzer.

## Acceptance matrix

- Interpolation, Python-valued attributes, structural expressions, nested
  templates, and loop clauses report exact free-root ranges.
- Lexical bindings, members, Python-local bindings, strings, and comments do
  not produce root findings.
- Runtime globals suppress the finding without a lint declaration.
- Application, component, and extension declarations suppress the finding and
  retain portable type/description metadata.
- Closed, explicit-extra, unknown, absent, Pydantic v1/v2, dataclass,
  NamedTuple, opaque, inferred-closed, and inferred-unknown namespaces follow
  the severity table.
- Shared templates join every consumer without duplicate findings or partial
  namespace claims.
- Unsaved schema, component inheritance, template ownership, and template text
  use current synchronized source or decline conservatively.
- Batch and LSP tests assert identical code, message, severity, and authored
  range for the same registry-backed template.
