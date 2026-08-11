-brand = Citry

-account-kind = { $style ->
    [formal] účet
   *[plain] profil
}

account-summary = { -brand } { -account-kind(style: "formal") }: { CITRY_TEXT($account_name) }

account-actions = Akce
    .aria-label = Akce pro { CITRY_TEXT($account_name) }

inbox-count = { CITRY_PLURAL($count, exact: "0") ->
    [exact-0] Žádné položky
    [one] { NUMBER($count, profile: "integer") } položka
    [few] { NUMBER($count, profile: "integer") } položky
    [many] { NUMBER($count, profile: "decimal") } desetinné položky
   *[other] { NUMBER($count, profile: "integer") } položek
}

balance = Zůstatek: { NUMBER($amount, profile: "currency", currency: "USD") }

due-date = Termín: { DATETIME($due_ms, profile: "short-date") }

multiline-fallback = První odstavec náhradního textu
    Druhý odstavec náhradního textu

ordinal-position = { CITRY_PLURAL($position, mode: "ordinal") ->
   *[other] { NUMBER($position, profile: "integer") }. pořadí
}

acceptance = { CITRY_PLURAL($count) ->
    [one] { CITRY_TEXT($account_name) } přijal(a) { SLOT($terms_link) }.
    [few] { CITRY_TEXT($account_name) } přijal(a) { SLOT($terms_link) } { NUMBER($count, profile: "integer") }krát; podrobnosti: { SLOT($terms_link) }.
    [many] { CITRY_TEXT($account_name) } přijal(a) { SLOT($terms_link) } { NUMBER($count, profile: "decimal") }krát.
   *[other] { CITRY_TEXT($account_name) } přijal(a) { SLOT($terms_link) } { NUMBER($count, profile: "integer") }krát.
}
