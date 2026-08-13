"""Private dependency materialization and serialization security accounting."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
from dataclasses import dataclass
from secrets import token_hex
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from citry.attrs import format_attrs
from citry.citry_render import SerializedScriptSecurity
from citry.ext.dependencies.types import _JAVASCRIPT_MIME_TYPES, Dependency, Script, Style

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry._owned_resource import _OwnedResource
    from citry.settings import SecurityCspMode

_DIGEST_LENGTHS = {"sha256": 32, "sha384": 48, "sha512": 64}
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


@dataclass(frozen=True, slots=True)
class _RenderedDependency:
    """One immutable result of calling a structured dependency's ``_render()`` once."""

    tag_name: Literal["script", "style", "link"]
    attrs: Mapping[str, str | bool]
    content: str
    is_void: bool
    metadata: SerializedScriptSecurity | None = None
    csp_hashes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "attrs", MappingProxyType(dict(self.attrs)))

    def html(self, extra_attrs: dict[str, str | bool] | None = None) -> str:
        attrs = self.attrs if extra_attrs is None else {**self.attrs, **extra_attrs}
        attrs_text = format_attrs(attrs)
        attrs_prefix = f" {attrs_text}" if attrs_text else ""
        if self.is_void:
            return f"<{self.tag_name}{attrs_prefix}/>"
        return f"<{self.tag_name}{attrs_prefix}>{self.content}</{self.tag_name}>"

    def descriptor(self) -> dict[str, str | dict[str, str | bool]]:
        return {"tag": self.tag_name, "attrs": dict(self.attrs), "content": self.content}


@dataclass(frozen=True, slots=True)
class _TrustedTag:
    marker_name: str | None
    provisional_html: str
    final_html: str


