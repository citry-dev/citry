# Extensions bundled with Citry. Cache, Dependencies, Events, and i18n are built in
# and always installed; Debug is public but opt-in. Mirrors citry/components/ as
# the package-level grouping surface.
#
# See docs/design/asset_loading.md section 7.2 and docs/design/extensions.md
# section 2.

# Each submodule is its own public surface (the `citry.ext.<name>` entrypoint
# shape); this package only groups them.
__all__ = [
    "cache",
    "debug",
    "dependencies",
    "events",
    "i18n",
]
