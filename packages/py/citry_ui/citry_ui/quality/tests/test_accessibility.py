from citry_ui.quality.accessibility import AXE_INCOMPLETE_DISPOSITIONS, disposition_manifest


def test_every_axe_incomplete_disposition_has_automated_and_manual_ownership():
    assert set(AXE_INCOMPLETE_DISPOSITIONS) == {
        "color-contrast",
        "aria-valid-attr-value",
        "form-field-multiple-labels",
    }
    assert all(disposition.reason for disposition in AXE_INCOMPLETE_DISPOSITIONS.values())
    assert all(disposition.automated_evidence for disposition in AXE_INCOMPLETE_DISPOSITIONS.values())
    assert all(disposition.manual_task for disposition in AXE_INCOMPLETE_DISPOSITIONS.values())
    assert [item["rule"] for item in disposition_manifest()] == [
        "color-contrast",
        "aria-valid-attr-value",
        "form-field-multiple-labels",
    ]
