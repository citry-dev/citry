---
title: v0.2.0
url: https://citry.dev/v/0.4.4/releases/v0.2.0/
description: "What changed in citry v0.2.0."
---
# v0.2.0

## Feat

- Citry now logs through the standard `logging` module, under the `"citry"`
  logger, with a `TRACE` level (5, below `DEBUG`). The logger traces each component,
  slot, and node as it renders. Turn it on to debug a render:

  ```python
  import logging
  logging.getLogger("citry").setLevel(5)
  ```

## Fix

- A default value for a slot set at `Component.Slot.<attr>` is now correctly used.

- Include JS runtime script when a Component has any JS/CSS scripts

## Refactor

- Citry now raises error when template contains `<c-slot name="X">`, but `Component.Slots` omits `X`.

  A component without a `Slots` class accepts any fills
  and is unaffected.