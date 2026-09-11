Implement the task below in /workspace using the installed Citry package.
This directory is an application project. Python, Node, Git, curl, ripgrep,
pytest, and Playwright with Chromium are available.

Keep the installed dependency versions. Put the application and any tests you
write in /workspace. You may use public documentation and inspect installed
package source. Do not clone the upstream repository or search for evaluation
solutions. Use the available terminal and browser libraries to check your work.
Complete the task autonomously within the time limit. In your final response,
state what works, what you tested, and any remaining problems.

Time limit: 900 seconds.

Use https://citry.dev/.

# Render product cards

Implement `app.py` using the installed `citry==0.4.6` public API. Export
`ProductCard`, a Citry component, and `render_cards(items) -> str`. The starter
defines the input record. You may add files inside the workspace.

`render_cards` accepts a list of records with `title: str`, `price_cents: int`,
`description: str`, and optional `footer: str | None`. Prices are nonnegative
integers. Return HTML containing one `article.product-card` per record, in
input order. Each article has an `h2` title, `.price` with a dollar price such
as `$12.05`, `.description` with the description, and a `footer`.
An omitted or `None` footer shows `Available now`; an empty string stays empty.
Render every supplied string as escaped text, including titles and slot fills.
An empty list produces no cards. Calls must be independent: later calls must
not reuse another call's text or prices. Do not mutate the input records.

Give `ProductCard` a nested typed `Kwargs` schema with `title: str` and
`price_cents: int`, and a typed `Slots` schema with `default` and `footer`.
The default slot supplies the description; the footer slot overrides the
fallback. Direct Python composition must work:

```python
str(ProductCard(
    title="Notebook",
    price_cents=1205,
    slots={"default": "Plain paper", "footer": "In stock"},
))
```

Use Citry templates and slots for the rendered cards. Add simple styling
through component CSS. Visual polish has no numeric score; the executable
checks cover the exported component contract and rendered HTML.

The evaluator imports `app` from the workspace. It may vary all input text,
prices, item counts, and consecutive calls. Keep dependencies at their
preinstalled versions. Finish by briefly describing what you implemented and
which checks you ran.
