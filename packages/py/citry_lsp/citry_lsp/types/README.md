# Vue type declarations shipped with citry-lsp

This folder holds Vue's TypeScript declaration files (`.d.ts` and
`.d.mts`), plus the packages those declarations import: the `@vue/*`
packages, `@babel/types`, `@babel/parser`, and `csstype`. Each package keeps its `package.json` and
license file. citry-lsp ships them inside its wheel, so the editor and
`citry check --types` can type-check component code against Vue's own types
without downloading anything or needing a project `node_modules`.

## Why the folder is called `node_modules`

The TypeScript files that citry-lsp writes for each component import
`types/node_modules/vue` by its absolute path. Vue's declarations then import `@vue/runtime-dom`, `@vue/shared`, and
the other packages by name, and TypeScript finds a package by name only by
looking in a folder called `node_modules`. Any other folder name breaks those
imports.

The repository's `.gitignore` ignores every `node_modules` folder, then
re-includes this one on purpose, so these files are committed.

## Regenerate the files

Do not edit the files under `node_modules/` or `inventory.json` by hand.
`packages/js/citry-client/build-vue-types.mjs` copies them from the Vue
version that `packages/js/citry-client/package.json` installs. To change
the Vue version, edit `vue` in that `package.json` and `VUE_VERSION` in
`packages/js/citry-client/build-support.mjs`, then run from the repository
root:

```console
pnpm install
pnpm --dir packages/js/citry-client run build:vue-types
```

The distribution test in
`packages/py/citry_lsp/tests/test_lsp_distribution_artifacts.py` reads the
Vue version from `package.json`. If the `@babel/*` or `csstype` versions in
`inventory.json` change, update them in that test's `VUE_TYPE_PACKAGES`.

`pnpm --dir packages/js/citry-client run check:vue-types` checks that the
committed files match the installed packages. It runs as part of that
package's `check` script, so the repository gate fails on a stale or
extra file.

`inventory.json` records the Vue version and, for each package, its name,
version, the files copied, and a SHA-256 hash of those files' contents
joined in order. The citry-lsp tests read it to confirm that the files on
disk are exactly the ones listed, each with a license.

This README is written by hand. The script leaves it in place, and the
wheel includes it next to the files it describes.
