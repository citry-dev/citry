"""Tests for ``Component.class_id`` and the ``Citry`` class-id reverse index."""

import re

import pytest

from citry import Citry, Component


class TestClassId:
    def test_format_is_name_plus_short_hash(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        assert re.fullmatch(r"Card_[0-9a-f]{6}", Card.class_id)

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