class _ScriptSecurityMaterializer:
    """Call-local authority for structured dependency output and trusted tags."""

    __slots__ = (
        "_captures",
        "_collect_integrity",
        "_csp_findings",
        "_csp_hashes",
        "_csp_mode",
        "_has_executable_script",
        "_has_inline_style",
        "_marker_prefix",
        "_nonce",
        "_scripts",
        "_trusted_tags",
    )

    def __init__(
        self,
        *,
        collect_integrity: bool,
        csp_nonce: str | None,
        csp_mode: SecurityCspMode = "off",
    ) -> None:
        self._collect_integrity = collect_integrity
        self._nonce = csp_nonce
        self._csp_mode = csp_mode
        self._marker_prefix = f"data-citry-security-{token_hex(16)}"
        self._captures: dict[int, tuple[Dependency, _RenderedDependency]] = {}
        self._csp_findings: list[str] = []
        self._scripts: list[SerializedScriptSecurity] = []
        self._csp_hashes: list[str] = []
        self._trusted_tags: list[_TrustedTag] = []
        self._has_executable_script = False
        self._has_inline_style = False

    @property
    def csp_nonce(self) -> str | None:
        return self._nonce

    @property
    def integrity_enabled(self) -> bool:
        return self._collect_integrity

    @property
    def csp_mode(self) -> SecurityCspMode:
        return self._csp_mode

    @property
    def marker_prefix(self) -> str:
        """Return the unpredictable marker prefix used by the final CSP scan."""
        return self._marker_prefix

    @property
    def scripts(self) -> tuple[SerializedScriptSecurity, ...]:
        return tuple(self._scripts)

    @property
    def csp_script_hashes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self._csp_hashes))

    @property
    def csp_findings(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self._csp_findings))

    def validate_declared_nonce(self, dependency: Dependency) -> None:
        """Fail on a component-hook nonce conflict before dependency deduplication."""
        if self._nonce is None:
            return
        if not isinstance(dependency, (Script, Style)):
            raise self._structured_dependency_error(dependency)
        if isinstance(dependency, Style) and dependency.url is not None:
            return
        _validate_nonce_mapping(dependency.attrs, self._nonce, type(dependency).__name__)

    def render(self, dependency: Dependency) -> str:
        """Materialize and mark one structured top-level dependency tag."""
        if self._compatibility_only:
            if isinstance(dependency, Style):
                if type(dependency).render is not Style.render:
                    self._record_opaque_warning(dependency)
            elif isinstance(dependency, Script):
                if type(dependency).render is not Dependency.render:
                    self._record_opaque_warning(dependency)
            else:
                self._record_opaque_warning(dependency)
            html = str(dependency.render())
            self._trusted_tags.append(_TrustedTag(marker_name=None, provisional_html=html, final_html=html))
            return html
        if isinstance(dependency, Style):
            if self._nonce is None and not self._collect_integrity and self._csp_mode == "off":
                return str(dependency.render())
            rendered = self._materialize(dependency)
            if rendered.tag_name == "link":
                return rendered.html()
            return self._trusted_html(rendered)
        if not isinstance(dependency, Script):
            if self._csp_mode == "warn":
                self._record_opaque_warning(dependency)
                return str(dependency.render())
            raise self._structured_dependency_error(dependency)
        rendered = self._materialize(dependency)
        self._record_rendered(rendered)
        return self._trusted_html(rendered)

    def render_style(self, dependency: Dependency) -> str:
        """Render one stylesheet, applying and protecting an inline-style nonce."""
        if not isinstance(dependency, Style):
            if self._csp_mode == "warn":
                self._record_opaque_warning(dependency)
                return str(dependency.render())
            raise self._structured_dependency_error(dependency)
        return self.render(dependency)

    def _trusted_html(self, rendered: _RenderedDependency) -> str:
        final_html = rendered.html()
        if self._csp_mode == "warn" and self._nonce is None and not self._collect_integrity:
            self._trusted_tags.append(
                _TrustedTag(marker_name=None, provisional_html=final_html, final_html=final_html)
            )
            return final_html
        marker_name = f"{self._marker_prefix}-{len(self._trusted_tags)}"
        provisional_html = rendered.html({marker_name: True})
        self._trusted_tags.append(
            _TrustedTag(marker_name=marker_name, provisional_html=provisional_html, final_html=final_html)
        )
        return provisional_html

    def trusted_tag_starts(self, html: str) -> frozenset[int]:
        """Locate marker-free warning-mode dependencies without changing hook input."""
        starts: set[int] = set()
        used: set[int] = set()
        for trusted in self._trusted_tags:
            if trusted.marker_name is not None:
                continue
            position = html.find(trusted.final_html)
            while position >= 0 and position in used:
                position = html.find(trusted.final_html, position + 1)
            if position < 0:
                continue
            used.add(position)
            starts.add(len(html[:position].encode()))
        return frozenset(starts)

    def descriptor(self, dependency: Dependency) -> dict[str, str | dict[str, str | bool]]:
        """Materialize one dependency descriptor without leaking a trusted-tag marker."""
        if self._compatibility_only:
            if not isinstance(dependency, Script) or type(dependency).render_json is not Dependency.render_json:
                self._record_opaque_warning(dependency)
            return dependency.render_json()
        if not isinstance(dependency, Script):
            if self._csp_mode == "warn":
                self._record_opaque_warning(dependency)
                return dependency.render_json()
            raise self._structured_dependency_error(dependency)
        rendered = self._materialize(dependency)
        self._record_rendered(rendered)
        return rendered.descriptor()

    def style_descriptor(self, dependency: Dependency) -> dict[str, str | dict[str, str | bool]]:
        """Render one stylesheet descriptor, applying an inline-style nonce when supplied."""
        if self._compatibility_only:
            if not isinstance(dependency, Style) or type(dependency).render_json is not Dependency.render_json:
                self._record_opaque_warning(dependency)
            return dependency.render_json()
        if self._nonce is None and not self._collect_integrity and self._csp_mode == "off":
            return dependency.render_json()
        if not isinstance(dependency, Style):
            if self._csp_mode == "warn":
                self._record_opaque_warning(dependency)
                return dependency.render_json()
            raise self._structured_dependency_error(dependency)
        rendered = self._materialize(dependency)
        return rendered.descriptor()

    @property
    def _compatibility_only(self) -> bool:
        return self._csp_mode == "warn" and self._nonce is None and not self._collect_integrity

    def require_strict_nonce(self, *, deps_strategy: str) -> None:
        """Require a response nonce when strict output creates active code or CSS."""
        if (
            self._csp_mode == "strict"
            and self._nonce is None
            and (self._has_executable_script or self._has_inline_style)
        ):
            raise ValueError(
                f"security_csp='strict' with deps_strategy={deps_strategy!r} emits executable scripts or inline "
                "styles and therefore requires csp_nonce from the host response."
            )

    def owned_integrity(self, resource: _OwnedResource) -> str:
        """Return SRI for a Citry-owned dynamic fetch without recording it yet."""
        if not self._collect_integrity:
            raise RuntimeError("Owned-resource integrity was requested while script integrity is disabled.")
        return _digest(resource.body, "sha384")

    def record_owned_dynamic(
        self,
        resource: _OwnedResource,
        *,
        origin_class_id: str | None = None,
    ) -> None:
        """Record a Citry-owned fetch after the structured loader that starts it."""
        if not self._collect_integrity:
            return
        digest = self.owned_integrity(resource)
        self._record(
            SerializedScriptSecurity(
                location="external",
                url=resource.url,
                digests=(digest,),
                provenance="citry-computed",
                origin_class_id=origin_class_id,
            ),
            (digest,),
        )

    def finalize(self, html: str) -> str:
        """Verify trusted tags after string hooks, then remove private markers."""
        for trusted in self._trusted_tags:
            if trusted.marker_name is None:
                continue
            count = html.count(trusted.provisional_html)
            if count != 1:
                msg = (
                    "A structured dependency tag was altered, removed, or duplicated after security attributes "
                    "were applied. Modify dependencies through on_dependencies instead of on_serialize."
                )
                raise RuntimeError(msg)
            html = html.replace(trusted.provisional_html, trusted.final_html, 1)
        if self._marker_prefix in html:
            msg = "A private dependency-security marker survived final serialization."
            raise RuntimeError(msg)
        return html

    def _materialize(self, dependency: Dependency) -> _RenderedDependency:
        if not isinstance(dependency, (Script, Style)):
            raise self._structured_dependency_error(dependency)
        cached = self._captures.get(id(dependency))
        if cached is not None and cached[0] is dependency:
            return cached[1]
        if isinstance(dependency, Script):
            rendered = self._materialize_script(dependency)
        else:
            rendered = self._materialize_style(dependency)
        self._captures[id(dependency)] = (dependency, rendered)
        return rendered

    def _materialize_script(self, dependency: Script) -> _RenderedDependency:
        tag_name, raw_attrs, content = dependency._render()
        if tag_name != "script":
            raise self._structured_dependency_error(dependency, produced=tag_name)
        attrs = _copy_exact_attrs(raw_attrs, "Script")
        _apply_nonce(attrs, self._nonce, "Script")
        self._has_executable_script = self._has_executable_script or _is_executable(attrs)
        if not self._collect_integrity:
            return _RenderedDependency(tag_name="script", attrs=attrs, content=content, is_void=False)

        declared = _take_integrity(attrs)
        resource = dependency._owned_resource
        src = _canonicalize_html_attr(attrs, "src", "Script")
        _canonicalize_html_attr(attrs, "type", "Script")

        if src is None and dependency.url is not None:
            raise ValueError("A URL-based Script must materialize a src attribute in integrity mode.")
        if src is not None and (dependency.url is None or src != dependency.url):
            raise ValueError("Set an external Script URL with Script(url=...), not through its attrs mapping.")

        if src is None:
            if declared is not None:
                msg = (
                    "Inline Script integrity attributes are not enforced by browsers. Remove the attribute "
                    "and use SerializedSecurity.csp_script_hashes for the inline content."
                )
                raise ValueError(msg)
            digest = _digest(content.encode(), "sha384")
            csp_hashes = (digest,) if _is_executable(attrs) else ()
            metadata = SerializedScriptSecurity(
                location="inline",
                url=None,
                digests=(digest,),
                provenance="citry-computed",
                origin_class_id=dependency.origin_class_id,
            )
            return _RenderedDependency(
                tag_name="script",
                attrs=attrs,
                content=content,
                is_void=False,
                metadata=metadata,
                csp_hashes=csp_hashes,
            )

        if type(src) is not str or not src:
            raise ValueError("A Script src attribute must be a non-empty string in integrity mode.")

        if resource is not None:
            if dependency.url != resource.url or src != resource.url:
                msg = (
                    "A Citry-owned Script URL changed after its authoritative response bytes were attached. "
                    "Replace it with a new Script in on_dependencies."
                )
                raise RuntimeError(msg)
            declared_tokens = () if declared is None else _parse_integrity(declared)
            for algorithm, encoded, _token, declared_bytes in declared_tokens:
                expected_bytes = hashlib.new(algorithm, resource.body).digest()
                actual = f"{algorithm}-{encoded}"
                if not hmac.compare_digest(declared_bytes, expected_bytes):
                    msg = f"Integrity value {actual!r} does not match the Citry-owned bytes at {resource.url!r}."
                    raise ValueError(msg)
            computed = _digest(resource.body, "sha384")
            declared_digests = tuple(f"{algorithm}-{encoded}" for algorithm, encoded, _, _ in declared_tokens)
            digests = declared_digests
            if not any(algorithm == "sha384" for algorithm, _, _, _ in declared_tokens):
                attrs["integrity"] = computed if declared is None else f"{declared} {computed}"
                digests = (*digests, computed)
            else:
                attrs["integrity"] = declared or computed
            provenance: Literal["citry-computed", "declared-verified"] = (
                "citry-computed" if declared is None else "declared-verified"
            )
            metadata = SerializedScriptSecurity(
                location="external",
                url=resource.url,
                digests=digests,
                provenance=provenance,
                origin_class_id=dependency.origin_class_id,
            )
            return _RenderedDependency(
                tag_name="script",
                attrs=attrs,
                content=content,
                is_void=False,
                metadata=metadata,
                csp_hashes=digests,
            )

        if declared is None:
            return _RenderedDependency(tag_name="script", attrs=attrs, content=content, is_void=False)

        declared_tokens = _parse_integrity(declared)
        digests = tuple(f"{algorithm}-{encoded}" for algorithm, encoded, _, _ in declared_tokens)
        attrs["integrity"] = declared
        metadata = SerializedScriptSecurity(
            location="external",
            url=src,
            digests=digests,
            provenance="declared-unverified",
            origin_class_id=dependency.origin_class_id,
        )
        return _RenderedDependency(
            tag_name="script",
            attrs=attrs,
            content=content,
            is_void=False,
            metadata=metadata,
            csp_hashes=digests,
        )

    def _materialize_style(self, dependency: Style) -> _RenderedDependency:
        tag_name, raw_attrs, content = dependency._render()
        if tag_name not in ("style", "link"):
            raise self._structured_dependency_error(dependency, produced=tag_name)
        attrs = _copy_exact_attrs(raw_attrs, "Style")
        if tag_name == "style":
            _apply_nonce(attrs, self._nonce, "Style")
            self._has_inline_style = True
        style_tag: Literal["style", "link"] = "style" if tag_name == "style" else "link"
        return _RenderedDependency(
            tag_name=style_tag,
            attrs=attrs,
            content=content,
            is_void=tag_name == "link",
        )

    def _record_rendered(self, rendered: _RenderedDependency) -> None:
        if rendered.metadata is not None:
            self._record(rendered.metadata, rendered.csp_hashes)

    def _record(self, metadata: SerializedScriptSecurity, csp_hashes: tuple[str, ...]) -> None:
        self._scripts.append(metadata)
        self._csp_hashes.extend(f"'{digest}'" for digest in csp_hashes)

    def _structured_dependency_error(self, dependency: Dependency, *, produced: str | None = None) -> TypeError:
        configured = (
            "csp_nonce" if self._nonce is not None and not self._collect_integrity else "serialization security"
        )
        detail = "" if produced is None else f" that produced a {produced!r} tag"
        return TypeError(
            f"Dependency entries must be structured Script objects or Style objects when {configured} is active; "
            f"got {type(dependency).__name__}{detail}. Return a structured dependency from on_dependencies."
        )

    def _record_opaque_warning(self, dependency: Dependency) -> None:
        self._csp_findings.append(
            f"{type(dependency).__name__} uses opaque dependency rendering that strict CSP cannot authenticate; "
            "return a structured Script or Style dependency"
        )


