"""
Import every module of Citry and Citry UI, then render two components and check the escaped output.

smoke.mjs runs this file inside Pyodide, after it installs the wheels built
from this checkout, then calls `main()`. A failed check raises, and the
message carries the module or the output that failed it.
"""

from __future__ import annotations

import importlib
import pkgutil

import citry
import citry_ui
from citry import Citry, Component

# A value a browser would read as markup. A render that skipped escaping would
# let the tag reach the page.
UNSAFE = "<b>bold</b> & more"
ESCAPED = "&lt;b&gt;bold&lt;/b&gt; &amp; more"

# Building the app creates Citry's built-in extensions, and some of them
# import their modules only at that point, so it belongs to the import check.
app = Citry(autodiscover=False)
app.register_library(citry_ui)


class Greeting(Component):
    citry = app

    class Kwargs:
        name: str

    def template_data(self, kwargs: Greeting.Kwargs, _slots: object) -> dict[str, str]:
        return {"name": kwargs.name}

    template = """
    <p class="greeting">Hello, {{ name }}!</p>
    """


class Page(Component):
    citry = app

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, str]:
        return {"label": UNSAFE}

    template = """
    <main>
      <c-CButton>{{ label }}</c-CButton>
    </main>
    """


def import_every_module() -> int:
    """Import every module of both packages, and return how many there are."""
    names = [
        info.name
        for package in (citry, citry_ui)
        for info in pkgutil.walk_packages(package.__path__, f"{package.__name__}.")
    ]
    failures = []
    for name in names:
        # A render loads only the modules it reaches. Importing all of them
        # also covers the ones that Events, the reload server, and the
        # commands load later, which a Pyodide-only import error would
        # otherwise hide until someone used them.
        try:
            importlib.import_module(name)
        except Exception as error:  # noqa: BLE001 - every failure is reported below
            failures.append(f"{name}: {type(error).__name__}: {error}")
    if failures:
        msg = "These modules failed to import in Pyodide:\n" + "\n".join(failures)
        raise AssertionError(msg)
    return len(names)


def render(component: Component) -> str:
    """Render a component to HTML, and require that its markup-like value came out escaped."""
    html = component.render().serialize()
    if ESCAPED not in html or UNSAFE in html:
        msg = f"Expected {ESCAPED!r} and not {UNSAFE!r} in:\n{html[:2000]}"
        raise AssertionError(msg)
    return html


def main() -> str:
    """Run the import check and both renders, and return a one-line summary for the log."""
    modules = import_every_module()
    greeting = render(Greeting(name=UNSAFE))
    # Citry UI is the other package built from this checkout. The page calls
    # its button by tag, which goes through the library registration above.
    page = render(Page())
    return (
        f"Imported {modules} modules. Rendered Greeting ({len(greeting)} characters) "
        f"and Page with CButton ({len(page)} characters)."
    )
