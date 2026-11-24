r"""
Check that a URL from the request stays on this site before a handler redirects to it.

A login handler often sends the visitor on to a ``next`` URL that arrived
with the request. Anyone can write that URL, so without a check a link to
your login page can send visitors to another site. ``is_local_url()``
answers whether a browser would load the URL from this site, and
``local_url_or()`` swaps a URL that fails the check for a fixed one.

The check reads the URL the way a browser does, not the way
``urllib.parse`` does: a browser reads ``\`` like ``/`` and loads
``//other.example`` from another site, so a prefix check such as
``url.startswith("/")`` lets both through. The rules follow Django's
``url_has_allowed_host_and_scheme``, but Django is not needed.
"""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

from citry._urls import url_scheme

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = ["is_local_url", "local_url_or"]

# Lowercase A to Z only, as the browser does for an ASCII host. str.lower()
# also changes non-ASCII letters, which the browser's IDNA mapping may map
# differently.
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def is_local_url(
    url: str | None,
    *,
    allowed_hosts: Iterable[str] = (),
    require_https: bool = False,
) -> bool:
    r"""
    Return whether a browser would load ``url`` from this site.

    Use it before you redirect to a URL that came from the request, such
    as a ``next`` parameter after a login. Anyone can write that URL, so
    without a check a link to your site can send visitors to another one.

    The URL passes when it is relative, such as ``/orders/7``,
    ``?page=2`` or ``next``, or when it is an absolute ``http:`` or
    ``https:`` URL whose host is in ``allowed_hosts``. A URL that starts
    with ``//`` names a host just like an absolute URL. The check reads
    the URL as a browser does, so ``/\other.example`` and
    ``\\other.example`` fail: the browser reads ``\`` as ``/`` and loads
    them from ``other.example``.

    These URLs also fail:

    - an empty URL, ``None``, or one that is only spaces;
    - a URL with a control character anywhere in it, including a tab or
      a newline. [`Redirect`][citry.ext.events.actions.Redirect] refuses
      these too;
    - whitespace other than a space at either end, such as a no-break
      space. Plain spaces at either end are fine;
    - an invisible character at the start, such as a zero-width space;
    - any scheme other than ``http:`` and ``https:``, such as
      ``javascript:`` or ``data:``;
    - ``http:`` or ``https:`` without ``//`` after the colon, such as
      ``https:next``: a browser on a page with the other scheme reads
      ``next`` as a host name;
    - a host that starts with a third slash, such as
      ``///other.example`` or ``https:///other.example``: the browser
      skips the extra slashes and loads ``other.example``;
    - a host with a user name or password, such as
      ``https://me@shop.example/``.

    The host is compared with each entry of ``allowed_hosts`` as text.
    Upper and lower case ASCII letters match, but nothing else is
    rewritten: a port must match (``shop.example:8000``), and a trailing
    dot or an internationalized name in another spelling does not match,
    so list each spelling you accept. Any string gives ``True`` or
    ``False``, so request data cannot crash the handler; a malformed
    host such as ``http://[::1`` fails because it is not in
    ``allowed_hosts``.

    Args:
        url: The URL to check, usually taken from the request.
            ``None`` gives ``False``.
        allowed_hosts: The hosts an absolute URL may name, such as
            ``{"shop.example"}``. Write a port as part of the name, such
            as ``"shop.example:8000"``. A single string counts as one
            host. Each entry is a host exactly as a URL writes it, so
            ``"*"``, a leading-dot wildcard such as ``".shop.example"``,
            or an entry with a scheme never matches. When it is empty,
            only relative URLs pass. It must be iterable; ``None``
            raises ``TypeError``.
        require_https: Also refuse ``http:`` URLs and URLs that start
            with ``//``, even on an allowed host. Set it when your site
            is served over HTTPS, so a redirect cannot drop to plain
            HTTP.

    Returns:
        ``True`` when a browser would load the URL from this site.

    Raises:
        TypeError: If ``url`` is neither a string nor ``None``, or an
            entry of ``allowed_hosts`` is not a string. That is a bug in
            the calling code, not bad input from the request.

    Example:
        ```python
        from citry.ext.events import actions, is_local_url


        class Events:
            def login(self, data: LoginIn, request):
                log_in(request, data)
                if is_local_url(data.next):
                    return actions.Redirect(data.next)
                return actions.Redirect("/")
        ```

    """
    return _is_local(url, _host_set(allowed_hosts), require_https=require_https)


