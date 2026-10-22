"""
Warnings that point at the code that called Citry.

Python shows a warning with the file and line it was raised for. A warning
about the author's component or page is only useful when that line is in the
author's code, not somewhere inside Citry. How many Citry frames sit between
the author's call and the warning depends on the path the call took (``str()``,
``serialize()``, a framework adapter), so a fixed ``stacklevel`` points into
Citry on some paths. ``warn_at_caller`` walks the stack instead, and points at
the first frame outside the citry package.

That frame is the author's code only when the author's code started the
work. An Events response (the reply Citry sends when the browser calls an
event handler) is different: the web framework calls Citry's event
route, Citry runs the handler, and the handler has returned by the time Citry
turns its result into HTML. So a warning raised while Citry builds that
response points at the framework code that called the route (for example a
line in Starlette's routing module), not at the handler. When every frame on
the stack is Citry's own, such as under the ``citry`` command, the warning
points at the outermost frame, which is then inside Citry.

Python 3.12 can do this with ``warnings.warn(skip_file_prefixes=...)``; Citry
supports Python 3.10, so the walk is written out here.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import FrameType

# Every module of the citry package lives under these directories. A frame
# names its file by the path Python imported it from, which keeps a symlink in
# place (macOS `/tmp` is one), so both the imported path and the resolved one
# are checked. `dict.fromkeys` drops the second when they are the same.
CITRY_PACKAGE_DIRS = tuple(
    dict.fromkeys(
        (
            str(Path(__file__).absolute().parent) + os.sep,
            str(Path(__file__).resolve().parent) + os.sep,
        )
    )
)


def warn_at_caller(message: str, category: type[Warning]) -> None:
    """
    Issue a warning attributed to the first frame outside the citry package.

    The default warning filter shows each message once per line it points
    at, so pointing at the author's line also shows it once per call site,
    however many renders reach that call. A warning raised while Citry builds
    an Events response points at the web framework's line that called Citry,
    so the same message from any event handler shows only once.
    """
    # Frame 1 is whoever called this helper, which is inside Citry.
    frame: FrameType | None = sys._getframe(1)
    stacklevel = 2
    # Stop at the outermost frame when every frame is Citry's own (such as
    # the `citry` command), so the warning still names a real file and line.
    while frame is not None and frame.f_back is not None and frame.f_code.co_filename.startswith(CITRY_PACKAGE_DIRS):
        frame = frame.f_back
        stacklevel += 1
    warnings.warn(message, category, stacklevel=stacklevel)
