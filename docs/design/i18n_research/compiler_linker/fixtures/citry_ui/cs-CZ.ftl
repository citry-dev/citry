-shared = LIBRARY-CS

citry-ui-account = { -shared }: { $name } přijímá { $terms_link }.
    .aria-label = Akce účtu pro { $name }

citry-ui-count = { $count ->
    [0] Žádné položky
    [one] Jedna položka
    [few] { NUMBER($count, profile: "integer") } položky
    [many] { NUMBER($count, profile: "decimal") } položky
   *[other] { NUMBER($count, profile: "integer") } položek
}

# The target is intentionally absent at cs-CZ. The whole candidate must fall
# back to the owner's en-US source rather than mixing locales inside one output.
citry-ui-ref-wrapper = Český obal: { citry-ui-ref-target }
