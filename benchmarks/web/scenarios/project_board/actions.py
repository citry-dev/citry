"""Drive the same trusted browser actions in every application."""

from typing import TYPE_CHECKING

from model import FILTER_QUERY

if TYPE_CHECKING:
    from playwright.sync_api import Page


ACTIONS = [
    {"name": "select", "selector": '[data-bench-action="select-1"]', "event": "click"},
    {"name": "filter", "selector": '[data-bench-action="filter"]', "event": "click"},
    {"name": "clear-filter", "selector": '[data-bench-action="filter"]', "event": "click"},
    {"name": "invalid-save", "selector": '[data-bench-action="save"]', "event": "click"},
    {"name": "save", "selector": '[data-bench-action="save"]', "event": "click"},
    {"name": "insert", "selector": '[data-bench-action="insert"]', "event": "click"},
    {"name": "reorder", "selector": '[data-bench-action="reorder"]', "event": "click"},
    {"name": "remove", "selector": '[data-bench-action="remove"]', "event": "click"},
    {"name": "probe", "selector": '[data-bench-action="probe"]', "event": "click"},
]


def perform(page: "Page", action: dict[str, str]) -> None:
    name = action["name"]
    if name in ("filter", "clear-filter"):
        page.locator("#query").fill(FILTER_QUERY if name == "filter" else "")
    elif name in ("invalid-save", "save"):
        page.locator("#title-input").fill("" if name == "invalid-save" else "Reviewed project")
    page.locator(action["selector"]).click()
