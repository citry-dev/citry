"""Check exact canonical project state after every browser action."""

# These assertions also run without pytest in the standalone benchmark runner.
# ruff: noqa: S101

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page, Request


CANONICAL_OUTPUT_COUNT = 14
FILTER_QUERY = "Lorem ipsum 12"
PHASE_TYPES = ("PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4", "PHASE_5")


def _source() -> dict[str, Any]:
    return json.loads(Path(__file__).with_name("canonical_project.json").read_text())["data"]


def initial_expected(count: int) -> dict[str, Any]:
    """Build the oracle from frozen data without calling the application model."""
    if count not in (14, 140, 1400):
        raise ValueError("count must be 14, 140 or 1400 outputs")
    source = _source()
    scale = count // CANONICAL_OUTPUT_COUNT
    templates = {item["pk"]: item["fields"] for item in source["phase_templates"]}
    phases_by_type = {templates[item["fields"]["phase_template"]]["type"]: item["pk"] for item in source["phases"]}
    phase_order = [phases_by_type[phase_type] for phase_type in PHASE_TYPES]
    # Browser arguments require object keys to be strings. The production model
    # remains free to use integer phase IDs internally.
    phase_titles = {str(phases_by_type[kind]): source["phase_titles"][kind] for kind in PHASE_TYPES}
    source_outputs = {item[0]["pk"]: item[0] for item in source["outputs"]}
    ordered = [
        (replica, item)
        for phase_id in phase_order
        for replica in range(scale)
        for item in source["outputs"]
        if item[0]["fields"]["phase"] == phase_id
    ]
    output_ids = {(replica, item[0]["pk"]): row_id for row_id, (replica, item) in enumerate(ordered, 1)}
    rows = []
    attachment_id = 1
    for row_id, (replica, (output, attachments, dependencies)) in enumerate(ordered, 1):
        fields = output["fields"]
        normalized_attachments = []
        for attachment, tags in attachments:
            normalized_attachments.append(
                {
                    "id": attachment_id,
                    "name": attachment["fields"]["text"],
                    "url": attachment["fields"]["url"],
                    "tags": [str(tag) for tag in tags],
                }
            )
            attachment_id += 1
        normalized_dependencies = []
        for dependency, _metadata in dependencies:
            dependency_fields = source_outputs[dependency["pk"]]["fields"]
            normalized_dependencies.append(
                {
                    "id": output_ids[(replica, dependency["pk"])],
                    "title": dependency_fields["name"],
                    "completed": bool(dependency_fields["completed"]),
                }
            )
        completed = bool(fields["completed"])
        rows.append(
            {
                "id": row_id,
                "source_id": output["pk"],
                "title": fields["name"],
                "status": "done" if completed else "open",
                "completed": completed,
                "description": fields["description"],
                "phase_id": fields["phase"],
                "attachments": normalized_attachments,
                "dependencies": normalized_dependencies,
                "selected": False,
            }
        )

    users = {item["pk"]: item["fields"] for item in source["users"]}
    note_tabs = []
    note_id = 1
    comment_id = 1
    for tab_number in range(1, 4):
        notes = []
        for _replica in range(scale):
            for note in source[f"notes_{tab_number}"]:
                comments = []
                for comment in source[f"comments_by_notes_{tab_number}"].get(str(note["pk"]), []):
                    fields = comment["fields"]
                    author = users.get(fields["modified_by"], source["users"][0]["fields"])["name"]
                    comments.append(
                        {
                            "id": comment_id,
                            "text": fields.get("text", fields.get("notes", "")),
                            "author": author,
                        }
                    )
                    comment_id += 1
                notes.append({"id": note_id, "text": note["fields"]["text"], "comments": comments})
                note_id += 1
        note_tabs.append({"id": f"notes-{tab_number}", "title": f"Notes {tab_number}", "notes": notes})

    roles = []
    role_id = 1
    for _replica in range(scale):
        for role in source["roles_with_users"]:
            fields = role["fields"]
            roles.append({"id": role_id, "name": fields["name"], "user_name": users[fields["user"]]["name"]})
            role_id += 1
    project_fields = source["project"]["fields"]
    organizations = {item["pk"]: item["fields"] for item in source["organizations"]}
    project = {
        "id": source["project"]["pk"],
        "name": project_fields["name"],
        "status": project_fields["status"],
        "start_date": project_fields["start_date"],
        "end_date": project_fields["end_date"],
        "organization": organizations[project_fields["organization"]]["name"],
    }
    return {
        "rows": rows,
        "phase_order": phase_order,
        "phase_titles": phase_titles,
        "project": project,
        "note_tabs": note_tabs,
        "roles": roles,
        "bookmarks": [
            {"id": replica + 1, "text": "Test bookmark", "url": "/bookmarks/9/create"} for replica in range(scale)
        ],
        "contacts": list(source["contacts"]),
        "status_updates": list(source["status_updates"]),
        "project_tags": list(source["project_tags"]),
        "title": project["name"],
        "title_input": project["name"],
        "query": "",
        "error": "",
        "notice": "",
        "next_id": count + 1,
        "inserted": 0,
    }


