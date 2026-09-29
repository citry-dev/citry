from pathlib import Path

from app.citry_app import citry_app, document_ids
from app.components.project_page import ProjectPage
from app.data import find_projects

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "_build" / "index.html"


def render_document() -> str:
    """Render the page with its CSS and JavaScript embedded in the HTML."""
    # Restart the id numbering so unchanged inputs produce the same output.
    document_ids.restart()
    citry_app.initialize()
    page = ProjectPage(projects=find_projects())
    return page.render().serialize(deps_strategy="document")


def write_document(output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_document(), encoding="utf-8")
    return output


def main() -> None:
    output = write_document()
    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
