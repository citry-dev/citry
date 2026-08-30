from pathlib import Path

from citry import Citry
from citry.contrib.django import secret

PROJECT_ROOT = Path(__file__).resolve().parents[1]

citry_app = Citry(
    autodiscover=True,
    dirs=[PROJECT_ROOT / "project_explorer" / "components"],
    secret=secret(),
)