def _digest(body: bytes, algorithm: str) -> str:
    digest = hashlib.new(algorithm, body).digest()
    return f"{algorithm}-{base64.b64encode(digest).decode('ascii')}"


def _copy_exact_attrs(raw_attrs: object, owner: str) -> dict[str, str | bool]:
    if type(raw_attrs) is not dict:
        msg = f"{owner}._render() must return an exact attribute dict when serialization security is active."
        raise TypeError(msg)
    return dict(raw_attrs)


def _validate_nonce_mapping(attrs: Mapping[str, object], nonce: str, owner: str) -> None:
    aliases = [key for key in attrs if isinstance(key, str) and key.lower() == "nonce"]
    if len(aliases) > 1:
        raise ValueError(f"A {owner} cannot declare the nonce attribute more than once with different casing.")
    if not aliases:
        return
    value = attrs[aliases[0]]
    if type(value) is not str or value != nonce:
        raise ValueError(
            f"A {owner} carries a nonce that differs from this serialization call's csp_nonce. "
            "Remove the explicit attribute or pass the matching nonce."
        )


def _apply_nonce(attrs: dict[str, str | bool], nonce: str | None, owner: str) -> None:
    if nonce is None:
        return
    _validate_nonce_mapping(attrs, nonce, owner)
    aliases = [key for key in attrs if isinstance(key, str) and key.lower() == "nonce"]
    if aliases and aliases[0] != "nonce":
        attrs.pop(aliases[0])
    attrs["nonce"] = nonce


