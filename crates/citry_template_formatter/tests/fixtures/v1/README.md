# Formatter corpus v1

This directory is the formatter contract. The versioned `index.json` names every case. 

Most source and expected output lives in separate files. Byte-edge cases use JSON-escaped inline text so CRLF and a
missing final newline survive exactly in a text-only repository checkout. Rust
owns the corpus, and Python, CLI, LSP, and editor tests will consume the same
index as those surfaces are implemented.

Opening-tag outputs lock the internal vertical slice. Structural-layout outputs
lock the first releasable Citry/HTML formatter, and provider-target outputs lock
later embedded-language expectations without claiming those providers already
exist. The test suite verifies that each positive pair parses and satisfies its
available structural and whitespace-preservation projection. The opening-tag
printer executes every opening-tag golden; structural-layout and provider pairs
remain contract fixtures until their owning capabilities land.

Error cases name their owning phase and stable Citry error code. Parse errors
must fail the current parser. Format errors must parse successfully.
Opening-tag format errors execute against the Rust formatter now; later cases
become executable when their owning capability lands. Required feature labels
are asserted in the Rust test so the core matrix cannot silently shrink.

This corpus covers parser-level Citry templates, including CRLF and
missing-final-newline byte contracts, plus the Python host framing and rewrite
eligibility cases implemented in implementation-order step 3. Each later
provider adds its cases before its implementation, not afterward.
