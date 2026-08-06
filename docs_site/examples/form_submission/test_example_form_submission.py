"""Render the form-submission example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_form_submission_example_page_renders() -> None:
    html = str(get_example_registry()["form_submission"].page_cls())
    # The contact form renders its input and submit button.
    assert 'placeholder="Ada Lovelace"' in html
    assert '<button class="contact-form__button" type="submit">Submit</button>' in html
    assert 'class="contact-form__result" role="status" aria-live="polite"' in html
