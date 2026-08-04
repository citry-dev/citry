from citry_core import _rust


def parse_diagnostic(error: BaseException) -> _rust.template_parser.ParseDiagnostic | None:
    """
    Return the structured details attached to a template parse failure.

    Parser failures remain ordinary ``SyntaxError`` or ``ValueError``
    instances. This helper provides typed access to their stable diagnostic
    code and root-template UTF-8 byte range. Errors raised before template
    parsing, such as an unsupported language value, return ``None``.

    Args:
        error: An exception raised while calling [`parse_template`]
            [citry_core.template_parser.parse_template].

    Returns:
        The attached parse diagnostic, or ``None`` when the exception did not
        come from the template parser.

    """
    diagnostic = getattr(error, "diagnostic", None)
    if isinstance(diagnostic, _rust.template_parser.ParseDiagnostic):
        return diagnostic
    return None


def parse_template(
    input: str,
    lang: str | None = None,
    user_rules: dict[str, _rust.template_parser.TagRules] | None = None,
) -> _rust.template_parser.Template:
    """
    Parse a Citry template string into a Template AST.

    Args:
        input: The template string to parse.
        lang: Expression language. One of "python" (default), "js", "php",
            "go", "rust".
        user_rules: Optional dict mapping tag names to TagRules for custom
            attribute/slot validation. Keys must be lowercase tag names
            (e.g. ``"c-my-card"``); tags in the template match the rules
            case-insensitively.

    Returns:
        The parsed Template AST.

    Raises:
        SyntaxError: If the template has invalid syntax. Pass the exception to
            [`parse_diagnostic`][citry_core.template_parser.parse_diagnostic]
            for its stable code and UTF-8 byte range.
        ValueError: If an unknown language is specified.

    Examples:
        Basic parsing::

            from citry_core.template_parser import parse_template

            t = parse_template('<p>{{ name }}</p>')
            print(t.used_variables)  # [Token(content='name', ...)]

        With custom tag validation rules::

            from citry_core.template_parser import parse_template, TagRules

            rules = {
                "c-card": TagRules(
                    allowed_attrs=[["title", "c-title"]],
                    required_attrs=[["title", "c-title"]],
                ),
            }
            t = parse_template('<c-card title="Hello"></c-card>', user_rules=rules)

    """
    return _rust.template_parser.parse_template(input, lang, user_rules)