def expected_after(previous: dict[str, Any], name: str) -> dict[str, Any]:
    """Describe the next state without calling the application model."""
    result = deepcopy(previous)
    if name == "select":
        for row in result["rows"]:
            row["selected"] = row["id"] == 1
    elif name in ("filter", "clear-filter"):
        result["query"] = FILTER_QUERY if name == "filter" else ""
    elif name == "invalid-save":
        result.update(error="Use between 3 and 80 characters.", notice="", title_input="")
    elif name == "save":
        result.update(title="Reviewed project", title_input="Reviewed project", error="", notice="Saved on server.")
        result["project"]["name"] = "Reviewed project"
    elif name == "insert":
        row_id = result["next_id"]
        result["rows"].append(
            {
                "id": row_id,
                "source_id": None,
                "title": f"New output {row_id:04d}",
                "status": "open",
                "completed": False,
                "description": "",
                "phase_id": result["phase_order"][-1],
                "attachments": [],
                "dependencies": [],
                "selected": False,
            }
        )
        result["inserted"] = row_id
        result["next_id"] += 1
    elif name == "reorder":
        result["rows"].reverse()
        result["phase_order"].reverse()
    elif name == "remove":
        result["rows"] = [row for row in result["rows"] if row["id"] != result["inserted"]]
        result["inserted"] = 0
    elif name != "probe":
        raise ValueError(f"Unknown scenario action: {name}")
    return result


def expected_view(expected: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in expected["rows"] if expected["query"].casefold() in row["title"].casefold()]
    grouped = {phase_id: [] for phase_id in expected["phase_order"]}
    for row in rows:
        grouped[row["phase_id"]].append(row)
    return {
        "rows": rows,
        "phase_groups": [
            {"id": phase_id, "title": expected["phase_titles"][str(phase_id)], "outputs": grouped[phase_id]}
            for phase_id in expected["phase_order"]
        ],
        "project": expected["project"],
        "note_tabs": expected["note_tabs"],
        "roles": expected["roles"],
        "bookmarks": expected["bookmarks"],
        "contacts": expected["contacts"],
        "status_updates": expected["status_updates"],
        "project_tags": expected["project_tags"],
        "title": expected["title"],
        "title_input": expected["title_input"],
        "query": expected["query"],
        "error": expected["error"],
        "notice": expected["notice"],
        "visible_count": len(rows),
        "total_count": len(expected["rows"]),
    }


def capture_view(page: Page) -> dict[str, Any]:
    return page.evaluate("() => window.__citryBench.semanticSnapshot()")


