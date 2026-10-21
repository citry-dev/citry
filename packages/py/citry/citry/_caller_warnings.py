"""
Warnings that point at the code that called Citry.

Python shows a warning with the file and line it was raised for. A warning
about the author's component or page is only useful when that line is in the
author's code, not somewhere inside Citry. How many Citry frames sit between
the author's call and the warning depends on the path the call took (``str()``,
``serialize()``, a framework adapter), so a fixed ``stacklevel`` points into
Citry on some paths. ``warn_at_caller`` walks the stack instead.

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

# Every module of the citry package lives under this directory.
CITRY_PACKAGE_DIR = str(Path(__file__).resolve().parent) + os.sep


def warn_at_caller(message: str, category: type[Warning]) -> None:
    """
    Issue a warning attributed to the first frame outside the citry package.

    The default warning filter shows each message once per line it points
    at, so pointing at the author's line also shows it once per call site,
    however many renders reach that call.
    """
    # Frame 1 is whoever called this helper, which is inside Citry.
    frame: FrameType | None = sys._getframe(1)
    stacklevel = 2
    # Stop at the outermost frame when every frame is Citry's own (such as
    # the `citry` command), so the warning still names a real file and line.
    while frame is not None and frame.f_back is not None and frame.f_code.co_filename.startswith(CITRY_PACKAGE_DIR):
        frame = frame.f_back
        stacklevel += 1
    warnings.warn(message, category, stacklevel=stacklevel)
