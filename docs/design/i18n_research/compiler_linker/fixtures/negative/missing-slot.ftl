# @param {int} $count
# @param {Slot} $terms_link
missing-slot = { $count ->
    [one] { $terms_link }
   *[other] No link here
}
