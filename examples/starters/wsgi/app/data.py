from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Project:
    name: str
    summary: str
    status: str
    language: str


PROJECTS = (
    Project("Atlas", "Turn field research into a searchable knowledge base.", "In review", "Python"),
    Project("Beacon", "Track service health and make incident handoffs calmer.", "Active", "TypeScript"),
    Project("Canopy", "Give community gardens one shared seasonal plan.", "Planning", "Python"),
    Project("Drift", "Compare design revisions without losing decisions.", "Active", "Rust"),
    Project("Ember", "Coordinate small grants from application to outcome.", "In review", "Python"),
    Project("Fathom", "Explain product metrics in language teams can act on.", "Planning", "SQL"),
)


def find_projects(query: str = "") -> tuple[Project, ...]:
    """Stand in for an authorized database query with deterministic data."""
    normalized = query.strip().casefold()
    if not normalized:
        return PROJECTS
    return tuple(
        project
        for project in PROJECTS
        if normalized in " ".join((project.name, project.summary, project.status, project.language)).casefold()
    )
