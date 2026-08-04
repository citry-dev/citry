# Formatter corpus v1

This directory is the formatter contract. The versioned `index.json` names every case
and pins the built-in Python expression provider identity.

Most source and expected output lives in separate files. Byte-edge cases use JSON-escaped inline text so CRLF and a
missing final newline survive exactly in a text-only repository checkout. Rust
owns the corpus, and Python, CLI, LSP, and editor tests consume the same index.

Opening-tag outputs lock the internal vertical slice. Structural-layout outputs
lock the first releasable Citry/HTML formatter. Python-expression outputs lock
the built-in provider, while later provider targets may still describe
unimplemented capabilities. The test suite verifies that each positive pair
parses and satisfies its capability-aware semantic and whitespace projection.
The formatter executes every opening-tag, structural-layout, and
Python-expression golden.

Error cases name their owning phase and stable Citry error code. Parse errors
must fail the current parser. Format errors must parse successfully.
Opening-tag, structural-layout, and Python-expression errors execute against
the Rust formatter now. Required feature labels are asserted in the Rust test
so the core matrix cannot silently shrink.

This corpus covers parser-level Citry templates, including CRLF and
missing-final-newline byte contracts, plus the Python host framing and rewrite
eligibility cases implemented through implementation-order step 7. Each later
provider adds its cases before its implementation, not afterward.
