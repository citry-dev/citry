import sys

from citry_core import _rust

# TODO - Remove this conditional once Django drops support for Python 3.8 and 3.9
if sys.version_info >= (3, 10):
    from typing import TypeAlias

    transform_html: TypeAlias = _rust.html_transform.transform_html
else:
    transform_html = _rust.html_transform.transform_html


__all__ = ["transform_html"]
