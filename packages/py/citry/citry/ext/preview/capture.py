"""Browser capture for command-owned preview servers."""

import json
import math
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

from citry.ext.preview.types import Viewport

_REQUIRED_RESOURCES = {"document", "script", "stylesheet", "image", "font"}


class CaptureError(RuntimeError):
    """A capture batch failed; ``manifest`` records completed attempts."""

    def __init__(self, message: str, manifest: dict | None = None) -> None:
        super().__init__(message)
        self.manifest = manifest


def validate_base_url(base_url: str) -> str:
    """Validate the mounted root of a preview command server."""
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Preview base URL must be HTTP(S), without credentials, query, or fragment")
    return base_url.rstrip("/")


def _origin(url: str) -> tuple[str, str | None, int]:
    parsed = urlsplit(url)
    return parsed.scheme, parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


def _url(base_url: str, value: str) -> str:
    resolved = urljoin(base_url + "/", value)
    if _origin(resolved) != _origin(base_url) or urlsplit(resolved).username or urlsplit(resolved).fragment:
        raise ValueError("Preview catalog URL must remain on the supplied origin")
    return resolved


def fetch_catalog(base_url: str, timeout: float = 10.0) -> dict:
    """Fetch the command service catalog with a bounded HTTP request."""
    base_url = validate_base_url(base_url)
    # Verify redirected responses too: an ordinary application's redirect is not a preview service.
    with urlopen(base_url + "/ext/preview/catalog", timeout=timeout) as response:  # noqa: S310
        _url(base_url, response.url)
        value = json.load(response)
    if not isinstance(value, dict):
        raise TypeError("Preview catalog must be a JSON object")
    return value


def _segment(value: object) -> str:
    # Restrict both separators and platform-dependent names before constructing any path.
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", value):
        raise ValueError(f"Unsafe preview output segment: {value!r}")
    if value.endswith(".") or value.split(".")[0].upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        raise ValueError(f"Unsafe preview output segment: {value!r}")
    return value


def _entries(catalog: dict, base_url: str, *, require_urls: bool = True) -> list[dict]:
    if catalog.get("service") != "citry-preview" or type(catalog.get("version")) is not int or catalog["version"] != 1:
        raise ValueError("Expected a version-1 citry-preview command service catalog")
    if not isinstance(catalog.get("components"), list):
        raise TypeError("Preview catalog components must be an array")
    entries, seen = [], set()
    for component in catalog["components"]:
        component_id = _segment(component["id"])
        if component_id in seen:
            raise ValueError(f"Duplicate preview component: {component_id}")
        seen.add(component_id)
        slugs = set()
        for variant in component["variants"]:
            slug = _segment(variant["slug"])
            if slug in slugs:
                raise ValueError(f"Duplicate preview variant: {component_id}/{slug}")
            slugs.add(slug)
            viewport = variant["viewport"]
            # Remote catalogs obey the same allocation bounds as authored declarations.
            Viewport(**viewport)
            entries.append(
                {
                    "component_id": component_id,
                    "slug": slug,
                    "label": variant["label"],
                    "viewport": viewport,
                    "url": _url(base_url, variant["url"]) if require_urls else None,
                    "output": f"{component_id}/{slug}.png",
                }
            )
    return entries


def validate_remote_catalog(local: dict, remote: dict, base_url: str) -> dict:
    """Select remote entries and reject missing or changed local identities and labels."""
    base_url = validate_base_url(base_url)
    desired = _entries(local, base_url, require_urls=False)
    available = {(entry["component_id"], entry["slug"]): entry for entry in _entries(remote, base_url)}
    selected: dict[str, set[str]] = {}
    for entry in desired:
        identity = entry["component_id"], entry["slug"]
        actual = available.get(identity)
        if actual is None or actual["label"] != entry["label"]:
            raise ValueError(f"Preview catalog changed or selection unavailable: {identity[0]}/{identity[1]}")
        selected.setdefault(identity[0], set()).add(identity[1])
    by_id = {component["id"]: component for component in remote["components"]}
    return {
        "service": "citry-preview",
        "version": 1,
        "components": [
            {
                **by_id[component_id],
                "variants": [variant for variant in by_id[component_id]["variants"] if variant["slug"] in slugs],
            }
            for component_id, slugs in selected.items()
        ],
    }


def _safe_path(root: Path, relative: str, overwrite: bool) -> Path:
    path = root / relative
    # resolve catches existing directory symlinks, including links to files outside the root.
    if not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError(f"Preview output escapes its directory: {relative}")
    if path.exists() and (not overwrite or not path.is_file()):
        raise FileExistsError(f"Preview output already exists: {path}")
    return path


