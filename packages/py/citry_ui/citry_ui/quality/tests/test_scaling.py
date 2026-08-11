import pytest

from citry_ui.quality.scaling import scaling_report


def test_scaling_report_records_counts_without_claiming_timing_gates():
    report = scaling_report(counts=(1, 10), samples=1)

    assert report["schema"] == "citry-ui-scaling-report/v1"
    assert [(result["profile"], result["count"]) for result in report["results"]] == [
        ("accordion-items", 1),
        ("disclosure-instances", 1),
        ("alert-instances", 1),
        ("button-instances", 1),
        ("avatar-instances", 1),
        ("badge-instances", 1),
        ("divider-instances", 1),
        ("progress-instances", 1),
        ("spinner-instances", 1),
        ("radio-items", 1),
        ("skeleton-instances", 1),
        ("switch-instances", 1),
        ("breadcrumbs-items", 1),
        ("table-rows", 1),
        ("icon-instances", 1),
        ("card-instances", 1),
        ("textarea-instances", 1),
        ("native-select-instances", 1),
        ("checkbox-instances", 1),
        ("flow-groups", 1),
        ("grid-instances", 1),
        ("button-group-instances", 1),
        ("toggle-items", 1),
        ("pagination-instances", 1),
        ("list-items", 1),
        ("popover-instances", 1),
        ("drawer-instances", 1),
        ("toast-queued-items", 1),
        ("tooltip-instances", 1),
        ("menu-instances", 1),
        ("accordion-items", 10),
        ("disclosure-instances", 10),
        ("alert-instances", 10),
        ("button-instances", 10),
        ("avatar-instances", 10),
        ("badge-instances", 10),
        ("divider-instances", 10),
        ("progress-instances", 10),
        ("spinner-instances", 10),
        ("radio-items", 10),
        ("skeleton-instances", 10),
        ("switch-instances", 10),
        ("breadcrumbs-items", 10),
        ("table-rows", 10),
        ("icon-instances", 10),
        ("card-instances", 10),
        ("textarea-instances", 10),
        ("native-select-instances", 10),
        ("checkbox-instances", 10),
        ("flow-groups", 10),
        ("grid-instances", 10),
        ("button-group-instances", 10),
        ("toggle-items", 10),
        ("pagination-instances", 10),
        ("list-items", 10),
        ("popover-instances", 10),
        ("drawer-instances", 10),
        ("toast-queued-items", 10),
        ("tooltip-instances", 10),
        ("menu-instances", 10),
    ]
    assert all(result["status"] == "diagnostic-only" for result in report["results"])
    assert all(result["output_bytes"] > 0 for result in report["results"])


@pytest.mark.parametrize(("counts", "samples"), [((0,), 1), ((), 1), ((1,), 0)])
def test_scaling_report_rejects_invalid_profiles(counts, samples):
    with pytest.raises(ValueError, match=r"samples|counts"):
        scaling_report(counts=counts, samples=samples)
