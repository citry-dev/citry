"""Server contracts for CImage."""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import get_type_hints

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cimage import (
    CImage,
    CImageSource,
    CImageStatusChangeDetail,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-image-tests", (CImage,)))
    return app


def _render(image: object, *, deps: str = "ignore", app: Citry | None = None) -> str:
    app = app or _app()

    class Page(Component):
        citry = app
        template = """
          <main>{{ image }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"image": image}

    return Page().render().serialize(deps_strategy=deps)


def _tag(html: str, part: str) -> str:
    match = re.search(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_exports_records_and_schema_are_exact() -> None:
    import citry_ui.components.cimage as family

    assert family.__all__ == [
        "CImage",
        "CImageCrossOrigin",
        "CImageDecoding",
        "CImageFetchPriority",
        "CImageFit",
        "CImageLoading",
        "CImageReferrerPolicy",
        "CImageSource",
        "CImageStatus",
        "CImageStatusChangeDetail",
    ]
    assert [field.name for field in fields(CImage.Kwargs)] == [
        "src",
        "alt",
        "width",
        "height",
        "srcset",
        "sizes",
        "sources",
        "loading",
        "decoding",
        "fetch_priority",
        "cross_origin",
        "referrer_policy",
        "fit",
        "position",
        "draggable",
        "onStatusChange",
        "class_",
        "style",
        "attrs",
        "img_attrs",
    ]
    assert [field.name for field in fields(CImage.Slots)] == ["placeholder", "fallback"]
    assert [field.name for field in fields(CImageSource)] == [
        "srcset",
        "media",
        "type",
        "sizes",
        "width",
        "height",
    ]
    assert [field.name for field in fields(CImageStatusChangeDetail)] == [
        "status",
        "src",
        "current_src",
        "natural_width",
        "natural_height",
    ]
    assert get_type_hints(CImage.Kwargs)["sources"] is not None
    with pytest.raises(FrozenInstanceError):
        CImageSource("/next.png").srcset = "/changed.png"  # type: ignore[misc]


def test_smallest_image_renders_native_semantics_and_no_server_status() -> None:
    html = _render(CImage(src="/orion.jpg", alt="Orion Nebula", width=1280, height=720))
    root = _tag(html, "image-root")
    image = _tag(html, "image")

    assert root.startswith("<span")
    assert "data-status" not in root
    assert "data-citry-image-initialized" not in root
    assert "<picture" not in html
    assert 'src="/orion.jpg"' in image
    assert 'alt="Orion Nebula"' in image
    assert 'width="1280"' in image
    assert 'height="720"' in image
    assert 'loading="eager"' in image
    assert 'decoding="auto"' in image
    assert 'fetchpriority="auto"' in image
    assert 'draggable="false"' in image


def test_decorative_image_keeps_explicit_empty_alt() -> None:
    html = _render(CImage(src="/wash.jpg", alt="", width=320, height=180))
    image = _tag(html, "image")
    assert re.search(r"\salt(?:=\"\")?(?:\s|/?>)", image)
    assert "role=" not in image
    assert "aria-label" not in image


def test_data_image_payload_is_not_misclassified_as_an_active_url() -> None:
    src = "data:image/svg+xml,javascript:%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E"
    html = _render(CImage(src=src, alt="Literal payload", width=20, height=10))
    assert "data:image/svg+xml,javascript:" in _tag(html, "image")


def test_data_image_srcset_payload_is_not_misclassified_as_an_active_url() -> None:
    srcset = "data:image/svg+xml,javascript:%3Csvg%20xmlns='http://www.w3.org/2000/svg'/%3E 1x"
    html = _render(
        CImage(
            src="/fallback.png",
            srcset=srcset,
            alt="Literal responsive payload",
            width=20,
            height=10,
        )
    )
    assert "data:image/svg+xml,javascript:" in _tag(html, "image")


def test_picture_sources_render_in_exact_native_order() -> None:
    image = CImage(
        src="/fallback.jpg",
        alt="Observatory",
        width=960,
        height=640,
        srcset="/small.jpg 480w, /fallback.jpg 960w",
        sizes="100vw",
        sources=(
            CImageSource(
                srcset="/wide.jpg 1600w",
                media="(min-width: 64rem)",
                sizes="100vw",
                width=1600,
                height=700,
            ),
            CImageSource(srcset="/modern.avif", type="image/avif"),
        ),
    )
    html = _render(image)

    assert html.count("<picture") == 1
    assert html.count("<source") == 2
    assert html.count("<img") == 1
    assert html.index("/wide.jpg") < html.index("/modern.avif") < html.index("/fallback.jpg")
    picture = _tag(html, "picture")
    assert picture.startswith("<picture")


def test_source_sequence_is_consumed_once_for_template_and_browser_data() -> None:
    class OnePassSources(Sequence[CImageSource]):
        def __init__(self) -> None:
            self.iterations = 0
            self.values = (CImageSource("/modern.avif", type="image/avif"),)

        def __len__(self) -> int:
            return len(self.values)

        def __getitem__(self, index: int) -> CImageSource:
            return self.values[index]

        def __iter__(self) -> Iterator[CImageSource]:
            self.iterations += 1
            if self.iterations > 1:
                raise RuntimeError("sources were consumed twice")
            return iter(self.values)

    sources = OnePassSources()
    html = _render(CImage(src="/base.jpg", alt="Plate", width=80, height=40, sources=sources), deps="simple")
    assert sources.iterations == 1
    assert "/modern.avif" in html


def test_python_slots_are_inert_hidden_visual_siblings() -> None:
    html = _render(
        CImage(
            src="/delayed.jpg",
            alt="Delayed plate",
            width=800,
            height=600,
            slots={"placeholder": "Loading plate", "fallback": "Plate unavailable"},
        )
    )
    root = _tag(html, "image-root")
    placeholder = _tag(html, "placeholder")
    fallback = _tag(html, "fallback")

    assert "data-has-placeholder" in root
    assert "data-has-fallback" in root
    for tag in (placeholder, fallback):
        assert "hidden" in tag
        assert "inert" in tag
        assert 'aria-hidden="true"' in tag
    assert "Loading plate" in html
    assert "Plate unavailable" in html


def test_literal_and_python_interactive_visual_slots_fail_server_render() -> None:
    app = _app()

    class LiteralPage(Component):
        citry = app
        template = """
          <c-CImage src="/plate.jpg" alt="Plate" c-width="20" c-height="10">
            <c-fill name="placeholder"><button type="button">Retry</button></c-fill>
          </c-CImage>
        """

    with pytest.raises(ValueError, match="cannot contain interactive or image content"):
        str(LiteralPage())

    class InteractiveFallback(Component):
        citry = app
        template = '<a href="/retry">Retry</a>'

    with pytest.raises(ValueError, match="cannot contain interactive or image content"):
        _render(
            CImage(
                src="/plate.jpg",
                alt="Plate",
                width=20,
                height=10,
                slots={"fallback": InteractiveFallback()},
            ),
        )

    for markup in (
        "<details><summary>Details</summary></details>",
        '<embed src="/media">',
        '<label for="outside">Label</label>',
        '<area href="/area">',
        '<object data="/object"></object>',
    ):

        class AdditionalInteractiveFallback(Component):
            citry = _app()
            template = markup

        with pytest.raises(ValueError, match="cannot contain interactive or image content"):
            _render(
                CImage(
                    src="/plate.jpg",
                    alt="Plate",
                    width=20,
                    height=10,
                    slots={"fallback": AdditionalInteractiveFallback()},
                )
            )

    class NativeImageFallback(Component):
        citry = app
        template = '<img src="/nested.jpg" alt="Nested" />'

    with pytest.raises(ValueError, match="cannot contain interactive or image content"):
        _render(
            CImage(
                src="/plate.jpg",
                alt="Plate",
                width=20,
                height=10,
                slots={"fallback": NativeImageFallback()},
            ),
        )


def test_root_and_image_attribute_destinations_are_distinct_and_copied() -> None:
    root_attrs = {"lang": "en", "data-test-root": "plate"}
    image_attrs = {
        "title": "Long exposure",
        "aria-describedby": "plate-note",
        "class": "archive-pixels",
        "@load": "$dispatch('plate-ready')",
    }
    html = _render(
        CImage(
            src="/plate.jpg",
            alt="Calibration plate",
            width=640,
            height=480,
            fit="cover",
            position="20% 40%",
            class_="archive-image",
            style={"inline-size": "20rem"},
            attrs=root_attrs,
            img_attrs=image_attrs,
        )
    )

    assert root_attrs == {"lang": "en", "data-test-root": "plate"}
    assert image_attrs == {
        "title": "Long exposure",
        "aria-describedby": "plate-note",
        "class": "archive-pixels",
        "@load": "$dispatch('plate-ready')",
    }
    root = _tag(html, "image-root")
    image = _tag(html, "image")
    assert "archive-image" in root
    assert 'data-test-root="plate"' in root
    assert "inline-size: 20rem" in root
    assert "--_cui-image-input-fit: cover" in root
    assert "--_cui-image-input-position: 20% 40%" in root
    assert 'title="Long exposure"' in image
    assert 'aria-describedby="plate-note"' in image
    assert "archive-pixels" in image
    assert "@load=" in image


@pytest.mark.parametrize(
    ("inputs", "error", "match"),
    [
        ({"src": ""}, ValueError, "src must be non-empty"),
        ({"src": 3}, TypeError, "src must be a string"),
        ({"src": " javaScript:alert(1)"}, ValueError, "active URL scheme"),
        ({"alt": None}, TypeError, "alt must be a string"),
        ({"width": True}, TypeError, "width must be a positive integer"),
        ({"width": 0}, ValueError, "width must be greater than zero"),
        ({"height": -1}, ValueError, "height must be greater than zero"),
        ({"loading": "auto"}, ValueError, "loading must be one of"),
        ({"decoding": "defer"}, ValueError, "decoding must be one of"),
        ({"fetch_priority": "urgent"}, ValueError, "fetch_priority must be one of"),
        ({"cross_origin": "credentialed"}, ValueError, "cross_origin must be one of"),
        ({"referrer_policy": "always"}, ValueError, "referrer_policy must be one of"),
        ({"fit": "crop"}, ValueError, "fit must be one of"),
        ({"position": "center; color:red"}, ValueError, "declaration-breaking"),
        ({"draggable": 1}, TypeError, "draggable must be a bool"),
        ({"srcset": "/small.jpg 480w"}, ValueError, "srcset requires sizes"),
        ({"sizes": "auto"}, ValueError, "auto sizes requires loading='lazy'"),
        ({"sources": iter(())}, TypeError, "sources must be a sequence"),
        ({"sources": tuple(CImageSource(f"/{index}.jpg") for index in range(33))}, ValueError, "at most 32"),
    ],
)
def test_invalid_top_level_inputs_fail_with_constant_errors(inputs, error, match) -> None:
    kwargs = {"src": "/image.jpg", "alt": "Image", "width": 20, "height": 10}
    kwargs.update(inputs)
    with pytest.raises(error, match=match):
        _render(CImage(**kwargs))


@pytest.mark.parametrize(
    ("sources", "image_inputs", "match"),
    [
        ((object(),), {}, r"sources\[0\] must be CImageSource"),
        ((CImageSource("/a.jpg", width=20),), {}, "width and height must be supplied together"),
        ((CImageSource("/a.jpg 200w"),), {}, "width descriptors require sizes"),
        ((CImageSource("/a.jpg", media="   "),), {}, "media must be non-empty"),
        (
            (CImageSource("/a.jpg", media=" all "), CImageSource("/b.jpg")),
            {},
            "requires type or a nontrivial media",
        ),
        ((CImageSource("/a.jpg", type="image/svg+xml; charset=utf-8"),), {}, "image MIME essence"),
        (
            (CImageSource("/a.jpg", sizes="auto"),),
            {"loading": "lazy", "sizes": "100vw"},
            "requires a lazy image with auto sizes",
        ),
    ],
)
def test_invalid_source_records_fail_cross_record_validation(sources, image_inputs, match) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _render(
            CImage(
                src="/fallback.jpg",
                alt="Image",
                width=20,
                height=10,
                sources=sources,
                **image_inputs,
            )
        )


def test_lazy_auto_sizes_is_valid_only_across_the_whole_picture() -> None:
    html = _render(
        CImage(
            src="/fallback.jpg",
            alt="Image",
            width=20,
            height=10,
            loading="lazy",
            srcset="/fallback.jpg 20w",
            sizes="auto, 100vw",
            sources=(
                CImageSource(
                    "/wide.jpg 40w",
                    media="(min-width: 1px)",
                    sizes="auto, 100vw",
                ),
            ),
        )
    )
    assert html.count('sizes="auto, 100vw"') == 2


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "role"),
        ("attrs", "ARIA-DESCRIBEDBY"),
        ("attrs", "tabindex"),
        ("attrs", "data-status"),
        ("attrs", ":data-fit"),
        ("attrs", "data-citry-hostile"),
        ("attrs", "data-has-alpine-state"),
        ("attrs", "X-Citry-Fill-Source"),
        ("attrs", "x-citry-boundary.modifier"),
        ("attrs", "x-data"),
        ("attrs", "x-bind"),
        ("attrs", "onclick"),
        ("img_attrs", "src"),
        ("img_attrs", "srcset"),
        ("img_attrs", "alt"),
        ("img_attrs", "usemap"),
        ("img_attrs", "ismap"),
        ("img_attrs", "aria-hidden"),
        ("img_attrs", "tabindex"),
        ("img_attrs", "onload"),
        ("img_attrs", "data-has-alpine-state"),
        ("img_attrs", "X-Citry-Fill-Source"),
        ("img_attrs", "x-citry-boundary.modifier"),
        ("img_attrs", "x-bind:src"),
        ("img_attrs", "x-bind"),
    ],
)
def test_owned_attributes_and_runtime_paths_are_rejected(destination, attribute) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(
            CImage(
                src="/image.jpg",
                alt="Image",
                width=20,
                height=10,
                **{destination: {attribute: "consumer"}},
            )
        )


def test_assets_expose_only_the_ratified_image_surface() -> None:
    css = (Path(__file__).parents[1] / "runtime.source.css").read_text(encoding="utf8")
    assert "IntersectionObserver" not in CImage.js
    assert "ResizeObserver" not in CImage.js
    assert 'addEventListener("load"' in CImage.js
    assert 'addEventListener("error"' in CImage.js
    assert "image.decode()" in CImage.js
    for variable in (
        "aspect-ratio",
        "fit",
        "position",
        "radius",
        "background",
        "fallback-color",
        "fallback-background",
    ):
        assert f"--_cui-image-{variable}: var(--cui-image-{variable}," in css
