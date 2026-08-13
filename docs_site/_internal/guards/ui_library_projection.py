"""Check component-owned Citry UI pages and reject obsolete public copies."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING

from docs_site._internal.config_loading import load_yaml
from docs_site._internal.guards.base import GuardResult
from docs_site._internal.project import current_docs_project
from docs_site._internal.ui_library_projection import ui_library_source_path
from docs_site._internal.ui_library_reference import (
    compose_ui_library_source,
    ui_library_reference_path,
)
from docs_site._internal.ui_previews import UiPreviewError, discover_ui_previews

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from docs_site._internal.guards.base import GuardContext

_GUARD = "ui_library_projection"
_PREVIEW_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_GUIDE_REQUIRED_FRAGMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "command-palette": (
        ("callback-only options", "teach the callback-only command semantic boundary"),
        ("frozen value records", "teach the immutable record composition model"),
        ("never fuzzy-ranked", "state the deterministic filtering boundary"),
        ("presentational text only", "state that shortcut hints register no listener"),
        ("completed close clears", "teach accepted-close query reset timing"),
        ("installs no document or window shortcut listener", "teach application-owned shortcuts"),
        ("Every noncomposing Enter is contained", "teach native Form containment"),
        ("During composition", "teach the IME interaction boundary"),
        ("same native Dialog controller", "teach shared modal ownership"),
        ("Without JavaScript", "teach the progressive-enhancement fallback"),
    ),
    "image": (
        (
            "`src`, `alt`, `width`, and `height` are required",
            "teach required native geometry and text alternative inputs",
        ),
        ("WAI alternative-text decision tree", "link the official alternative-text decision aid"),
        ('Use `alt=""` only', "teach the explicit decorative alternative-text decision"),
        ("frozen `CImageSource` records", "teach structured ordered responsive sources"),
        ("important above-fold image", "teach bounded native fetch priority"),
        ("isolated expression scope", "state the native image listener expression boundary"),
        ("native event truth", "state the browser-owned responsive settlement boundary"),
        ("potentially sensitive application data", "state the currentSrc privacy boundary"),
        ("`img-src` CSP", "state the browser-owned CSP boundary"),
        ("Without JavaScript", "teach the native image progressive-enhancement fallback"),
    ),
    "context-menu": (
        ("Context Menu key or Shift+F10", "teach a focusable keyboard target and both opening keys"),
        ("data-citry-context-menu-native", "teach the explicit browser-menu preservation marker"),
        ("literal Boolean `true`", "teach the exact synchronous controlled-opening claim"),
        ("operating system's callout timing", "state the real-device long-press limit"),
        ("/ui-library/components/menu/", "link the reused Menu declaration contract"),
        ("no public coordinate", "state that consumers cannot supply arbitrary points"),
        ("isolated expression scope", "state the native-listener expression boundary"),
        ("Without JavaScript", "teach the native progressive-enhancement fallback"),
    ),
}
_PREVIEW_REQUIRED_FRAGMENTS: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "command-palette": {
        "basic-command-palette": (
            ("Open settings", "include the frozen workspace command copy"),
            ('name="activator"', "bind the owned activator slot"),
            ('c-disabled="activator_disabled"', "bind compatible Button disabledness separately"),
            ("onAction", "include callback-driven activation"),
        ),
        "python-command-records": (
            ("CCommandPaletteGroup", "include grouped frozen Python records"),
            ("CCommandPaletteSeparator", "include the visual separator record"),
            ("python_palette", "render the family through direct Python composition"),
        ),
        "search-and-empty": (
            ("appearance", "include keyword-only search"),
            ("Show no match", "include the explicit empty-result control"),
            ("disabled=True", "include an all-disabled matching result"),
        ),
        "disabled-and-shortcuts": (
            ("Deploy production", "include a disabled command"),
            ("Shift Delete", "include presentational shortcut text"),
            ('intent="danger"', "include destructive visual intent"),
        ),
        "command-adornments": (
            ('name="item_start"', "include the leading visual renderer"),
            ('name="item_end"', "include the trailing visual renderer"),
            ("close_on_action", "bind the complete immutable renderer slot data"),
        ),
        "controlled-command-palette": (
            ("acceptClose", "include a declined and accepted close control"),
            ("acceptQuery", "include a declined and accepted query control"),
            ("Release query control", "include null-release behavior"),
        ),
        "command-actions": (
            ("Copy ID", "include a stay-open command"),
            ("Delete draft", "include a close command"),
            ("Owner focus target", "include owner-moved focus"),
            ("Throw in next action", "include callback exception behavior"),
        ),
        "application-shortcut": (
            ("@keydown.window", "show the application-owned global listener"),
            ("contenteditable", "exclude editable content from the shortcut"),
            ("Help palette", "include multiple palette isolation"),
        ),
        "form-safe-palette": (
            ("requestSubmit", "include explicit callback-owned Form submission"),
            ("IME fixture", "name the composition acceptance fixture"),
            ('type="submit"', "include native submitter controls"),
        ),
        "palette-layers": (
            ("<c-CDialog", "compose the palette inside a native Dialog owner"),
            ("<c-CPopover", "include shared anchored-layer behavior"),
            ("Open ShadowRoot fixture", "name the open-ShadowRoot lifecycle fixture"),
        ),
        "command-palette-environment": (
            ("sm, md, and lg", "cover all public sizes"),
            ("200% and 400% zoom", "name both zoom profiles"),
            ("virtual keyboard", "include mobile viewport behavior"),
            ("forced colors", "include the high-contrast profile"),
        ),
    },
    "image": {
        "basic-image": (
            ("python_image", "include direct Python composition"),
            ("orion-nebula-1280.jpg", "use the licensed local Orion fixture"),
            ('c-width="1280"', "show required template geometry"),
        ),
        "alternative-text": (
            ("c-alt=\"''\"", "include the deliberate decorative case"),
            ("<a href=", "include the functional image-link case"),
            ("<table>", "include an equivalent-data complex image case"),
        ),
        "fit-and-geometry": (
            ('fit="contain"', "include contain geometry"),
            ('fit="cover"', "include cover geometry"),
            ("--cui-image-aspect-ratio", "demonstrate the public aspect-ratio variable"),
        ),
        "responsive-sources": (
            ("CImageSource", "use frozen responsive source records"),
            ('type="image/avif"', "include a native AVIF type discriminator"),
            ("srcset=", "include final-image width candidates"),
            ("sizes=", "pair width candidates with sizes"),
        ),
        "loading-priority": (
            ('loading="eager"', "include the above-fold eager fixture"),
            ('fetch_priority="high"', "include the scarce high-priority hint"),
            ('loading="lazy"', "include the below-fold native lazy fixture"),
        ),
        "placeholder-and-error": (
            ('name="placeholder"', "include the inert loading visual"),
            ('name="fallback"', "include the visual error fallback"),
            ("Recover with a small image", "include explicit error recovery"),
        ),
        "reactive-image": (
            ("image_attrs", "bind native load and error listeners through img_attrs"),
            ("$dispatch", "demonstrate the isolated native-event bridge"),
            ("Rapid A then B", "include request supersession"),
            ("Open ShadowRoot fixture", "name the ShadowRoot lifecycle fixture"),
        ),
        "image-composition": (
            ("<c-CCard", "compose Image in Card media"),
            ("<c-CSkeleton", "show a decorative Skeleton neighbor"),
            ("<figure>", "use native figure and figcaption"),
            ("<a class=", "include an image-only native link"),
        ),
        "delivery-and-security": (
            ('cross_origin="anonymous"', "include credential-free native CORS mode"),
            ('referrer_policy="no-referrer"', "include native referrer policy"),
            ("Browser CSP remains authoritative", "teach CSP-owned failure"),
            ("data, blob, raster, and SVG", "state supported URL trust categories"),
        ),
        "image-lifecycle": (
            ('@c-click="retain"', "include signed server lifecycle controls"),
            ('#c-key="image_key"', "include retained and replaced identity"),
            ("Insert an unowned clone", "include the clone ownership falsifier"),
            ("hostile status fail-closed", "include hostile reflection invalidation"),
        ),
    },
    "context-menu": {
        "choices-and-submenus": (("LTR peer card", "include the frozen LTR peer fixture"),),
        "touch-and-pen": (
            ("Test 700 ms hold", "include the synthetic hold control"),
            ("Test movement cancel", "include the movement-cancel control"),
            ("Test scroll cancel", "include the scroll-cancel control"),
            ("Test lost pointerup", "include the lost-pointerup control"),
            ("Test second pointer", "include the second-pointer control"),
        ),
        "focus-and-keyboard": (("Open composed modal fixture", "include the composed-modal focus fixture"),),
        "layers-and-roots": (
            ("Tooltip-bound target", "include the valid Tooltip ancestry fixture"),
            ("Open sibling Menu", "include the ordinary Menu coexistence fixture"),
            ("Open ShadowRoot scope", "include the open-ShadowRoot fixture"),
            ("Refresh layer counters", "expose layer and registration counters"),
        ),
        "positioning-and-rtl": (
            ("Open from owner state", "include external owner opening"),
            ("Test fully offscreen rejection", "include the fully-offscreen fixture"),
            ("Scroll repair fixture", "include scroll repair"),
            ("Resize repair fixture", "include resize repair"),
        ),
        "customization-and-fallback": (
            ("Toggle server-disabled Orchard enhancement", "include pre-readiness disabled fallback"),
            ("Disable or restore ready Harbor enhancement", "include post-readiness disable and restore"),
        ),
    },
}


def _component_guide_problem(family: str, source: str) -> str:
    if "<c-example" in source or "/examples/" in source:
        return "component pages must use component-owned source instead of the Examples surface"
    for fragment, requirement in _GUIDE_REQUIRED_FRAGMENTS.get(family, ()):
        if fragment not in source:
            return f"component guide must {requirement}"
    return ""


def _load_preview_catalog(path: Path) -> tuple[str, ...]:
    raw = load_yaml(path)
    if not isinstance(raw, Mapping) or set(raw) != {"schema_version", "previews"}:
        raise ValueError("preview catalog must contain only schema_version and previews")
    if raw["schema_version"] != 1:
        raise ValueError("preview catalog schema_version must be 1")
    previews = raw["previews"]
    if not isinstance(previews, list) or not previews:
        raise ValueError("preview catalog previews must be a nonempty list")
    if any(not isinstance(slug, str) or _PREVIEW_SLUG_RE.fullmatch(slug) is None for slug in previews):
        raise ValueError("preview catalog slugs must use lowercase kebab-case")
    if len(previews) != len(set(previews)):
        raise ValueError("preview catalog slugs must be unique")
    return tuple(previews)


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    project = ctx.project or current_docs_project()
    projections = project.ui_library.projections
    sources_ready = True
    for projection in projections:
        source = ui_library_source_path(projection, repo_root=ctx.repo_root)
        source_label = projection.source.as_posix()
        if not source.is_file():
            sources_ready = False
            yield GuardResult.error(
                guard=_GUARD,
                message=f"Component-owned API source is missing for {projection.family!r}",
                source=source_label,
            )
            continue
        source_text = source.read_text(encoding="utf-8")
        problem = _component_guide_problem(projection.family, source_text)
        if not problem:
            try:
                compose_ui_library_source(source, family=projection.family)
            except (OSError, UnicodeError, ValueError) as error:
                reference = ui_library_reference_path(source)
                yield GuardResult.error(
                    guard=_GUARD,
                    message=f"Citry UI API data is invalid for {projection.family!r}: {error}.",
                    source=reference.relative_to(ctx.repo_root).as_posix()
                    if reference.is_relative_to(ctx.repo_root)
                    else str(reference),
                )
                continue
        if problem:
            yield GuardResult.error(
                guard=_GUARD,
                message=f"Component page is incomplete for {projection.family!r}: {problem}.",
                source=source_label,
            )

    if sources_ready:
        try:
            previews = discover_ui_previews(project.ui_library, repo_root=ctx.repo_root)
        except UiPreviewError as error:
            yield GuardResult.error(
                guard=_GUARD,
                message=f"Citry UI preview declaration is invalid: {error}",
                source=project.runtime.ui_library_config.relative_to(ctx.repo_root).as_posix()
                if project.runtime.ui_library_config.is_relative_to(ctx.repo_root)
                else str(project.runtime.ui_library_config),
            )
        else:
            for preview in previews:
                requirements = _PREVIEW_REQUIRED_FRAGMENTS.get(preview.family, {}).get(preview.slug, ())
                if not requirements:
                    continue
                preview_source = ctx.repo_root / preview.source
                preview_text = preview_source.read_text(encoding="utf-8")
                for fragment, requirement in requirements:
                    if fragment in preview_text:
                        continue
                    yield GuardResult.error(
                        guard=_GUARD,
                        message=(f"Citry UI preview {preview.family!r}/{preview.name!r} must {requirement}."),
                        source=preview.source.as_posix(),
                    )
            for projection in projections:
                source = ui_library_source_path(projection, repo_root=ctx.repo_root)
                catalog = source.parent / "snippets/catalog.yml"
                if not catalog.is_file():
                    continue
                try:
                    expected = _load_preview_catalog(catalog)
                except (OSError, UnicodeError, ValueError) as error:
                    yield GuardResult.error(
                        guard=_GUARD,
                        message=f"Citry UI preview catalog is invalid for {projection.family!r}: {error}.",
                        source=catalog.relative_to(ctx.repo_root).as_posix(),
                    )
                    continue
                actual = tuple(preview.slug for preview in previews if preview.family == projection.family)
                if actual != expected:
                    source_text = source.read_text(encoding="utf-8")
                    marker = source_text.find("<c-ui-demo")
                    yield GuardResult.error(
                        guard=_GUARD,
                        message=(
                            f"Citry UI preview order for {projection.family!r} is {actual!r}; "
                            f"the component-owned catalog requires {expected!r}."
                        ),
                        source=projection.source.as_posix(),
                        line=1 if marker < 0 else source_text.count("\n", 0, marker) + 1,
                    )

    target_dir = ctx.content_dir / "ui-library" / "components"
    if target_dir.is_dir():
        for target in sorted(target_dir.glob("*.md")):
            yield GuardResult.error(
                guard=_GUARD,
                message="Obsolete Citry UI page copy; the catalog renders component api.md sources directly",
                source=target.relative_to(ctx.content_dir).as_posix(),
            )
