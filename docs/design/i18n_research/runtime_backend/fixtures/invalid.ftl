unknown-variable = Broken { $missing }
unknown-function = Broken { NOT_REGISTERED($value) }
slot-function-scalar = { SLOT($value) }
invalid-plural-input = { CITRY_PLURAL($value) ->
    [one] This branch must not be reached
   *[other] This default must not hide an invalid input
}
slot-as-selector = { $terms_link ->
    [known] Invalid
   *[other] Also invalid
}
