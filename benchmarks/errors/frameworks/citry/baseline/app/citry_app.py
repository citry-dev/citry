import os
from pathlib import Path

from citry import Citry

PROJECT_ROOT = Path(__file__).resolve().parents[1]

secret = os.environ.get("CITRY_SECRET")
if not secret:
    raise RuntimeError("Set CITRY_SECRET before starting the app.")

citry_app = Citry(
    autodiscover=True,
    dirs=[PROJECT_ROOT / "app" / "components"],
    secret=secret,
)
