-shared = LIBRARY-EN

# @param {str} $name - Account holder name.
# @param {Slot} $terms_link - Link to the terms page.
citry-ui-account = { -shared }: { $name } accepts { $terms_link }; details: { $terms_link }.
    .aria-label = Account actions for { $name }

citry-ui-fallback-only = LIBRARY SOURCE FALLBACK
citry-ui-ref-target = library target
citry-ui-ref-wrapper = English wrapper: { citry-ui-ref-target }

# @param {Decimal} $count - Exact item count.
citry-ui-item-count = { $count ->
    [0] No items
    [one] One item
   *[other] { NUMBER($count, profile: "decimal") } items
}

# @param {int} $position - One-based rank.
citry-ui-rank = { NUMBER($position, type: "ordinal") ->
    [one] { NUMBER($position, profile: "integer") }st
    [two] { NUMBER($position, profile: "integer") }nd
    [few] { NUMBER($position, profile: "integer") }rd
   *[other] { NUMBER($position, profile: "integer") }th
}

# @param {Decimal} $amount - Exact account balance.
citry-ui-balance = Balance: { NUMBER($amount, profile: "decimal") }

# @param {datetime} $when - Exact instant with offset.
citry-ui-due = Due: { DATETIME($when, profile: "medium") }
