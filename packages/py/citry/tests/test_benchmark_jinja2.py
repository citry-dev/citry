# Jinja2 port of the django-components large benchmark scenario
# (test_benchmark_djc.py, vendored in this directory): the same project page
# (35 components, the same data, JS dependencies, slots, dynamic elements),
# expressed in Jinja2 as the first engine beyond the Django family
# (docs/design/benchmarking.md section 2.1). The benchmark harness reads this
# file as a source string and slices it at the markers below, so the code
# outside the pytest section must stay self-contained.
#
# Faithfulness notes (docs/design/benchmarking.md sections 6.2, 6.5):
# - Jinja2 has no component model: each citry component becomes a Jinja2 macro,
#   provide/inject is threaded as macro arguments, and each component's inline
#   JS is collected by a small per-render registry and injected at the <c-js>
#   marker (the native parallel to citry/django-components dependency rendering).
# - The DJC filters (|json, |alpine, ...) are registered as real Jinja2 filters
#   (Jinja2 has filter syntax; citry does not).
# - Django form rendering is hand-written (shared with the citry port).
# - The data, types, and helpers are shared verbatim with the citry port; only
#   the engine setup and the component-as-macro layer differ.

from __future__ import annotations

import json
from dataclasses import MISSING, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from inspect import signature
from types import MappingProxyType, SimpleNamespace
from typing import Any, Callable, Iterable, Literal, NamedTuple, TypeAlias, TypedDict, TypeVar

from jinja2 import Environment
from markupsafe import Markup, escape

# ----------- IMPORTS END ------------ #

SafeString = Markup

# This is the plain citry variant. The Const optimization is exercised by a
# separate file, test_benchmark_citry_const.py, which marks each component's
# render-invariant literals Const (docs/design/benchmarking.md section 6.4).

T = TypeVar("T")
U = TypeVar("U")


#####################################
# DJANGO STAND-INS
#####################################
# Tiny local replacements so this file imports no Django (the import-time
# benchmark must measure citry, not Django). Each covers only what the
# scenario actually reads.


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


def naturaltime(value: Any) -> str:
    """A minimal stand-in for django.contrib.humanize's naturaltime."""
    if not isinstance(value, datetime):
        return str(value)
    delta = now() - value
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "a moment ago"
    if seconds < 3600:
        return f"{seconds // 60} minutes ago"
    if seconds < 86400:
        return f"{seconds // 3600} hours ago"
    return f"{seconds // 86400} days ago"


def make_request(user: Any) -> SimpleNamespace:
    """Stand-in for django.http.HttpRequest, carrying only the read fields."""
    return SimpleNamespace(user=user, method="GET", path="/projects/1")


def get_csrf_token(_request: Any) -> str:
    """Stand-in for django.middleware.csrf.get_token (a fixed fake token)."""
    return "benchmarkcsrftoken0000000000000000"


#####################################
# TEMPLATE HELPERS (DJC filters as functions)
#####################################
# In V3 there is no filter syntax; these are plain functions called from
# `template_data` (Python), never from templates.


