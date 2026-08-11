-brand = Citry

-account-kind = { $style ->
    [formal] account
   *[plain] profile
}

account-summary = { -brand } { -account-kind(style: "formal") }: { CITRY_TEXT($account_name) }

account-actions = Actions
    .aria-label = Actions for { CITRY_TEXT($account_name) }

inbox-count = { CITRY_PLURAL($count, exact: "0") ->
    [exact-0] No items
    [one] { NUMBER($count, profile: "integer") } item
   *[other] { NUMBER($count, profile: "integer") } items
}

balance = Balance: { NUMBER($amount, profile: "currency", currency: "USD") }

due-date = Due: { DATETIME($due_ms, profile: "short-date") }

multiline-fallback = First fallback paragraph
    Second fallback paragraph

ordinal-position = { CITRY_PLURAL($position, mode: "ordinal") ->
    [one] { NUMBER($position, profile: "integer") }st
    [two] { NUMBER($position, profile: "integer") }nd
    [few] { NUMBER($position, profile: "integer") }rd
   *[other] { NUMBER($position, profile: "integer") }th
}

acceptance = { CITRY_PLURAL($count) ->
    [one] { SLOT($terms_link) } accepted by { CITRY_TEXT($account_name) }.
   *[other] { SLOT($terms_link) } accepted { NUMBER($count, profile: "integer") } times; details: { SLOT($terms_link) }. Accepted by { CITRY_TEXT($account_name) }.
}
