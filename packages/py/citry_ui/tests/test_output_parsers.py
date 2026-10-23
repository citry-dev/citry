"""Every citry-ui parser of rendered output reads numeric references of any length."""

from __future__ import annotations

import pytest

from citry.util.html import LongReferenceSafeParser
from citry_ui.components.caccordion.caccordion import _DirectItemParser
from citry_ui.components.ccommand_palette.ccommand_palette import _VisualParser
from citry_ui.components.cdisclosure.cdisclosure import _ContentOutputParser, _TitleOutputParser
from citry_ui.components.cimage.cimage import _CImageVisualParser
from citry_ui.components.clistbox.clistbox import _ListboxOutputParser
from citry_ui.components.cmenu.cmenu import _DirectMenuParser
from citry_ui.components.ctree.ctree import _TreeOutputParser


@pytest.mark.parametrize(
    "parser",
    [
        _DirectItemParser,
        _VisualParser,
        _ContentOutputParser,
        _TitleOutputParser,
        _CImageVisualParser,
        _ListboxOutputParser,
        _DirectMenuParser,
        _TreeOutputParser,
    ],
)
def test_output_parsers_use_the_long_reference_parser(parser: type) -> None:
    # Python's HTMLParser raises ValueError for a decimal reference with more
    # than 4,300 digits; this base class reads it as the browser does.
    assert issubclass(parser, LongReferenceSafeParser)