def assert_view(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    view = expected_view(expected)
    assert actual == view, {"actual": actual, "expected": view}


def assert_initial(page: Page, count: int, ready: dict[str, Any] | None = None) -> None:
    assert page.locator("#board").get_attribute("data-revision") == "0"
    expected = initial_expected(count)
    assert_view(capture_view(page), expected)
    if ready is not None:
        assert_view(ready["semantic"], expected)
    geometry = page.evaluate(
        """() => ({
            bodyMaxWidth: getComputedStyle(document.body).maxWidth,
            boardWidth: document.querySelector('#board').getBoundingClientRect().width,
            viewportWidth: window.innerWidth,
            typography: (() => {
              const style = selector => {
                const element = document.querySelector(selector);
                if (!element) return null;
                const computed = getComputedStyle(element);
                return {
                  fontSize: computed.fontSize,
                  fontWeight: computed.fontWeight,
                  marginBlockStart: computed.marginBlockStart,
                  marginBlockEnd: computed.marginBlockEnd,
                };
              };
              const textarea = document.querySelector('#board textarea[data-output-description]');
              const formStyle = textarea ? getComputedStyle(textarea) : null;
              return {
                headings: Object.fromEntries(['h1', 'h2', 'h3', 'h4'].map(tag => [tag, style(`#board ${tag}`)])),
                paragraph: style('#board p'),
                textarea: formStyle ? {
                  fontFamily: formStyle.fontFamily,
                  fontSize: formStyle.fontSize,
                  fontWeight: formStyle.fontWeight,
                  lineHeight: formStyle.lineHeight,
                  color: formStyle.color,
                  backgroundColor: formStyle.backgroundColor,
                  paddingTop: formStyle.paddingTop,
                  paddingRight: formStyle.paddingRight,
                  paddingBottom: formStyle.paddingBottom,
                  paddingLeft: formStyle.paddingLeft,
                  borderTopWidth: formStyle.borderTopWidth,
                  borderTopStyle: formStyle.borderTopStyle,
                  borderTopColor: formStyle.borderTopColor,
                  borderRadius: formStyle.borderRadius,
                  boxSizing: formStyle.boxSizing,
                  resize: formStyle.resize,
                } : null,
              };
            })(),
        })"""
    )
    assert geometry["bodyMaxWidth"] == "960px", geometry
    assert geometry["viewportWidth"] == 1440, geometry
    assert abs(geometry["boardWidth"] - 960) <= 2, geometry
    expected_headings = {
        "h1": (32, 21.44),
        "h2": (24, 19.92),
        "h3": (18.72, 18.72),
        "h4": (16, 21.28),
    }
    for tag, (font_size, margin) in expected_headings.items():
        computed = geometry["typography"]["headings"][tag]
        assert computed is not None, geometry
        assert computed["fontWeight"] == "700", geometry
        assert abs(float(computed["fontSize"].removesuffix("px")) - font_size) <= 0.05, geometry
        assert abs(float(computed["marginBlockStart"].removesuffix("px")) - margin) <= 0.05, geometry
        assert abs(float(computed["marginBlockEnd"].removesuffix("px")) - margin) <= 0.05, geometry
    paragraph = geometry["typography"]["paragraph"]
    assert paragraph is not None, geometry
    assert paragraph["fontSize"] == "16px", geometry
    assert paragraph["fontWeight"] == "400", geometry
    assert paragraph["marginBlockStart"] == "16px", geometry
    assert paragraph["marginBlockEnd"] == "16px", geometry
    textarea = geometry["typography"]["textarea"]
    assert textarea is not None, geometry
    assert textarea["boxSizing"] in {"border-box", "content-box"}, geometry
    assert {key: value for key, value in textarea.items() if key != "boxSizing"} == {
        "fontFamily": "monospace",
        "fontSize": "13.3333px",
        "fontWeight": "400",
        "lineHeight": "normal",
        "color": "rgb(0, 0, 0)",
        "backgroundColor": "rgb(255, 255, 255)",
        "paddingTop": "2px",
        "paddingRight": "2px",
        "paddingBottom": "2px",
        "paddingLeft": "2px",
        "borderTopWidth": "1px",
        "borderTopStyle": "solid",
        "borderTopColor": "rgb(118, 118, 118)",
        "borderRadius": "0px",
        "resize": "both",
    }, geometry
    page.evaluate("value => window.__projectBoardExpected = value", expected)


def assert_action(
    page: Page, action: dict[str, str], count: int, previous_revision: int, ready: dict[str, Any] | None = None
) -> None:
    assert int(page.locator("#board").get_attribute("data-revision")) == previous_revision + 1
    previous = page.evaluate("window.__projectBoardExpected")
    assert len(previous["rows"]) in (count, count + 1)
    assert_view(page.evaluate("window.__projectBoardBefore"), previous)
    expected = expected_after(previous, action["name"])
    assert_view(capture_view(page), expected)
    if ready is not None:
        assert_view(ready["semantic"], expected)
    page.evaluate("value => window.__projectBoardExpected = value", expected)
    assert page.locator("#preserved-input").input_value() == "Draft survives every server update"
    assert page.locator("#disclosure-content").is_visible()


def assert_local_behavior(page: Page) -> None:
    """Exercise native tabs, disclosure, and output controls without timing them."""
    before = page.locator("#board").get_attribute("data-revision")
    requests = []

    def listener(request: Request) -> None:
        requests.append(request.url)

    page.on("request", listener)
    for panel_id in ("project-info", "notes-1", "notes-2", "notes-3", "outputs"):
        page.locator(f'[data-tab-target="{panel_id}"]').click()
        page.locator(f"#{panel_id}").wait_for(state="visible")
    content_issues = page.evaluate(
        """() => {
            const visible = element => {
              if (!element) return false;
              for (let current = element; current; current = current.parentElement) {
                const style = getComputedStyle(current);
                if (current.hidden || style.display === 'none' || style.visibility === 'hidden') return false;
              }
              return true;
            };
            const rows = [...document.querySelectorAll('[data-row-id]')];
            return rows.flatMap(row => {
              const issues = [];
              const headings = [...row.querySelectorAll('h4')];
              const dependencies = headings.find(node => node.textContent.trim() === 'Dependencies');
              const attachments = headings.find(node => node.textContent.trim() === 'Attachments');
              const form = row.querySelector('form.output-form');
              const attachmentSection = attachments?.closest('section');
              const dependencySection = dependencies?.closest('section');
              const detailControl = [...row.querySelectorAll('summary,button')]
                .find(node => node.textContent.trim() === 'Output details');
              if (!visible(row.querySelector('.row-title'))) issues.push(`${row.dataset.rowId}: title not visible`);
              if (!visible(row.querySelector('.row-status'))) issues.push(`${row.dataset.rowId}: status not visible`);
              if (!visible(row.querySelector('[data-output-badge]')))
                issues.push(`${row.dataset.rowId}: badge not visible`);
              if (!dependencies || !visible(dependencies))
                issues.push(`${row.dataset.rowId}: Dependencies heading missing/hidden`);
              if (!attachments || !visible(attachments))
                issues.push(`${row.dataset.rowId}: Attachments heading missing/hidden`);
              if (!detailControl) issues.push(`${row.dataset.rowId}: Output details control missing`);
              if (!form || (attachmentSection && form.contains(attachmentSection)))
                issues.push(`${row.dataset.rowId}: select form missing or contains attachments`);
              if (!row.querySelector('[data-dependency-id]')
                  && !dependencySection?.textContent.includes('No dependencies'))
                issues.push(`${row.dataset.rowId}: empty dependencies fallback missing`);
              if (!row.querySelector('[data-attachment-id]')
                  && !attachmentSection?.textContent.includes('No attachments'))
                issues.push(`${row.dataset.rowId}: empty attachments fallback missing`);
              return issues;
            });
        }"""
    )
    assert content_issues == [], f"Output row content contract failed: {content_issues}"
    first_row = page.locator('[data-row-id="1"]')
    detail_control = first_row.get_by_text("Output details", exact=True)
    assert detail_control.count() == 1
    dependencies_heading = first_row.get_by_role("heading", name="Dependencies", exact=True)
    attachments_heading = first_row.get_by_role("heading", name="Attachments", exact=True)
    output_form = first_row.locator("form.output-form")
    assert dependencies_heading.is_visible()
    assert attachments_heading.is_visible()
    assert output_form.is_visible()
    detail_control.click()
    dependencies_heading.wait_for(state="hidden")
    attachments_heading.wait_for(state="hidden")
    assert output_form.is_visible()
    detail_control.click()
    dependencies_heading.wait_for(state="visible")
    attachments_heading.wait_for(state="visible")
    page.locator('[data-bench-action="disclosure"]').click()
    page.locator("#disclosure-content").wait_for(state="visible")
    description = page.locator('[data-row-id="1"] [data-output-description]')
    completed = page.locator('[data-row-id="1"] [data-output-completed]')
    original_description = description.input_value()
    original_completed = completed.is_checked()
    description.fill("Local output draft")
    completed.set_checked(not original_completed)
    assert description.input_value() == "Local output draft"
    assert completed.is_checked() is not original_completed
    # These controls prove native local behavior without changing the semantic
    # state supplied to the first measured server action.
    description.fill(original_description)
    completed.set_checked(original_completed)
    page.locator("#preserved-input").fill("Draft survives every server update")
    page.remove_listener("request", listener)
    assert requests == []
    assert page.locator("#board").get_attribute("data-revision") == before
