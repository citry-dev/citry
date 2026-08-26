from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Project:
    name: str
    summary: str
    status: str
    language: str


PROJECTS = (
    Project("Atlas", "Organize field notes and make them easy to search.", "In review", "Python"),
    Project("Beacon", "Track service health and hand off incidents between teams.", "Active", "TypeScript"),
    Project("Canopy", "Plan each season across a network of community gardens.", "Planning", "Python"),
    Project("Drift", "Compare design revisions and keep decisions with the work.", "Active", "Rust"),
    Project("Ember", "Manage small grants from application through reporting.", "In review", "Python"),
    Project("Fathom", "Turn product metrics into explanations teams can use.", "Planning", "SQL"),
)


def find_projects(query: str = "") -> tuple[Project, ...]:
    """Return sample projects whose visible fields contain the query."""
    normalized = query.strip().casefold()
    if not normalized:
        return PROJECTS
    return tuple(
        project
        for project in PROJECTS
        if normalized in " ".join((project.name, project.summary, project.status, project.language)).casefold()
    )