def _take_integrity(attrs: dict[str, str | bool]) -> str | None:
    value = _canonicalize_html_attr(attrs, "integrity", "Script")
    if value is None:
        return None
    if type(value) is not str or not value.strip():
        raise ValueError("A Script integrity attribute must be a non-empty string.")
    attrs.pop("integrity")
    return value


def _canonicalize_html_attr(
    attrs: dict[str, str | bool],
    name: str,
    owner: str,
) -> str | bool | None:
    aliases = [key for key in attrs if isinstance(key, str) and key.lower() == name]
    if len(aliases) > 1:
        raise ValueError(f"A {owner} cannot declare the {name} attribute more than once with different casing.")
    if not aliases:
        return None
    if aliases[0] == name:
        return attrs[name]
    value = attrs.pop(aliases[0])
    attrs[name] = value
    return value


def _parse_integrity(value: str) -> tuple[tuple[str, str, str, bytes], ...]:
    parsed: list[tuple[str, str, str, bytes]] = []
    for token in value.split():
        if "?" in token:
            raise ValueError(f"Script integrity metadata options are not supported yet: {token!r}.")
        algorithm, separator, encoded = token.partition("-")
        if separator != "-" or algorithm not in _DIGEST_LENGTHS or not encoded:
            raise ValueError(f"Unsupported or malformed Script integrity value {token!r}.")
        normalized = encoded.translate(str.maketrans("-_", "+/"))
        padded = normalized + "=" * (-len(normalized) % 4)
        try:
            decoded = base64.b64decode(padded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError(f"Malformed base64 in Script integrity value {token!r}.") from error
        canonical = base64.b64encode(decoded).decode("ascii")
        canonical_urlsafe = canonical.translate(str.maketrans("+/", "-_"))
        valid_encodings = {
            canonical,
            canonical.rstrip("="),
            canonical_urlsafe,
            canonical_urlsafe.rstrip("="),
        }
        if len(decoded) != _DIGEST_LENGTHS[algorithm] or encoded not in valid_encodings:
            raise ValueError(f"Script integrity value {token!r} has a non-canonical or wrong-length digest.")
        parsed.append((algorithm, encoded, token, decoded))
    if not parsed:
        raise ValueError("A Script integrity attribute must contain at least one digest.")
    return tuple(parsed)


def _is_executable(attrs: Mapping[str, object]) -> bool:
    """Classify a script from its browser-canonical MIME essence."""
    aliases = [key for key in attrs if isinstance(key, str) and key.translate(_ASCII_LOWER) == "type"]
    if len(aliases) > 1:
        raise ValueError("A Script cannot declare the type attribute more than once with different casing.")
    value = None if not aliases else attrs[aliases[0]]
    if value is None or isinstance(value, bool):
        return True
    if type(value) is not str:
        raise ValueError("A Script type attribute must be a string or boolean.")
    normalized = value.strip(" \t\n\r\f").translate(_ASCII_LOWER)
    essence = normalized.partition(";")[0].rstrip(" \t\n\r\f")
    if essence in {"module", "importmap", "speculationrules"}:
        return ";" not in normalized
    return essence == "" or essence in _JAVASCRIPT_MIME_TYPES
