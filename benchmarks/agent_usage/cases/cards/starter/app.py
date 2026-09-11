"""Render a small catalog with Citry components."""

from typing import NotRequired, TypedDict


class Item(TypedDict):
    title: str
    price_cents: int
    description: str
    footer: NotRequired[str | None]


def render_cards(items: list[Item]) -> str:
    raise NotImplementedError
