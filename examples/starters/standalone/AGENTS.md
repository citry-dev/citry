# Agent instructions for the Citry standalone starter

- Read [README.md](README.md) first. It owns installation, run commands,
  environment setup, and production guidance. Run commands from this directory.
- Use [Citry's documentation index](https://citry.dev/llms.txt) to find the
  relevant guide and API reference before changing Citry behavior.
- Check the Citry requirement in `pyproject.toml`, the version in `uv.lock`,
  and the installed version before using a documented API. Choose documentation
  compatible with that version and verify uncertain behavior in a small test.
- Use public `citry` APIs and follow the existing component patterns.
  Keep explicit `Kwargs` and `Slots` schemas and typed component inputs.
- Start with `app/render.py` for the render command, `app/citry_app.py`
  for Citry setup, `app/components/` for components, and `app/data.py` for data.
- Keep the generated document self-contained. Alpine interactions run locally;
  Python finishes when the render command exits.
- Keep secrets and private data out of rendered HTML and browser data.
- After changes, follow the README environment setup, run
  `uv run citry --app app.citry_app:citry_app check`, then run `uv run pytest`
  (tests live in `tests/test_standalone.py`) and `uv run python -m app.render`
  to produce `_build/index.html`.
- For template, CSS, or browser behavior changes, open `_build/index.html`
  in a browser. Check the help button, rendered layout, console errors, and
  that the page works without network requests.
- Keep this file current when project paths or commands change. See the
  [AI agent setup guide](https://citry.dev/getting-started/ai-agents/)
  for configuring your coding tool.