def _plain(value: Any) -> Any:
    """
    Strip Const markers (transparent proxies) recursively.

    json.dumps and other C-level APIs reject the proxy, and the scenario marks
    inputs Const in const mode (and static attrs are auto-marked anyway), so
    the serializing helpers unwrap first. See docs/design/constness.md.
    """
    if isinstance(value, dict):
        return {_plain(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def to_alpine_json(value: Any) -> str:
    """Serialize for an Alpine attribute; single quotes so it survives in HTML."""
    return json.dumps(_plain(value)).replace('"', "'")


def to_json(value: Any) -> str:
    return json.dumps(_plain(value))


def get_item(dictionary: Any, key: Any) -> Any:
    return dictionary.get(key)


def serialize_to_js(obj: Any) -> str:
    """Serialize a Python object to a JS-like expression (recursive)."""
    obj = _plain(obj)
    if isinstance(obj, dict):
        items = [f"{key}: {serialize_to_js(value)}" for key, value in obj.items()]
        return f"{{ {', '.join(items)} }}"
    if isinstance(obj, (list, tuple)):
        return f"[{', '.join(serialize_to_js(item) for item in obj)}]"
    if isinstance(obj, str):
        return obj
    return str(obj)


def default_if_none(value: Any, fallback: Any) -> Any:
    return fallback if value is None else value


def title_case(value: Any) -> str:
    return str(value).title()


def linebreaksbr(value: Any) -> str:
    return str(value).replace("\n", "<br>")


# The DJC filters above (to_json, to_alpine_json, ...) are plain functions
# called from `template_data`, the idiomatic citry shape: data is shaped in
# Python and the template only references the resulting variables. So nothing
# is injected into the template scope, and templates carry no filter/helper
# calls (V3 has no filter syntax by design).



data_json = """
{
  "project": {
    "pk": 1,
    "fields": {
      "name": "Project Name",
      "organization": 1,
      "status": "INPROGRESS",
      "start_date": "2022-02-06",
      "end_date": "2024-02-07"
    }
  },
  "project_tags": [],
  "phases": [
    {
      "pk": 8,
      "fields": {
        "project": 1,
        "phase_template": 3
      }
    },
    {
      "pk": 7,
      "fields": {
        "project": 1,
        "phase_template": 4
      }
    },
    {
      "pk": 6,
      "fields": {
        "project": 1,
        "phase_template": 5
      }
    },
    {
      "pk": 5,
      "fields": {
        "project": 1,
        "phase_template": 6
      }
    },
    {
      "pk": 4,
      "fields": {
        "project": 1,
        "phase_template": 2
      }
    }
  ],
  "notes_1": [
    {
      "pk": 1,
      "fields": {
        "created": "2025-02-07T08:59:58.689Z",
        "modified": "2025-02-07T08:59:58.689Z",
        "project": 1,
        "text": "Test note 1"
      }
    },
    {
      "pk": 2,
      "fields": {
        "created": "2025-02-07T08:59:58.689Z",
        "modified": "2025-02-07T08:59:58.689Z",
        "project": 1,
        "text": "Test note 2"
      }
    }
  ],
  "comments_by_notes_1": {
    "1": [
      {
        "pk": 3,
        "fields": {
          "parent": 1,
          "notes": "Test note one two three",
          "modified_by": 1
        }
      },
      {
        "pk": 4,
        "fields": {
          "parent": 1,
          "notes": "Test note 2",
          "modified_by": 1
        }
      }
    ]
  },
  "notes_2": [
    {
      "pk": 1,
      "fields": {
        "created": "2024-02-07T11:20:49.085Z",
        "modified": "2024-02-07T11:20:55.003Z",
        "project": 1,
        "text": "Test note x"
      }
    }
  ],
  "comments_by_notes_2": {
    "1": [
      {
        "pk": 1,
        "fields": {
          "parent": 1,
          "text": "Test note 6",
          "modified_by": 1
        }
      },
      {
        "pk": 2,
        "fields": {
          "parent": 1,
          "text": "Test note 5",
          "modified_by": 1
        }
      },
      {
        "pk": 4,
        "fields": {
          "parent": 1,
          "text": "Test note 4",
          "modified_by": 1
        }
      },
      {
        "pk": 6,
        "fields": {
          "parent": 1,
          "text": "Test note 3",
          "modified_by": 1
        }
      }
    ]
  },
  "notes_3": [
    {
      "pk": 2,
      "fields": {
        "created": "2024-02-07T11:20:49.085Z",
        "modified": "2024-02-07T11:20:55.003Z",
        "project": 1,
        "text": "Test note 2"
      }
    }
  ],
  "comments_by_notes_3": {
    "2": [
      {
        "pk": 1,
        "fields": {
          "parent": 2,
          "text": "Test note 1",
          "modified_by": 1
        }
      },
      {
        "pk": 3,
        "fields": {
          "parent": 2,
          "text": "Test note 0",
          "modified_by": 1
        }
      }
    ]
  },
  "roles_with_users": [
    {
      "pk": 6,
      "fields": {
        "user": 2,
        "project": 1,
        "name": "Assistant"
      }
    },
    {
      "pk": 7,
      "fields": {
        "user": 2,
        "project": 1,
        "name": "Owner"
      }
    }
  ],
  "contacts": [],
  "outputs": [
    [
      {
        "pk": 14,
        "fields": {
          "name": "Lorem ipsum 16",
          "description": "",
          "completed": false,
          "phase": 8,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 15,
        "fields": {
          "name": "Lorem ipsum 15",
          "description": "",
          "completed": false,
          "phase": 8,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 16,
        "fields": {
          "name": "Lorem ipsum 14",
          "description": "",
          "completed": false,
          "phase": 8,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 17,
        "fields": {
          "name": "Lorem ipsum 13",
          "description": "",
          "completed": false,
          "phase": 8,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 18,
        "fields": {
          "name": "Lorem ipsum 12",
          "description": "",
          "completed": true,
          "phase": 4,
          "dependency": null
        }
      },
      [
        [
          {
            "pk": 19,
            "fields": {
              "text": "Test bookmark",
              "url": "http://localhost:8000/create/bookmmarks/9/",
              "created_by": 1,
              "output": 18
            }
          },
          []
        ]
      ],
      []
    ],
    [
      {
        "pk": 20,
        "fields": {
          "name": "Lorem ipsum 11",
          "description": "",
          "completed": false,
          "phase": 7,
          "dependency": 14
        }
      },
      [],
      [
        [
          {
            "pk": 14,
            "fields": {
              "name": "Lorem ipsum 10",
              "description": "",
              "completed": false,
              "phase": 8,
              "dependency": null
            }
          },
          []
        ]
      ]
    ],
    [
      {
        "pk": 21,
        "fields": {
          "name": "Lorem ipsum 9",
          "description": "",
          "completed": false,
          "phase": 7,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 22,
        "fields": {
          "name": "Lorem ipsum 8",
          "description": "",
          "completed": false,
          "phase": 7,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 23,
        "fields": {
          "name": "Lorem ipsum 7",
          "description": "",
          "completed": false,
          "phase": 7,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 24,
        "fields": {
          "name": "Lorem ipsum 6",
          "description": "",
          "completed": false,
          "phase": 7,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 25,
        "fields": {
          "name": "Lorem ipsum 5",
          "description": "",
          "completed": false,
          "phase": 6,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 26,
        "fields": {
          "name": "Lorem ipsum 4",
          "description": "",
          "completed": false,
          "phase": 6,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 27,
        "fields": {
          "name": "Lorem ipsum 3",
          "description": "",
          "completed": false,
          "phase": 5,
          "dependency": null
        }
      },
      [],
      []
    ],
    [
      {
        "pk": 28,
        "fields": {
          "name": "Lorem ipsum 2",
          "description": "",
          "completed": false,
          "phase": 7,
          "dependency": 14
        }
      },
      [],
      [
        [
          {
            "pk": 14,
            "fields": {
              "name": "Lorem ipsum 1",
              "description": "",
              "completed": false,
              "phase": 8,
              "dependency": null
            }
          },
          []
        ]
      ]
    ]
  ],
  "status_updates": [],
  "user_is_project_member": true,
  "user_is_project_owner": true,
  "phase_titles": {
    "PHASE_0": "Phase 0",
    "PHASE_1": "Phase 1",
    "PHASE_2": "Phase 2",
    "PHASE_3": "Phase 3",
    "PHASE_4": "Phase 4",
    "PHASE_5": "Phase 5",
    "LEGACY": "Legacy"
  },
  "users": [
    {
      "pk": 2,
      "fields": {
        "name": "UserName",
        "is_staff": true
      }
    }
  ],
  "organizations": [
    {
      "pk": 1,
      "fields": {
        "created": "2025-02-07T16:27:49.837Z",
        "modified": "2025-02-07T16:27:49.837Z",
        "name": "Org Name"
      }
    }
  ],
  "phase_templates": [
    {
      "pk": 3,
      "fields": {
        "created": "2025-02-07T16:27:49.837Z",
        "modified": "2025-02-07T16:27:49.837Z",
        "name": "Phase 3",
        "description": "## Phase 3",
        "type": "PHASE_3"
      }
    },
    {
      "pk": 4,
      "fields": {
        "created": "2025-02-07T16:27:49.837Z",
        "modified": "2025-02-07T16:27:49.837Z",
        "name": "Phase 2",
        "description": "## Phase 2",
        "type": "PHASE_2"
      }
    },
    {
      "pk": 5,
      "fields": {
        "created": "2025-02-07T16:27:49.837Z",
        "modified": "2025-02-07T16:27:49.837Z",
        "name": "Phase 4",
        "description": "## Phase 4",
        "type": "PHASE_4"
      }
    },
    {
      "pk": 6,
      "fields": {
        "created": "2025-02-07T16:27:49.837Z",
        "modified": "2025-02-07T16:27:49.837Z",
        "name": "Phase 5",
        "description": "## Phase 5",
        "type": "PHASE_5"
      }
    },
    {
      "pk": 2,
      "fields": {
        "created": "2025-02-07T16:27:49.837Z",
        "modified": "2025-02-07T16:27:49.837Z",
        "name": "Phase 1",
        "description": "## Phase 1",
        "type": "PHASE_1"
      }
    }
  ]
}
"""


# DATA LOADER
#####################################


def load_project_data_from_json(contents: str) -> dict:
    """
    Load project data from JSON and resolves references between objects.
    Returns the data with all resolvable references replaced with actual object references.
    """
    data = json.loads(contents)

    # First create lookup tables for objects that will be referenced
    users_by_id = {user["pk"]: {"id": user["pk"], **user["fields"]} for user in data.get("users", [])}

    def _get_user(user_id: int):
        return users_by_id[user_id] if user_id in users_by_id else data.get("users", [])[0]

    organizations_by_id = {org["pk"]: {"id": org["pk"], **org["fields"]} for org in data.get("organizations", [])}

    phase_templates_by_id = {pt["pk"]: {"id": pt["pk"], **pt["fields"]} for pt in data.get("phase_templates", [])}

    # 1. Resolve project's organization reference
    project = {"id": data["project"]["pk"], **data["project"]["fields"]}
    if "organization" in project:
        org_id = project.pop("organization")  # Remove the ID field
        project["organization"] = organizations_by_id[org_id]  # Add the reference

    # 2. Project tags - no changes needed
    project_tags = data["project_tags"]

    # 3. Resolve phases' references
    phases = []
    phases_by_id = {}  # We'll need this for resolving output references later
    for phase_data in data["phases"]:
        phase = {"id": phase_data["pk"], **phase_data["fields"]}
        if "project" in phase:
            phase["project"] = project
        if "phase_template" in phase:
            template_id = phase.pop("phase_template")
            phase["phase_template"] = phase_templates_by_id[template_id]
        phases.append(phase)
        phases_by_id[phase["id"]] = phase

    # 4. Resolve notes_1 references
    notes_1 = []
    notes_1_by_id = {}  # We'll need this for resolving notes references
    for note_data in data["notes_1"]:
        note = {"id": note_data["pk"], **note_data["fields"]}
        if "project" in note:
            note["project"] = project
        notes_1.append(note)
        notes_1_by_id[note["id"]] = note

    # 5. Resolve comments_by_notes_1 references
    comments_by_notes_1 = {}
    for note_id, comments_list in data["comments_by_notes_1"].items():
        resolved_comments = []
        for comment_data in comments_list:
            comment = {"id": comment_data["pk"], **comment_data["fields"]}
            if "modified_by" in comment:
                comment["modified_by"] = _get_user(comment["modified_by"])
            if "parent" in comment:
                comment["parent"] = notes_1_by_id[comment["parent"]]
            resolved_comments.append(comment)
        comments_by_notes_1[note_id] = resolved_comments

    # 6. Resolve notes_2' references
    notes_2 = []
    notes_2_by_id = {}  # We'll need this for resolving notes references
    for note_data in data["notes_2"]:
        note = {"id": note_data["pk"], **note_data["fields"]}
        if "project" in note:
            note["project"] = project
        notes_2.append(note)
        notes_2_by_id[note["id"]] = note

    # 7. Resolve comments_by_notes_2 references
    comments_by_notes_2 = {}
    for note_id, comments_list in data["comments_by_notes_2"].items():
        resolved_comments = []
        for comment_data in comments_list:
            comment = {"id": comment_data["pk"], **comment_data["fields"]}
            if "modified_by" in comment:
                comment["modified_by"] = _get_user(comment["modified_by"])
            if "parent" in comment:
                comment["parent"] = notes_2_by_id[comment["parent"]]
            resolved_comments.append(comment)
        comments_by_notes_2[note_id] = resolved_comments

    # 8. Resolve notes_3 references
    notes_3 = []
    notes_3_by_id = {}  # We'll need this for resolving notes references
    for note_data in data["notes_3"]:
        note = {"id": note_data["pk"], **note_data["fields"]}
        if "project" in note:
            note["project"] = project
        notes_3.append(note)
        notes_3_by_id[note["id"]] = note

    # 9. Resolve comments_by_notes_3 references
    comments_by_notes_3 = {}
    for note_id, comments_list in data["comments_by_notes_3"].items():
        resolved_comments = []
        for comment_data in comments_list:
            comment = {"id": comment_data["pk"], **comment_data["fields"]}
            if "modified_by" in comment:
                comment["modified_by"] = _get_user(comment["modified_by"])
            if "parent" in comment:
                comment["parent"] = notes_3_by_id[comment["parent"]]
            resolved_comments.append(comment)
        comments_by_notes_3[note_id] = resolved_comments

    # 10. Resolve roles_with_users references
    roles = []
    for role_data in data["roles_with_users"]:
        role = {"id": role_data["pk"], **role_data["fields"]}
        if "project" in role:
            role["project"] = project
        if "user" in role:
            role["user"] = _get_user(role["user"])
        roles.append(role)

    # 11. Contacts - EMPTY, so no changes needed
    contacts = data["contacts"]

    # 12. Resolve outputs references
    resolved_outputs = []
    outputs_by_id = {}  # For resolving dependencies

    # First pass: Create all output objects and build lookup
    for output_tuple in data["outputs"]:
        output_data = output_tuple[0]
        output = {"id": output_data["pk"], **output_data["fields"]}
        if "phase" in output:
            output["phase"] = phases_by_id[output["phase"]]
        outputs_by_id[output["id"]] = output

    # Second pass: Process each output with its attachments and dependencies
    for output_tuple in data["outputs"]:
        output_data, attachments_data, dependencies_data = output_tuple
        output = outputs_by_id[output_data["pk"]]

        # Process attachments
        resolved_attachments = []
        for attachment_tuple in attachments_data:
            attachment_data = attachment_tuple[0]
            attachment = {"id": attachment_data["pk"], **attachment_data["fields"]}
            if "created_by" in attachment:
                attachment["created_by"] = _get_user(attachment["created_by"])
            if "output" in attachment:
                attachment["output"] = outputs_by_id[attachment["output"]]
            # Keep tags as is
            resolved_attachments.append((attachment, attachment_tuple[1]))

        # Process dependencies
        resolved_dependencies = []
        for dep_tuple in dependencies_data:
            dep_data = dep_tuple[0]
            dep_output = outputs_by_id[dep_data["pk"]]
            # Keep the tuple structure but with resolved references
            resolved_dependencies.append((dep_output, dep_tuple[1]))

        resolved_outputs.append((output, resolved_attachments, resolved_dependencies))

    return {
        "project": project,
        "project_tags": project_tags,
        "phases": phases,
        "notes_1": notes_1,
        "comments_by_notes_1": comments_by_notes_1,
        "notes_2": notes_2,
        "comments_by_notes_2": comments_by_notes_2,
        "notes_3": notes_3,
        "comments_by_notes_3": comments_by_notes_3,
        "roles_with_users": roles,
        "contacts": contacts,
        "outputs": resolved_outputs,
        "status_updates": data["status_updates"],
        "user_is_project_member": data["user_is_project_member"],
        "user_is_project_owner": data["user_is_project_owner"],
        "phase_titles": data["phase_titles"],
        "users": data["users"],
    }




#####################################
# TYPES
#####################################


class User(TypedDict):
    id: int
    name: str


class Organization(TypedDict):
    id: int
    name: str


class Project(TypedDict):
    id: int
    name: str
    organization: Organization
    status: str
    start_date: date
    end_date: date


class ProjectRole(TypedDict):
    id: int
    user: User
    project: Project
    name: str


class ProjectBookmark(TypedDict):
    id: int
    project: Project
    text: str
    url: str
    attachment: "ProjectOutputAttachment | None"


class ProjectStatusUpdate(TypedDict):
    id: int
    project: Project
    text: str
    modified_by: User
    modified: str


class ProjectContact(TypedDict):
    id: int
    project: Project
    link_id: str
    name: str
    job: str


class PhaseTemplate(TypedDict):
    id: int
    name: str
    description: str
    type: str


class ProjectPhase(TypedDict):
    id: int
    project: Project
    phase_template: PhaseTemplate


class ProjectOutput(TypedDict):
    id: int
    name: str
    description: str
    completed: bool
    phase: ProjectPhase
    dependency: "ProjectOutput | None"


class ProjectOutputAttachment(TypedDict):
    id: int
    text: str
    url: str
    created_by: User
    output: ProjectOutput


class ProjectNote(TypedDict):
    id: int
    project: Project
    text: str
    created: str


class ProjectNoteComment(TypedDict):
    id: int
    parent: ProjectNote
    text: str
    modified_by: User
    modified: str



#####################################
# CONSTANTS
#####################################

FORM_SHORT_TEXT_MAX_LEN = 255


# This allows us to compare Enum values against strings
class StrEnum(str, Enum):
    pass


class TagResourceType(StrEnum):
    PROJECT = "PROJECT"
    PROJECT_BOOKMARK = "PROJECT_BOOKMARK"
    PROJECT_OUTPUT = "PROJECT_OUTPUT"
    PROJECT_OUTPUT_ATTACHMENT = "PROJECT_OUTPUT_ATTACHMENT"
    PROJECT_TEMPLATE = "PROJECT_TEMPLATE"


class ProjectPhaseType(StrEnum):
    PHASE_1 = "PHASE_1"
    PHASE_2 = "PHASE_2"
    PHASE_3 = "PHASE_3"
    PHASE_4 = "PHASE_4"
    PHASE_5 = "PHASE_5"


class TagTypeMeta(NamedTuple):
    allowed_values: tuple[str, ...]


# Additional metadata for Tags
#
# NOTE: We use MappingProxyType as an immutable dict.
#       See https://stackoverflow.com/questions/2703599
TAG_TYPE_META = MappingProxyType(
    {
        TagResourceType.PROJECT: TagTypeMeta(
            allowed_values=(
                "Tag 1",
                "Tag 2",
                "Tag 3",
                "Tag 4",
            ),
        ),
        TagResourceType.PROJECT_BOOKMARK: TagTypeMeta(
            allowed_values=(
                "Tag 5",
                "Tag 6",
                "Tag 7",
                "Tag 8",
            ),
        ),
        TagResourceType.PROJECT_OUTPUT: TagTypeMeta(
            allowed_values=(),
        ),
        TagResourceType.PROJECT_OUTPUT_ATTACHMENT: TagTypeMeta(
            allowed_values=(
                "Tag 9",
                "Tag 10",
                "Tag 11",
                "Tag 12",
                "Tag 13",
                "Tag 14",
                "Tag 15",
                "Tag 16",
                "Tag 17",
                "Tag 18",
                "Tag 19",
                "Tag 20",
            ),
        ),
        TagResourceType.PROJECT_TEMPLATE: TagTypeMeta(
            allowed_values=("Tag 21",),
        ),
    },
)


class ProjectOutputDef(NamedTuple):
    title: str
    description: str | None = None
    dependency: str | None = None


class ProjectPhaseMeta(NamedTuple):
    type: ProjectPhaseType
    outputs: list[ProjectOutputDef]


# This constant decides in which order the project phases are shown,
# as well as what kind of name of description they have.
#
# NOTE: We use MappingProxyType as an immutable dict.
#       See https://stackoverflow.com/questions/2703599
PROJECT_PHASES_META = MappingProxyType(
    {
        ProjectPhaseType.PHASE_1: ProjectPhaseMeta(
            type=ProjectPhaseType.PHASE_1,
            outputs=[
                ProjectOutputDef(title="Lorem ipsum 0"),
            ],
        ),
        ProjectPhaseType.PHASE_2: ProjectPhaseMeta(
            type=ProjectPhaseType.PHASE_2,
            outputs=[
                ProjectOutputDef(title="Lorem ipsum 1"),
                ProjectOutputDef(title="Lorem ipsum 2"),
                ProjectOutputDef(title="Lorem ipsum 3"),
                ProjectOutputDef(title="Lorem ipsum 4"),
            ],
        ),
        ProjectPhaseType.PHASE_3: ProjectPhaseMeta(
            type=ProjectPhaseType.PHASE_3,
            outputs=[
                ProjectOutputDef(
                    title="Lorem ipsum 6",
                    dependency="Lorem ipsum 1",
                ),
                ProjectOutputDef(
                    title="Lorem ipsum 7",
                    dependency="Lorem ipsum 1",
                ),
                ProjectOutputDef(title="Lorem ipsum 8"),
                ProjectOutputDef(title="Lorem ipsum 9"),
                ProjectOutputDef(title="Lorem ipsum 10"),
                ProjectOutputDef(title="Lorem ipsum 11"),
            ],
        ),
        ProjectPhaseType.PHASE_4: ProjectPhaseMeta(
            type=ProjectPhaseType.PHASE_4,
            outputs=[
                ProjectOutputDef(title="Lorem ipsum 12"),
                ProjectOutputDef(title="Lorem ipsum 13"),
            ],
        ),
        ProjectPhaseType.PHASE_5: ProjectPhaseMeta(
            type=ProjectPhaseType.PHASE_5,
            outputs=[
                ProjectOutputDef(title="Lorem ipsum 14"),
            ],
        ),
    },
)


#####################################
# THEME
#####################################

ThemeColor: TypeAlias = Literal["default", "error", "success", "alert", "info"]
ThemeVariant: TypeAlias = Literal["primary", "secondary"]

VARIANTS = ["primary", "secondary"]


class ThemeStylingUnit(NamedTuple):
    """
    Smallest unit of info, this class defines a specific styling of a specific
    component in a specific state.

    E.g. styling of a disabled "Error" button.
    """

    color: str
    """CSS class(es) specifying color"""
    css: str = ""
    """Other CSS classes not specific to color"""


class ThemeStylingVariant(NamedTuple):
    """
    Collection of styling combinations that are meaningful as a group.

    E.g. all "error" variants - primary, disabled, secondary, ...
    """

    primary: ThemeStylingUnit
    primary_disabled: ThemeStylingUnit
    secondary: ThemeStylingUnit
    secondary_disabled: ThemeStylingUnit


class Theme(NamedTuple):
    """Class for defining a styling and color theme for the app."""

    default: ThemeStylingVariant
    error: ThemeStylingVariant
    alert: ThemeStylingVariant
    success: ThemeStylingVariant
    info: ThemeStylingVariant

    sidebar: str
    sidebar_link: str
    background: str
    tab_active: str
    tab_text_active: str
    tab_text_inactive: str
    check_interactive: str
    check_static: str
    check_outline: str


_secondary_btn_styling = "ring-1 ring-inset"

theme = Theme(
    default=ThemeStylingVariant(
        primary=ThemeStylingUnit(
            color="bg-blue-600 text-white hover:bg-blue-500 focus-visible:outline-blue-600 transition",
        ),
        primary_disabled=ThemeStylingUnit(
            color="bg-blue-300 text-blue-50 focus-visible:outline-blue-600 transition",
        ),
        secondary=ThemeStylingUnit(
            color="bg-white text-gray-800 ring-gray-300 hover:bg-gray-100 focus-visible:outline-gray-600 transition",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-gray-300 ring-gray-300 focus-visible:outline-gray-600 transition",
            css=_secondary_btn_styling,
        ),
    ),
    error=ThemeStylingVariant(
        primary=ThemeStylingUnit(
            color="bg-red-600 text-white hover:bg-red-500 focus-visible:outline-red-600",
        ),
        primary_disabled=ThemeStylingUnit(
            color="bg-red-300 text-white focus-visible:outline-red-600",
        ),
        secondary=ThemeStylingUnit(
            color="bg-white text-red-600 ring-red-300 hover:bg-red-100 focus-visible:outline-red-600",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-red-200 ring-red-100 focus-visible:outline-red-600",
            css=_secondary_btn_styling,
        ),
    ),
    alert=ThemeStylingVariant(
        primary=ThemeStylingUnit(
            color="bg-amber-500 text-white hover:bg-amber-400 focus-visible:outline-amber-500",
        ),
        primary_disabled=ThemeStylingUnit(
            color="bg-amber-100 text-orange-300 focus-visible:outline-amber-500",
        ),
        secondary=ThemeStylingUnit(
            color="bg-white text-amber-500 ring-amber-300 hover:bg-amber-100 focus-visible:outline-amber-500",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-orange-200 ring-amber-100 focus-visible:outline-amber-500",
            css=_secondary_btn_styling,
        ),
    ),
    success=ThemeStylingVariant(
        primary=ThemeStylingUnit(
            color="bg-green-600 text-white hover:bg-green-500 focus-visible:outline-green-600",
        ),
        primary_disabled=ThemeStylingUnit(
            color="bg-green-300 text-white focus-visible:outline-green-600",
        ),
        secondary=ThemeStylingUnit(
            color="bg-white text-green-600 ring-green-300 hover:bg-green-100 focus-visible:outline-green-600",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-green-200 ring-green-100 focus-visible:outline-green-600",
            css=_secondary_btn_styling,
        ),
    ),
    info=ThemeStylingVariant(
        primary=ThemeStylingUnit(
            color="bg-sky-600 text-white hover:bg-sky-500 focus-visible:outline-sky-600",
        ),
        primary_disabled=ThemeStylingUnit(
            color="bg-sky-300 text-white focus-visible:outline-sky-600",
        ),
        secondary=ThemeStylingUnit(
            color="bg-white text-sky-600 ring-sky-300 hover:bg-sky-100 focus-visible:outline-sky-600",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-sky-200 ring-sky-100 focus-visible:outline-sky-600",
            css=_secondary_btn_styling,
        ),
    ),
    sidebar="bg-neutral-900 text-neutral-200",
    sidebar_link="hover:bg-neutral-700 hover:text-white transition",
    background="bg-neutral-200",
    tab_active="border-blue-700",
    tab_text_active="text-blue-700",
    tab_text_inactive="text-gray-500 hover:text-blue-700",
    check_interactive="bg-blue-600 group-hover:bg-blue-500 transition",
    check_static="bg-blue-600",
    check_outline="border-2 border-blue-600 bg-white",
)


def get_styling_css(
    variant: "ThemeVariant | None" = None,
    color: "ThemeColor | None" = None,
    disabled: bool | None = None,
):
    """
    Dynamically access CSS styling classes for a specific variant and state.

    E.g. following two calls get styling classes for:
    1. Secondary error state
    1. Secondary alert disabled state
    2. Primary default disabled state
    ```py
    get_styling_css('secondary', 'error')
    get_styling_css('secondary', 'alert', disabled=True)
    get_styling_css(disabled=True)
    ```
    """
    variant = variant or "primary"
    color = color or "default"
    disabled = disabled if disabled is not None else False

    color_variants: ThemeStylingVariant = getattr(theme, str(color))

    if variant not in VARIANTS:
        raise ValueError(
            f'Unknown theme variant "{variant}", must be one of {VARIANTS}',
        )

    variant_name = variant if not disabled else f"{variant}_disabled"
    styling: ThemeStylingUnit = getattr(color_variants, str(variant_name))

    css = f"{styling.color} {styling.css}".strip()
    return css




def group_by(
    lst: Iterable[T],
    keyfn: Callable[[T, int], Any],
    mapper: Callable[[T, int], U] | None = None,
):
    """
    Given a list, generates a key for each item in the list using the `keyfn`.

    Returns a dictionary of generated keys, where each value is a list of corresponding
    items.

    Similar to Lodash's `groupby`.

    Optionally map the values in the lists with `mapper`.
    """
    grouped: dict[Any, list[U | T]] = {}
    for index, item in enumerate(lst):
        key = dynamic_apply(keyfn, item, index)
        if key not in grouped:
            grouped[key] = []

        mapped_item = dynamic_apply(mapper, item, index) if mapper else item
        grouped[key].append(mapped_item)
    return grouped


def dynamic_apply(fn: Callable, *args):
    """
    Given a function and positional arguments that should be applied to given function,
    this helper will apply only as many arguments as the function defines, or only
    as much as the number of arguments that we can apply.
    """
    mapper_args_count = len(signature(fn).parameters)
    num_args_to_apply = min(mapper_args_count, len(args))
    first_n_args = args[:num_args_to_apply]

    return fn(*first_n_args)


#####################################
# TIMESTAMP HELPER
#####################################


def format_timestamp(timestamp: Any) -> str:
    """More than 7 days ago -> "Jan 1, 2025"; otherwise a relative string."""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    if now() - timestamp > timedelta(days=7):
        return timestamp.strftime("%b %-d, %Y")
    return naturaltime(timestamp)


#####################################
# LAYOUT DATA + RENDER ENTRYPOINT
#####################################


class ProjectLayoutData(NamedTuple):
    request: Any
    active_projects: "list[Project]"
    project: "Project"
    bookmarks: "list[ProjectBookmark]"


def gen_render_data() -> dict:
    data = load_project_data_from_json(data_json)

    users = data.pop("users")
    user = users[0]

    bookmarks: "list[ProjectBookmark]" = [
        {
            "id": 82,
            "project": data["project"],
            "text": "Test bookmark",
            "url": "http://localhost:8000/bookmarks/9/create",
            "attachment": None,
        },
    ]

    request = make_request(user)

    data["layout_data"] = ProjectLayoutData(
        bookmarks=bookmarks,
        project=data["project"],
        active_projects=[data["project"]],
        request=request,
    )

    return data




#####################################
#
# COMPONENTS
#
#####################################


# ----- Button -----




# ----- Icon + HeroIcon -----

# Single hard-coded icon (the benchmark only ever renders this one).
ICONS = {
    "outline": {
        "academic-cap": [
            {
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
                "d": "M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5",  # noqa: E501
            },
        ],
    },
}


class ComponentDefaultsMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:
        return dataclass(super().__new__(mcs, name, bases, namespace))  # type: ignore[arg-type]


class ComponentDefaults(metaclass=ComponentDefaultsMeta):
    def __post_init__(self) -> None:
        fields = self.__class__.__dataclass_fields__  # type: ignore[attr-defined]
        for field_name, dataclass_field in fields.items():
            if dataclass_field.default is not MISSING and getattr(self, field_name) is None:
                setattr(self, field_name, dataclass_field.default)


class IconDefaults(ComponentDefaults):
    name: str
    variant: str = "outline"
    size: int = 24
    color: str = "currentColor"
    stroke_width: float = 1.5
    viewbox: str = "0 0 24 24"
    attrs: "dict | None" = None






# ----- Menu + MenuList -----

MaybeNestedList: TypeAlias = list
MenuItemGroup: TypeAlias = list


@dataclass(frozen=True)
class MenuItem:
    value: Any
    link: "str | None" = None
    item_attrs: "dict | None" = None




def _normalize_item(item):
    return item if isinstance(item, MenuItem) else MenuItem(value=item)


def _normalize_items_to_groups(items):
    def is_group(item):
        return isinstance(item, Iterable) and not isinstance(item, str)

    groups: list = []
    curr_group = None
    for index, item_or_grp in enumerate(items):
        if isinstance(item_or_grp, Iterable) and not isinstance(item_or_grp, str):
            group = item_or_grp
        else:
            group = curr_group if curr_group is not None else []
            if curr_group is None:
                curr_group = group
            group.append(item_or_grp)
            is_not_last = index < len(items) - 1
            if is_not_last and not is_group(items[index + 1]):
                continue
        groups.append(group)
        curr_group = None
    return groups


def prepare_menu_items(items):
    return [list(map(_normalize_item, group)) for group in _normalize_items_to_groups(items)]




# ----- Table -----


class TableHeader(NamedTuple):
    name: str
    key: str
    hidden: "bool | None" = None
    cell_attrs: "dict | None" = None


@dataclass(frozen=True)
class TableCell:
    value: Any
    colspan: int = 1
    link: "str | None" = None
    link_attrs: "dict | None" = None
    cell_attrs: "dict | None" = None
    linebreaks: "bool | None" = None


NULL_CELL = TableCell("")


@dataclass(frozen=True)
class TableRow:
    cols: dict = field(default_factory=dict)
    row_attrs: "dict | None" = None
    col_attrs: "dict | None" = None


def create_table_row(cols=None, row_attrs=None, col_attrs=None):
    resolved_cols: dict = {}
    if cols:
        for key, val in cols.items():
            resolved_cols[key] = val if isinstance(val, TableCell) else TableCell(value=val)
    return TableRow(cols=resolved_cols, row_attrs=row_attrs, col_attrs=col_attrs)


def prepare_row_headers(row, headers):
    final_row_headers = []
    headers_to_skip = 0
    for header in headers:
        if headers_to_skip > 0:
            headers_to_skip -= 1
            continue
        final_row_headers.append(header)
        cell = row.cols.get(header.key)
        if cell is not None:
            headers_to_skip = cell.colspan - 1
    return final_row_headers




# ----- ExpansionPanel -----




# ----- Dialog -----


def construct_btn_onclick(model: str, btn_on_click: "str | None") -> Any:
    on_click_cb = f"{model} = false;"
    if btn_on_click:
        on_click_cb = f"{btn_on_click}; {on_click_cb}"
    return SafeString(on_click_cb)




# ----- Tags -----


class TagEntry(NamedTuple):
    tag: str
    selected: bool = False




# ----- Breadcrumbs -----


@dataclass(frozen=True)
class Breadcrumb:
    value: Any
    link: "str | None" = None
    item_attrs: "dict | None" = None




# ----- ListComponent -----


@dataclass(frozen=True)
class ListItem:
    value: Any
    link: "str | None" = None
    attrs: "dict | None" = None
    meta: "dict | None" = None




# ----- Bookmarks + Bookmark -----


class BookmarkItem(NamedTuple):
    id: int
    text: str
    url: str
    edit_url: str


class ProjectPageTabsToQueryParams(Enum):
    PROJECT_INFO = {"tabs-proj-right": "1"}
    OUTPUTS = {"tabs-proj-right": "5"}


_bookmark_item_class = "px-4 py-1 text-sm text-gray-900 hover:bg-gray-100 cursor-pointer"
bookmark_menu_items = [
    [MenuItem(value="Edit", link="#", item_attrs={"class": _bookmark_item_class, ":href": "contextMenuItem.value.edit_url"})],
]






# ----- Tabs family -----


class TabEntry(NamedTuple):
    header: str
    content: Any
    disabled: bool = False


class TabStaticEntry(NamedTuple):
    header: str
    href: str
    content: str | None
    disabled: bool = False










# ----- ProjectUserAction -----




# ----- ProjectStatusUpdates -----


def _make_status_update_data(status_update):
    modified_time_str = format_timestamp(datetime.fromisoformat(status_update["modified"]))
    return {
        "timestamp": modified_time_str + " " + status_update["modified_by"]["name"],
        "text": status_update["text"],
        "edit_href": f"/edit/{status_update['project']['id']}/status_update/{status_update['id']}",
    }




# ----- ProjectUsers (Django form hand-written) -----

roles_table_headers = [
    TableHeader(key="name", name="Name"),
    TableHeader(key="role", name="Role"),
    TableHeader(key="delete", name="", hidden=True),
]


def _render_choice_field(field_name, label, choices):
    """Hand-written replacement for a Django ChoiceField's table row."""
    options = "".join(f'<option value="{escape(value)}">{escape(text)}</option>' for value, text in choices)
    return (
        f'<tr><th><label for="id_{field_name}">{label}:</label></th>'
        f'<td><select name="{field_name}" id="id_{field_name}" required>{options}</select></td></tr>'
    )




# ----- Form (dynamic content tag via <c-element>, feature B) -----




# ----- ProjectOutput data types + ProjectOutputBadge -----

OUTPUT_DESCRIPTION_PLACEHOLDER = "Placeholder text"
FORM_SHORT_TEXT_MAX_LEN = 255


class ProjectInfoEntry(NamedTuple):
    title: str
    value: str


class AttachmentWithTags(NamedTuple):
    attachment: Any
    tags: list


class OutputWithAttachments(NamedTuple):
    output: Any
    attachments: list


class OutputWithAttachmentsAndDeps(NamedTuple):
    output: Any
    attachments: list
    dependencies: list


class RenderedAttachment(NamedTuple):
    url: str
    text: str
    tags: list


class RenderedOutputDep(NamedTuple):
    dependency: Any
    phase_url: str
    attachments: list


class RenderedProjectOutput(NamedTuple):
    output: Any
    dependencies: list
    has_missing_deps: bool
    output_data: dict
    attachments: list
    update_output_url: str




# ----- ProjectOutputAttachments -----




# ----- ProjectOutputDependency -----




# ----- ProjectOutputForm -----




# ----- ProjectOutputs -----




# ----- ProjectOutputsSummary -----




# ----- ProjectInfo -----




# ----- ProjectNotes -----


def _make_comment_data(note, comment):
    modified_time_str = format_timestamp(datetime.fromisoformat(comment["modified"]))
    return {
        "timestamp": modified_time_str + " " + comment["modified_by"]["name"],
        # DJC stored this under "notes" but its template reads `comment.text`
        # (so it rendered empty); keyed as "text" here so the text renders.
        "text": comment["text"],
        "edit_href": f"/update/{note['project']['id']}/note/{note['id']}/comment/{comment['id']}/",
    }


def _make_notes_data(notes, comments_by_notes):
    notes_data = []
    for note in notes:
        comments = comments_by_notes.get(note["id"], [])
        notes_data.append(
            {
                "text": note["text"],
                "timestamp": note["created"],
                "edit_href": f"/edit/{note['project']['id']}/note/{note['id']}/",
                "comments": [_make_comment_data(note, c) for c in comments],
                "create_comment_url": f"/create/{note['project']['id']}/note/{note['id']}/",
            }
        )
    return notes_data




# ----- Navbar -----




# ----- RenderContextProvider + Sidebar -----


class RenderContext(NamedTuple):
    request: Any
    user: Any
    csrf_token: str




class SidebarItem(NamedTuple):
    name: str
    icon: str | None = None
    icon_variant: str | None = None
    href: str | None = None
    children: list | None = None


def gen_sidebar_menu_items(active_projects):
    return [
        SidebarItem(name="Homepage", icon="home", icon_variant="outline", href="/"),
        SidebarItem(
            name="Projects",
            icon="folder",
            icon_variant="outline",
            href="/projects",
            children=[SidebarItem(name=p["name"], icon=None, href=f"/projects/{p['id']}") for p in active_projects],
        ),
        SidebarItem(name="Page 3", icon="folder", icon_variant="outline", href="/page-3"),
        SidebarItem(name="Page 4", icon="bars-arrow-down", icon_variant="outline", href="/page-4"),
        SidebarItem(name="page-5", icon="forward", icon_variant="outline", href="/page-5"),
        SidebarItem(name="FAQ", icon="archive-box", icon_variant="outline", href="/faq"),
    ]




# ----- Base (document shell; <c-css>/<c-js> are feature C) -----


def static(path):
    return f"/static/{path}"




# ----- Layout -----


class LayoutData(NamedTuple):
    request: Any
    active_projects: list




# ----- ProjectLayoutTabbed -----


def gen_tabs(project_id):
    return [
        TabStaticEntry(header="Tab 2", href=f"/projects/{project_id}/tab-2", content=None),
        TabStaticEntry(header="Tab 1", href=f"/projects/{project_id}/tab-1", content=None),
    ]


# The breadcrumb home icon never varies, so it is built once at import rather
# than on every layout render (a component instance is reusable; rendering it
# does not mutate it).




# ----- ProjectPage (root) -----


#####################################
# COMPONENT INLINE JS (collected at the <c-js> marker)
#####################################
COMPONENT_JS = {
    'ExpansionPanel': """
        document.addEventListener("alpine:init", () => {
            Alpine.data("expansion_panel", () => ({
                isOpen: false,
                init() {
                    const initData = JSON.parse(this.$el.dataset.init);
                    this.isOpen = initData.open;
                    const panelId = this.$el.dataset.panelid;
                    const panel = new URL(location.href).searchParams.get("panel");
                    if (panel && panel == panelId) {
                        this.isOpen = true;
                        this.$el.scrollIntoView();
                    }
                },
                togglePanel(event) { this.isOpen = !this.isOpen; },
            }));
        });
    """,
    'Bookmarks': """
        document.addEventListener('alpine:init', () => {
            AlpineComposition.registerComponent(Alpine, AlpineComposition.defineComponent({
                name: "bookmarks", props: {}, emits: {},
                setup(props, vm, reactivity) {
                    const { ref } = reactivity;
                    const contextMenuItem = ref(null);
                    const contextMenuRef = ref(null);
                    const onContextMenuToggle = (data) => {
                        const { item, el } = data;
                        const willUntoggle = contextMenuItem.value && contextMenuItem.value.id === item.id;
                        contextMenuItem.value = null; contextMenuRef.value = null;
                        if (willUntoggle) return;
                        setTimeout(() => { contextMenuItem.value = item; contextMenuRef.value = el; });
                    };
                    const onContextMenuClickOutside = () => { contextMenuItem.value = null; contextMenuRef.value = null; };
                    return { contextMenuItem, contextMenuRef, onContextMenuToggle, onContextMenuClickOutside };
                },
            }));
        });
    """,
    'Bookmark': """
        document.addEventListener('alpine:init', () => {
            AlpineComposition.registerComponent(Alpine, AlpineComposition.defineComponent({
                name: "bookmark",
                props: { bookmark: { type: Object, required: true } },
                emits: { menuToggle: (obj) => true },
                setup(props, vm) {
                    const onMenuToggle = () => { vm.$emit('menuToggle', { item: props.bookmark, el: vm.$refs.bookmark_menu }); };
                    return { bookmark: props.bookmark, onMenuToggle };
                },
            }));
        });
    """,
    'TabsImpl': """
        document.addEventListener("alpine:init", () => {
            Alpine.data("tabs", () => ({
                openTab: 1,
                name: null,
                get tabQueryName() { return `tabs-${this.name}`; },
                init() {
                    if (this.$el.dataset['init']) {
                        const { name } = JSON.parse(this.$el.dataset['init']);
                        if (name) {
                            this.name = name;
                            app.query.registerParam(this.tabQueryName,
                                (newVal, oldVal) => this.onTabQueryParamChange(newVal, oldVal));
                        }
                    }
                    const containerEl = this.$refs.container;
                    if (containerEl.scrollTop) { this.$refs.container.scrollTop = 0; }
                },
                setOpenTab(tabIndex) {
                    this.openTab = tabIndex;
                    if (this.name) { app.query.setParams({ [this.tabQueryName]: tabIndex }); }
                },
                onTabQueryParamChange(newValue, oldValue) {
                    if (newValue == null) return;
                    const n = typeof newValue === "number" ? newValue : Number.parseInt(newValue);
                    if (n === this.openTab) return;
                    this.setOpenTab(n);
                },
            }));
        });
    """,
    'ProjectUsers': """
        document.addEventListener('alpine:init', () => {
            Alpine.data('project_users', () => ({
                isDeleteDialogOpen: false,
                role: null,
                onUserDelete(event) {
                    const { role } = event.detail;
                    this.role = role;
                    this.isDeleteDialogOpen = !!role;
                },
            }));
        });
    """,
    'Form': """
        document.addEventListener('alpine:init', () => {
            Alpine.data('form', () => {
                const data = Alpine.reactive({
                    formData: {}, isSubmitting: false,
                    updateFormModel(event) {
                        const form = this.$el.closest("form");
                        if (!form) { this.formData = null; return; }
                        const formDataObj = new FormData(form);
                        this.formData = [...formDataObj.entries()].reduce((agg, [k, v]) => { agg[k] = v; return agg; }, {});
                    },
                    onSubmit(event) {
                        if (this.isSubmitting) return;
                        this.isSubmitting = true;
                        event.target.submit();
                    },
                });
                Alpine.watch(() => data.formData, (newVal, oldVal) => {
                    if (JSON.stringify(newVal || null) === JSON.stringify(oldVal || null)) return;
                    data.$dispatch('change', newVal);
                });
                return data;
            });
        });
    """,
    'ProjectOutputAttachments': """
        document.addEventListener("alpine:init", () => {
            AlpineComposition.registerComponent(Alpine, AlpineComposition.defineComponent({
                name: "project_output_attachments",
                props: { attachments: { type: Object, required: true } },
                emits: {
                    updateAttachmentData: (index, data) => true,
                    setAttachmentTags: (index, tags) => true,
                    removeAttachment: (index) => true,
                    toggleAttachment: (index) => true,
                },
                setup(props, vm, { toRefs }) {
                    const { attachments } = toRefs(props);
                    return { attachments };
                },
            }));
        });
    """,
    'ProjectOutputDependency': """
        document.addEventListener('alpine:init', () => {
            AlpineComposition.registerComponent(Alpine, AlpineComposition.defineComponent({
                name: 'project_output_dependency',
                props: { initAttachments: { type: String, required: true } },
                setup(props, vm, { ref }) {
                    const attachments = ref([]);
                    if (props.initAttachments) {
                        attachments.value = JSON.parse(props.initAttachments).map(({ url, text, tags }) => ({
                            url, text, tags, isPreview: true,
                        }));
                    }
                    return { attachments };
                },
            }));
        });
    """,
    'ProjectOutputForm': """
        document.addEventListener('alpine:init', () => {
            AlpineComposition.registerComponent(Alpine, AlpineComposition.defineComponent({
                name: 'project_output_form',
                props: { initAttachments: { type: String, required: true } },
                setup(props, vm, { ref }) {
                    const attachments = ref([]);
                    if (props.initAttachments) {
                        attachments.value = JSON.parse(props.initAttachments);
                    }
                    return { attachments };
                },
            }));
        });
    """,
    'Base': """
        const app = { query: createQueryManager() };
        app.query.load();
        const createQueryManager = () => {
            const callbacks = {};
            const previousParamValues = {};
            const registerParam = (key, cb) => {
                callbacks[key] = callbacks[key] || [];
                callbacks[key].push(cb);
                return () => { callbacks[key] = (callbacks[key] || []).filter((c) => c !== cb); };
            };
            const setParams = (params) => {
                const url = new URL(location.href);
                Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
                history.pushState({}, "", url);
            };
            const load = () => {};
            return { registerParam, setParams, load };
        };
    """,
    'Layout': """
        document.addEventListener('alpine:init', () => {
            const computeSidebarState = (prevState) => {
                const width = (window.innerWidth > 0) ? window.innerWidth : screen.width;
                if (!prevState && width >= 1024) return true;
                if (prevState && width < 1024) return false;
                return prevState;
            };
            Alpine.data('layout', () => ({
                sidebarOpen: computeSidebarState(false),
                init() { this.onWindowResize(); },
                toggleSidebar() { this.sidebarOpen = !this.sidebarOpen; },
                onWindowResize() { this.sidebarOpen = computeSidebarState(this.sidebarOpen); },
            }));
        });
    """,
}


#####################################
# COMPONENT DATA HELPERS (the citry template_data bodies)
#####################################

# --- Menu ---
def _Menudata(items, model=None, attrs=None, activator_attrs=None, list_attrs=None,
              close_on_esc=True, close_on_click_outside=True, anchor=None, anchor_dir="bottom",
              has_activator=False):
    is_model_overriden = bool(model)
    model = model or "open"
    all_list_attrs: dict = {}
    if list_attrs:
        all_list_attrs.update(list_attrs)
    if anchor:
        all_list_attrs[f"x-anchor.{anchor_dir}"] = anchor
    all_list_attrs.update({"x-show": model, "x-cloak": ""})
    # The Alpine x-data object, with the same interpolated values DJC built with
    # the `|alpine` filter, assembled here (V3 has no template filters).
    x_data_lines = [
        "{",
        f"'isModelOverriden': {to_alpine_json(is_model_overriden)},",
        f"'modelName': {to_alpine_json(model)},",
        f"'closeOnClickOutside': {to_alpine_json(close_on_click_outside)},",
    ]
    if not is_model_overriden:
        x_data_lines.append(f"'{model}': false,")
    x_data_lines.append(
        "onClickOutside(event) { if (this.closeOnClickOutside) {"
        " if (!this.isModelOverriden) { this[this.modelName] = false; }"
        " $dispatch('click_outside', { origEvent: event }); } }, }"
    )
    root_attrs = {"x-data": " ".join(x_data_lines)}
    if close_on_esc:
        root_attrs["@keydown.escape"] = f"{model} = false"
    activator_attrs_out = {
        "@click": f"{model} = !{model}",
        "@keydown.enter": f"{model} = !{model}",
        "tabindex": "0",
        "aria-haspopup": "true",
        ":aria-expanded": f"!!{model}",
        "x-ref": "activator",
        **(activator_attrs or {}),
    }
    return {
        "items": items,
        "list_attrs": all_list_attrs,
        "attrs": attrs,
        "root_attrs": root_attrs,
        "activator_attrs": activator_attrs_out,
        "has_activator": has_activator,
    }


# --- Table ---
def _Tabledata(headers, rows, attrs=None):
    headers_with_first = [(h, i == 0) for i, h in enumerate(headers)]
    rows_out = []
    for row in rows:
        cells = []
        for header in prepare_row_headers(row, headers):
            cell = row.cols.get(header.key)
            cell = NULL_CELL if cell is None else cell
            display = SafeString(linebreaksbr(cell.value)) if cell.linebreaks else cell.value
            cells.append((cell, display))
        rows_out.append((row, cells))
    return {
        "headers_with_first": headers_with_first,
        "rows_out": rows_out,
        "attrs": attrs,
    }


# --- Tags ---
def _Tagsdata(tag_type, js_props, editable=True, max_width="300px", attrs=None, has_title=False):
    # `.upper()` forwards through a string or Const-wrapped string (and a
    # StrEnum); StrEnum keys hash equal to their string value.
    all_tags = TAG_TYPE_META[tag_type.upper()].allowed_values
    x_props = (
        "{ initAllTags: '" + to_json(all_tags) + "',"
        " initTags: " + str(js_props.get("initTags", "[]")) + ","
        " onChange: " + str(js_props.get("onChange", "() => {}")) + ", }"
    )
    return {
        "editable": editable,
        "max_width": max_width,
        "attrs": attrs,
        "x_props": x_props,
        "remove_btn_attrs": {"class": "!py-1", "@click": "removeTag(index)"},
        "add_btn_attrs": {"class": "!py-1", "@click": "addTag"},
        "has_title": has_title,
    }


# --- ExpansionPanel ---
def _ExpansionPaneldata(open=False, panel_id=None, attrs=None, header_attrs=None, content_attrs=None, icon_position="left"):
    return {
        "attrs": attrs,
        "header_attrs": header_attrs,
        "content_attrs": content_attrs,
        "icon_position": icon_position,
        "init_data_json": to_json({"open": open}),
        "panel_id": panel_id or False,
        # Plain dict handed to Icon's `attrs` kwarg (the DJC attrs:style / attrs::class
        # nested syntax collapses to this here).
        "icon_attrs": {"style": "width: fit-content;", ":class": "{ 'rotate-180': isOpen }"},
    }


# --- Dialog ---
def _Dialogdata(model=None, attrs=None, activator_attrs=None, title_attrs=None, content_attrs=None,
               confirm_hide=None, confirm_text="Confirm", confirm_href=None, confirm_disabled=None,
               confirm_variant="primary", confirm_color=None, confirm_type=None, confirm_on_click="",
               confirm_attrs=None, cancel_hide=None, cancel_text="Cancel", cancel_href=None,
               cancel_disabled=None, cancel_variant="secondary", cancel_color=None, cancel_type=None,
               cancel_on_click="", cancel_attrs=None, close_on_esc=True, close_on_click_outside=True,
               has_activator=False, has_title=False):
    is_model_overriden = bool(model)
    model = model or "open"

    cancel_attrs = {**(cancel_attrs or {}), "@click": construct_btn_onclick(model, cancel_on_click)}
    confirm_attrs = {**(confirm_attrs or {}), "@click": construct_btn_onclick(model, confirm_on_click)}

    x_data = "{ id: $id('modal-title'), " + ("'" + model + "': false, " if not is_model_overriden else "") + "}"
    root_attrs = {"x-data": x_data}
    if close_on_esc:
        root_attrs["@keydown.escape"] = model + " = false"

    panel_attrs = {}
    if close_on_click_outside:
        panel_attrs["@click.away"] = model + " = false"

    return {
        "model": model,
        "attrs": attrs,
        "activator_attrs": {"@click": model + " = true", **(activator_attrs or {})},
        "content_attrs": content_attrs,
        "title_attrs": title_attrs,
        "root_attrs": root_attrs,
        "backdrop_attrs": {"x-show": model},
        "panel_attrs": panel_attrs,
        "confirm_hide": confirm_hide,
        "confirm_text": confirm_text,
        "confirm_href": confirm_href,
        "confirm_disabled": confirm_disabled,
        "confirm_variant": confirm_variant,
        "confirm_color": confirm_color,
        "confirm_type": confirm_type,
        "confirm_attrs": confirm_attrs,
        "cancel_hide": cancel_hide,
        "cancel_text": cancel_text,
        "cancel_href": cancel_href,
        "cancel_disabled": cancel_disabled,
        "cancel_variant": cancel_variant,
        "cancel_color": cancel_color,
        "cancel_type": cancel_type,
        "cancel_attrs": cancel_attrs,
        "has_activator": has_activator,
        "has_title": has_title,
    }


# --- Bookmarks ---
def _Bookmarksdata(project_id, bookmarks, attrs=None):
    bookmark_data = []
    attachment_data = []
    for bookmark in bookmarks:
        is_attachment = bookmark["attachment"] is not None
        if is_attachment:
            edit_url = (
                f"/edit/{project_id}/bookmark/{bookmark['id']}"
                f"?{ProjectPageTabsToQueryParams.OUTPUTS.value}"
                f"&panel={bookmark['attachment']['output']['id']}"
            )
        else:
            edit_url = f"/edit/{project_id}/bookmark/{bookmark['id']}"
        entry = BookmarkItem(text=bookmark["text"], url=bookmark["url"], id=bookmark["id"], edit_url=edit_url)
        (attachment_data if is_attachment else bookmark_data).append(entry)

    return {
        "bookmark_data": bookmark_data,
        "attachment_data": attachment_data,
        "create_bookmark_url": f"/create/{project_id}/bookmark",
        "menu_items": bookmark_menu_items,
        "attrs": attrs,
        "theme": theme,
        "bookmark_icon_text_attrs": {"class": "py-2 text-sm"},
        "plus_icon_text_attrs": {"class": "px-2 py-1 text-xs"},
        "plus_icon_svg_attrs": {"class": "mt-0.5 ml-1"},
        "menu_list_attrs": {"class": "w-24 ml-8 z-40"},
        "menu_attrs": {"@click_outside": "onContextMenuClickOutside"},
        "bookmark_js": {"onMenuToggle": "onContextMenuToggle"},
    }


# --- Bookmark ---
def _Bookmarkdata(bookmark, js=None):
    bookmark = bookmark._asdict()
    js = js or {}
    x_props = (
        "{ onMenuToggle: " + str(js.get("onMenuToggle", "() => {}")) + ","
        " bookmark: " + to_alpine_json(bookmark) + ", }"
    )
    return {
        "theme": theme,
        "bookmark": bookmark,
        "x_props": x_props,
        "menu_icon_attrs": {"class": "self-center cursor-pointer", "x-ref": "bookmark_menu", "@click": "onMenuToggle"},
        "menu_icon_svg_attrs": {"class": "inline"},
        "menu_icon_text_attrs": {"class": "p-0"},
    }


# --- TabsImpl ---
def _TabsImpldata(tabs, name=None, attrs=None, header_attrs=None, content_attrs=None):
    header_data = []
    content_data = []
    for i, tab in enumerate(tabs, 1):
        header_data.append(
            (
                tab,
                {
                    "@click": f"setOpenTab( {i} )",
                    ":class": "{ 'border-b-2 " + theme.tab_active + "': openTab === " + str(i) + " }",
                },
                {":class": f"openTab === {i} ? '{theme.tab_text_active}' : '{theme.tab_text_inactive}'"},
            )
        )
        content_data.append((tab, {"x-show": f"openTab === {i}"}))
    return {
        "attrs": attrs,
        "header_data": header_data,
        "content_data": content_data,
        "header_attrs": header_attrs,
        "content_attrs": content_attrs,
        "data_init_json": to_json({"name": name}),
    }


# --- TabsStatic ---
def _TabsStaticdata(tabs, index=0, hide_body=False, attrs=None, header_attrs=None, content_attrs=None):
    tabs_data = []
    for tab_index, tab in enumerate(tabs):
        is_selected = tab_index == index
        styling = {
            "tab": "border-b-2 " + theme.tab_active if is_selected else "",
            "text": theme.tab_text_active if is_selected else theme.tab_text_inactive,
        }
        tabs_data.append((tab, styling))
    return {
        "attrs": attrs,
        "tabs_data": tabs_data,
        "header_attrs": header_attrs,
        "content_attrs": content_attrs,
        "hide_body": hide_body,
        "selected_content": tabs[index].content,
    }


# --- ProjectUserAction ---
def _ProjectUserActiondata(project_id, role_id, user_name):
    role_data = {
        "delete_url": f"/delete/{project_id}/{role_id}",
        "role_id": role_id,
        "user_name": user_name,
    }
    return {
        "x_data": "{ role: " + to_alpine_json(role_data) + ", }",
        "icon_svg_attrs": {"class": "inline mb-1"},
        "icon_attrs": {"class": "p-2", "@click.stop": "$dispatch('user_delete', { role })"},
    }


# --- ProjectStatusUpdates ---
def _ProjectStatusUpdatesdata(project_id, status_updates, editable):
    return {
        "create_status_update_url": f"/create/{project_id}/status_update",
        "updates_data": [_make_status_update_data(su) for su in status_updates],
        "editable": editable,
    }


# --- ProjectUsers ---
def _ProjectUsersdata(project_id, roles_with_users, available_roles, available_users, editable):
    table_rows = []
    for role in roles_with_users:
        user = role["user"]
        # The nested action is rendered in place; in Jinja2 we render the
        # ProjectUserAction macro to a string here and stash it in the cell.
        delete_action = (
            ProjectUserAction(user_name=user["name"], project_id=project_id, role_id=role["id"])
            if editable
            else ""
        )
        table_rows.append(
            create_table_row(
                cols={
                    "name": TableCell(user["name"]),
                    "role": TableCell(role["name"]),
                    "delete": TableCell(delete_action),
                },
            )
        )

    role_choices = [(r, r) for r in available_roles] if available_roles else []
    user_choices = [(str(u["id"]), u["name"]) for u in available_users] if available_users else []
    add_user_form = SafeString(
        _render_choice_field("user_id", "User", user_choices) + _render_choice_field("role", "Role", role_choices)
    )

    return {
        "editable": editable,
        "table_headers": roles_table_headers,
        "table_rows": table_rows,
        "add_user_form": add_user_form,
        "submit_url": f"/submit/{project_id}/role/create",
        "project_url": f"/project/{project_id}",
        "table_attrs": {"@user_delete": "onUserDelete"},
        "dialog_confirm_attrs": {":href": "role.delete_url"},
        "dialog_content_attrs": {"class": "w-full"},
        "title_icon_attrs": {"class": "p-2 self-center"},
    }


# --- ProjectInfo ---
def _ProjectInfodata(project, project_tags, contacts, status_updates, roles_with_users, editable):
    pid = project["id"]
    contacts_data = [
        {"name": c["name"], "job": c["job"], "link_url": f"/contacts/{c['link_id']}"} for c in contacts
    ]
    project_info = [
        ProjectInfoEntry("Org", project["organization"]["name"]),
        ProjectInfoEntry("Duration", f"{project['start_date']} - {project['end_date']}"),
        ProjectInfoEntry("Status", project["status"]),
        ProjectInfoEntry("Tags", ", ".join(project_tags) or "-"),
    ]
    return {
        "project_id": pid,
        "project_edit_url": f"/edit/{pid}/",
        "edit_contacts_url": f"/edit/{pid}/contacts/",
        "edit_project_roles_url": f"/edit/{pid}/roles/",
        "contacts_data": contacts_data,
        "roles_with_users": roles_with_users,
        "project_info": project_info,
        "status_updates": status_updates,
        "editable": editable,
        "edit_btn_attrs": {"class": "not-prose"},
    }


# --- ProjectNotes ---
def _ProjectNotesdata(project_id, notes, comments_by_notes, editable):
    return {
        "create_note_url": f"/create/{project_id}/note/",
        "notes_data": _make_notes_data(notes, comments_by_notes),
        "editable": editable,
    }


# --- ProjectOutputAttachments ---
def _ProjectOutputAttachmentsdata(has_attachments, js_props, editable, attrs=None):
    return {
        "has_attachments": has_attachments,
        "editable": editable,
        "attrs": attrs,
        "x_props": "{ ..." + serialize_to_js(js_props) + ", }",
        "text_max_len": FORM_SHORT_TEXT_MAX_LEN,
        "tag_type": "project_output_attachment",
        "preview_btn_attrs": {
            "x-bind:href": "attachment.url",
            "x-text": "attachment.text",
            "target": "_blank",
            "class": "hover:text-gray-600 !underline",
            "style": "color: cornflowerblue;",
        },
        "edit_btn_attrs": {"class": "!py-1", "x-text": "attachment.isPreview ? 'Edit' : 'Preview'", "@click": "() => $emit('toggleAttachment', index)"},
        "remove_btn_attrs": {"class": "!py-1", "@click": "() => $emit('removeAttachment', index)"},
        "tags_js_props": {"initTags": "attachment.tags", "onChange": "(tags) => $emit('setAttachmentTags', index, tags)"},
        "tags_attrs": {"class": "pb-8"},
    }
# FORM_SHORT_TEXT_MAX_LEN and serialize_to_js are shared infra globals.


# --- ProjectOutputDependency ---
def _ProjectOutputDependencydata(dependency):
    dep = dependency  # RenderedOutputDep
    output = dep.dependency.output  # the output dict
    return {
        "attachments": dep.attachments,
        "x_props": "{ initAttachments: '" + to_json(dep.attachments) + "' }",
        "output_completed": output["completed"],
        "output_description": output.get("description"),
        "output_name": output["name"],
        "phase_type_title": title_case(output["phase"]["phase_template"]["type"]),
        "phase_url": dep.phase_url,
        "placeholder": OUTPUT_DESCRIPTION_PLACEHOLDER,
        "warn_icon_attrs": {"class": "float-left pr-1"},
        "phase_btn_attrs": {"target": "_blank", "class": "hover:text-gray-600 !underline"},
    }
# to_json, title_case, OUTPUT_DESCRIPTION_PLACEHOLDER are shared infra globals.


# --- ProjectOutputForm ---
def _ProjectOutputFormdata(data, editable):
    # data is a RenderedProjectOutput namedtuple
    return {
        "editable": editable,
        "update_output_url": data.update_output_url,
        "output_description": data.output.get("description"),
        "output_completed": data.output["completed"],
        "attachments": data.attachments,
        "x_props": "{ initAttachments: '" + to_json([d._asdict() for d in data.attachments]) + "' }",
        "placeholder": OUTPUT_DESCRIPTION_PLACEHOLDER,
        "add_btn_attrs": {"@click": "addAttachment"},
        "save_btn_attrs": {"@click": "onOutputSubmit({ reload: true })"},
        "attach_js_props": {
            "attachments": "attachments.value",
            "onToggleAttachment": "(index) => toggleAttachmentPreview(index)",
            "onSetAttachmentTags": "(index, tags) => setAttachmentTags(index, tags)",
            "onUpdateAttachmentData": "(index, data) => updateAttachmentData(index, data)",
            "onRemoveAttachment": "(index) => removeAttachment(index)",
        },
    }
# data.attachments are RenderedAttachment namedtuples -> ._asdict() for to_json.
# to_json, OUTPUT_DESCRIPTION_PLACEHOLDER are shared infra globals.


# --- ProjectOutputs ---
def _ProjectOutputsdata(project_id, phase_type, outputs, editable):
    outputs_data = []
    for output, attachments, dependencies in outputs:
        attach_data = [RenderedAttachment(url=a[0]["url"], text=a[0]["text"], tags=a[1]) for a in attachments]
        deps = []
        for dep in dependencies:
            dep_output, dep_attachments = dep
            deps.append(
                RenderedOutputDep(
                    dependency=OutputWithAttachments(output=dep_output, attachments=dep_attachments),
                    phase_url=f"/phase/{project_id}/{dep_output['phase']['phase_template']['type']}",
                    attachments=[{"url": a[0]["url"], "text": a[0]["text"], "tags": a[1]} for a in dep_attachments],
                )
            )
        has_missing_deps = any(not o["completed"] for o, _ in dependencies)
        outputs_data.append(
            RenderedProjectOutput(
                output=output,
                dependencies=deps,
                has_missing_deps=has_missing_deps,
                output_data={"editable": editable},
                attachments=attach_data,
                update_output_url="/update",
            )
        )
    return {
        "outputs_data": outputs_data,
        "editable": editable,
        "panel_attrs": {"class": "border-b border-solid border-gray-300 pb-2 mb-3"},
        "panel_header_attrs": {"class": "flex align-center justify-between"},
    }
# RenderedAttachment, RenderedOutputDep, OutputWithAttachments, RenderedProjectOutput are shared infra types.


# --- ProjectOutputsSummary ---
def _ProjectOutputsSummarydata(project_id, outputs, editable, phase_titles):
    outputs_by_phase = group_by(outputs, lambda output, _: output[0]["phase"]["phase_template"]["type"])
    groups = []
    for phase_meta in PROJECT_PHASES_META.values():
        phase_outputs = outputs_by_phase.get(phase_meta.type, [])
        groups.append(
            {
                "phase_title": phase_titles[phase_meta.type],
                "phase_type": phase_meta.type,
                "outputs": phase_outputs,
                "has_outputs": bool(phase_outputs),
            }
        )
    return {
        "project_id": project_id,
        "editable": editable,
        "groups": groups,
        "panel_header_attrs": {"class": "flex gap-x-2 prose"},
    }
# group_by and PROJECT_PHASES_META are shared infra globals.


# --- Form ---
def _Formdata(type=None, editable=True, method="post", submit_hide=None, submit_text="Submit", submit_href=None, submit_disabled=None, submit_variant="primary", submit_color=None, submit_type="submit", submit_attrs=None, cancel_hide=None, cancel_text="Cancel", cancel_href=None, cancel_disabled=None, cancel_variant="secondary", cancel_color=None, cancel_type="button", cancel_attrs=None, actions_hide=None, actions_attrs=None, form_content_attrs=None, attrs=None):
    form_content_tag = {"table": "table", "paragraph": "div", "ul": "ul"}.get(type, "div")
    form_attrs = {}
    if submit_href and editable:
        form_attrs["action"] = submit_href
    return {
        "form_content_tag": form_content_tag,
        "form_attrs": form_attrs,
        "form_content_attrs": form_content_attrs,
        "method": method,
        "attrs": attrs,
        "actions_hide": actions_hide,
        "actions_attrs": actions_attrs,
        "submit_hide": submit_hide,
        "submit_text": submit_text,
        "submit_disabled": submit_disabled or not editable,
        "submit_variant": submit_variant,
        "submit_color": submit_color,
        "submit_type": submit_type,
        "submit_attrs": {**(submit_attrs or {}), ":disabled": "isSubmitting"},
        "cancel_hide": cancel_hide,
        "cancel_text": cancel_text,
        "cancel_href": cancel_href,
        "cancel_disabled": cancel_disabled,
        "cancel_variant": cancel_variant,
        "cancel_color": cancel_color,
        "cancel_type": cancel_type,
        "cancel_attrs": cancel_attrs,
    }

#####################################
#
# JINJA2 ENGINE SETUP
#
#####################################
# Citry components become Jinja2 macros (one per component). Jinja2 has no
# component model, provide/inject, or dependency collection, so this section
# supplies the small amount of native machinery the macros lean on:
#   - html_attrs / merge_attrs: render and merge element attributes, including
#     the Vue/django-components style class merge (the parallel to citry's
#     c-bind + c-class). This is the Jinja2 stand-in for Django's
#     {% html_attrs %} tag.
#   - the DJC filters (to_json, naturaltime, ...) registered as real Jinja2
#     filters (Jinja2 has filter syntax; citry does not).
#   - a per-render JS dependency collector, post-processed into the page at the
#     <c-js> marker, mirroring how citry/django-components dedupe and inject
#     each rendered component's inline JS.


def _class_tokens(*sources: Any) -> list[str]:
    """Flatten class sources (str / list / dict{name: enabled}) to deduped tokens."""
    seen: set[str] = set()
    out: list[str] = []

    def add(src: Any) -> None:
        if src is None or src is False:
            return
        if isinstance(src, (list, tuple)):
            for item in src:
                add(item)
        elif isinstance(src, dict):
            for key, enabled in src.items():
                if enabled:
                    add(key)
        else:
            for token in str(src).split():
                if token not in seen:
                    seen.add(token)
                    out.append(token)

    for source in sources:
        add(source)
    return out


def html_attrs(attrs: Any = None, *extra_classes: Any, **extra: Any) -> Markup:
    """
    Render an HTML attribute string from a dict plus extra classes/attrs.

    Mirrors citry's `c-bind` spread + `c-class`: `class` sources (the dict's own
    `class`, each extra class, and a `class=` keyword) merge and dedupe in source
    order; other attributes are last-one-wins, with `True` rendering as a bare
    boolean attribute and `False`/`None` dropped.
    """
    attrs = dict(attrs or {})
    classes = _class_tokens(attrs.pop("class", None), *extra_classes, extra.pop("class", None))
    merged = {**attrs, **extra}

    parts: list[Markup] = []
    if classes:
        parts.append(Markup(' class="{}"').format(" ".join(classes)))
    for key, value in merged.items():
        if value is True:
            parts.append(Markup(" {}").format(key))
        elif value is False or value is None:
            continue
        else:
            parts.append(Markup(' {}="{}"').format(key, value))
    return Markup("").join(parts)


def merge_attrs(*dicts: Any) -> dict:
    """Merge several attribute dicts (multiple `c-bind`): non-class last-wins, class concatenated."""
    out: dict = {}
    classes: list[str] = []
    for source in dicts:
        if not source:
            continue
        for key, value in source.items():
            if key == "class":
                if value:
                    classes.append(str(value))
            else:
                out[key] = value
    if classes:
        out["class"] = " ".join(classes)
    return out


# ----- JS dependency collection (the parallel to citry's dependency render) -----

_JS_PLACEHOLDER = "<!--JINJA2_JS_DEPS-->"
_CSS_PLACEHOLDER = "<!--JINJA2_CSS_DEPS-->"

# Per-render set of component names whose inline JS was collected (dedupe by
# component, matching how citry/django-components emit each component's JS once).
_collected_js: list[str] = []
_collected_js_seen: set[str] = set()


def register_js(name: str) -> Markup:
    """Record a component's inline JS for injection at the <c-js> marker. Renders nothing inline."""
    if name in COMPONENT_JS and name not in _collected_js_seen:
        _collected_js_seen.add(name)
        _collected_js.append(name)
    return Markup("")


# `finalize` renders None as empty text (citry and Django templates both do; plain
# Jinja2 would print the literal "None").
env = Environment(
    autoescape=True,
    extensions=["jinja2.ext.do"],
    finalize=lambda value: "" if value is None else value,
)
env.globals.update(
    html_attrs=html_attrs,
    merge_attrs=merge_attrs,
    register_js=register_js,
    JS_PLACEHOLDER=Markup(_JS_PLACEHOLDER),
    CSS_PLACEHOLDER=Markup(_CSS_PLACEHOLDER),
)
env.filters.update(
    to_json=to_json,
    to_alpine_json=to_alpine_json,
    serialize_to_js=serialize_to_js,
    get_item=get_item,
    default_if_none=default_if_none,
    title_case=title_case,
    linebreaksbr=linebreaksbr,
    naturaltime=naturaltime,
    format_timestamp=format_timestamp,
)
# Expose every helper/type/constant defined in this module to the macros, so a
# macro can mirror citry's `template_data` by calling these in `{% set %}`
# expressions (the data is shaped in Python, the macro renders the result).
_this_module = html_attrs.__module__  # whatever this file is run as (script/import)
for _name, _obj in list(globals().items()):
    if _name.startswith("__"):
        continue
    if callable(_obj) and getattr(_obj, "__module__", None) == _this_module:
        env.globals.setdefault(_name, _obj)
env.globals.update(
    theme=theme,
    ICONS=ICONS,
    VARIANTS=VARIANTS,
    PROJECT_PHASES_META=PROJECT_PHASES_META,
    NULL_CELL=NULL_CELL,
    COMPONENT_JS=COMPONENT_JS,
)


#####################################
# MACROS (one per citry component)
#####################################

_MACROS_SRC = r"""
{% macro Button(href=none, link=none, disabled=false, variant="primary", color="default", type="button", attrs=none) %}
{%- set common_css = "inline-flex w-full text-sm font-semibold sm:mt-0 sm:w-auto focus-visible:outline-2 focus-visible:outline-offset-2" -%}
{%- if variant == "plain" -%}{%- set btn_class = common_css -%}
{%- else -%}{%- set btn_class = get_styling_css(variant, color, disabled) ~ " " ~ common_css ~ " px-3 py-2 justify-center rounded-md shadow-sm" -%}{%- endif -%}
{%- set is_link = (not disabled) and (href or link) -%}
{%- set all_attrs = dict(attrs or {}) -%}
{%- if disabled %}{% do all_attrs.update({"aria-disabled": "true"}) %}{% endif -%}
{%- if is_link -%}
<a{{ html_attrs(all_attrs, btn_class, "no-underline", href=href) }}>{% if caller %}{{ caller() }}{% endif %}</a>
{%- else -%}
<button{{ html_attrs(all_attrs, btn_class, type=type, disabled=disabled) }}>{% if caller %}{{ caller() }}{% endif %}</button>
{%- endif -%}
{% endmacro %}


{% macro heroicons(name=none, variant=none, size=none, color=none, stroke_width=none, viewbox=none, attrs=none) %}
{%- set kw = IconDefaults(name=name, variant=variant, size=size, color=color, stroke_width=stroke_width, viewbox=viewbox, attrs=attrs) -%}
{%- set icon_paths = ICONS["outline"]["academic-cap"] -%}
{%- set default_attrs = {"viewBox": kw.viewbox, "style": "width: " ~ kw.size ~ "px; height: " ~ kw.size ~ "px", "aria-hidden": "true"} -%}
{%- if kw.variant == "outline" -%}{%- do default_attrs.update({"fill": "none", "stroke": kw.color, "stroke-width": kw.stroke_width}) -%}
{%- else -%}{%- do default_attrs.update({"fill": kw.color, "stroke": "none"}) -%}{%- endif -%}
<svg{{ html_attrs(merge_attrs(default_attrs, kw.attrs)) }}>
{%- for path_attrs in icon_paths %}<path{{ html_attrs(path_attrs) }} />{% endfor -%}
</svg>
{% endmacro %}


{% macro Icon(name=none, variant=none, size=none, stroke_width=none, viewbox=none, svg_attrs=none, color="", icon_color="", text_color="", href=none, text_attrs=none, link_attrs=none, attrs=none) %}
{%- set color = color or "" -%}
{%- set icon_color = icon_color or color -%}
{%- set text_color = text_color or color -%}
{%- set svg_attrs2 = dict(svg_attrs or {}) -%}
{%- do svg_attrs2.update({"class": (svg_attrs2.get("class") or "") ~ " " ~ (icon_color or "") ~ " h-6 w-6 shrink-0"}) -%}
<div{{ html_attrs(attrs) }}>
{%- set icon_link_class = "group flex gap-x-3 rounded-md text-sm leading-6 font-semibold" -%}
{%- if href -%}
<a{{ html_attrs(merge_attrs(link_attrs, text_attrs), text_color, icon_link_class, href=href) }}>
{{- heroicons(name=name, variant=variant, size=size, viewbox=viewbox, stroke_width=stroke_width, attrs=svg_attrs2) }}{% if caller %}{{ caller() }}{% endif %}</a>
{%- else -%}
<span{{ html_attrs(text_attrs, text_color, icon_link_class) }}>
{{- heroicons(name=name, variant=variant, size=size, viewbox=viewbox, stroke_width=stroke_width, attrs=svg_attrs2) }}{% if caller %}{{ caller() }}{% endif %}</span>
{%- endif -%}
</div>
{% endmacro %}


{% macro Breadcrumbs(items, attrs=none) %}
<nav aria-label="Breadcrumb"{{ html_attrs(attrs, "flex border-b border-gray-200 bg-white") }}>
<ol role="list" class="mx-auto flex w-full max-w-screen-xl space-x-4 px-4 sm:px-6 lg:px-8">
{%- for crumb in items %}
<li class="flex"><div class="flex items-center">
{%- if not loop.first %}<svg class="h-full w-6 flex-shrink-0 text-gray-200" viewBox="0 0 24 44" preserveAspectRatio="none" fill="currentColor" aria-hidden="true"><path d="M.293 0l22 22-22 22h1.414l22-22-22-22H.293z" /></svg>{% endif -%}
{%- if crumb.link %}<a{{ html_attrs(crumb.item_attrs, "ml-4 text-sm font-medium text-gray-500 hover:text-gray-700", href=crumb.link) }}>{{ crumb.value }}</a>
{%- else %}<span{{ html_attrs(crumb.item_attrs, "ml-4 text-sm font-medium text-gray-500 hover:text-gray-700") }}>{{ crumb.value }}</span>{% endif -%}
</div></li>
{%- endfor %}
</ol></nav>
{% endmacro %}


{% macro List(items, attrs=none, item_attrs=none, empty="") %}
<ul role="list"{{ html_attrs(attrs, "flex flex-col gap-4") }}>
{%- for item in items %}
<li{{ html_attrs(merge_attrs(item.attrs, item_attrs), "group flex justify-between gap-x-6 border border-gray-300 pl-4 pr-6 bg-white") }}>
<div class="flex min-w-0 w-full gap-x-4"><div class="min-w-0 flex-auto">
{%- if item.link %}<a href="{{ item.link }}"><p class="text-sm font-semibold leading-6 text-gray-900 hover:text-gray-500">{{ item.value }}</p></a>
{%- else %}<p class="text-sm font-semibold leading-6 text-gray-900 hover:text-gray-500">{{ item.value }}</p>{% endif -%}
</div></div></li>
{%- else %}{{ empty }}{% endfor %}
</ul>
{% endmacro %}

{# ===== MenuList ===== #}
{% macro MenuList(items, attrs=none) %}
{%- set item_groups = prepare_menu_items(items) -%}
<div role="menu" aria-orientation="vertical"{{ html_attrs(attrs, "mt-2 divide-y divide-gray-300 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none") }}>
{%- for group in item_groups %}
<div class="py-1" role="group">
{%- for item in group -%}
{% if item.link %}<a role="menuitem" tabindex="0"{{ html_attrs(item.item_attrs, "block", href=item.link) }}>{{ item.value }}</a>
{%- else %}<div role="menuitem" tabindex="0"{{ html_attrs(item.item_attrs) }}>{{ item.value }}</div>{% endif -%}
{% endfor -%}
</div>
{%- endfor %}
</div>
{% endmacro %}


{# ===== Menu ===== #}
{% macro Menu(items, model=none, attrs=none, activator_attrs=none, list_attrs=none, close_on_esc=true, close_on_click_outside=true, anchor=none, anchor_dir="bottom", activator="") %}
{%- set has_activator = (activator != "") or (caller is defined and caller) -%}
{%- set d = _Menudata(items, model=model, attrs=attrs, activator_attrs=activator_attrs, list_attrs=list_attrs, close_on_esc=close_on_esc, close_on_click_outside=close_on_click_outside, anchor=anchor, anchor_dir=anchor_dir, has_activator=has_activator) -%}
<div{{ html_attrs(merge_attrs(d["attrs"], d["root_attrs"])) }}>
{%- if d["has_activator"] %}<div{{ html_attrs(d["activator_attrs"]) }}>
{%- if activator %}{{ activator }}{% elif caller %}{{ caller() }}{% endif -%}
</div>{% endif -%}
{{ MenuList(items=d["items"], attrs=d["list_attrs"]) }}
</div>
{% endmacro %}


{# ===== Table ===== #}
{% macro Table(headers, rows, attrs=none) %}
{%- set d = _Tabledata(headers, rows, attrs=attrs) -%}
<div{{ html_attrs(d["attrs"], "flow-root") }}>
<div class="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
<div class="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
<table class="min-w-full divide-y divide-gray-300">
<thead><tr>
{%- for h, first in d["headers_with_first"] %}
<th scope="col"{{ html_attrs(h.cell_attrs, ['text-left text-sm font-semibold text-gray-900 py-3.5', 'pl-4 pr-3 sm:pl-0' if first else 'px-3']) }}>
{%- if h.hidden %}<span class="sr-only">{{ h.name }}</span>{% else %}{{ h.name }}{% endif -%}
</th>
{%- endfor %}
</tr></thead>
<tbody class="divide-y divide-gray-200">
{%- for row, cells in d["rows_out"] %}
<tr{{ html_attrs(row.row_attrs) }}>
{%- for cell, display in cells %}
<td{{ html_attrs(merge_attrs(cell.cell_attrs, row.col_attrs), colspan=cell.colspan) }}>
{%- if cell.link %}<a{{ html_attrs(cell.link_attrs, href=cell.link) }}>{{ display }}</a>{% else %}{{ display }}{% endif -%}
</td>
{%- endfor %}
</tr>
{%- endfor %}
</tbody>
</table>
</div></div></div>
{% endmacro %}


{# ===== Tags ===== #}
{% macro Tags(tag_type, js_props, editable=true, max_width="300px", attrs=none, title="") %}
{%- set has_title = (title != "") -%}
{%- set d = _Tagsdata(tag_type, js_props, editable=editable, max_width=max_width, attrs=attrs, has_title=has_title) -%}
<div{{ html_attrs(d["attrs"], "pt-3 flex flex-col gap-y-3 items-start", **{"x-data": "tags", "x-props": d["x_props"]}) }}>
<input x-ref="tagsInput" type="hidden" name="tags" value="" />
{%- if title %}{{ title }}{% else %}<p class="text-sm">Tags:</p>{% endif %}
<template x-for="(tag, index) in tags.value">
<div class="tag text-sm flex flex-col gap-1 w-full"{{ html_attrs(none, style="max-width:" ~ d["max_width"]) }}>
<div class="flex gap-6 w-full justify-between items-center">
<select name="_tags" class="flex-auto py-1 px-2" @change="(ev) => setTag(index, ev.target.value)"{{ html_attrs(none, disabled=(not d["editable"])) }}>
<template x-for="option in tag.options">
<option :value="option" :selected="option === tag.value" x-text="option"></option>
</template>
</select>
{%- if d["editable"] %}<div>
{%- call Button(color="error", attrs=d["remove_btn_attrs"]) %}Remove{% endcall -%}
</div>{% endif %}
</div>
</div>
</template>
{%- if d["editable"] %}<div x-show="tags.value.length < allTags.value.length">
{%- call Button(attrs=d["add_btn_attrs"]) %}Add tag{% endcall -%}
</div>{% endif %}
</div>
{% endmacro %}


{# ===== ExpansionPanel ===== #}
{% macro ExpansionPanel(open=false, panel_id=none, attrs=none, header_attrs=none, content_attrs=none, icon_position="left", header="", content="") %}
{{- register_js("ExpansionPanel") -}}
{%- set d = _ExpansionPaneldata(open=open, panel_id=panel_id, attrs=attrs, header_attrs=header_attrs, content_attrs=content_attrs, icon_position=icon_position) -%}
<div x-data="expansion_panel"{{ html_attrs(d["attrs"], **{"data-init": d["init_data_json"], "data-panelid": d["panel_id"]}) }}>
<div @click="togglePanel"{{ html_attrs(d["header_attrs"], 'pb-2 cursor-pointer') }}>
{%- if d["icon_position"] == 'left' %}{{ Icon(name="chevron-down", variant="outline", attrs=d["icon_attrs"]) }}{% endif -%}
{{ header }}
{%- if d["icon_position"] == 'right' %}{{ Icon(name="chevron-down", variant="outline", attrs=d["icon_attrs"]) }}{% endif -%}
</div>
<div x-show="isOpen"{{ html_attrs(d["content_attrs"]) }}>{{ content }}</div>
</div>
{% endmacro %}


{# ===== Dialog ===== #}
{% macro Dialog(model=none, attrs=none, activator_attrs=none, title_attrs=none, content_attrs=none, confirm_hide=none, confirm_text="Confirm", confirm_href=none, confirm_disabled=none, confirm_variant="primary", confirm_color=none, confirm_type=none, confirm_on_click="", confirm_attrs=none, cancel_hide=none, cancel_text="Cancel", cancel_href=none, cancel_disabled=none, cancel_variant="secondary", cancel_color=none, cancel_type=none, cancel_on_click="", cancel_attrs=none, close_on_esc=true, close_on_click_outside=true, activator="", prepend="", title="", content="", append="") %}
{%- set has_activator = (activator or caller) | default(false, true) | bool if false else (true if (activator or caller) else false) -%}
{%- set has_title = true if title else false -%}
{%- set d = _Dialogdata(model=model, attrs=attrs, activator_attrs=activator_attrs, title_attrs=title_attrs, content_attrs=content_attrs, confirm_hide=confirm_hide, confirm_text=confirm_text, confirm_href=confirm_href, confirm_disabled=confirm_disabled, confirm_variant=confirm_variant, confirm_color=confirm_color, confirm_type=confirm_type, confirm_on_click=confirm_on_click, confirm_attrs=confirm_attrs, cancel_hide=cancel_hide, cancel_text=cancel_text, cancel_href=cancel_href, cancel_disabled=cancel_disabled, cancel_variant=cancel_variant, cancel_color=cancel_color, cancel_type=cancel_type, cancel_on_click=cancel_on_click, cancel_attrs=cancel_attrs, close_on_esc=close_on_esc, close_on_click_outside=close_on_click_outside, has_activator=has_activator, has_title=has_title) -%}
<div{{ html_attrs(merge_attrs(d["root_attrs"], d["attrs"])) }}>
{%- if d["has_activator"] %}<div{{ html_attrs(d["activator_attrs"]) }}>{% if activator %}{{ activator }}{% elif caller %}{{ caller() }}{% endif %}</div>{% endif -%}
<div class="relative z-50" :aria-labelledby="id" role="dialog" aria-modal="true" x-cloak>
<div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"{{ html_attrs(d["backdrop_attrs"]) }}></div>
<div class="fixed inset-0 z-50 w-screen overflow-y-auto"{{ html_attrs(d["backdrop_attrs"]) }}>
<div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
<div class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg"{{ html_attrs(d["panel_attrs"]) }}>
<div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
<div class="sm:flex sm:items-start">
{{ prepend }}
<div{{ html_attrs(d["content_attrs"]) }}>
{%- if d["has_title"] %}<h3 :id="id"{{ html_attrs(d["title_attrs"], 'font-semibold text-gray-900') }}>{{ title }}</h3>{% endif -%}
{{ content }}
</div>
{{ append }}
</div>
</div>
<div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 gap-5">
{%- if not d["confirm_hide"] %}{{ Button(variant=d["confirm_variant"], color=d["confirm_color"], disabled=d["confirm_disabled"], href=d["confirm_href"], type=d["confirm_type"], attrs=d["confirm_attrs"], _body=d["confirm_text"]) }}{% endif -%}
{%- if not d["cancel_hide"] %}{{ Button(variant=d["cancel_variant"], color=d["cancel_color"], disabled=d["cancel_disabled"], href=d["cancel_href"], type=d["cancel_type"], attrs=d["cancel_attrs"], _body=d["cancel_text"]) }}{% endif -%}
</div>
</div>
</div>
</div>
</div>
</div>
{% endmacro %}


{# ===== Bookmarks ===== #}
{% macro Bookmarks(project_id, bookmarks, attrs=none) %}
{{- register_js("Bookmarks") -}}
{%- set d = _Bookmarksdata(project_id=project_id, bookmarks=bookmarks, attrs=attrs) -%}
<li x-data="bookmarks"{{ html_attrs(d["attrs"], 'pt-4') }}>
{%- call Icon(name="bookmark", variant="outline", text_attrs=d["bookmark_icon_text_attrs"]) %}Project Bookmarks{% endcall %}
<ul class="mx-4">
{%- for bookmark in d["bookmark_data"] %}{{ Bookmark(bookmark=bookmark, js=d["bookmark_js"]) }}{% endfor %}
<li>
{%- call Icon(name="plus", variant="outline", size=18, href=d["create_bookmark_url"], color=d["theme"].sidebar_link, text_attrs=d["plus_icon_text_attrs"], svg_attrs=d["plus_icon_svg_attrs"]) %}Add New Bookmark{% endcall %}
</li>
<div class="border-b border-gray-200 my-2 pt-2 text-sm font-bold">Attachments:</div>
{%- for bookmark in d["attachment_data"] %}{{ Bookmark(bookmark=bookmark, js=d["bookmark_js"]) }}{% endfor %}
</ul>
<template x-if="contextMenuItem.value">
<div class="self-center">
{{- Menu(items=d["menu_items"], model="contextMenuItem.value", anchor="contextMenuRef.value", anchor_dir="bottom", list_attrs=d["menu_list_attrs"], attrs=d["menu_attrs"]) }}
</div>
</template>
</li>
{% endmacro %}


{# ===== Bookmark ===== #}
{% macro Bookmark(bookmark, js=none) %}
{{- register_js("Bookmark") -}}
{%- set d = _Bookmarkdata(bookmark=bookmark, js=js) -%}
<li x-data="bookmark" x-props="{{ d["x_props"] }}" class="list-disc ml-8">
<div class="flex">
<a{{ html_attrs(none, ['grow px-2 py-1 text-xs font-semibold', d["theme"].sidebar_link], href=d["bookmark"]['url'], target="_blank") }}>{{ d["bookmark"]['text'] }}</a>
{{- Icon(name="ellipsis-vertical", variant="outline", color=d["theme"].sidebar_link, svg_attrs=d["menu_icon_svg_attrs"], text_attrs=d["menu_icon_text_attrs"], attrs=d["menu_icon_attrs"]) }}
</div>
</li>
{% endmacro %}


{# ===== TabsImpl ===== #}
{% macro TabsImpl(tabs, name=none, attrs=none, header_attrs=none, content_attrs=none) %}
{%- do register_js("TabsImpl") -%}
{%- set d = _TabsImpldata(tabs, name=name, attrs=attrs, header_attrs=header_attrs, content_attrs=content_attrs) -%}
<div x-data="tabs"{{ html_attrs(d["attrs"], "flex flex-col", **{"data-init": d["data_init_json"]}) }}>
<ul class="flex border-b text-sm">
{%- for tab, li_attrs, a_attrs in d["header_data"] %}
{%- if not tab.disabled %}
<li{{ html_attrs(merge_attrs(li_attrs, d["header_attrs"])) }}>
<a href="#"{{ html_attrs(a_attrs, "bg-white inline-block py-2 px-4 font-semibold transition") }}>{{ tab.header }}</a>
</li>
{%- else %}
<li class="mr-1"><p class="text-gray-300 bg-white inline-block py-2 px-4 font-semibold">{{ tab.header }}</p></li>
{%- endif -%}
{%- endfor %}
</ul>
<div class="w-full h-full flex-grow-1 relative overflow-y-scroll" x-ref="container">
<article class="px-4 pt-5 absolute w-full h-full">
{%- for tab, show_attrs in d["content_data"] %}
<div{{ html_attrs(merge_attrs(show_attrs, d["content_attrs"])) }}>{{ tab.content }}</div>
{%- endfor %}
</article>
</div>
</div>
{% endmacro %}


{# ===== Tabs ===== #}
{% macro Tabs(tabs, name=none, attrs=none, header_attrs=none, content_attrs=none) %}
{{- TabsImpl(tabs=tabs, name=name, attrs=attrs, header_attrs=header_attrs, content_attrs=content_attrs) -}}
{% endmacro %}


{# ===== TabItem ===== #}
{% macro TabItem(header, disabled=false) %}{% if caller %}{{ caller() }}{% endif %}{% endmacro %}


{# ===== TabsStatic ===== #}
{% macro TabsStatic(tabs, index=0, hide_body=false, attrs=none, header_attrs=none, content_attrs=none) %}
{%- set d = _TabsStaticdata(tabs, index=index, hide_body=hide_body, attrs=attrs, header_attrs=header_attrs, content_attrs=content_attrs) -%}
<div{{ html_attrs(d["attrs"], "flex flex-col") }}>
<ul class="flex border-b mb-5 bg-white">
{%- for tab, styling in d["tabs_data"] %}
{%- if not tab.disabled %}
<li{{ html_attrs(d["header_attrs"], ['border-b-2', styling['tab']]) }}>
<a{{ html_attrs(d["header_attrs"], ['bg-white inline-block py-2 px-4 font-semibold transition', styling['text']], href=tab.href) }}>{{ tab.header }}</a>
</li>
{%- else %}
<li class="mr-1"><p class="text-gray-300 bg-white inline-block py-2 px-4 font-semibold">{{ tab.header }}</p></li>
{%- endif -%}
{%- endfor %}
</ul>
{%- if not d["hide_body"] %}
<div class="w-full h-full flex-grow-1 relative overflow-y-scroll">
<article class="px-4 pt-5 absolute w-full h-full">
<div{{ html_attrs(d["content_attrs"]) }}>{{ d["selected_content"] }}</div>
</article>
</div>
{%- endif %}
</div>
{% endmacro %}


{# ===== ProjectUserAction ===== #}
{% macro ProjectUserAction(project_id=none, role_id=none, user_name=none) %}
{%- set d = _ProjectUserActiondata(project_id, role_id, user_name) -%}
<div x-data="{{ d['x_data'] }}">
{{- Icon(name="trash", variant="outline", size=18, href="#", color="text-gray-500 hover:text-gray-400", svg_attrs=d["icon_svg_attrs"], attrs=d["icon_attrs"]) -}}
</div>
{% endmacro %}


{# ===== ProjectStatusUpdates ===== #}
{% macro ProjectStatusUpdates(project_id=none, status_updates=none, editable=none) %}
{%- set d = _ProjectStatusUpdatesdata(project_id, status_updates, editable) -%}
<div class="prose border-b border-neutral-300 pb-8">
  <div class="flex justify-between items-start mb-4">
    <h3 class="mt-0">Status Updates</h3>
    {% if d["editable"] %}{% call Button(href=d["create_status_update_url"]) %}Add status update{% endcall %}{% endif %}
  </div>
  {% if d["updates_data"] %}
  <div class="mt-8">
    {% for update in d["updates_data"] %}
    <div class="px-3 py-2" style="border-top: solid 1px lightgrey">
      <div class="flex justify-between gap-4 pt-2">
        <span class="prose-sm prose-figure">{{ update['timestamp'] }}</span>
        {% if d["editable"] %}{{ Icon(name="pencil-square", variant="outline", href=update['edit_href'], color="text-gray-400 hover:text-gray-500") }}{% endif %}
      </div>
      <p class="my-0 text-gray-900">{{ update['text'] }}</p>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endmacro %}


{# ===== ProjectUsers ===== #}
{% macro ProjectUsers(project_id=none, roles_with_users=none, available_roles=none, available_users=none, editable=false) %}
{{- register_js("ProjectUsers") -}}
{%- set d = _ProjectUsersdata(project_id, roles_with_users, available_roles, available_users, editable) -%}
<div x-data="project_users">
  {% if d["table_rows"] %}{{ Table(headers=d["table_headers"], rows=d["table_rows"], attrs=d["table_attrs"]) }}{% endif %}
  {% if d["editable"] %}
  <div>
    <h4>Set project roles</h4>
    <form{{ html_attrs(none, **{"hx-post": d["submit_url"], "hx-swap": "outerHTML", "method": "post"}) }}>
      <table>{{ d["add_user_form"] }}</table>
      {% call Button(type="submit") %}Set role{% endcall %}
      {% call Button(variant="secondary", href=d["project_url"]) %}Go back{% endcall %}
    </form>
    <template x-if="role && isDeleteDialogOpen">
      {% set _dlg_title %}<div class="flex"><span>Remove <span x-text="role && role.user_name"></span> from this project?</span>{{ Icon(name="trash", variant="outline", size=18, attrs=d["title_icon_attrs"]) }}</div>{% endset %}
      {% set _dlg_content %}<div>This action cannot be undone.</div>{% endset %}
      {{ Dialog(model="isDeleteDialogOpen", confirm_text="Delete", confirm_href="#", confirm_color="error", confirm_attrs=d["dialog_confirm_attrs"], content_attrs=d["dialog_content_attrs"], title=_dlg_title, content=_dlg_content) }}
    </template>
  </div>
  {% endif %}
</div>
{% endmacro %}


{# ===== ProjectInfo ===== #}
{% macro ProjectInfo(project=none, project_tags=none, contacts=none, status_updates=none, roles_with_users=none, editable=none) %}
{%- set d = _ProjectInfodata(project, project_tags, contacts, status_updates, roles_with_users, editable) -%}
<div class="prose flex flex-col gap-8">
  <div class="border-b border-neutral-300">
    <div class="flex justify-between items-start">
      <h3 class="mt-0">Project Info</h3>
      {% if d["editable"] %}{% call Button(href=d["project_edit_url"], attrs=d["edit_btn_attrs"]) %}Edit Project{% endcall %}{% endif %}
    </div>
    <table>
      {% for key, value in d["project_info"] %}
      <tr>
        <td class="font-bold pr-4">{{ key }}:</td>
        <td>{{ value }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>
  {{ ProjectStatusUpdates(project_id=d["project_id"], status_updates=d["status_updates"], editable=d["editable"]) }}
  <div class="xl:grid xl:grid-cols-2 gap-10">
    <div class="border-b border-neutral-300">
      <div class="flex justify-between items-start">
        <h3 class="mt-0">Team</h3>
        {% if d["editable"] %}{% call Button(href=d["edit_project_roles_url"], attrs=d["edit_btn_attrs"]) %}Edit Team{% endcall %}{% endif %}
      </div>
      {{ ProjectUsers(project_id=d["project_id"], roles_with_users=d["roles_with_users"], available_roles=none, available_users=none, editable=false) }}
    </div>
    <div>
      <div class="flex justify-between items-start max-xl:mt-6">
        <h3 class="mt-0">Contacts</h3>
        {% if d["editable"] %}{% call Button(href=d["edit_contacts_url"], attrs=d["edit_btn_attrs"]) %}Edit Contacts{% endcall %}{% endif %}
      </div>
      {% if d["contacts_data"] %}
      <table>
        <tr><th>Name</th><th>Job</th><th>Link</th></tr>
        {% for row in d["contacts_data"] %}
        <tr>
          <td>{{ row['name'] }}</td>
          <td>{{ row['job'] }}</td>
          <td>{{ Icon(href=row['link_url'], name="arrow-top-right-on-square", variant="outline", color="text-gray-400 hover:text-gray-500") }}</td>
        </tr>
        {% endfor %}
      </table>
      {% else %}
      <p class="text-sm italic">No entries</p>
      {% endif %}
    </div>
  </div>
</div>
{% endmacro %}


{# ===== ProjectNotes ===== #}
{% macro ProjectNotes(project_id=none, notes=none, comments_by_notes=none, editable=none) %}
{%- set d = _ProjectNotesdata(project_id, notes, comments_by_notes, editable) -%}
<div class="prose">
  <h3>Notes</h3>
  {% if d["notes_data"] %}
  <div class="mt-8">
    {% for note in d["notes_data"] %}
    <div class="py-2" style="border-top: solid 1px lightgrey">
      <div class="flex justify-between gap-4 pt-2">
        <span class="prose-sm prose-figure">{{ note['timestamp'] }}</span>
        {% if d["editable"] %}{{ Icon(name="pencil-square", variant="outline", href=note['edit_href'], color="text-gray-400 hover:text-gray-500") }}{% endif %}
      </div>
      <p class="my-0 text-gray-900">{{ note['text'] }}</p>
      <details class="px-8 py-2">
        <summary class="font-medium">Comments</summary>
        {% for comment in note['comments'] %}
        <div class="pl-8 pb-2" style="border-top: solid 1px grey;">
          <div class="flex justify-between gap-4 pt-2">
            <span class="prose-sm prose-figure">{{ comment['timestamp'] }}</span>
            {% if d["editable"] %}{{ Icon(name="pencil-square", variant="outline", href=comment['edit_href'], color="text-gray-400 hover:text-gray-500") }}{% endif %}
          </div>
          <div class="flex-auto"><p class="my-0">{{ comment['text'] }}</p></div>
        </div>
        {% endfor %}
        <div class="text-right">
          {% if d["editable"] %}{% call Button(href=note['create_comment_url']) %}Add comment{% endcall %}{% endif %}
        </div>
      </details>
    </div>
    {% endfor %}
  </div>
  {% endif %}
  {% if d["editable"] %}{% call Button(href=d["create_note_url"]) %}Add Note{% endcall %}{% endif %}
</div>
{% endmacro %}


{# ===== ProjectOutputBadge ===== #}
{% macro ProjectOutputBadge(completed, missing_deps) %}
{%- set check_interactive = theme.check_interactive -%}
{%- set warn_icon_attrs = {"title": "A dependent dependency has not been met!"} -%}
{%- set check_icon_attrs = {"class": "p-2"} -%}
<span class="flex h-9 items-center">
{%- if missing_deps -%}
{{ Icon(name="exclamation-triangle", variant="outline", color="text-black", size=32, stroke_width=2, attrs=warn_icon_attrs) }}
{%- elif completed -%}
<span{{ html_attrs(none, ['relative z-10 flex h-8 w-8 items-center justify-center rounded-full', check_interactive]) }}>
{{- Icon(name="check", variant="outline", color="text-white", size=20, stroke_width=2, attrs=check_icon_attrs) }}</span>
{%- else -%}
<span class="flex h-9 items-center" aria-hidden="true"><span class="relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-300 bg-white"></span></span>
{%- endif -%}
</span>
{% endmacro %}


{# ===== ProjectOutputAttachments ===== #}
{% macro ProjectOutputAttachments(has_attachments, js_props, editable, attrs=none) %}
{{- register_js("ProjectOutputAttachments") -}}
{%- set d = _ProjectOutputAttachmentsdata(has_attachments, js_props, editable, attrs) -%}
<div x-data="project_output_attachments"{{ html_attrs(d["attrs"], 'pt-3 flex flex-col gap-y-3 items-start', **{"x-props": d["x_props"]}) }}>
<div>
{%- if not d["has_attachments"] and d["editable"] -%}This output does not have any attachments, create one below:
{%- elif not d["has_attachments"] and not d["editable"] -%}This output does not have any attachments.
{%- elif d["has_attachments"] and not d["editable"] -%}Attachments:
{%- else -%}{%- endif -%}
</div>
<template x-for="(attachment, index) in attachments.value">
<div class="project-output-form-attachment w-full">
<div class="text-sm flex gap-3 w-full justify-between">
<div x-show="attachment.isPreview">{{ Button(variant="plain", link=True, attrs=d["preview_btn_attrs"]) }}</div>
<div x-show="!attachment.isPreview" class="flex flex-col gap-1">
<label for="id_text">Text:</label>
<input type="text" name="text" id="id_text"{{ html_attrs(none, maxlength=d["text_max_len"], required=True, disabled=(not d["editable"])) }} class="text-sm py-1 px-2" :value="attachment.text" @change="(ev) => $emit('updateAttachmentData', index, { text: ev.target.value })" />
<label for="id_url">Url:</label>
<input type="url" name="url" id="id_url" required{{ html_attrs(none, disabled=(not d["editable"])) }} class="text-sm py-1 px-2" :value="attachment.url" @change="(ev) => $emit('updateAttachmentData', index, { url: ev.target.value })" />
</div>
{%- if d["editable"] %}<div class="flex gap-2 flex-wrap justify-end">
<div>{% call Button(attrs=d["edit_btn_attrs"]) %}Edit{% endcall %}</div>
<div>{% call Button(color="error", attrs=d["remove_btn_attrs"]) %}Remove{% endcall %}</div>
</div>{% endif -%}
</div>
{{ Tags(tag_type=d["tag_type"], editable=d["editable"], js_props=d["tags_js_props"], attrs=d["tags_attrs"]) }}
</div>
</template>
</div>
{% endmacro %}


{# ===== ProjectOutputDependency ===== #}
{% macro ProjectOutputDependency(dependency) %}
{{- register_js("ProjectOutputDependency") -}}
{%- set d = _ProjectOutputDependencydata(dependency) -%}
<div class="pb-3 mb-3 border-b border-solid border-gray-300" x-data="project_output_dependency"{{ html_attrs(none, **{"x-props": d["x_props"]}) }}>
<div class="w-full bg-gray-100 text-sm p-2" style="min-height: 100px;">
{%- if d["output_completed"] -%}
{%- if d["output_description"] -%}{{ d["output_description"] }}
{%- else -%}<span class="italic text-gray-500">{{ d["placeholder"] }}</span>{%- endif -%}
{%- else -%}
<span class="text-gray-500 italic">
{{- Icon(name="exclamation-triangle", variant="outline", size=24, stroke_width=2, color="text-gray-500", attrs=d["warn_icon_attrs"]) }}
Missing '{{ d["output_name"] }}' from
{% call Button(variant="plain", href=d["phase_url"], attrs=d["phase_btn_attrs"]) %}{{ d["phase_type_title"] }}{% endcall %}
</span>
{%- endif -%}
</div>
{{ ProjectOutputAttachments(editable=False, has_attachments=d["attachments"], js_props={'attachments': 'attachments.value'}) }}
</div>
{% endmacro %}


{# ===== ProjectOutputForm ===== #}
{% macro ProjectOutputForm(data, editable) %}
{{- register_js("ProjectOutputForm") -}}
{%- set d = _ProjectOutputFormdata(data, editable) -%}
<div x-data="project_output_form"{{ html_attrs(none, **{"x-props": d["x_props"]}) }}>
{% call Form(submit_href=d["update_output_url"], actions_hide=True) %}
{%- if d["editable"] -%}
<textarea name="description" class="w-full text-sm p-2 mb-2"{{ html_attrs(none, placeholder=d["placeholder"]) }} style="min-height: 100px;">{{ d["output_description"] }}</textarea>
{%- else -%}
<div class="w-full bg-gray-100 italic text-gray-500 text-sm p-2 mb-2" style="min-height: 100px;">
{%- if d["output_description"] -%}{{ d["output_description"] }}{%- else -%}{{ d["placeholder"] }}{%- endif -%}
</div>
{%- endif -%}
<div class="flex flex-wrap justify-between items-center gap-y-3">
<div class="flex items-center gap-x-2">
Completed:
<input type="hidden" value="0" name="completed"{{ html_attrs(none, disabled=(not d["editable"])) }} />
<input type="checkbox" name="completed" style="height: 20px; width: 20px"{{ html_attrs(none, checked=d["output_completed"], disabled=(not d["editable"])) }} />
</div>
{%- if d["editable"] %}<div class="flex gap-x-2 ml-auto items-center justify-between basis-52">
{% call Button(variant="secondary", attrs=d["add_btn_attrs"]) %}Add attachment{% endcall %}
{% call Button(attrs=d["save_btn_attrs"]) %}Save{% endcall %}
</div>{% endif -%}
</div>
{{ ProjectOutputAttachments(has_attachments=d["attachments"], editable=d["editable"], js_props=d["attach_js_props"]) }}
{% endcall %}
</div>
{% endmacro %}


{# ===== ProjectOutputs ===== #}
{% macro ProjectOutputs(project_id, phase_type, outputs, editable) %}
{%- set d = _ProjectOutputsdata(project_id, phase_type, outputs, editable) -%}
<div class="flex flex-col">
{%- for data in d["outputs_data"] %}
<div class="flex gap-x-3">
<div>{{ ProjectOutputBadge(completed=data.output['completed'], missing_deps=data.has_missing_deps) }}</div>
<div class="w-full">
{%- set _hdr %}<div>{{ data.output['name'] }}</div>{% endset -%}
{%- set _content -%}
<div>
{%- for dep in data.dependencies %}{{ ProjectOutputDependency(dependency=dep) }}{% endfor -%}
{{ ProjectOutputForm(data=data, editable=d["editable"]) }}
</div>
{%- endset -%}
{{ ExpansionPanel(panel_id=data.output['id'], icon_position="right", attrs=d["panel_attrs"], header_attrs=d["panel_header_attrs"], header=_hdr, content=_content) }}
</div>
</div>
{%- endfor %}
</div>
{% endmacro %}


{# ===== ProjectOutputsSummary ===== #}
{% macro ProjectOutputsSummary(project_id, outputs, editable, phase_titles) %}
{%- set d = _ProjectOutputsSummarydata(project_id, outputs, editable, phase_titles) -%}
<div class="flex flex-col gap-y-3">
{%- for group in d["groups"] %}
{%- set _hdr %}<h3 class="m-0">{{ group['phase_title'] }}</h3>{% endset -%}
{%- set _content -%}
{%- if group['outputs'] -%}
{{ ProjectOutputs(outputs=group['outputs'], project_id=d["project_id"], phase_type=group['phase_type'], editable=d["editable"]) }}
{%- else -%}No outputs{%- endif -%}
{%- endset -%}
{{ ExpansionPanel(open=group['has_outputs'], header_attrs=d["panel_header_attrs"], header=_hdr, content=_content) }}
{%- endfor %}
</div>
{% endmacro %}


{# ===== Form ===== #}
{% macro Form(type=none, editable=true, method="post", submit_hide=none, submit_text="Submit", submit_href=none, submit_disabled=none, submit_variant="primary", submit_color=none, submit_type="submit", submit_attrs=none, cancel_hide=none, cancel_text="Cancel", cancel_href=none, cancel_disabled=none, cancel_variant="secondary", cancel_color=none, cancel_type="button", cancel_attrs=none, actions_hide=none, actions_attrs=none, form_content_attrs=none, attrs=none, below_form="", actions_prepend="", actions_append="") %}
{{- register_js("Form") -}}
{%- set d = _Formdata(type, editable, method, submit_hide, submit_text, submit_href, submit_disabled, submit_variant, submit_color, submit_type, submit_attrs, cancel_hide, cancel_text, cancel_href, cancel_disabled, cancel_variant, cancel_color, cancel_type, cancel_attrs, actions_hide, actions_attrs, form_content_attrs, attrs) -%}
<form{{ html_attrs(merge_attrs(d["form_attrs"], d["attrs"]), method=d["method"]) }} x-data="form">
{%- set _tag = d["form_content_tag"] -%}
<{{ _tag }}{{ html_attrs(d["form_content_attrs"], **{"@click": "updateFormModel", "@change": "updateFormModel"}) }}>{% if caller %}{{ caller() }}{% endif %}</{{ _tag }}>
{{ below_form }}
{%- if not d["actions_hide"] %}<div{{ html_attrs(d["actions_attrs"], 'pt-4') }}>
{{ actions_prepend }}
{%- if not d["submit_hide"] %}{% call Button(variant=d["submit_variant"], color=d["submit_color"], disabled=d["submit_disabled"], type=d["submit_type"], attrs=d["submit_attrs"]) %}{{ d["submit_text"] }}{% endcall %}{% endif -%}
{%- if not d["cancel_hide"] %}{% call Button(variant=d["cancel_variant"], color=d["cancel_color"], disabled=d["cancel_disabled"], href=d["cancel_href"], type=d["cancel_type"], attrs=d["cancel_attrs"]) %}{{ d["cancel_text"] }}{% endcall %}{% endif -%}
{{ actions_append }}
</div>{% endif -%}
</form>
{% endmacro %}

{% macro Navbar(attrs=none) %}
<div{{ html_attrs(attrs, "sticky top-0 z-30 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8") }}>
<button type="button" class="-m-2.5 p-2.5 text-gray-700" @click="$dispatch('sidebar_toggle')">
<span class="sr-only">Open sidebar</span>
{{ Icon(name="bars-3", variant="outline") }}</button>
<div class="h-6 w-px bg-gray-900/10 lg:hidden" aria-hidden="true"></div>
<div class="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
<form class="relative flex flex-1 items-center" action="#" method="GET"></form>
<div class="flex items-center gap-x-4 lg:gap-x-6">
<div class="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-900/10" aria-hidden="true"></div>
</div></div></div>
{% endmacro %}


{% macro Sidebar(active_projects, attrs=none, render_context=none, content="") %}
{%- set user = render_context.user -%}
{%- set is_staff = (user.get("is_staff", false) if user is mapping else user.is_staff) -%}
{%- set items = gen_sidebar_menu_items(active_projects) -%}
{%- set sidebar_link = theme.sidebar_link -%}
{%- set icon_text_attrs = {"class": "p-2"} -%}
{%- set child_btn_attrs = {"class": "p-2 !w-full"} -%}
<div{{ html_attrs(attrs, ["flex grow flex-col gap-y-5 overflow-y-auto px-6 pb-4", theme.sidebar]) }}>
<div class="flex h-16 shrink-0 items-center">DEMO</div>
<nav class="flex flex-1 flex-col"><ul role="list" class="flex flex-1 flex-col gap-y-7"><li>
{{ content }}
<ul role="list" class="-mx-2 space-y-1">
{%- for sidebar_item in items %}
<li>{% call Icon(name=sidebar_item.icon, variant=sidebar_item.icon_variant, href=sidebar_item.href, color=sidebar_link, text_attrs=icon_text_attrs) %}{{ sidebar_item.name }}{% endcall %}</li>
{%- for child_item in sidebar_item.children or [] %}
<li{{ html_attrs(none, ["ml-8 rounded-md", sidebar_link]) }}>{% call Button(variant="plain", href=child_item.href, attrs=child_btn_attrs) %}{{ child_item.name }}{% endcall %}</li>
{%- endfor %}
{%- endfor %}
</ul>
<li class="mt-auto">
{% call Icon(name="user-group", variant="outline", href="/faq", color=sidebar_link, text_attrs=icon_text_attrs) %}FAQ{% endcall %}
{% call Icon(name="megaphone", variant="outline", color=sidebar_link, link_attrs={"target": "_blank"}, text_attrs=icon_text_attrs) %}Feedback{% endcall %}
</li>
{%- if is_staff %}<li>{% call Icon(name="document-arrow-down", variant="outline", color=sidebar_link, text_attrs=icon_text_attrs) %}Download{% endcall %}</li>{% endif %}
</li></ul></nav></div>
{% endmacro %}


{% macro Base(render_context=none, css="", content="", js="") %}{{ register_js("Base") }}
{%- set csrf_token = render_context.csrf_token -%}
{%- set htmx_url = static("js/htmx.js") -%}
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
<meta charset="UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DEMO</title>
{{ CSS_PLACEHOLDER }}
{{ css }}
</head>
<body{{ html_attrs(none, [theme.background, "h-full"]) }}>
{{ content }}
<script src="//unpkg.com/@alpinejs/anchor" defer></script>
<script src="https://cdn.jsdelivr.net/npm/alpine-reactivity@0.1.10/dist/cdn.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/alpine-composition@0.1.27/dist/cdn.min.js"></script>
<script src="//unpkg.com/alpinejs" defer></script>
<script type="text/javascript"{{ html_attrs(none, src=htmx_url) }}></script>
<script src="https://unpkg.com/axios/dist/axios.min.js"></script>
{{ JS_PLACEHOLDER }}
{{ js }}
<script>
(function () {
    const token = '{{ csrf_token }}';
    document.body.addEventListener('htmx:configRequest', (event) => {
        event.detail.headers['X-CSRFToken'] = token;
    });
    document.addEventListener('alpine:init', () => {
        Alpine.store('csrf', { token });
    });
})();
</script>
</body>
</html>
{% endmacro %}


{% macro Layout(data, attrs=none, js="", css="", header="", sidebar="", content="") %}{{ register_js("Layout") }}
{%- set request = data.request -%}
{%- set rc = RenderContext(request=request, user=request.user, csrf_token=get_csrf_token(request)) -%}
{%- set navbar_attrs = {"@sidebar_toggle": "toggleSidebar"} -%}
{%- set base_content %}
<div x-data="layout" @resize.window="onWindowResize"{{ html_attrs(attrs) }}>
<div class="hidden" :class="{ 'fixed inset-y-0 z-40 flex w-72 flex-col': sidebarOpen, 'hidden': !sidebarOpen }">
{{ Sidebar(active_projects=data.active_projects, render_context=rc, content=sidebar) }}
</div>
<div :class="{ 'pl-72': sidebarOpen }" class="flex flex-col" style="height: 100vh;">
{{ Navbar(attrs=navbar_attrs) }}
<main class="flex-auto flex flex-col">
{{ header }}
<div class="px-4 pt-10 sm:px-6 lg:px-8 flex-auto flex flex-col">
{{ content }}
</div></main></div></div>
{% endset -%}
{{ Base(render_context=rc, css=css, js=js, content=base_content) }}
{% endmacro %}


{% macro ProjectLayoutTabbed(data, breadcrumbs=none, top_level_tab_index=none, variant="thirds", js="", css="", header="", left_panel="", content="", tabs=none) %}
{%- set project = data.project -%}
{%- set prefixed_breadcrumbs = [Breadcrumb(link="/projects", value=HOME_ICON), Breadcrumb(value=project["name"], link="/projects/" ~ project["id"])] + (breadcrumbs or []) -%}
{%- set is_thirds = variant == "thirds" -%}
{%- set top_level_tabs = gen_tabs(project["id"]) -%}
{%- set has_left_panel = (left_panel != "") -%}
{%- set left_panel_attrs = {"class": "w-1/3" if is_thirds else "w-1/2"} -%}
{%- set right_panel_attrs = {"class": "w-2/3" if is_thirds else "w-1/2"} -%}
{%- set tabs_attrs = {"class": "p-6 h-full"} -%}
{%- set tabs_content_attrs = {"class": "flex flex-col"} -%}
{%- set layout_header %}{{ Breadcrumbs(items=prefixed_breadcrumbs) }}{% endset -%}
{%- set layout_sidebar %}{{ Bookmarks(bookmarks=data.bookmarks, project_id=project["id"]) }}{% endset -%}
{%- set layout_content %}
{{ header }}
{%- if top_level_tab_index is not none %}{{ TabsStatic(tabs=top_level_tabs, index=top_level_tab_index) }}{% endif %}
<div class="flex flex-auto gap-6">
{%- if has_left_panel %}<div{{ html_attrs(left_panel_attrs, "relative h-full pb-4") }}><div class="absolute w-full h-full">{{ left_panel }}</div></div>{% endif %}
{%- set _tag = "div" if has_left_panel else "template" %}
<{{ _tag }}{{ html_attrs(right_panel_attrs if has_left_panel else {}, "h-full" if has_left_panel else "") }}>
{%- if content %}{{ content }}{% else %}
<div class="h-full divide-y divide-gray-200 bg-white shadow overflow-y-hidden">
{{ Tabs(tabs=tabs or [], name="proj-right", attrs=tabs_attrs, content_attrs=tabs_content_attrs) }}
</div>
{%- endif %}
</{{ _tag }}>
</div>
{% endset -%}
{{ Layout(data=data, js=js, css=css, header=layout_header, sidebar=layout_sidebar, content=layout_content) }}
{% endmacro %}


{% macro ProjectPage(phases, project_tags, notes_1, comments_by_notes_1, notes_2, comments_by_notes_2, notes_3, comments_by_notes_3, status_updates, roles_with_users, contacts, outputs, user_is_project_member, user_is_project_owner, phase_titles, layout_data, project, breadcrumbs=none) %}
{%- set phases_by_type = {} -%}
{%- for p in phases %}{% do phases_by_type.update({p["phase_template"]["type"]: p}) %}{% endfor -%}
{%- set rendered_phases = [] -%}
{%- for pm in PROJECT_PHASES_META.values() %}{% do rendered_phases.append(ListItem(value=phase_titles[pm.type], link="/projects/" ~ project["id"] ~ "/phases/" ~ phases_by_type[pm.type]["phase_template"]["type"])) %}{% endfor -%}
{%- set phases_list_item_attrs = {"class": "py-5"} -%}
{%- set plt_header %}<div class="flex pb-6"><div class="flex justify-between gap-x-12"><div class="prose"><h3>{{ project["name"] }}</h3></div><div class="prose font-semibold text-gray-500 pt-1">{{ project["start_date"] }} - {{ project["end_date"] }}</div></div></div>{% endset -%}
{%- set plt_left_panel %}{{ List(items=rendered_phases, item_attrs=phases_list_item_attrs) }}{% endset -%}
{# citry collects <c-TabItem> children into the parent Tabs via provide/inject;
   Jinja2 has no such collection, so the tab entries (header + rendered content)
   are built directly and passed as the Tabs `tabs` list. #}
{%- set tab_entries = [] -%}
{%- set _tab0 %}{{ ProjectInfo(project=project, project_tags=project_tags, roles_with_users=roles_with_users, contacts=contacts, status_updates=status_updates, editable=user_is_project_owner) }}{% endset -%}
{%- do tab_entries.append(TabEntry(header="Project Info", content=_tab0)) -%}
{%- set _tab1 %}{{ ProjectNotes(project_id=project["id"], notes=notes_1, comments_by_notes=comments_by_notes_1, editable=user_is_project_member) }}{% endset -%}
{%- do tab_entries.append(TabEntry(header="Notes 1", content=_tab1)) -%}
{%- set _tab2 %}{{ ProjectNotes(project_id=project["id"], notes=notes_2, comments_by_notes=comments_by_notes_2, editable=user_is_project_member) }}{% endset -%}
{%- do tab_entries.append(TabEntry(header="Notes 2", content=_tab2)) -%}
{%- set _tab3 %}{{ ProjectNotes(project_id=project["id"], notes=notes_3, comments_by_notes=comments_by_notes_3, editable=user_is_project_member) }}{% endset -%}
{%- do tab_entries.append(TabEntry(header="Notes 3", content=_tab3)) -%}
{%- set _tab4 %}{{ ProjectOutputsSummary(project_id=project["id"], outputs=outputs, editable=user_is_project_member, phase_titles=phase_titles) }}{% endset -%}
{%- do tab_entries.append(TabEntry(header="Outputs", content=_tab4)) -%}
{{ ProjectLayoutTabbed(data=layout_data, breadcrumbs=breadcrumbs, top_level_tab_index=1, header=plt_header, left_panel=plt_left_panel, tabs=tab_entries) }}
{% endmacro %}
"""

#####################################
# RENDER ENTRYPOINT
#####################################

# The macro template is compiled on first render, not at import, so the
# parse/compile cost lands in the `first` measurement (the benchmark's column
# semantics, and what the lazy-loading Django/citry ports also do). The compiled
# module is cached for subsequent renders.
_macros = None


def _get_macros():
    global _macros
    if _macros is None:
        _macros = env.from_string(_MACROS_SRC).module
        # The breadcrumb home icon never varies, so it is rendered once and reused.
        env.globals["HOME_ICON"] = _macros.Icon(
            name="home", variant="outline", size=20, stroke_width=2, color="text-gray-400 hover:text-gray-500"
        )
    return _macros


def render(data: dict) -> str:
    """Render the project page and inject the collected JS at the <c-js> marker."""
    _collected_js.clear()
    _collected_js_seen.clear()
    macros = _get_macros()
    html = str(macros.ProjectPage(**data))
    js_blocks = "".join(f"<script>{COMPONENT_JS[name]}</script>" for name in _collected_js)
    return html.replace(_JS_PLACEHOLDER, js_blocks).replace(_CSS_PLACEHOLDER, "")


# ----------- TESTS START ------------ #
# The code above is also used when benchmarking.
# The section below is NOT included.

# The full page is non-deterministic (naturaltime is relative to now), so this
# is a structural smoke test, mirroring the citry/django-components ports: it
# guards that the benchmarked logic still renders the whole page.


def test_render():
    data = gen_render_data()
    rendered = render(data)
    assert len(rendered) > 100_000  # the full project page, not a truncated render
    for anchor in ("<!DOCTYPE html>", "Project Name", "<body", "x-data", "Submit"):
        assert anchor in rendered
