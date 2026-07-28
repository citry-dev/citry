"""Tests for ``Component.class_id`` and the ``Citry`` class-id reverse index."""

import re

import pytest

from citry import AlreadyRegistered, Citry, Component


def _reload_like_component(c: Citry, registry_name: str) -> type[Component]:
    """Create distinct classes with the same import-derived class ID."""
    return type(
        "ReloadedComponent",
        (Component,),
        {
            "__module__": __name__,
            "__qualname__": "ReloadedComponent",
            "citry": c,
            "name": registry_name,
            "template": "<p>x</p>",
        },
    )


class TestClassId:
    def test_format_is_name_plus_short_hash(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        assert re.fullmatch(r"Card_[0-9a-f]{6}", Card.class_id)

    @pytest.mark.parametrize("class_name", ["../evil", "has space", "<script>", '"quoted"', "Žlutý"])
    def test_generated_class_name_is_sanitized_for_route_identity(self, class_name):
        c = Citry()
        card = type(
            class_name,
            (Component,),
            {
                "__module__": __name__,
                "__qualname__": class_name,
                "citry": c,
                "name": "safe",
                "template": "<p>x</p>",
            },
        )

        assert re.fullmatch(r"[A-Za-z0-9_-]+_[0-9a-f]{6}", card.class_id)

    def test_generated_all_punctuation_class_name_uses_safe_fallback(self):
        c = Citry()
        card = type(
            "...",
            (Component,),
            {
                "__module__": __name__,
                "__qualname__": "...",
                "citry": c,
                "name": "safe",
            },
        )

        assert re.fullmatch(r"Component_[0-9a-f]{6}", card.class_id)

    def test_stable_across_reads(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        assert Card.class_id == Card.class_id

    def test_distinct_classes_get_distinct_ids(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        class Table(Component):
            citry = c
            template = "<p>y</p>"

        assert Card.class_id != Table.class_id

    def test_subclass_gets_its_own_id(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        parent_id = Card.class_id

        class FancyCard(Card):
            pass

        assert FancyCard.class_id != parent_id
        # The subclass's id must not overwrite the parent's cached one.
        assert Card.class_id == parent_id


class TestClassIdLookup:
    def test_lookup_by_class_id(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        assert c.get_component_by_class_id(Card.class_id) is Card

    def test_unknown_id_raises_key_error(self):
        c = Citry()
        with pytest.raises(KeyError, match="nope"):
            c.get_component_by_class_id("nope")

    def test_index_is_per_citry_instance(self):
        c1 = Citry()
        c2 = Citry()

        class Card(Component):
            citry = c1
            template = "<p>x</p>"

        with pytest.raises(KeyError):
            c2.get_component_by_class_id(Card.class_id)

    def test_clear_empties_the_index(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        c.clear()
        with pytest.raises(KeyError):
            c.get_component_by_class_id(Card.class_id)

    def test_live_class_id_collision_is_rejected(self):
        c = Citry()
        original = _reload_like_component(c, "original")

        with pytest.raises(AlreadyRegistered, match=rf"class_id {original.class_id!r}"):
            _reload_like_component(c, "replacement")

        assert c.get("original") is original
        assert not c.has("replacement")
        assert c.get_component_by_class_id(original.class_id) is original

    def test_unregister_one_alias_keeps_index_until_last_alias(self):
        c = Citry()

        class MyCard(Component):
            citry = c
            template = "<p>x</p>"

        class_id = MyCard.class_id
        c.unregister("mycard")

        assert c.get("my-card") is MyCard
        assert c.get_component_by_class_id(class_id) is MyCard

        c.unregister("my-card")
        with pytest.raises(KeyError, match=class_id):
            c.get_component_by_class_id(class_id)

    def test_unregister_then_register_replacement_with_same_class_id(self):
        c = Citry()
        original = _reload_like_component(c, "original")
        class_id = original.class_id

        c.unregister(original)
        with pytest.raises(KeyError, match=class_id):
            c.get_component_by_class_id(class_id)

        replacement = _reload_like_component(c, "replacement")

        assert replacement is not original
        assert replacement.class_id == class_id
        assert c.get_component_by_class_id(class_id) is replacement
