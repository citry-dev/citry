"""The native extension reports which Cargo profile compiled it."""

from citry_core import _rust


def test_build_profile_names_a_cargo_profile() -> None:
    # Tests run on either build, so only the set of values is fixed here;
    # benchmarks are the callers that refuse "debug".
    assert _rust.BUILD_PROFILE in {"release", "debug"}


def test_native_render_depth_limits_are_reported_for_this_build() -> None:
    # The limits differ between a debug and a release build, so callers read
    # them here; each must leave room for a top-level `{{ name }}` (level 2)
    # and a one-subscript path (level 2).
    for limit in (_rust.NATIVE_RENDER_MAX_BODY_DEPTH, _rust.NATIVE_RENDER_MAX_READ_DEPTH):
        assert type(limit) is int
        assert limit >= 2
