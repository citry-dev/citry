"""Python's ``symtable`` module, where the interpreter has it, and the notices shown where it does not."""

from __future__ import annotations

try:
    import symtable
except ImportError:  # PyPy ships symtable.py but not the _symtable C module it imports.
    symtable = None  # type: ignore[assignment]

# Two analyses read the symbol table: `_function_local_names` in `_checker` (the
# js_data() value checks) and `_renamable_method_locals` in `_template_python`
# (template name types). Without it they give no answer, so `citry check` and the
# editor say once that they do less, rather than doing less silently.
CHECK_NOTE = (
    "this Python has no _symtable module, so citry check reads no module values sent by "
    "js_data(), and --types skips a template that uses a name its template_data() method "
    "assigns; run citry check on CPython for full results"
)
EDITOR_NOTE = (
    "This Python has no _symtable module, so a template that uses a name its "
    "template_data() method assigns gets no types. Run citry check --types on CPython "
    "for full results."
)


def symtable_missing() -> bool:
    """Whether this interpreter lacks the symbol table module that two check analyses read."""
    return symtable is None
