# Handler signature binding models: a comparative study for citry Events

Prepared July 2026 for the citry Events extension redesign. All framework
claims were verified against current official documentation or source code
in July 2026; every load-bearing claim carries its source URL.

## 1. The citry context this report answers to

From `/Users/mac/repos/citry/docs/design/events.md` (sections 3.3, 3.4,
4.2, 6.2, 9):

- The wire protocol is fixed: one JSON call envelope with a named `args`
  object ("a JSON object, named keys only. Validated server-side.",
  section 4.2), plus `updates`, an opaque `state` token, `instance`,
  `epoch`. Payload codecs normalize urlencoded, multipart, and GET-query
  transports into that same envelope before dispatch (section 6.2).
- The current handler design: `def rate(self, stars: int, comment: str =
  "")`, bound arg-by-arg from the wire `args` object with JSON-to-annotation
  coercion and structured 422s (section 3.3). `self.state`, `self.context`,
  `self.request`, `self.event`, `self.actions`, `self.component_class` are
  instance attributes on the per-call Events config instance.
- `*args` / `**kwargs` are rejected at class definition; "the signature is
  the schema" (section 3.1), and each handler compiles at class creation to
  an argument model that powers both runtime validation and OpenAPI 3.1
  emission (section 9).
- Multipart is planned for v1.x: "files bind to parameters annotated
  `UploadedFile`" (section 6.2).

Under consideration: passing state/context (and possibly event/request) as
annotatable parameters; wrapping user data into a single input schema
object (Django Ninja style) instead of arg-by-arg; injection-on-request
(only pass what the handler declares).

The report surveys how the field solves each of these, then recommends.

## 2. FastAPI: type-driven implicit binding

### 2.1 How parameters are classified

FastAPI classifies each function parameter from the path template, the
annotation type, and any explicit marker. The defaulting rules, verbatim
from https://fastapi.tiangolo.com/tutorial/body/:

- "If the parameter is also declared in the path, it will be used as a
  path parameter."
- "If the parameter is of a singular type (like `int`, `float`, `str`,
  `bool`, etc) it will be interpreted as a query parameter."
- "If the parameter is declared to be of the type of a Pydantic model,
  it will be interpreted as a request body."

