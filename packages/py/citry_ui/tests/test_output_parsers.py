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


@pytest.mark.parametrize("parser", [_DirectMenuParser, _DirectItemParser])
def test_parsers_that_never_read_attribute_values_skip_decoding_them(parser: type[LongReferenceSafeParser]) -> None:
    assert not parser._keeps_source


@pytest.mark.parametrize("extra", ["", " &#" + "0" * 5000 + "1;=x"], ids=["plain", "long-reference-in-a-name"])
def test_the_content_parser_reads_a_popover_value_as_the_browser_does(extra: str) -> None:
    def problem(popover: str) -> str | None:
        parser = _ContentOutputParser(actions=False)
        parser.feed(f'<div popover="{popover}" data-citry-ui-part="hover-card"{extra}>')
        parser.close()
        return parser.problem

    assert problem("manual") is None
    # A browser reads man&#1;ual as "man", U+0001, "ual", which is not "manual".
    assert problem("man&#1;ual") == "raw or unrecognized native popovers are not accepted"
