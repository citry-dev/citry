import os

from citry import Citry

secret = os.environ.get("CITRY_SECRET")
if not secret:
    raise RuntimeError("Set CITRY_SECRET before starting the app.")

citry_app = Citry(autodiscover=False, secret=secret)
