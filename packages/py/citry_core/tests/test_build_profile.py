"""The native extension reports which Cargo profile compiled it."""

from citry_core import _rust


def test_build_profile_names_a_cargo_profile() -> None:
    # Tests run on either build, so only the set of values is fixed here;
    # benchmarks are the callers that refuse "debug".
    assert _rust.BUILD_PROFILE in {"release", "debug"}
