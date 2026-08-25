from itertools import count
from pathlib import Path

from .citry_app import citry_app
from .components import ProjectPage
from .data import find_projects

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "_build" / "index.html"


def render_document() -> str:
    """Render the page with its CSS and JavaScript embedded in the HTML."""
    # Start a fresh ID sequence for each document so unchanged inputs produce the same output.
    render_ids = count(1)
    citry_app.id_generator = lambda: f"standalone-{next(render_ids)}"
    citry_app.initialize()
    return ProjectPage(projects=find_projects()).render().serialize(deps_strategy="document")


def write_document(output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_document(), encoding="utf-8")
    return output


def main() -> None:
    output = write_document()
    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
