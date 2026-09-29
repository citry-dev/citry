from itertools import count
from pathlib import Path

from citry import Citry

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DocumentIds:
    """Number component ids from 1 again in each rendered document."""

    def __init__(self) -> None:
        self._numbers = count(1)

    def restart(self) -> None:
        # Each document starts its own sequence, so unchanged inputs render
        # byte-for-byte the same file however many documents came before.
        self._numbers = count(1)

    def __call__(self) -> str:
        return f"standalone-{next(self._numbers)}"


# Citry calls this object for every component id. It is set once here, and
# `render_document()` only restarts its numbering.
document_ids = DocumentIds()

citry_app = Citry(
    autodiscover=True,
    dirs=[PROJECT_ROOT / "app" / "components"],
    id_generator=document_ids,
)
