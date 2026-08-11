"""Public errors raised by Citry's built-in i18n extension."""


class I18nError(Exception):
    """Base class for i18n errors."""


class I18nNotConfiguredError(I18nError):
    """Raised when configured i18n behavior is used on a dormant engine."""


class I18nRuntimeUnavailableError(I18nError):
    """Raised for an API whose production runtime has not been installed yet."""