Path parameters are the one name-matched case ("they will be detected by
name" against `{item_id}` segments); everything else is type-and-marker
driven (https://fastapi.tiangolo.com/tutorial/query-params/).
Requiredness comes from defaults: no default means required.

Markers override the defaults, each forcing a source:
`Annotated[X, Query(...)]` (query, plus validation and OpenAPI metadata,
https://fastapi.tiangolo.com/tutorial/query-params-str-validations/),
`Annotated[X, Body()]` (forces a scalar into the JSON body; without it "because
it is a singular value, FastAPI will assume that it is a query parameter",
https://fastapi.tiangolo.com/tutorial/body-multiple-params/),
`Annotated[X, Form()]` ("without it the parameters would be interpreted as
query parameters or body (JSON) parameters",
https://fastapi.tiangolo.com/tutorial/request-forms/; `Form` subclasses
`Body`), `Annotated[bytes, File()]` (multipart,
https://fastapi.tiangolo.com/tutorial/request-files/), and
`Annotated[X, Depends(fn)]` (value comes from calling the dependency,
whose own parameters are analyzed "the same way as the parameters for a
path operation function", https://fastapi.tiangolo.com/tutorial/dependencies/).

The docs now recommend the `Annotated` style over the old
default-value style (`q: str | None = Query(default=None)`): "Prefer to
use the `Annotated` version if possible", because the function default
stays a real Python default, the function stays callable outside FastAPI,
and the metadata composes with other tools
(https://fastapi.tiangolo.com/tutorial/query-params-str-validations/).

### 2.2 What is injected by declaration, and how it is recognized

FastAPI injects framework objects based only on the annotation type,
never the parameter name:

- `Request`: "By declaring a path operation function parameter with the
  type being the `Request` FastAPI will know to pass the `Request` in
  that parameter"
  (https://fastapi.tiangolo.com/advanced/using-request-directly/). Other
  parameters beside it keep their normal extraction and OpenAPI
  documentation.
- `Response`: declare a `Response`-typed parameter to set status code,
  cookies, headers on the outgoing response
  (https://fastapi.tiangolo.com/advanced/response-change-status-code/).
- `BackgroundTasks`: "FastAPI will create the object of type
  `BackgroundTasks` for you and pass it as that parameter"
  (https://fastapi.tiangolo.com/tutorial/background-tasks/).
- `WebSocket` in websocket endpoints
  (https://fastapi.tiangolo.com/advanced/websockets/).
- `SecurityScopes` from `fastapi.security`, which the docs explicitly
  compare to `Request` recognition
  (https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/).

Because recognition is purely type-driven, a parameter named `request`
typed `str` is just a query parameter; the name carries no meaning. And
the injectable types are re-exports of the Starlette classes, so
importing `Request` from `starlette.requests` instead of `fastapi` works
identically ("You could also use `from starlette.requests import
Request`. FastAPI provides it directly just as a convenience",
https://fastapi.tiangolo.com/advanced/using-request-directly/).

### 2.3 Multiple body params and embed

From https://fastapi.tiangolo.com/tutorial/body-multiple-params/:

- Two Pydantic model params (`item: Item, user: User`) make FastAPI "use
  the parameter names as keys" in an outer JSON object:
  `{"item": {...}, "user": {...}}`.
- A single model param is NOT wrapped ("FastAPI will then expect its
  body directly") unless `Body(embed=True)` is given.
- A scalar joins the body object via `importance: Annotated[int, Body()]`.

The important consequence: the wrapping decision is per-operation, not
per-parameter. Adding a second body parameter changes the wire shape of
the first. In citry's terms, FastAPI's body wire format is an output of
the signature; citry's is fixed and the signature must conform to it.

### 2.4 Files

`file: Annotated[bytes, File()]` reads the file into memory;
`file: UploadFile` needs no marker at all, the type alone triggers
multipart extraction, with a spooled temp file and
`filename`/`content_type`/async `read`
(https://fastapi.tiangolo.com/tutorial/request-files/). `File` and `Form`
params mix freely in one operation, but not with JSON `Body` params:
"the request will have the body encoded using `multipart/form-data`
instead of `application/json`. This is not a limitation of FastAPI, it's
part of the HTTP protocol"
(https://fastapi.tiangolo.com/tutorial/request-forms-and-files/).

Since 0.113 to 0.115, whole Pydantic models can be re-routed to non-JSON
sources: `Annotated[FormModel, Form()]`
(https://fastapi.tiangolo.com/tutorial/request-form-models/),
`Annotated[FilterParams, Query()]`
(https://fastapi.tiangolo.com/tutorial/query-param-models/), and header
and cookie models. With `model_config = {"extra": "forbid"}` unknown
fields become 422s (`"type": "extra_forbidden"`). So the "model means
body" rule now has marker-based exceptions, and FastAPI's own evolution
is toward grouped model objects for every source.

### 2.5 OpenAPI derivation and errors

Every declaration simultaneously produces parsing, validation, and
documentation: query/path declarations become the OpenAPI parameters
array, Pydantic body models become JSON Schema in `requestBody`,
File/Form produce multipart or urlencoded request bodies, and
`response_model` (or the return annotation) adds the response schema and
filters output data (https://fastapi.tiangolo.com/tutorial/response-model/).
Validation failures are 422s with a `detail` array of
`{type, loc, msg, input}` entries where `loc[0]` names the source
(`"path"`, `"query"`, `"body"`)
(https://fastapi.tiangolo.com/tutorial/path-params/,
https://fastapi.tiangolo.com/tutorial/handling-errors/). citry's
`invalid_args` 422 with a per-field map is the same idea minus the
source dimension, which citry does not have.

### 2.6 How FastAPI handlers avoid too many parameters

The community-converged patterns, all officially documented:

- Classes as dependencies: the `CommonQueryParams` pattern, with the
  `commons: Annotated[CommonQueryParams, Depends()]` shortcut where the
  annotation type doubles as the callable
  (https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/).
- Shared `Annotated` aliases reused across endpoints
  (`CommonsDep = Annotated[dict, Depends(common_parameters)]`), "the best
  part is that the type information will be preserved"
  (https://fastapi.tiangolo.com/tutorial/dependencies/).
- Pydantic models for query params (0.115.0+),
  https://fastapi.tiangolo.com/tutorial/query-param-models/.
- Community guidance (e.g.
  https://github.com/zhanymkanov/fastapi-best-practices) pushes
  dependencies as the grouping unit and "excessively use Pydantic";
  GitHub discussions on grouping params include
  https://github.com/fastapi/fastapi/discussions/11116 and
  https://github.com/fastapi/fastapi/discussions/13964.

The trend line matters for citry: FastAPI started arg-by-arg and its
ecosystem has been steadily adding ways to group args into model objects
(query models, header models, form models, class dependencies). The
grouping direction won.

### 2.7 Why type-driven, in FastAPI's own words

"It's all based on standard Python type declarations (thanks to
Pydantic). No new syntax to learn. Just standard modern Python", with
editor autocompletion as the explicitly tested design driver
(https://fastapi.tiangolo.com/features/). The lineage page credits Hug
and APIStar for "declaring multiple things (data validation,
serialization and documentation) with the same Python types"
(https://fastapi.tiangolo.com/alternatives/).

Documented failure modes of the implicit model:

- Scalar-intended-as-body silently becomes query; the user POSTing JSON
  gets a 422 about a missing *query* param
  (https://fastapi.tiangolo.com/tutorial/body-multiple-params/).
- A login endpoint written `username: str, password: str` without
  `Form()` reads the query string, not the form body
  (https://fastapi.tiangolo.com/tutorial/request-forms/).
- Adding a second body param changes the wire shape of the first (2.3).

All three failure modes are source-classification mistakes. None of them
can exist in a fixed-envelope design, because there is no classification
to get wrong. That is the single most transferable fact in this section.

## 3. Django Ninja: request-first, schema-object-first

### 3.1 The always-passed request, and why Ninja diverged from FastAPI

Every Ninja operation takes Django's `HttpRequest` as its first argument:
`def add(request, a: int, b: int)` on the landing page
(https://django-ninja.dev/) and in every docs example. The docs never
state the rule explicitly; the source does. The signature parser skips
any parameter named exactly `request` from binding (name check, not type
or position, `ninja/signature/details.py`,
https://github.com/vitalik/django-ninja/blob/master/ninja/signature/details.py),
and the runner always calls `view_func(request, **values)`
(https://github.com/vitalik/django-ninja/blob/master/ninja/operation.py).
So in practice it is mandatory and must be named `request`: name it
anything else and it becomes a bindable query param AND receives the
positional request, collapsing into `TypeError: got multiple values`.
The annotation is ignored for detection. A source TODO ("maybe better
assert that 1st param is request or check by type? ... so that users can
ignore passing request if not needed") shows the author has considered
relaxing it. Even unused, it must be declared, which is enough of a wart
that a ruff `ARG001` false-positive issue was filed
(https://github.com/vitalik/django-ninja/issues/1458).

The stated motivation for diverging from FastAPI
(https://django-ninja.dev/motivation/): Django's ORM fought FastAPI's
async stack; and FastAPI's dependency injection was judged too verbose
for Django use because auth and DB context are needed in "about 99% of
all operations", so Ninja puts them on request attributes Django-style
(`request.auth`) instead of threading DI arguments everywhere. Ninja has
no dependency injection system at all; middleware, authenticators, and
request attributes replace `Depends`. And Pydantic's `BaseModel` is
aliased `Schema` because "model" already means something in Django.

This is the closest prior art to citry's current `self.request` /
`self.context` design: an interactive component framework is even more
"99% of handlers need auth/context" than a Django API is. Ninja's answer
was ambient availability, not per-handler declaration, and it is the one
mainstream Python API framework that explicitly rejected
declaration-based injection on ergonomic grounds. The cost it paid is
the dead `request` token in every signature that does not use it.

### 3.2 Body binding and the single-payload idiom

`data: MySchema` (a `ninja.Schema`) binds the whole JSON body to one
object, no envelope (https://django-ninja.dev/guides/input/body/). The
docs' examples default to this everywhere: `data: HelloSchema`
(https://django-ninja.dev/tutorial/step2/), `payload: EmployeeIn` in the
CRUD tutorial, "This schema will be our input payload"
(https://django-ninja.dev/tutorial/other/crud/). Schema-object-first is
the documented idiom, and the framework nudges toward it structurally: a
bare scalar can never bind to the body without an explicit `Body(...)`
(scalars default to query even on POST, verified in the form guide's
`def update(request, item_id: int, q: str, item: Form[Item])`,
https://django-ninja.dev/guides/input/form-params/).

Multiple body params behave like FastAPI's implicit embed and are
undocumented: verified in source, one body param gets
`__read_from_single_attr__` and consumes the whole body; two or more
switch to keyed-by-parameter-name, changing the wire shape of the first
(`ninja/params/models.py` `BodyModel`,
https://github.com/vitalik/django-ninja/blob/master/ninja/params/models.py,
which carries the comment "::TODO:: this is still sus"). The same cliff
as FastAPI, in lightly maintained form.

### 3.3 Source markers and the default-source rules

The documented default rules match FastAPI's word-for-word in structure:
path if in the path template, query if scalar, body if Schema/BaseModel
(https://django-ninja.dev/guides/input/body/). Source-level priority
(details.py): explicit marker wins, then path-name match, then
collection-or-model means body, else query. Two undocumented details:
bare `List[int]` defaults to body (FastAPI would need `Query()`), and
`UploadedFile` annotations are auto-promoted to `File(...)` with the
source comment "People often forgot to mark UploadedFile as a File, so
we better assign it automatically". That auto-promotion is prior art for
citry's planned type-driven file binding: Ninja found in practice that
making users mark the file source was pure friction, because the type
already says everything.

All seven markers exist (`Path`, `Query`, `Body`, `Form`, `File`,
`Header`, `Cookie`), each in three spellings since v1: `Form[str]`,
`Annotated[str, Form()]`, legacy `= Form(...)`
(https://django-ninja.dev/whatsnew_v1/). Schema against non-body sources
flattens field-by-field (`Query[Filters]` reads each field from its own
query key, https://django-ninja.dev/guides/input/query-params/;
`FilterSchema` builds ORM filters on top,
https://django-ninja.dev/guides/input/filtering/). Colliding flattened
names across two schemas fail at startup with a `ConfigError`, a
detect-at-class-creation discipline citry already practices.

### 3.4 Strictness

Extra body fields are silently ignored by default (plain Pydantic v2
default; `ninja.Schema` only sets `from_attributes=True`,
https://github.com/vitalik/django-ninja/blob/master/ninja/schema.py),
opt-in `extra="forbid"` per schema. Unknown query params never error and
cannot even reach validation (the flatten map copies only declared keys,
params/models.py). Validation failures are 422 `{"detail": [...]}` in
the Pydantic shape (https://django-ninja.dev/guides/errors/). Note the
contrast: citry's design already chose the stricter default (undeclared
`args` keys are a 422, design doc 3.3, motivated by an audit finding of
a client silently sending a dropped field). Ninja's permissive default
is Pydantic inertia, not a considered position.

### 3.5 Files: the documented JSON-part-in-multipart pattern

Base pattern `file: File[UploadedFile]` with Django's file object
(https://django-ninja.dev/guides/input/file-params/). The page documents
BOTH flavors of files-plus-fields, wire-incompatible with each other:

- Flattened form fields: `details: Form[UserDetails], file:
  File[UploadedFile]`, every schema field its own multipart part.
- One JSON part: "You can as well send payload in single field as JSON -
  just remove the Form mark": `details: UserDetails, file:
  File[UploadedFile]` expects "multipart/form-data with 2 fields:
  details: JSON as string, file: file".

The second is exactly citry's envelope-in-a-part shape (and Tetra's,
section 7.1), shipped and documented in a mainstream Django framework.
Mechanism: body params coexisting with File/Form params are rebound to a
`_MultiPartBodyModel` that JSON-parses the named part
(params/models.py).

### 3.6 OpenAPI derivation

Everything flows from the signature: body schemas enter the OpenAPI
schema and docs UIs (https://django-ninja.dev/guides/input/body/),
`operation_id` defaults to module name plus function name, `description`
comes from the docstring ("When you need to provide a long multi line
description, you can use Python docstrings"), `response=` declares
per-status response schemas
(https://django-ninja.dev/reference/operations-parameters/,
https://django-ninja.dev/guides/response/). citry's section 9 plan
(operationId from component and event, docstrings as descriptions) is
this model, and the signatures-are-schema premise is shared.

## 4. Litestar: name-based injection, and its 2026 retreat from it

Version context matters here: the current release is Litestar 2.24.0
(June 2026, https://pypi.org/project/litestar/), and 2.24 deprecated the
implicit name-based recognition mechanisms described below, with removal
scheduled for 3.0
(https://docs.litestar.dev/latest/release-notes/changelog.html,
https://docs.litestar.dev/main/release-notes/whats-new-3.html). So
Litestar is both the field's main name-based example and, as of last
month, the field's main evidence against name-based.

### 4.1 Reserved keyword arguments

Litestar injects by parameter NAME. The reserved list from
https://docs.litestar.dev/latest/usage/routing/handlers.html: `cookies`,
`headers`, `query`, `request`, `scope`, `socket`, `state`, `body`
(each injecting the corresponding framework object, e.g. `state`
"injects a copy of the application State", `body` "the raw request
body"). Plus `data`, documented separately as "the special data
parameter" for the parsed request body
(https://docs.litestar.dev/latest/usage/requests.html). Nine magic names
in practice.

The name triggers the binding; the annotation is only validated
afterward. The proof case is GitHub issue #2765: a user wrote
`async def hello(state: int = 0)` intending a query parameter and got
`ImproperlyConfiguredException: ... The type annotation <class 'int'> is
an invalid type for the 'state' reserved kwarg`
(https://github.com/litestar-org/litestar/issues/2765). A handler
parameter named `state` can never be a query parameter. The docs carry
an explicit collision Tip ("if your parameters collide with any of the
reserved keyword arguments above, you can provide an alternative name")
linking to the aliasing escape hatch:
`my_state: Annotated[str, QueryParameter(name="state")]`
(https://docs.litestar.dev/latest/usage/routing/parameters.html#aliasing).
That Tip exists because a user filed an issue that the workaround was
undiscoverable (https://github.com/litestar-org/litestar/issues/2766).
Another real collision: a user named their form-body parameter `body`
instead of `data` and got a runtime 400 "Expected object, got bytes";
the maintainer confirmed "You must always use the name data"
(https://github.com/litestar-org/litestar/issues/3672). And on why the
error message for the `state` collision cannot be better, maintainer
provinzkraut was candid that the framework "can't know what the intent
was" between a query param named state and a mistyped injection
(https://github.com/litestar-org/litestar/issues/2765). That is the
intrinsic ambiguity cost of name-based recognition, stated by its own
maintainer.

### 4.2 `data`, DTOs, msgspec

The parsed body binds to the parameter literally named `data`, annotated
as a dataclass, TypedDict, msgspec Struct, Pydantic model, or attrs
class (https://docs.litestar.dev/latest/usage/requests.html). Content
type is switched by annotation shorthand: `URLEncodedBody[User]`,
`MultipartBody[User]` (including `UploadFile` fields inside the
dataclass), both sugar over
`Annotated[T, Body(media_type=RequestEncodingType...)]`. DTOs layer on
the same `data` name (`@post(dto=UserDTO)` with `data: User`,
https://docs.litestar.dev/latest/usage/dto/0-basic-use.html). So
Litestar is single-body-object by construction, like Ninja, with the
object's decoding configurable per layer.

msgspec, Litestar's native modeling layer, is fast and type-strict but
permissive on unknown fields by default: "If False (the default), no
error is raised and the unknown field is skipped"
(`forbid_unknown_fields`, https://msgspec.dev/api; flip request tracked
at https://github.com/jcrist/msgspec/issues/545). citry's
extra-keys-are-422 default is stricter than msgspec's, Pydantic's, and
Ninja's; only FastAPI's opt-in `extra="forbid"` models match it.

### 4.3 Dependency injection, and the deprecation

Dependencies are a dict of name to `Provide(fn)` at any layer (app,
router, controller, handler), injected into handlers by matching
parameter name to the dependency key
(https://docs.litestar.dev/latest/usage/dependency-injection.html).
Until 2.24 no marker was required, which produced the classic failure
their own docs now showcase: with `dependencies={"db_session": ...}` on
router A but not router B, the same handler works on `/a` and returns
"400 ... missing required query parameter 'db_session'" on `/b`,
because an unprovided dependency silently degrades into a required
query parameter
(https://docs.litestar.dev/latest/topics/explicit_declarations.html).

As of 2.24 (June 2026): "Relying on this name-based inference now emits
a LitestarDeprecationWarning and will stop working in Litestar 3.0. Mark
the parameter with NamedDependency instead" (DI page). Litestar 3
requires explicit source markers (`FromPath`, `FromQuery`, `FromHeader`,
`FromCookie`, `NamedDependency`), keeping name-keyed wiring but making
the ROLE explicit, which enables boot-time failure instead of
request-time surprises. Their stated principle: "easy to read over easy
to write" (https://docs.litestar.dev/latest/topics/explicit_declarations.html).

### 4.4 What is genuinely instructive beyond FastAPI and Ninja

- The explicit-declarations doc is the field's only first-party essay on
  implicit vs explicit parameter recognition, and it concludes against
  implicitness after years of shipping it
  (https://docs.litestar.dev/latest/topics/explicit_declarations.html).
- Injected values are validated against their annotation by default,
  with `SkipValidation` as the opt-out; unprovided marked dependencies
  fail at boot, not at request time (DI page). Boot-time failure for
  wiring mistakes is a discipline citry already applies at class
  creation and should keep.
- OpenAPI knows to EXCLUDE marked dependencies from the docs ("By
  declaring the parameter to be a dependency, Litestar knows to exclude
  it from the docs", DI page), while typed reserved kwargs like
  `query: SomeModel` still do not appear in OpenAPI at all (open issue
  https://github.com/litestar-org/litestar/issues/2015). Lesson: whatever
  the recognition mechanism, the schema generator must be able to
  classify every parameter as data or infrastructure with certainty.

## 5. How frameworks recognize injectables: type vs name vs marker

Four mechanisms exist in the surveyed field. citry's current design is
the fourth, which the API frameworks do not use but the component
frameworks and Ninja effectively do.

### 5.1 By annotation type (FastAPI)

`request: Request` injects because of the TYPE; the name is meaningless
(https://fastapi.tiangolo.com/advanced/using-request-directly/, section
2.2). Properties:

- **No shadowing of user data.** A data field named `request` or `state`
  binds normally as long as it is not annotated with the magic type. The
  namespaces are separated by the type system, which user JSON can never
  produce.
- **Refactor safety.** Renaming a parameter changes nothing; changing an
  annotation changes behavior, and annotations are the thing code review
  looks at. The failure mode is silent reclassification: annotate
  `request: str` and you have a query parameter, with no error, because
  the framework "can't" know you meant the injectable (the same
  ambiguity Litestar's maintainer named, just landing on the permissive
  side instead of the erroring side).
- **IDE experience.** The annotation IS the type; completion,
  go-to-definition, and mypy all work with zero framework knowledge.
- **Cross-import robustness.** Recognition by class identity means
  re-exports must be the same object (FastAPI/Starlette handle this by
  actual re-export, section 2.2).

### 5.2 By parameter name (Litestar reserved kwargs, pytest, Ninja's request)

Litestar's nine reserved names (section 4.1); pytest, the largest
name-based injector in Python, which "looks at the parameters in that
test function's signature, and then searches for fixtures that have the
same names as those parameters"
(https://docs.pytest.org/en/stable/how-to/fixtures.html); and Ninja's
`request`, skipped from binding by a literal name check in the signature
parser (section 3.1). Properties:

- **Shadowing is structural.** A user data field named `state` or
  `request` is unreachable under the reserved name; the only fix is an
  aliasing escape hatch (`Annotated[str, QueryParameter(name="state")]`)
  that users demonstrably fail to discover
  (https://github.com/litestar-org/litestar/issues/2766). For citry this
  is not hypothetical: wire `args` keys come from templates and form
  field names, and `state` is a common form field (addresses), `query`
  a common search field.
- **Refactor hazard.** Renaming a parameter silently changes its
  meaning: rename `data` to `body` in Litestar and the parsed body
  becomes raw bytes and a runtime 400
  (https://github.com/litestar-org/litestar/issues/3672). An IDE rename
  refactor cannot know the name is load-bearing.
- **Error quality is capped.** When name and annotation disagree, the
  framework cannot tell which one expresses the intent
  (https://github.com/litestar-org/litestar/issues/2765).
- **The upside is real but small:** zero imports, zero ceremony, and in
  pytest's case the name doubles as the lookup key in an open registry,
  which is the actual reason pytest needs names (fixtures are
  user-defined and unbounded; there is no closed set of types to
  recognize). A framework with a CLOSED set of injectables (citry has
  four or five) does not get pytest's justification.
- The field's direction: Litestar deprecated its name-based inference in
  June 2026 and requires markers in 3.0 (section 4.3). Ninja's source
  carries a TODO wishing the request check were "by type" so unused
  requests could be omitted (section 3.1).

### 5.3 By marker (Annotated metadata: FastAPI Query/Body/Depends, Litestar 3 FromQuery/NamedDependency)

The marker names the ROLE explicitly, independent of both the name and
the type. Properties: no reserved names, no type magic, boot-time
verifiability (Litestar 3 fails at startup for an unprovided marked
dependency, section 4.3), OpenAPI always knows the classification, and
markers compose into reusable `Annotated` aliases
(https://fastapi.tiangolo.com/tutorial/dependencies/). Cost: verbosity
and an import, mitigated by aliases (`CurrentUser =
Annotated[User, Depends(get_current_user)]`). Notably both ecosystems
converged here from opposite directions: FastAPI moved from
default-value markers to Annotated markers for editor and reuse
reasons, Litestar moved from bare names to markers for explicitness
reasons.

### 5.4 Ambient attributes (citry today; Ninja's request.auth; Livewire/Tetra $this)

Ninja rejected per-handler declaration of cross-cutting context outright:
auth and DB are needed in "about 99% of all operations", so they ride
`request` attributes (https://django-ninja.dev/motivation/). Livewire
and Tetra handlers likewise reach component state as object state
(`$this->...`), not parameters. citry's `self.state` / `self.context` /
`self.request` / `self.event` is this model with a cleaner carrier (a
per-call config instance instead of a mutated request). Properties: zero
signature noise, zero collision with wire args (the namespaces are
physically separate), but the static type of `self.state` is the weak
point: a generic `Events` base class cannot know the component's
concrete `State` type without help (a class-level annotation or a
generic parameter), and `self.context` is whatever `_context` returned,
which is invisible to the type checker without the same help.

### 5.5 The collision question, answered concretely

What happens when a user data field is named `state` or `request`:

| Mechanism | Outcome |
|---|---|
| By name (Litestar 2.x) | Field is unreachable under that parameter name; boot error if annotated as a scalar; escape hatch is rename-plus-alias, which users fail to find (issues #2765, #2766). |
| By type (FastAPI) | Binds fine as `state: str`. Collision only if the same handler ALSO wants the injectable, and even then only the parameter names must differ, not the wire names. |
| By marker | Binds fine; the marker disambiguates; wire aliasing available. |
| Ambient (`self.*`) | No collision possible; `args` keys and attribute names live in different namespaces. |

For citry the ranking on this axis alone is ambient, then marker, then
type, then name. Name-based recognition of injectables is the one model
the evidence rules out: its original champion is abandoning it, its
justifying use case (open, user-extensible registries like pytest
fixtures) does not apply to a closed set of four injectables, and
citry's `args` names are user-authored template and form vocabulary,
exactly the population most likely to contain `state` and `query`.

## 6. Single input schema vs arg-by-arg for the data parameters

### 6.1 What the frameworks default to

- **FastAPI** is arg-by-arg for query and path, but the JSON body was
  always a single schema object (one Pydantic model param, unwrapped,
  https://fastapi.tiangolo.com/tutorial/body/). Its recent evolution
  (0.113 to 0.115) extended model-grouping to the other sources: form
  models, query models, header models (section 2.4). The grouping
  direction is where FastAPI is moving, not where it started.
- **Django Ninja** is schema-object-first for the body: every docs
  example binds the POST body to one Schema (`data: HelloSchema`,
  `payload: EmployeeIn`, https://django-ninja.dev/tutorial/step2/,
  https://django-ninja.dev/tutorial/other/crud/), and the framework
  nudges that way structurally, since a scalar can never reach the body
  without an explicit `Body(...)` and multi-body params change the wire
  format (section 3.2). Scalars stay arg-by-arg for query and path.
- **tRPC** is single-input by construction: one `.input()` validator per
  procedure, chained inputs merge into one object, handler reads
  `opts.input` (https://trpc.io/docs/server/procedures).
- **GraphQL** is the instructive middle: the schema declares arguments
  individually (named, typed, defaultable, per the spec's
  Language.Arguments section), but the resolver receives them as one
  `args` object (https://www.apollographql.com/docs/apollo-server/data/resolvers).
  Per-argument declaration and single-object delivery are not opposites;
  GraphQL does both at once.
- **Django itself** answered the form question two decades ago with a
  single declarative `Form` class bound to the whole payload at once,
  validated as a unit, errors collected per field on the form object
  (https://docs.djangoproject.com/en/6.0/topics/forms/).
- **The component frameworks** all bind arg-by-arg (Livewire and Tetra
  verified here, and they even use positional args on the wire,
  https://livewire.laravel.com/docs/actions and the Tetra source cited
  in 7.1; django-unicorn likewise per the design doc's own prior-art
  survey, section 1.3). None of them requires a schema class per action. Component events are
  short: `delete(id)`, `rate(stars)`, `add(text)`. Even client-side
  Stimulus delivers its action params as one `event.params` object
  (https://stimulus.hotwired.dev/reference/actions).

### 6.2 What communities converged on for forms specifically

A form is the case where the schema-object pattern wins across every
ecosystem surveyed: Django's `Form` (above), FastAPI's form models with
`extra: forbid` (https://fastapi.tiangolo.com/tutorial/request-form-models/),
Ninja's `Form[UserDetails]` binding a whole Schema from form fields and
its `FilterSchema` doing the same from the query string
(https://django-ninja.dev/guides/input/form-params/,
https://django-ninja.dev/guides/input/filtering/). The reasons are
consistent: a form is validated as a unit,
its errors are per-field and belong to an object that can be re-rendered,
and its field set evolves. citry's current design binds form posts
per-field (`def submit(self, name: str = "", email: str = "")`, design
doc 5.1, with the 422 `fields` map feeding the error display); that is
fine at two or three fields and increasingly awkward past that.

### 6.3 Consequences for OpenAPI and for evolution

- **OpenAPI.** A schema-object param yields a named, reusable component
  schema (`$ref`), a stable identity for client codegen (citry's planned
  TypeScript codegen, design doc section 9, benefits directly). Arg-by-arg
  yields an anonymous inline object schema per operation; citry can still
  emit it (synthesizing a `ComponentName_event_args` name), but the name
  is generated, not authored, and two handlers with the same shape get
  two schemas.
- **Evolution.** In FastAPI, moving from one body param to two changes
  the wire shape (the embed behavior, section 2.3), so arg-by-arg
  evolution is wire-breaking there. citry does not have that failure
  mode: the envelope's `args` object is fixed, so adding
  `def rate(self, stars: int, comment: str = "")` a third defaulted
  parameter is wire-compatible either way. In a fixed-envelope design the
  schema-vs-args choice is a *code-level* question (reuse across handlers,
  passing the bundle to a service whole, per-field error objects), not a
  wire-level one. That is a genuine simplification citry gets for free.
- **The ambiguity hazard.** FastAPI's embed lesson: never let the number
  of parameters silently change what a parameter means. citry's current
  rule is that a dataclass-annotated parameter binds from
  `args[param_name]` (a nested object, design doc 3.3). If a
  whole-args-object mode is ever added, it must be explicit (a marker or
  a deliberate single-rule), never inferred from "the handler happens to
  have exactly one parameter". Otherwise adding a second parameter to a
  one-schema handler would silently re-key the first, which is exactly
  the FastAPI wart.

### 6.4 The honest summary

Arg-by-arg matches what component events are (short, imperative,
template-called); the schema object matches what forms and API-shaped
endpoints are (field sets validated as units, evolving, codegen-relevant).
Every surveyed framework that started on one side grew a bridge to the
other: FastAPI grew model-grouping, GraphQL always delivered per-arg
declarations as one object, Ninja lets scalars ride beside a schema.
The design question for citry is not which one wins but which is the
default and how explicit the bridge is (section 8).

## 7. Files and query in a fixed-envelope world

citry's codecs already normalize urlencoded fields, multipart parts, and
GET query strings into the one named-args object before dispatch. The
question is whether any per-source marker (`Body()`, `Query()`, `Form()`)
still has a job in the handler signature. The prior art of protocol-fixed
RPC-ish frameworks says no.

### 7.1 Frameworks that dropped source markers entirely

**tRPC: one validated input, zero markers.** A procedure declares a single
`.input()` validator (Zod or similar) and the handler reads `opts.input`;
chained `.input()` calls merge into one validated object. Context rides
separately as `opts.ctx`, created per request and enriched by middleware
(https://trpc.io/docs/server/procedures). Nothing in the procedure says
"query" or "body": the transport mapping is fixed by the protocol
(queries serialize input into the URL, mutations into the body) and is
invisible to handler code. When tRPC v11 needed binary payloads it did not
add per-parameter markers either: the *input validator type* declares it
("tRPC can use FormData, File, and other binary types as procedure
inputs", `z.instanceof(FormData)` or the `octetInputParser`), and the
limitation lands in the transport layer, not the handler: batching links
do not support non-JSON types, so clients add a `splitLink`
(https://trpc.io/docs/server/non-json-content-types).

**GraphQL: named args as spec law, transport below the schema.** "Fields
are conceptually functions which return values, and occasionally accept
arguments which alter their behavior", and "Arguments may be provided in
any syntactic order and maintain identical semantic meaning" (GraphQL
spec, Language.Arguments section,
https://spec.graphql.org/October2021/#sec-Language.Arguments, text
verified via
https://raw.githubusercontent.com/graphql/graphql-spec/main/spec/Section%202%20--%20Language.md).
Resolvers receive exactly one args value: Apollo Server's signature is
`(parent, args, contextValue, info)` where `args` is "an object that
contains all GraphQL arguments provided for this field" and
`contextValue` is shared across resolvers per operation for auth and
loaders (https://www.apollographql.com/docs/apollo-server/data/resolvers).
GET vs POST is a transport detail the schema never sees. What GraphQL
gained: introspection and codegen that cannot drift from behavior. What it
lost: files needed a side spec (see 7.2).

**Livewire: everything rides the component-update payload.** Actions are
public PHP methods; template call syntax (`wire:click="delete({{ $post->id
}})"`) evaluates in Blade and passes arguments positionally, with the
explicit doctrine that "Action parameters should be treated just like
HTTP request input, meaning action parameter values should not be
trusted" (https://livewire.laravel.com/docs/actions). No source markers
exist. Files never enter the payload at all: the JS requests a temporary
signed upload URL, uploads the file in a separate multipart request to a
`livewire-tmp/` directory (or straight to S3), then a final request sets
the property to the temp-file handle
(https://livewire.laravel.com/docs/uploads).

**Tetra: the shape citry's design cites, verified in source.** The client
builds one JSON envelope, `{protocol: "tetra-1.0", id, type: "call",
payload: {component_id, method, args, state, ...}}`. With no files it
posts that as `application/json`. When component state holds `File`
instances it switches to `FormData`: the JSON envelope goes in a part
named `tetra_payload` (file values replaced by `{}` placeholders) and
each file is appended as its own part
(https://raw.githubusercontent.com/tetra-framework/tetra/main/src/tetra/js/tetra.core.js).
The server mirrors it: `if request.content_type.startswith("multipart/form-data"):
payload = from_json(request.POST["tetra_payload"])`, then splices
`request.FILES[key]` back into the state
(https://raw.githubusercontent.com/tetra-framework/tetra/main/src/tetra/views.py).
One honest difference: Tetra's `args` is a positional list splatted into
the method (`*component_state["args"]`). citry's named-only `args` object
is the stricter choice and matches GraphQL and tRPC rather than Tetra.

**Hotwire is the control group.** Turbo has no RPC surface at all:
interactions are ordinary links and form submissions returning HTML
(https://turbo.hotwired.dev/handbook/introduction). And even pure
client-side Stimulus converged on a named bag rather than a parameter
list: action params are `data-[identifier]-[name]-param` attributes,
"automatically typecast to either a Number, String, Object, or Boolean",
delivered as one `event.params` object
(https://stimulus.hotwired.dev/reference/actions).

### 7.2 Nobody base64s files into JSON

Confirmed across the field; the converged shapes are multipart-with-JSON-part
or a separate upload channel:

- The GraphQL multipart request spec is multipart/form-data with an
  `operations` part (the JSON operation, `null` where files go), a `map`
  part (part name to variable path), then the file parts. Adopted by
  Apollo Server, graphql-yoga, gqlgen, Lighthouse, Strawberry, Hot
  Chocolate on the server side and apollo-upload-client, urql, Apollo
  iOS/Android on the client side. Its stated motivation is streaming and
  aborting uploads in resolvers, which base64-in-JSON cannot do
  (https://github.com/jaydenseric/graphql-multipart-request-spec).
- Apollo's file upload guidance does not even list base64 as an option;
  the discussed approaches are signed URLs, dedicated image services, and
  multipart via `graphql-upload`
  (https://www.apollographql.com/blog/file-upload-best-practices).
- tRPC v11: FormData and octet-stream inputs, not base64
  (https://trpc.io/docs/server/non-json-content-types).
- Livewire: separate multipart upload to a temp endpoint or S3
  (https://livewire.laravel.com/docs/uploads).
- Tetra: multipart with the `tetra_payload` JSON part (source links
  above).

One caution worth carrying over: Apollo warns that "supporting multipart
requests directly in your GraphQL server introduces major security
issues" unless CSRF prevention is on, because multipart/form-data is a
form-submittable content type that sidesteps the CORS preflight that
protects `application/json` endpoints
(https://www.apollographql.com/blog/file-upload-best-practices). citry's
events routes already require CSRF on state-changing calls (design doc
section 7.4), so the exposure is handled; the multipart codec should get
a conformance fixture proving the CSRF check fires for multipart exactly
as for JSON.

### 7.3 Conclusion: no remaining job for Body/Query/Form markers

What `Query()`/`Body()`/`Form()` buy in FastAPI and Ninja is the ability
for one handler to read *several sources at once* (path + query + body +
header + form) on an open HTTP surface. citry's protocol forbids that by
construction: every transport is normalized into the one `args` object
before binding, so a source marker would have exactly one legal value per
parameter, which is dead weight. The two source-shaped things that remain
are not markers:

- **GET/query** is per-handler transport config
  (`@event(methods=("GET",))`), and the query codec turns the query
  string into `args`. The signature stays source-free.
- **Files** cannot ride JSON, and the field's converged answer is the one
  the design already picked (multipart part + JSON envelope part). The
  binding cue is the parameter's *type* (`UploadedFile`), which says what
  the value is, not where it came from; the codec decides where it came
  from. This is the same move tRPC made (the validator type declares
  FormData) and the opposite of FastAPI's `File()` marker.

What the marker-free frameworks gained: signatures that are pure domain
data, schema/codegen derivable with no HTTP vocabulary in it, and no way
to write a handler that contradicts the protocol. What they lost:
per-request content negotiation, which each had to buy back later (tRPC's
v11 non-JSON feature plus `splitLink`; GraphQL's side spec for
multipart). citry's payload-codec registry is the pre-built answer to
exactly that loss, and it lives at the transport layer where those
frameworks ended up putting it too.

## 8. Recommendations for citry Events

Constraints taken as fixed: the envelope (named `args` object, `updates`,
`state` token; codecs normalize every transport into it), the Python 3.10
floor (`Annotated`, `dataclass(slots=True)`, and class-creation
introspection are all available; PEP 695 generics are not), and the
existing rules that the signature is the schema and `*args`/`**kwargs`
are rejected at class creation.

Findings that constrain the design:

1. Source markers (`Body`/`Query`/`Form`) exist to let one handler read
   several sources on an open HTTP surface. citry's protocol has one
   source. Every marker would have exactly one legal value, so they
   should not exist (section 7.3). Files are the exception, and the cue
   there is the TYPE (`UploadedFile`), which Ninja independently
   validated by auto-promoting the annotation because marking it was
   pure user friction (section 3.3).
2. Name-based recognition of injectables is ruled out by the evidence:
   Litestar deprecated it in June 2026 after documenting its failure
   modes, and citry's `args` keys are user-authored template and form
   vocabulary where `state` and `query` are common (section 5.5).
3. Type-based recognition and marker-based recognition are both healthy;
   the field converged on "explicit role, checked at boot". citry's
   equivalent of boot is component class creation, where it already
   errors on `*args` and builds the argument model.
4. Arg-by-arg fits component events (short, imperative, template-called;
   no surveyed component framework requires a schema class per action),
   while the schema object wins for forms and codegen-relevant payloads.
   In a fixed envelope the two differ only at the code level, so
   supporting both is cheap, PROVIDED the bridge is explicit and arity
   never changes wire meaning (FastAPI's embed lesson, section 6.3).
5. Ambient context has a strong precedent exactly for citry's situation:
   Ninja rejected per-handler DI because auth/context are needed in
   "about 99% of all operations" (section 3.1).

### Design A: refined status quo (arg-by-arg data, everything else ambient)

```python
class Events:
    def rate(self, stars: int, comment: str = ""):
        self.state.avg = recompute(self.state.doc_id, stars)
        return self.state.render()
```

Data params bind from `args` arg-by-arg; `self.state`, `self.context`,
`self.request`, `self.event`, `self.actions` stay instance attributes.
The one real weakness is static typing of `self.state` and
`self.context`: a shared `Events` base cannot know the component's
concrete `State` or context type. On Python 3.10 the available fixes are
a generic base (`class Events(citry.Events[State, AppCtx])`, workable
but noisy) or accepting `Any` (what Livewire/Tetra users effectively
live with, but beneath citry's typing standards elsewhere).

OpenAPI story: unchanged from design doc section 9. Every parameter is a
data parameter, so the generator is trivially total; the request `args`
schema is synthesized per operation with a generated name
(`Document_rate_args`).

### Design B (recommended): arg-by-arg data + opt-in keyword-only injection, recognized by type, ambient kept

Data parameters stay exactly as designed. Additionally, a handler may
declare keyword-only parameters after `*`, and those are injected, never
bound from `args`:

```python
class Events:
    # simple handlers stay exactly as short as today
    def delete(self, item_id: int):
        remove(item_id)

    # handlers that want typing declare what they use
    def rate(self, stars: int, comment: str = "",
             *, state: State, ctx: Annotated[AppCtx, FromContext()]):
        state.avg = recompute(state.doc_id, stars)
        return state.render()
```

Recognition and rules, all checkable at class creation:

- Positional-or-keyword params (before `*`) are the wire schema, nothing
  else. Keyword-only params (after `*`) are injectables, nothing else.
  The `*` is the visible boundary between "what the client sends" and
  "what the server provides"; no reader ever has to apply a recognition
  rule to know which side a parameter is on.
- Injectables are recognized by citry-owned annotation types: the
  component's own `State` class (an `issubclass` check; wire JSON can
  never produce it, so there is no ambiguity), `Event`, and
  `EventRequest`. The context is user-typed, so type recognition cannot
  work for it; it gets the one marker, `Annotated[T, FromContext()]`
  (or a `FromContext[T]` alias), which also gives the checker the type.
- A pre-`*` param annotated with an injectable type, or a post-`*` param
  that is not recognizable, is a class-creation error naming the fix.
  This is Litestar-3-style boot-time failure with FastAPI-style
  recognition and zero reserved names: a wire arg named `state` binds
  fine, because recognition never looks at names.
- One implementation caveat to plan for: inside a nested `Events` class
  body, the sibling nested class `State` is not lexically visible, so
  the annotation `state: State` only works under
  `from __future__ import annotations` (or as the string `"State"`),
  with citry resolving the deferred annotation against the component
  namespace at class creation, where `State` is known. The binder should
  resolve hints itself with the component class in scope and document
  the future-import expectation; this is solvable but it is real work,
  and Design A avoids it entirely.
- Injected `state` is the SAME object as `self.state` (a typed alias,
  not a second channel), so mutation semantics and the refreshed-token
  flow are unchanged, and `self.*` remains for handlers that skip the
  declarations. Docs teach one style: declare `state` when you touch it;
  the rest stays on `self`. The Ninja evidence says ambient must remain
  available (context is near-universal); the typing evidence says
  declaration must be possible. This design prices both honestly:
  declaration costs one keyword-only param, ambience costs nothing.

OpenAPI story: identical to A, and provably total: the generator emits
pre-`*` params as the `args` schema and skips post-`*` params by
position, not by heuristic. The Litestar failure where the schema
generator cannot classify a parameter (section 4.4) is structurally
impossible.

Testing story (a real gain): a handler can be called directly in tests
with fakes for exactly the injectables it declares, without constructing
the per-call config instance.

### Design C: single input object (tRPC/Ninja style), as the explicit bridge, not the default

```python
@dataclass
class Signup:
    name: str
    email: str
    plan: str = "free"

class Events:
    def submit(self, form: Payload[Signup], *, state: State):
        create_account(form)
        return self.actions.Redirect("/welcome")
```

`Payload[Signup]` (an `Annotated` alias over a marker) binds the WHOLE
`args` object to one dataclass and is the only way to get whole-args
binding. As the universal default (every handler takes one schema
object) it would be the wrong trade: `delete(id)` becoming a class per
event is ceremony no component framework imposes, and citry's template
call sites (`rate(stars=5)`) and form-field binding (design doc 5.1)
map one-to-one onto named args. But as an opt-in it is the right home
for form-shaped handlers, mirrors where FastAPI's own evolution went
(query/form/header models), and it must be marker-explicit so that the
existing rule "a dataclass param binds from `args[param_name]`" keeps
its meaning and parameter count never re-keys the wire format (the
FastAPI embed cliff). When the roadmapped Pydantic integration lands,
`Payload[PydanticModel]` gives Ninja-grade form validation with
per-field errors feeding the existing 422 `fields` map.

OpenAPI story: the best of the three where used: the request schema is
a NAMED, authored component (`#/components/schemas/Signup`), reusable
across handlers and stable for the planned TypeScript codegen.

### Bottom line

Adopt B as the signature model, with C's `Payload[...]` marker as the
explicit whole-args bridge for form-shaped handlers, and keep A's
ambient attributes as the zero-ceremony floor. Do not add source
markers; bind files by the `UploadedFile` type as already designed
(the field's evidence, sections 3.3 and 7, is unanimous that in a fixed
envelope the type is the only cue needed). What would falsify B: if in
real use nearly every handler declares the same `*, state, ctx` tail,
the declarations have become ritual and the generic-base version of A
(typing via `citry.Events[State, Ctx]`) would serve better; watch for
that in the first dogfooding round. What would falsify keeping ambient
`self.*`: if handlers that mix `self.state` and injected `state` in one
body confuse readers in review, drop the ambient form for state
specifically and keep it for `actions`/`event`/`request`.

## Sources

Framework documentation and source verified July 2026. Primary URLs:
FastAPI (fastapi.tiangolo.com: tutorial/body, tutorial/query-params,
tutorial/body-multiple-params, tutorial/request-files,
tutorial/request-forms-and-files, tutorial/request-form-models,
tutorial/query-param-models, tutorial/dependencies,
advanced/using-request-directly, features, alternatives), Django Ninja
(django-ninja.dev: motivation, guides/input/body, guides/input/query-params,
guides/input/form-params, guides/input/file-params, guides/input/filtering,
guides/errors, whatsnew_v1, tutorial/step2, tutorial/other/crud;
github.com/vitalik/django-ninja: ninja/signature/details.py,
ninja/params/models.py, ninja/operation.py, ninja/schema.py), Litestar
(docs.litestar.dev: usage/routing/handlers, usage/routing/parameters,
usage/requests, usage/dependency-injection, usage/dto,
topics/explicit_declarations, onboarding/fastapi, release notes;
github.com/litestar-org/litestar issues 2765, 2766, 3672, 2015; msgspec.dev),
tRPC (trpc.io/docs/server/procedures, trpc.io/docs/server/non-json-content-types),
GraphQL (spec.graphql.org October2021 Language.Arguments via the
graphql-spec GitHub source; apollographql.com/docs/apollo-server/data/resolvers;
github.com/jaydenseric/graphql-multipart-request-spec;
apollographql.com/blog/file-upload-best-practices), Livewire
(livewire.laravel.com/docs/actions, livewire.laravel.com/docs/uploads),
Tetra (github.com/tetra-framework/tetra: src/tetra/js/tetra.core.js,
src/tetra/views.py), Hotwire (turbo.hotwired.dev/handbook/introduction,
stimulus.hotwired.dev/reference/actions), Django
(docs.djangoproject.com/en/6.0/topics/forms/), pytest
(docs.pytest.org/en/stable/how-to/fixtures.html).
