"""Build the Flask app once, so importing this module gives a ready app."""

from app import create_app
from app.citry_app import citry_app

# create_app() mounts Citry, and mounting lets `citry check` and the editor
# ask Flask which pages and static files it serves. The check's `--app`
# option and the editor's `citry.app` setting both import this module, so
# the factory must run here for links to be checked.
# A production WSGI server can serve `web_app` from here as well.
web_app = create_app()

# Re-export `citry_app` on purpose: `citry check` looks it up in this module by name.
__all__ = ["citry_app", "web_app"]
