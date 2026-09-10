# Agent instructions for the Citry Flask starter

- Read [README.md](README.md) first. It owns installation, run commands,
  environment setup, and production guidance. Run commands from this directory.
- Use [Citry's documentation index](https://citry.dev/llms.txt) to find the
  relevant guide and API reference before changing Citry behavior.
- Check the Citry requirement in `pyproject.toml`, the version in `uv.lock`,
  and the installed version before using a documented API. Choose documentation
  compatible with that version and verify uncertain behavior in a small test.
- Use public `citry` APIs and follow the existing component patterns.
  Keep explicit `Kwargs` and `Slots` schemas and typed component inputs.
- Start with `app/__init__.py` for the app factory, `app/citry_app.py`
  for Citry setup, `app/components/` for components, and `app/data.py` for data.
- Keep the shared Citry instance mounted under `/citry` and initialized
  before `create_app()` returns.
- Follow the README to set `CITRY_SECRET` before starting the server.
  The app reads the environment directly; `.env.example` records its setup.
- Treat `State` as browser input. Keep secrets on the server and check
  authorization before returning private data or performing writes.
- After changes, follow the README environment setup, run
  `uv run citry --app app.citry_app:citry_app check`, then run `uv run pytest`.
  The local tests live in `tests/test_app.py`.
- For template, CSS, Events, or host changes, run the README server command
  and check the page in a browser. Verify the help button, search results,
  input focus, and browser console and network errors.
- Keep this file current when project paths or commands change. See the
  [AI agent setup guide](https://citry.dev/getting-started/ai-agents/)
  for configuring your coding tool.
