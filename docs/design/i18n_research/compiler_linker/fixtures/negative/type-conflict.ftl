# @param {str} $value
conflict-left = { $value }

# @param {int} $value
conflict-right = { NUMBER($value, profile: "integer") }

conflict-wrapper = { conflict-left } / { conflict-right }
