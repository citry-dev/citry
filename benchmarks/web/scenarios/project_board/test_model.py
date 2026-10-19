"""Check canonical state isolation, scaling, and server validation."""

# Keep these checks runnable with the standard library in either app environment.
# ruff: noqa: PT009, PT027

import unittest
from unittest.mock import patch

from model import FILTER_QUERY, ActionInput, apply, reset, snapshot


class ModelTests(unittest.TestCase):
    def test_mutations_do_not_build_discarded_snapshots(self) -> None:
        with patch("model.snapshot", side_effect=AssertionError("Mutation requested a snapshot")):
            self.assertIsNone(reset("mutation-only", 14))
            self.assertIsNone(apply("mutation-only", ActionInput(action="probe", operation="probe-1")))
        self.assertEqual(snapshot("mutation-only")["revision"], 1)

    def test_sessions_and_returned_snapshots_are_independent(self) -> None:
        reset("first", 14)
        first = snapshot("first")
        reset("second", 140)
        first["rows"][0]["title"] = "Caller mutation"
        apply("first", ActionInput(action="filter", operation="filter-1", query=FILTER_QUERY))
        self.assertEqual(snapshot("first")["rows"][0]["title"], FILTER_QUERY)
        self.assertEqual(snapshot("first")["visible_count"], 1)
        self.assertEqual(snapshot("second")["visible_count"], 140)

    def test_source_normalization_preserves_canonical_relationships(self) -> None:
        reset("canonical", 14)
        result = snapshot("canonical")
        self.assertEqual(
            [(group["id"], len(group["outputs"])) for group in result["phase_groups"]],
            [(4, 1), (7, 6), (8, 4), (6, 2), (5, 1)],
        )
        self.assertEqual([row["source_id"] for row in result["phase_groups"][-2]["outputs"]], [25, 26])
        self.assertEqual([row["source_id"] for row in result["phase_groups"][-1]["outputs"]], [27])
        self.assertEqual(
            result["note_tabs"][0]["notes"][0]["comments"][0],
            {"id": 1, "text": "Test note one two three", "author": "UserName"},
        )
        self.assertEqual(result["roles"][0], {"id": 1, "name": "Assistant", "user_name": "UserName"})

    def test_scaled_dependencies_stay_in_their_replica(self) -> None:
        reset("scaled", 140)
        rows = snapshot("scaled")["rows"]
        by_source = {source_id: [row for row in rows if row["source_id"] == source_id] for source_id in (14, 20, 28)}
        targets = [row["id"] for row in by_source[14]]
        self.assertEqual([row["dependencies"][0]["id"] for row in by_source[20]], targets)
        self.assertEqual([row["dependencies"][0]["id"] for row in by_source[28]], targets)
        for key in ("rows", "roles", "bookmarks"):
            self.assertEqual(len({item["id"] for item in snapshot("scaled")[key]}), len(snapshot("scaled")[key]))

    def test_failed_business_validation_keeps_title_and_advances_revision(self) -> None:
        reset("validation", 14)
        apply("validation", ActionInput(action="save", operation="invalid", title=""))
        result = snapshot("validation")
        self.assertEqual(result["title"], "Project Name")
        self.assertEqual(result["project"]["name"], "Project Name")
        self.assertEqual(result["error"], "Use between 3 and 80 characters.")
        self.assertEqual(result["revision"], 1)
        apply("validation", ActionInput(action="save", operation="valid", title="Updated"))
        result = snapshot("validation")
        self.assertEqual(result["title"], "Updated")
        self.assertEqual(result["project"]["name"], "Updated")

    def test_insert_reorder_remove_keeps_flattened_group_order(self) -> None:
        for count in (14, 140, 1400):
            reset("repeat", count)
            apply("repeat", ActionInput(action="insert", operation="insert"))
            inserted = snapshot("repeat")
            self.assertEqual(inserted["phase_groups"][-1]["outputs"][-1]["id"], inserted["inserted"])
            before = [row["id"] for row in inserted["rows"]]
            apply("repeat", ActionInput(action="reorder", operation="reorder"))
            reordered = snapshot("repeat")
            flattened = [row["id"] for group in reordered["phase_groups"] for row in group["outputs"]]
            self.assertEqual(flattened, list(reversed(before)))
            apply("repeat", ActionInput(action="remove", operation="remove"))
            self.assertEqual(snapshot("repeat")["total_count"], count)

    def test_invalid_setup_or_action_is_rejected(self) -> None:
        for count in (0, 10, 100, 1000):
            with self.assertRaises(ValueError):
                reset("invalid", count)
        for session in ("", "../other", "x" * 129):
            with self.assertRaises(ValueError):
                reset(session, 14)
        reset("invalid", 14)
        for data in (
            ActionInput(action="unknown", operation="unknown"),
            ActionInput(action="probe", operation=""),
            ActionInput(action="select", operation="missing", row_id="999"),
            ActionInput(action="remove", operation="missing"),
        ):
            with self.assertRaises(ValueError):
                apply("invalid", data)


if __name__ == "__main__":
    unittest.main()