def local_url_or(
    url: str | None,
    fallback: str = "/",
    *,
    allowed_hosts: Iterable[str] = (),
    require_https: bool = False,
) -> str:
    """
    Return ``url`` when a browser would load it from this site, and ``fallback`` otherwise.

    This is [`is_local_url()`][citry.ext.events.is_local_url] in the
    form a redirect needs: pass the URL from the request and redirect to
    whatever comes back. The URL is returned as given, so a URL that
    passes keeps its spaces and case.

    ``fallback`` must pass the same check, or the call raises
    ``ValueError`` even when ``url`` passes. A mistyped fallback then
    fails in your first test, rather than sending visitors to another
    site only when the request carries a bad URL.

    Args:
        url: The URL to check, usually taken from the request.
            ``None`` gets the fallback.
        fallback: The URL to return when ``url`` fails the check.
            Defaults to ``"/"``.
        allowed_hosts: The hosts an absolute URL may name, as in
            [`is_local_url()`][citry.ext.events.is_local_url].
        require_https: Also refuse ``http:`` URLs and URLs that start
            with ``//``, as in
            [`is_local_url()`][citry.ext.events.is_local_url].

    Returns:
        ``url`` when it passes the check, otherwise ``fallback``.

    Raises:
        ValueError: If ``fallback`` fails the check itself.
        TypeError: If ``url`` is neither a string nor ``None``,
            ``fallback`` is neither a string nor ``None``, or an entry
            of ``allowed_hosts`` is not a string. A ``None`` fallback
            raises ``ValueError``, since it fails the check.

    Example:
        ```python
        from citry.ext.events import actions, local_url_or


        class Events:
            def login(self, data: LoginIn, request):
                log_in(request, data)
                return actions.Redirect(
                    local_url_or(
                        data.next,
                        "/account/",
                        allowed_hosts={"shop.example"},
                        require_https=True,
                    )
                )
        ```

    """
    # Read the hosts once: a generator passed as allowed_hosts would be
    # empty by the second check.
    hosts = _host_set(allowed_hosts)
    # Check the fallback on every call, not only when it is used, so a bad
    # one shows up the first time the handler runs.
    if not _is_local(fallback, hosts, require_https=require_https):
        msg = (
            f"local_url_or: the fallback {fallback!r} does not stay on this site under the same"
            " check. Pass a path such as '/' or an absolute URL on one of allowed_hosts."
        )
        raise ValueError(msg)
    if url is not None and _is_local(url, hosts, require_https=require_https):
        return url
    return fallback


def _host_set(allowed_hosts: Iterable[str]) -> frozenset[str]:
    """Return the allowed hosts with ASCII letters lowercased, ready for a lookup."""
    # A single string is one host, as in Django. Iterating it would allow
    # each of its characters as a host.
    hosts = (allowed_hosts,) if isinstance(allowed_hosts, str) else tuple(allowed_hosts)
    for host in hosts:
        if not isinstance(host, str):
            msg = f"allowed_hosts must hold host names as strings; got {host!r}."
            raise TypeError(msg)
    return frozenset(host.translate(_ASCII_LOWER) for host in hosts)


def _is_local(url: str | None, hosts: frozenset[str], *, require_https: bool) -> bool:
    """Check ``url`` against hosts already prepared by ``_host_set``."""
    if url is None:
        return False
    if not isinstance(url, str):
        msg = f"The URL to check must be a string or None; got {type(url).__name__}."
        raise TypeError(msg)
    # A browser drops tab, CR and LF anywhere, which can hide "//" inside a
    # URL, and Redirect refuses every ASCII control character, so
    # local_url_or must never return one. The C1 controls (U+0080 to
    # U+009F) are refused too, so "a control character" means every one.
    if any(ord(char) < 0x20 or 0x7F <= ord(char) <= 0x9F for char in url):
        return False
    # With controls refused, the browser strips only ASCII spaces from both
    # ends, so check the text it reads.
    stripped = url.strip(" ")
    if not stripped:
        return False
    # Other whitespace at either end, such as U+3000, stays part of the URL
    # for the browser but not for Python's strip(), which Django uses. Chromium
    # reads "//shop.example\u3000" as a host other than shop.example, so a
    # URL whose ends the two read differently fails.
    if stripped != stripped.strip():
        return False
    # Django refuses a URL that starts with any Unicode control or format
    # character, because some browsers have skipped such characters at the
    # start and then read "//" after them as a host. Keep the same rule.
    if unicodedata.category(stripped[0]).startswith("C"):
        return False
    # Browsers read "\" as "/" in http and https URLs and in relative URLs
    # on an http or https page, so "/\other.example" names a host.
    normalized = stripped.replace("\\", "/")

    # The same scheme reader as Redirect and the output checks, so a URL
    # reads the same here as everywhere else on the server.
    scheme = url_scheme(normalized)
    if scheme is not None:
        allowed_schemes = ("https",) if require_https else ("http", "https")
        if scheme not in allowed_schemes:
            return False
        authority_start = len(scheme) + 1
        # "https:next" is relative on an https page but names the host
        # "next" on an http page, and the browser skips any extra slashes
        # before a host, so only "scheme://host" can be checked safely.
        if not normalized.startswith("//", authority_start):
            return False
        return _authority_allowed(stripped, normalized, authority_start + 2, hosts)
    if normalized.startswith("//"):
        # The browser fills in the page's own scheme, which may be http.
        if require_https:
            return False
        return _authority_allowed(stripped, normalized, 2, hosts)
    # No scheme and no host: a path, query or fragment on this site.
    return True


def _authority_allowed(stripped: str, normalized: str, start: int, hosts: frozenset[str]) -> bool:
    r"""
    Return whether the host that starts at ``start`` is one of ``hosts``.

    ``normalized`` is ``stripped`` with ``\`` read as ``/``; both have the
    same length, so ``start`` points at the host in each.
    """
    # The browser skips every slash before the host, so "///other.example"
    # loads other.example. Django refuses these, and so does this check.
    if normalized.startswith("/", start):
        return False
    authority = _until_delimiter(normalized, start)
    # A user name before "@" hides the real host after it. Look for "@" in
    # the text where "\" is not yet a delimiter too, as Django does, so a
    # client that reads "\" literally cannot find a host there either.
    if "@" in _until_delimiter(stripped, start):
        return False
    # An empty host fails in the browser; it never names this site.
    if not authority:
        return False
    return authority.translate(_ASCII_LOWER) in hosts


def _until_delimiter(text: str, start: int) -> str:
    """Return the text from ``start`` up to the first ``/``, ``?`` or ``#``."""
    end = len(text)
    for delimiter in "/?#":
        found = text.find(delimiter, start)
        if found != -1:
            end = min(end, found)
    return text[start:end]
