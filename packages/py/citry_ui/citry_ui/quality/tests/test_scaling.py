import pytest

from citry_ui.quality.scaling import scaling_report


def test_scaling_report_records_counts_without_claiming_timing_gates():
    report = scaling_report(counts=(1, 10), samples=1)

    assert report["schema"] == "citry-ui-scaling-report/v1"
    assert [(result["profile"], result["count"]) for result in report["results"]] == [
        ("button-instances", 1),
        ("table-rows", 1),
        ("button-instances", 10),
        ("table-rows", 10),
    ]
    assert all(result["status"] == "diagnostic-only" for result in report["results"])
    assert all(result["output_bytes"] > 0 for result in report["results"])


@pytest.mark.parametrize(("counts", "samples"), [((0,), 1), ((), 1), ((1,), 0)])
def test_scaling_report_rejects_invalid_profiles(counts, samples):
    with pytest.raises(ValueError, match=r"samples|counts"):
        scaling_report(counts=counts, samples=samples)
