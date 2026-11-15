"""
``citry._urls`` keeps its names and signatures for all of citry 1.x.

Citry UI imports this private module, and a Citry UI release that is
already installed must keep working next to a newer citry 1.x, so a rename
or a changed signature would break it.
"""

from __future__ import annotations

import inspect

from citry import _urls


def test_the_module_keeps_its_names_and_signatures() -> None:
    public = {name for name in vars(_urls) if not name.startswith("_") and inspect.isfunction(getattr(_urls, name))}
    assert public == {"url_scheme", "url_scheme_and_rest"}
    # With `from __future__ import annotations` the annotations are strings,
    # which is what an importer's type checker sees too.
    assert str(inspect.signature(_urls.url_scheme)) == "(url: 'str') -> 'str | None'"
    assert str(inspect.signature(_urls.url_scheme_and_rest)) == "(url: 'str') -> 'tuple[str, str] | None'"
