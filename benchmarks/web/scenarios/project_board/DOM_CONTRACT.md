# Canonical project-page DOM contract

Every adapter renders the canonical project page with its native composition
and event mechanisms. The shared runner reads the selectors below at each
adapter's framework-ready endpoint. IDs must be unique within the document.
Entity data attributes contain decimal shared-model IDs.

## Page shell and controls

- `#board` is the scenario root and retains the existing `data-session`,
  `data-revision`, `data-operation`, `data-visible-count`, and
  `data-total-count` fields.
- `#board-title`, `#title-input`, `#query`, `#form-error`, and `#form-notice`
  retain their existing meanings.
- Existing `data-bench-action` controls remain: `select-1`, `filter`, `save`,
  `insert`, `reorder`, `remove`, `probe`, and `disclosure`.
- `#preserved-input` and `#disclosure-content` retain the local-state checks.
- `#project-navbar` and `#project-sidebar` are mounted inside `#board`.
- `#board` carries decimal `data-project-id`. `#project-status`,
  `#project-start-date`, `#project-end-date`, and `#project-organization`
  contain the corresponding plain-text project values. `#board-title` is the
  project name.

## Tabs and phase groups

- `#project-tabs` contains exactly five tab buttons. Their `data-tab-target`
  values are `project-info`, `notes-1`, `notes-2`, `notes-3`, and `outputs`.
- The corresponding panel IDs use those exact values, and each panel's
  `data-tab-panel` equals its ID. All panels stay mounted. `outputs` is active
  and visible initially; the native tab controls can show another panel.
- Every phase group has a decimal `data-phase-id` and contains its output rows
  in shared-model order. Its `.phase-title` contains the shared title. Groups
  follow `phase_groups`, including empty groups.
  Reorder reverses both the group order and each group's outputs so flattening
  the groups still equals `rows`. Every group starts open and carries
  `data-phase-expanded="true"`.
- Every output row has decimal `data-row-id`, `.row-title`, `.row-status`, and
  one textarea or display element marked `data-output-description`. The runner
  reads that element's value for a form control and text otherwise. The existing
  `data-selected` value is `true` or `false`, and its select control uses the
  model's `select_action`. Canonical rows carry decimal `data-source-id`; an
  inserted row omits it. A checkbox marked `data-output-completed` reflects the
  completed value. Every output starts open and carries
  `data-output-expanded="true"`.
- Each output badge has `data-output-badge` equal to `open` or `done`.
- Each row keeps its title, status, and badge in a visible header. The real
  select action and local description/completed controls stay in a standalone
  `.output-form` outside the disclosure.
- Every row has an initially open native `<details>` with the summary
  `Output details` (or an equivalent local disclosure control). Its visible
  `Dependencies` and `Attachments` sections each have an `h4` heading. Empty
  sections show `No dependencies` or `No attachments`, respectively. Attachment
  articles and tags remain outside the select form.
- Each attachment has decimal `data-attachment-id` and
  `data-attachment-name` equal to its `.attachment-name` text. Its link carries
  the shared URL, and each tag uses `data-attachment-tag` with its string value.
- Each dependency has decimal `data-dependency-id` and
  `data-dependency-title` equal to its `.dependency-title` text. Its
  `data-dependency-completed` value is `true` or `false`.

## Project details

- Every note has decimal `data-note-id` and a `.note-text` descendant containing
  its exact plain-text value. Capture comments within that note rather than as a
  page-wide list.
- Every comment has decimal `data-comment-id` and a `.comment-text` descendant
  containing its exact plain-text value. `.comment-author` contains its author.
- Every role has `data-role-id`, `.role-name`, and `.user-name` descendants.
- Every bookmark link has decimal `data-bookmark-id` and
  `data-bookmark-name` equal to its `.bookmark-name` descendant text.
- The empty canonical collections remain explicit through
  `[data-project-contacts]`, `[data-project-status-updates]`, and
  `[data-project-tags]` containers.

The shared semantic snapshot records these values synchronously inside the
ready callback. Adapters must not call ready until the complete model revision
has committed. The runner supplies expected state from the independent shared
oracle before each operation and rejects the mark if the snapshot differs.
The callback records its timestamp before capture and reports capture and
validation time separately as observer overhead.

Untimed qualification also calls `Element.checkVisibility` on every canonical
description, completed control, and select control, plus attachment and
dependency text. A computed-style ancestor fallback covers browsers without
that method. The static expanded markers do not by themselves qualify open
content, and these visibility reads do not run inside the timed callback.

Output forms expose their description textarea and completed checkbox as local
display controls, plus the real shared select action. Per-output Save/Add and
attachment editing behavior from the rendering fixture is outside this scenario
model; adapters omit or disable those controls unless the shared model is
extended in a coordinated change. The project-title Save action remains part of
the shared server sequence.
