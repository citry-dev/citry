"""
CImage and CAvatar check a long srcset or image URL in time proportional to its length.

Both the server and the browser checks are covered.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
import sys

import pytest

from citry_ui import CAvatar, CImage
from citry_ui.components.cimage.cimage import _uses_width_descriptor

# The rule _uses_width_descriptor implements, written as a regex. It is slow on
# long inputs, so the tests compare against it only on short ones.
_REFERENCE = r"(?:^|,)\s*[^,]+\s+[1-9][0-9]*w\s*(?=,|$)"

# Short strings built from the characters the rule cares about: commas,
# ASCII and non-ASCII whitespace, digits including 0, "w", and URL text.
_ALPHABET = [
    " ",
    "\t",
    "\n",
    "\x1c",
    "\x85",
    chr(0xA0),
    chr(0x2003),
    "\ufeff",
    ",",
    "0",
    "1",
    "9",
    "w",
    "W",
    "\u0661",
    "a",
]
# Fixed test data, not secrets, so the standard generator is fine.
_RANDOM = random.Random(0)  # noqa: S311
_SAMPLES = ["".join(_RANDOM.choices(_ALPHABET, k=_RANDOM.randint(0, 10))) for _ in range(4000)]
_LONG = 100_000
# Inputs a visitor or a stored record could supply that made the earlier
# regexes take time growing with the square or cube of their length.
_LONG_INPUTS = [
    " " * _LONG,
    "/a.png" + " " * _LONG + "2x",
    "/a.png" + " " * _LONG + "x",
    "a" + "," * _LONG + "b",
    "a" + " " * _LONG + "b",
    "/a.png 1" + "0" * _LONG + "w",
]


def _browser_function(js: str, name: str) -> str:
    # Cut one arrow function out of the runtime by its declaration line and
    # the closing line at the same indent.
    match = re.search(rf"^( *)const {name} = \(value\) => .*?^\1\}}\)?;$", js, re.MULTILINE | re.DOTALL)
    assert match is not None
    return match.group(0)


def _run_node(script: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    # Send the script on stdin: a long script is over the command-line limit on Linux and Windows.
    result = subprocess.run([node, "-"], input=script, capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def test_width_descriptor_check_matches_the_reference_rule() -> None:
    reference = re.compile(_REFERENCE)
    for sample in _SAMPLES:
        assert _uses_width_descriptor(sample) is (reference.search(sample) is not None), repr(sample)


def test_browser_width_descriptor_check_matches_the_reference_rule() -> None:
    script = (
        _browser_function(CImage.js, "usesWidthDescriptor")
        + f"\nconst samples = {json.dumps(_SAMPLES)};"
        + f"\nconst reference = new RegExp({json.dumps(_REFERENCE)});"
        + "\nprocess.stdout.write(JSON.stringify(samples.filter("
        + "(sample) => usesWidthDescriptor(sample) !== reference.test(sample))));"
    )
    assert _run_node(script) == []


# Each server check runs in a child process with a timeout, so slow code
# fails the test instead of keeping the test run busy for hours.
_SERVER_CHECKS = """
import sys
from citry_ui.components._url import is_image_url_allowed
from citry_ui.components.cimage.cimage import _srcset_urls, _uses_width_descriptor

long = int(sys.argv[1])
for value in [
    " " * long,
    "/a.png" + " " * long + "2x",
    "/a.png" + " " * long + "x",
    "a" + "," * long + "b",
    "/a.png 1" + "0" * long + "w",
]:
    _uses_width_descriptor(value)
    all(is_image_url_allowed(url) for url in _srcset_urls(value))
    is_image_url_allowed(value)
"""
_SERVER_RENDER = """
import sys

import citry_ui
from citry import Citry, Component

app = Citry(autodiscover=False)
app.register_library(citry_ui)


class Page(Component):
    citry = app
    template = '<c-CImage src="/a.png" c-srcset="srcset" alt="Ada" c-width="1" c-height="1" />'

    def template_data(self, kwargs, slots):
        return {"srcset": "/a.png" + " " * int(sys.argv[1]) + "2x"}


Page().render().serialize(deps_strategy="ignore")
"""


@pytest.mark.parametrize("script", [_SERVER_CHECKS, _SERVER_RENDER], ids=["checks", "render"])
def test_server_reads_long_srcset_quickly(script: str) -> None:
    # The earlier regex took 1.2 s at 1,000 spaces; linear code takes
    # milliseconds here, and the timeout leaves room for process start-up.
    subprocess.run([sys.executable, "-c", script, str(_LONG)], check=True, timeout=30)


def test_browser_reads_long_srcset_quickly() -> None:
    functions = "\n".join(
        _browser_function(CImage.js, name) for name in ("isImageUrlAllowed", "refusedSet", "usesWidthDescriptor")
    )
    avatar = _browser_function(CAvatar.js, "isImageUrlAllowed").replace(
        "isImageUrlAllowed", "avatarImageUrlAllowed", 1
    )
    script = (
        functions
        + "\n"
        + avatar
        + f"\nconst inputs = {json.dumps(_LONG_INPUTS)};"
        + "\nconst started = Date.now();"
        + "\nfor (const value of inputs) {"
        + " refusedSet(value); usesWidthDescriptor(value);"
        + " isImageUrlAllowed(value); avatarImageUrlAllowed(value); }"
        + "\nprocess.stdout.write(JSON.stringify(Date.now() - started));"
    )
    # The earlier regex took 94 s at 8,000 spaces in Node.
    assert _run_node(script) < 2000
