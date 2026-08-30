from pathlib import Path

from citry import Citry

PROJECT_ROOT = Path(__file__).resolve().parents[1]

citry_app = Citry(
    autodiscover=True,
    dirs=[PROJECT_ROOT / "app" / "components"],
)
