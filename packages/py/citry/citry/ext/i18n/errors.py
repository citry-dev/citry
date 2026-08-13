"""Public errors raised by Citry's built-in i18n extension."""


class I18nError(Exception):
    """Base class for i18n errors."""


class I18nNotConfiguredError(I18nError):
    """Raised when an i18n operation needs settings or messages that are absent."""


class I18nRuntimeUnavailableError(I18nError):
    """Raised when the requested i18n operation cannot run in the current context."""
