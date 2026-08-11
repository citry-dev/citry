### Semantic span probe

-brand = Citry
    .short = C

shared = Shared { $name }
wrapper = { shared } / { complex.aria-label }

# Greeting with repeated inputs, Unicode text, and a formatter.
# @param {str} $name - Account holder.
# @param {int} $count - Number of items.
# @param {Slot} $terms_link - Application-owned link.
complex = Přivítej { $name } and again { $name }.
    .aria-label = { NUMBER($count, minimumFractionDigits: 2) }

selector = { $count ->
    [0] Nothing
   *[other] { -brand(case: "short") } / { { "nested\u2069" } }
}

rich = Before { $terms_link }, between { $terms_link }, after.

trimmed = trailing spaces   
