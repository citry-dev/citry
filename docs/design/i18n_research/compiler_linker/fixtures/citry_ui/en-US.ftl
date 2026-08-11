-shared = LIBRARY-EN

# @param {str} $name - Account holder name.
# @param {Slot} $terms_link - Link to the terms page.
citry-ui-account = { -shared }: { $name } accepts { $terms_link }.
    .aria-label = Account actions for { $name }

# @param {int} $count - Number of inbox items.
citry-ui-count = { $count ->
    [0] No items
    [one] One item
   *[other] { NUMBER($count, profile: "integer") } items
}

citry-ui-fallback-only = LIBRARY SOURCE FALLBACK
citry-ui-ref-target = library target
citry-ui-ref-wrapper = English wrapper: { citry-ui-ref-target }
