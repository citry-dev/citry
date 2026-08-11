-shared = APPLICATION-CS

# @param {str} $name - Account holder name.
# @param {Slot} $terms_link - Link to the terms page.
my-app-target = { $name } přijal(a) { $terms_link }; podrobnosti: { $terms_link }.

my-app-wrapper = Aplikace: { my-app-target }
my-app-source-only = APP CS SOURCE FALLBACK

# This higher-precedence definition overrides a citry_ui-owned ID without
# changing its owner. Its term stays private to this layer.
citry-ui-account = { -shared }: { my-app-target }

# @param {int} $count - Number of notices.
# @param {str} $name - Account holder name.
# @param {Slot} $terms_link - Link to the terms page.
my-app-rich-choice = { $count ->
    [one] { $name }: { $terms_link } a znovu { $terms_link }
   *[other] { $name }: { $terms_link }, poté { $terms_link }
}
