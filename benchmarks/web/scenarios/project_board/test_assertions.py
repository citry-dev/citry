"""Prove plausible incorrect canonical results fail the shared oracle."""

# Keep these checks runnable with the standard library in either app environment.
# ruff: noqa: PT027

import json
import unittest
from copy import deepcopy

from assertions import assert_view, expected_after, expected_view, initial_expected


class AssertionTests(unittest.TestCase):
    def test_oracle_state_survives_a_browser_json_round_trip(self) -> None:
        expected = initial_expected(14)
        round_tripped = json.loads(json.dumps(expected))
        if round_tripped != expected:
            self.fail("Oracle state changed across JSON serialization")
        if expected_view(round_tripped) != expected_view(expected):
            self.fail("Oracle view changed across JSON serialization")

    def test_filter_keeps_empty_groups_and_rejects_wrong_output(self) -> None:
        initial = initial_expected(14)
        expected = expected_after(initial, "filter")
        view = expected_view(expected)
        filtered_counts = [len(group["outputs"]) for group in view["phase_groups"]]
        if filtered_counts != [1, 0, 0, 0, 0]:
            self.fail(f"Unexpected filtered group counts: {filtered_counts}")
        wrong = deepcopy(view)
        wrong["phase_groups"][0]["outputs"][0] = deepcopy(initial["rows"][1])
        wrong["rows"][0] = deepcopy(initial["rows"][1])
        with self.assertRaises(AssertionError):
            assert_view(wrong, expected)

    def test_nested_content_changes_are_rejected(self) -> None:
        expected = initial_expected(14)
        mutations = (
            ("dependency", lambda view: view["rows"][1]["dependencies"][0].update(title="Wrong")),
            ("attachment", lambda view: view["rows"][0]["attachments"].append({"id": 9})),
            ("comment", lambda view: view["note_tabs"][0]["notes"][0].update(text="Wrong")),
            ("role", lambda view: view["roles"][0].update(user_name="Wrong")),
        )
        for name, mutate in mutations:
            with self.subTest(name=name):
                wrong = deepcopy(expected_view(expected))
                mutate(wrong)
                with self.assertRaises(AssertionError):
                    assert_view(wrong, expected)

    def test_insertion_rejects_wrong_id_title_or_phase(self) -> None:
        expected = expected_after(initial_expected(14), "insert")
        for key, value in (("id", 99), ("title", "Wrong output"), ("phase_id", 4)):
            wrong = deepcopy(expected_view(expected))
            wrong["rows"][-1][key] = value
            with self.assertRaises(AssertionError):
                assert_view(wrong, expected)

    def test_invalid_save_rejects_changed_project_or_discarded_attempt(self) -> None:
        expected = expected_after(initial_expected(14), "invalid-save")
        for change in ("project", "attempt"):
            wrong = deepcopy(expected_view(expected))
            if change == "project":
                wrong["project"]["name"] = ""
            else:
                wrong["title_input"] = "Project Name"
            with self.assertRaises(AssertionError):
                assert_view(wrong, expected)

    def test_reorder_rejects_group_or_flat_order_drift(self) -> None:
        expected = expected_after(initial_expected(14), "reorder")
        wrong = deepcopy(expected_view(expected))
        wrong["phase_groups"][0], wrong["phase_groups"][1] = wrong["phase_groups"][1], wrong["phase_groups"][0]
        with self.assertRaises(AssertionError):
            assert_view(wrong, expected)
        wrong = deepcopy(expected_view(expected))
        wrong["rows"][0], wrong["rows"][1] = wrong["rows"][1], wrong["rows"][0]
        with self.assertRaises(AssertionError):
            assert_view(wrong, expected)


if __name__ == "__main__":
    unittest.main()
