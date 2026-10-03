import assert from "node:assert/strict";
import test from "node:test";

import { compile } from "vue";

test("the pinned Vue compiler accepts its full classic slot parameter grammar", () => {
  for (const pattern of ["x, y", "...args", "await", "yield", "eval", "arguments"]) {
    const errors = [];
    assert.equal(
      typeof compile(`<Child #default="${pattern}"><span /></Child>`, {
        onError: (error) => errors.push(error),
      }),
      "function",
    );
    assert.deepEqual(errors, []);
  }
});

test("the pinned Vue compiler owns dynamic slot delimiters and suffixes", () => {
  for (const directive of [
    "#[slots['[']].tail",
    "#[`$" + "{`[`}`].tail",
    "#[slots[名]].tail",
    "#[slots[a][foo.bar]].tail",
  ]) {
    const errors = [];
    const render = compile(`<Child><template ${directive}="{ item }" /></Child>`, {
      onError: (error) => errors.push(error),
    });
    assert.deepEqual(errors, []);
    assert.match(render.toString(), /\.tail\]: _withCtx/);
  }

  assert.throws(() => compile('<Child><template #[foo][bar]="{ item }" /></Child>'));
});
