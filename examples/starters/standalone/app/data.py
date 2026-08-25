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
        summary="Organize field notes and make them easy to search.",
        status="In review",
        language="Python",
    ),
    Project(
        name="Beacon",
        summary="Track service health and hand off incidents between teams.",
        status="Active",
        language="TypeScript",
    ),
    Project(
        name="Canopy",
        summary="Plan each season across a network of community gardens.",
        status="Planning",
        language="Python",
    ),
    Project(
        name="Drift",
        summary="Compare design revisions and keep decisions with the work.",
        status="Active",
        language="Rust",
    ),
    Project(
        name="Ember",
        summary="Manage small grants from application through reporting.",
        status="In review",
        language="Python",
    ),
    Project(
        name="Fathom",
        summary="Turn product metrics into explanations teams can use.",
        status="Planning",
        language="SQL",
    ),
)


def find_projects(query: str = "") -> tuple[Project, ...]:
    """Return sample projects whose visible fields contain the query."""
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
