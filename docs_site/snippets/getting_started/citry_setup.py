import os

from citry import Citry

# New in this step: create one Citry instance for the whole app.
secret = os.environ.get("CITRY_SECRET")
if not secret:
    msg = "Set CITRY_SECRET before starting the app."
    raise RuntimeError(msg)

citry_app = Citry(secret=secret)
