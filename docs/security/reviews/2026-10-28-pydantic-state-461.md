# Pydantic State (#461)

- **Pull request:** [#461](https://github.com/citry-dev/citry/pull/461),
  merged 2026-10-28 (ccf55afdb)
- **Reviewer:** a separate reviewing agent
- **Code:** the code that reads a State's fields for every caller
  (`citry/ext/events/state.py`) and the State token (`tokens.py`), both in
  `packages/py/citry/citry/ext/events/`; tests in
  `packages/py/citry/tests/test_pydantic_state.py`

## Who controls the input

State is the data Citry keeps for a component between Events calls. It can
now be a Pydantic v2 or v1 model. State travels to the browser and back:

- a signed token holds it between calls;
- the fields listed in `_public` appear in the page;
- the browser can write the fields listed in `_model`, a subset of the
  public fields.

Anyone using the page controls what the browser writes. So Pydantic options
such as aliases, serializers and excluded fields must not change what Citry
signs, what the page shows, or which field a browser write fills.

## How it was checked

The reviewer read how Citry signs State into a token and reads it back, and
how it applies a field the browser writes. The new suite
`test_pydantic_state.py` (65 tests) runs the shared State behaviors against
four kinds of State:

- a generated dataclass;
- a hand-written Pydantic v2 model;
- a hand-written Pydantic v1 model;
- a v2 model that Citry generated from a plain `class State:` because the
  app set `model_base`.

## Ruled out

- **A value that changes when it is read back:** Pydantic validators can
  change values when a model is restored. Before signing, Citry restores
  exactly what it will sign, keeps the values Pydantic converted (so `"2"`
  assigned to an int field is signed as `2`), and checks that a second store
  and restore gives the same values.
- **A browser write skipping validation:** writes are merged into the
  model's JSON form and validated, and the whole validated model is kept.
- **Options that change what is stored or shown** are refused when the
  component class is defined, at any depth of nested models:
  - a frozen model or field;
  - `exclude` or `exclude_if`;
  - serializers (`model_serializer`, `field_serializer`, `PlainSerializer`,
    `WrapSerializer`);
  - secret types such as `SecretStr`, which Pydantic writes masked;
  - an alias, unless the model also accepts the field's own name: on
    Pydantic v1 through `allow_population_by_field_name`, and on v2 before
    2.11 through `populate_by_name` or `validate_by_name`;
  - a State setting such as `_public` written as a type hint with no value
    (`_public: tuple`), which Pydantic v1 drops, so the setting would quietly
    not apply.

## Fixed during the review

- **Alias collision:** a browser write could use an alias that matched
  another field's name to fill a field the browser may not write (one not
  listed in `_model`). Citry now reads State by field name only, both when
  it restores the token and when it checks a browser write, so an alias
  never fills another field. `test_an_alias_never_fills_another_field`
  covers this.
- **Pydantic v1 nested subclass:** a subclass instance in a v1 nested field
  could put fields the State class does not declare into the page. Citry
  now dumps v1 values through the declared class.
  `test_a_v1_nested_subclass_does_not_leak_its_extra_fields` covers this.

## Not tested

- No browser pass by the reviewer is recorded. One existing browser test,
  `test_vue_state_refresh_e2e.py`, also runs with a Pydantic `model_base`.

## Follow-ups

- A field the browser may write (`_model`) with a type such as
  `ImportString` would import whatever module the browser names. The State
  docs (`docs_site/content/events/state.md`) say to keep such types out of
  writable fields.
