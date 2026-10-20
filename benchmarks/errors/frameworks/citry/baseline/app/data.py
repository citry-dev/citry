from dataclasses import dataclass

# The browser receives API_BASE; SECRET_TOKEN stays on the server.
API_BASE = "/api"
SECRET_TOKEN = "s3cr3t"


@dataclass(frozen=True, slots=True)
class Owner:
    name: str


@dataclass(frozen=True, slots=True)
class Project:
    title: str
    count: int
    slug: str
    # The page draws a featured project's card with the accent border.
    featured: bool


OWNER = Owner("Ada")

# Open tasks per project, as the task store reports them.
TASK_COUNTS = {"Alpha": 3, "Beta": 5, "Gamma": 8}

PROJECTS = tuple(
    Project(title, count, title.lower(), featured=title == "Alpha") for title, count in TASK_COUNTS.items()
)
