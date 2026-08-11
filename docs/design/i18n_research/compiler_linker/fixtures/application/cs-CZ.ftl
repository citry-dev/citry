-shared = APPLICATION-CS

# @param {str} $name - Account holder name.
# @param {Slot} $terms_link - Link to the terms page.
my-app-target = { $name } přijal(a) { $terms_link }; podrobnosti: { $terms_link }.

my-app-wrapper = Aplikace: { my-app-target }

# @param {int} $position - One-based position.
my-app-ordinal = { NUMBER($position, type: "ordinal") ->
   *[other] Pozice { NUMBER($position, profile: "integer") }
}

my-app-fallback-only = APP CS SOURCE FALLBACK

# This overrides a citry_ui-owned ID without changing its defining owner. Its
# private term and public reference must resolve in this application layer.
citry-ui-account = { -shared }: { my-app-target }
