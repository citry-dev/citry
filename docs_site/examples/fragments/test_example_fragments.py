"""Render the fragments example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry
from docs_site._internal.static_deps import CITRY_MOUNT_PREFIX

from citry import citry as default_citry


def test_fragments_example_page_renders() -> None:
    # The page asks Citry for the runtime's URL, which Citry can build only
    # once its routes are mounted. The docs build and server mount them at
    # this prefix; the autouse fixture in docs_site/conftest.py restores the
    # earlier value after the test.
    default_citry.set_mounted_prefix(CITRY_MOUNT_PREFIX)
    html = str(get_example_registry()["fragments"].page_cls())
    # The page loads the runtime up front, so the fragment it inserts later can run.
    assert f'src="{default_citry.runtime_url()}"' in html
    # The page offers a button that fetches the pre-rendered fragment endpoint.
    assert 'id="frag-load"' in html
    assert "Load fragment" in html
    assert 'data-fragment-url="/examples/fragments/demo/widget/"' in html
    assert "fetch(url)" in html
