# mypy: warn_unused_ignores=True
# pyright: reportUnnecessaryTypeIgnoreComment=error
"""Static typing contract for Citry UI composition and installation."""

from typing import TYPE_CHECKING, cast

from typing_extensions import assert_type

import citry
import citry_ui
from citry import (
    Citry,
    CitryElement,
    CitryRender,
    Component,
    ComponentLike,
    LibraryComponentInvocation,
    LibraryInstallation,
    SlotContext,
)
from citry_ui import (
    CButton,
    CButtonDefaultSlotData,
    CField,
    CInput,
    CTable,
    CTableColumn,
    CTableRow,
    CTabs,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def styled_content(ctx: SlotContext[CButtonDefaultSlotData], /) -> str:
    assert_type(ctx.data, CButtonDefaultSlotData)
    return "Save"


app = Citry(autodiscover=False)
ui: LibraryInstallation = app.register_library(citry_ui)
CButtonCall = cast("Callable[..., LibraryComponentInvocation]", CButton)
CFieldCall = cast("Callable[..., LibraryComponentInvocation]", CField)
CInputCall = cast("Callable[..., LibraryComponentInvocation]", CInput)
CTableCall = cast("Callable[..., LibraryComponentInvocation]", CTable)
CTabsCall = cast("Callable[..., LibraryComponentInvocation]", CTabs)

button = CButtonCall(slots={"default": styled_content})
field = CFieldCall(slots={"label": "Name", "default": CInputCall(name="name")})
table = CTableCall(
    columns=(CTableColumn("name", "Name"),),
    rows=(CTableRow("one", {"name": "Ada"}),),
)
tabs = CTabsCall(default_value="first", slots={"default": "content"})
raw_class: type[Component] = ui[CButton]
component_like: ComponentLike = button

assert_type(button, LibraryComponentInvocation)
assert_type(field, LibraryComponentInvocation)
assert_type(table, LibraryComponentInvocation)
assert_type(tabs, LibraryComponentInvocation)
assert_type(button.resolve(app), CitryElement)
assert_type(button.render(citry=app), CitryRender)
assert_type(raw_class, type[Component])
assert_type(citry.citry, Citry)

# Exact component-call keyword checking is intentionally not claimed by the
# current LibraryComponent API. Nested Kwargs and Slots schemas remain the
# runtime validation contract until Python typing can derive class-call
# signatures from those declarations.
CButtonCall(no_such=1, slots={"wrong": "Save"})
