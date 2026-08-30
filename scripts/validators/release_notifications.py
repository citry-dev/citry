"""Keep every GitHub Release publisher assigned to one Discord channel."""

from pathlib import Path

from discord_release import RELEASE_ROUTES

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
NOTIFIER = WORKFLOWS / "repo--discord-release.yml"
DISPATCH_EVENT = "citry-release-published"


def check() -> list[str]:
    """Return every release-notification routing problem."""
    problems: list[str] = []
    release_workflows = {
        path.name
        for path in WORKFLOWS.glob("*--publish.yml")
        if "gh release create" in path.read_text(encoding="utf-8")
    }
    routed_workflows = {route.workflow for route in RELEASE_ROUTES}
    if release_workflows != routed_workflows:
        missing = sorted(release_workflows - routed_workflows)
        stale = sorted(routed_workflows - release_workflows)
        problems.append(f"Discord release routes differ from publishers: missing={missing}, stale={stale}")

    prefixes = [route.tag_prefix for route in RELEASE_ROUTES]
    if len(prefixes) != len(set(prefixes)):
        problems.append("Discord release routes contain duplicate tag prefixes")

    for route in RELEASE_ROUTES:
        workflow_path = WORKFLOWS / route.workflow
        if not workflow_path.is_file():
            continue
        workflow = workflow_path.read_text(encoding="utf-8")
        tag_pattern = f'- "{route.tag_prefix}*"'
        if tag_pattern not in workflow:
            problems.append(f"{route.workflow} must publish tags matching {tag_pattern}")
        if workflow.count(f"event_type={DISPATCH_EVENT}") != 1:
            problems.append(f"{route.workflow} must dispatch one {DISPATCH_EVENT} notification")
        if workflow.count("client_payload[tag]=$GITHUB_REF_NAME") != 1:
            problems.append(f"{route.workflow} must identify its released tag in the notification dispatch")

    notifier = NOTIFIER.read_text(encoding="utf-8")
    for marker in (
        "repository_dispatch:",
        f"types: [{DISPATCH_EVENT}]",
        "workflow_dispatch:",
        "DISCORD_WEBHOOK_ANNOUNCEMENTS",
        "DISCORD_WEBHOOK_DEVELOPMENT",
        "scripts/discord_release.py route",
        "scripts/discord_release.py payload",
    ):
        if marker not in notifier:
            problems.append(f"Discord release notifier is missing {marker!r}")
    return problems