def _atomic_write(path: Path, content: bytes, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".preview-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        if overwrite:
            temporary.replace(path)
        else:
            # Hard-link publication preserves no-overwrite semantics even if another process races preflight.
            os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _playwright() -> Any:
    # Serving HTML must work without the optional browser package installed.
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError as error:
        raise CaptureError("Install citry[ext-preview], then run playwright install chromium") from error
    return sync_playwright()


def preflight(catalog: dict, outdir: Path, *, overwrite: bool = False) -> None:
    """Check output targets and browser installation before starting an owned host."""
    entries = _entries(catalog, "", require_urls=False)
    root = Path(outdir).resolve()
    for entry in entries:
        _safe_path(root, entry["output"], overwrite)
    _safe_path(root, "manifest.json", overwrite)
    if not entries:
        return
    # Starting the driver resolves its installed browser location without launching Chromium twice.
    with _playwright() as playwright:
        # executable_path is a local property. A public protocol round trip lets driver initialization
        # finish before shutdown; immediately stopping after reading that property leaves a pending task.
        request_context = playwright.request.new_context()
        request_context.dispose()
        if not Path(playwright.chromium.executable_path).is_file():
            raise CaptureError("Chromium is not installed; run playwright install chromium")


_READY = """async (timeout) => {
    const assets = async () => {
        await document.fonts.ready;
        await Promise.all(Array.from(document.images, async image => {
            if (image.currentSrc || image.src) await image.decode();
        }));
    };
    let timer;
    try {
        await Promise.race([assets(), new Promise((_, reject) => {
            timer = setTimeout(() => reject(new Error('Preview assets readiness timed out')), timeout);
        })]);
    } finally { clearTimeout(timer); }
}"""


def _capture_one(browser: Any, entry: dict, timeout: float, ready_selector: str | None) -> bytes:
    viewport = entry["viewport"]
    context = browser.new_context(
        viewport={"width": viewport["width"], "height": viewport["height"]},
        device_scale_factor=viewport["device_scale_factor"],
    )
    deadline = time.monotonic() + timeout

    def remaining() -> float:
        value = (deadline - time.monotonic()) * 1000
        if value <= 0:
            raise TimeoutError("Preview capture timed out")
        return value

    errors: list[str] = []
    try:
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "requestfailed",
            lambda request: errors.append(f"Resource failed: {request.url}")
            if request.resource_type in _REQUIRED_RESOURCES
            else None,
        )
        page.on(
            "response",
            lambda response: errors.append(f"HTTP {response.status}: {response.url}")
            if response.status >= 400 and response.request.resource_type in _REQUIRED_RESOURCES
            else None,
        )
        response = page.goto(entry["url"], wait_until="load", timeout=remaining())
        if response is None or not response.ok:
            raise CaptureError("Preview navigation did not return successful HTML")
        if "text/html" not in response.headers.get("content-type", ""):
            raise CaptureError("Preview navigation did not return HTML")
        if ready_selector:
            page.locator(ready_selector).wait_for(state="visible", timeout=remaining())
        # Document load plus fonts/images is deliberately narrower than application readiness.
        page.evaluate(_READY, remaining())
        png = page.screenshot(type="png", full_page=True, animations="disabled", timeout=remaining())
        if errors:
            raise CaptureError("; ".join(errors))
        return png
    finally:
        context.close()


def capture(
    catalog: dict,
    base_url: str,
    outdir: Path,
    *,
    overwrite: bool = False,
    timeout: float = 30.0,
    ready_selector: str | None = None,
) -> dict:
    """Capture selected variants, retaining a manifest when individual captures fail."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Preview timeout must be positive and finite")
    base_url = validate_base_url(base_url)
    entries = _entries(catalog, base_url)
    root = Path(outdir).resolve()
    paths = [_safe_path(root, entry["output"], overwrite) for entry in entries]
    manifest_path = _safe_path(root, "manifest.json", overwrite)
    manifest: dict = {"service": "citry-preview", "version": 1, "captures": []}
    if not entries:
        return manifest
    try:
        with _playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
            except Exception as error:
                raise CaptureError("Could not launch Chromium; run playwright install chromium") from error
            try:
                for entry, path in zip(entries, paths, strict=True):
                    result = {**entry, "success": False, "diagnostic": None}
                    try:
                        # Detect reload/selection changes before each capture; never silently capture another story.
                        validate_remote_catalog(catalog, fetch_catalog(base_url, min(timeout, 10)), base_url)
                        png = _capture_one(browser, entry, timeout, ready_selector)
                        _safe_path(root, entry["output"], overwrite)
                        _atomic_write(path, png, overwrite)
                        result["success"] = True
                    except Exception as error:  # noqa: BLE001 - each variant is an independent capture attempt
                        result["diagnostic"] = str(error)
                    manifest["captures"].append(result)
            finally:
                browser.close()
    finally:
        # Setup failure claims no captures; interruption after completed work still preserves that work.
        if manifest["captures"]:
            _safe_path(root, "manifest.json", overwrite)
            _atomic_write(manifest_path, json.dumps(manifest, indent=2).encode(), overwrite)
    if any(not result["success"] for result in manifest["captures"]):
        raise CaptureError("One or more preview captures failed; see manifest.json", manifest)
    return manifest
