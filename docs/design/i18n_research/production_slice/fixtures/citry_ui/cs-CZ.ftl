-shared = LIBRARY-CS

citry-ui-account = { -shared }: { $name } přijímá { $terms_link }.
    .aria-label = Akce účtu pro { $name }

# This candidate is incomplete because citry-ui-ref-target is absent in this
# locale. Resolution must fall back as one graph to the owner's English source.
citry-ui-ref-wrapper = Český obal: { citry-ui-ref-target }

citry-ui-item-count = { $count ->
    [0] Žádné položky
    [one] Jedna položka
    [few] { NUMBER($count, profile: "decimal") } položky
    [many] { NUMBER($count, profile: "decimal") } položky
   *[other] { NUMBER($count, profile: "decimal") } položek
}

citry-ui-rank = Pořadí: { NUMBER($position, profile: "integer") }
citry-ui-balance = Zůstatek: { NUMBER($amount, profile: "decimal") }
citry-ui-due = Termín: { DATETIME($when, profile: "medium") }
