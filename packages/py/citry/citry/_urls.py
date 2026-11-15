"""
Read the scheme of a URL the way browsers do.

The Python checks that decide where a URL may lead read its scheme here:
``Redirect``, the Events redirect resolver for the no-JavaScript form path,
and Citry UI's link and image checks. This module calls the same Rust reader
the output checks use, so these checks cannot read one URL differently.

Citry UI imports this module, so its names and signatures stay the same
for all of citry 1.x; ``tests/test_urls_module.py`` checks them. The reader
decodes no character references. A caller holding HTML (a ``Markup`` value
or attribute text) decodes it first, the way Citry decodes it when it
writes the page.
"""

from __future__ import annotations

from citry_core.html_transform import _read_url_scheme


def url_scheme(url: str) -> str | None:
    """
    Return the lowercase scheme a browser reads from ``url``, or ``None`` for a relative URL.

    This follows the first steps of the WHATWG URL parser: leading and
    trailing C0 controls and spaces (U+0000 to U+0020) are ignored, tab, LF
    and CR are removed anywhere, and a scheme is an ASCII letter followed by
    ASCII letters, digits, ``+``, ``-`` or ``.`` up to the first ``:``.
    """
    read = _read_url_scheme(url)
    return None if read is None else read[0]


def url_scheme_and_rest(url: str) -> tuple[str, str] | None:
    """
    Return the lowercase scheme and the text after its colon, or ``None`` for a relative URL.

    The scheme is read as ``url_scheme`` reads it.
    The text after the colon has trailing C0 controls and spaces trimmed
    and tab, LF and CR removed, as the browser reads it.
    """
    return _read_url_scheme(url)
