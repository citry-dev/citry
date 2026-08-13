"""Small public helpers for explicit i18n use outside components."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from citry.citry import Citry

    from .context import LocaleContext
    from .extension import I18nExtension


def make_context(
    app: Citry,
    *,
    locale: str | None = None,
    time_zone: str | None = None,
) -> LocaleContext:
    """
    Create a locale context for one Citry application.

    The application argument keeps the owning engine explicit while hiding
    the extension-registry lookup needed to reach its i18n extension. The
    returned context does not change application, task, or process state.

    Args:
        app: The Citry application that owns the i18n configuration.
        locale: A configured or inferred source locale, or ``None`` to use the
            configured or inferred default locale.
        time_zone: An IANA time-zone name, or ``None`` for a zone-free context.

    Returns:
        A validated immutable locale context for that application.

    Raises:
        I18nNotConfiguredError: The application has neither i18n settings nor
            registered component messages.
        ValueError: A locale or time-zone value is invalid or unavailable.

    Example:
        ```python
        from citry.ext.i18n import make_context

        context = make_context(app, locale=request.locale)
        html = Page().render(provides={"citry_i18n": context})
        ```

    """
    extension = cast("I18nExtension", app.extensions.get_extension("i18n"))
    return extension.make_context(locale=locale, time_zone=time_zone)
