from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Project:
    name: str
    summary: str
    status: str
    language: str


PROJECTS = (
    Project(
        name="Atlas",
        summary="Turn field research into a searchable knowledge base.",
        status="In review",
        language="Python",
    ),
    Project(
        name="Beacon",
        summary="Track service health and make incident handoffs calmer.",
        status="Active",
        language="TypeScript",
    ),
    Project(
        name="Canopy",
        summary="Give community gardens one shared seasonal plan.",
        status="Planning",
        language="Python",
    ),
    Project(
        name="Drift",
        summary="Compare design revisions without losing decisions.",
        status="Active",
        language="Rust",
    ),
    Project(
        name="Ember",
        summary="Coordinate small grants from application to outcome.",
        status="In review",
        language="Python",
    ),
    Project(
        name="Fathom",
        summary="Explain product metrics in language teams can act on.",
        status="Planning",
        language="SQL",
    ),
)


def find_projects(query: str = "") -> tuple[Project, ...]:
    """Return deterministic project records matching a user query."""
    normalized = query.strip().casefold()
    if not normalized:
        return PROJECTS
    return tuple(
        project
        for project in PROJECTS
        if normalized
        in " ".join(
            (
                project.name,
                project.summary,
                project.status,
                project.language,
            )
        ).casefold()
    )
