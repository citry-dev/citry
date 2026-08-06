# Citry UI manual release qualification

Use this checklist only for a release candidate built from the same commit as
the automated Phase 7.5 record. Automated axe, keyboard, screenshot capture,
and browser tests must pass first. A person records observations here; running
the route is not itself a pass.

## Record the environment

For every session, record:

- Citry UI wheel filename and SHA-256;
- commit SHA and Phase 7.5 exit-record artifact;
- operating system, browser, and exact versions;
- assistive technology and exact version, when used;
- physical device model, viewport or zoom, color scheme, contrast mode, and
  input method; and
- reviewer, date, result, and links to notes or captures.

Use `passed`, `failed`, `blocked`, or `not-applicable`. Never convert a tool or
device that was unavailable into `passed`.

## Review visual candidates

Generate the candidate ledger with:

```console
uv run --project packages/py/citry_ui --group e2e \
  python -m citry_ui.quality.capture_visuals /tmp/citry-ui-visuals
```

Review every file named in `manifest.json` at its recorded viewport. Check
hierarchy, typography, alignment, spacing, clipping, overflow, focus-visible,
disabled and loading treatment, errors, overlays, RTL, both color schemes,
forced colors, reduced motion, touch sizing, and 200- and 400-percent reflow.
Record one decision per image: `approved`, `rejected`, or
`awaiting-human-review`. A rejection links the issue that owns the follow-up.

## Assistive-technology sessions

Run at least these browser and assistive-technology pairs:

| Pair | Required routes | Tasks and expected result |
|---|---|---|
| VoiceOver with Safari on macOS | `field-input.states`, `tabs.overview`, `dialog.states`, `table.states` | Navigate labels and errors; select Tabs in automatic and manual modes; open, dismiss, and restore focus for Dialog; navigate headers and cells as a native table. Names, roles, states, relationships, and changes are announced once and in context. |
| NVDA with Firefox on Windows | `form.states`, `combobox.states`, `tabs.overview`, `table.states` | Submit invalid Form; navigate local and remote Combobox results; exercise horizontal, vertical, disabled, and nested Tabs; navigate ready, empty, loading, and error Table states. Focus order and announcements match the visible task. |
| JAWS with Chrome or Edge on Windows | `composition.orbit-access`, `composition.ledger-dashboard` | Complete the access form, change dashboard Tabs, inspect the Table, and open and close the Dialog. The composed page retains native landmarks, headings, forms, table navigation, and focus recovery. |
| TalkBack with Chrome on Android | `workflow.repeatable-contacts`, `combobox.states`, `dialog.states` | Add, edit, reorder, and remove contacts; select a Combobox option; open and dismiss a Dialog. Touch exploration reaches every control, dynamic changes remain understandable, and focus does not move to removed content. |

Also complete a keyboard-only pass with no screen reader. Use Tab and
Shift+Tab across the page, native form keys, Tabs arrow/Home/End/Enter/Space,
Combobox arrows/Enter/Escape, and Dialog Escape and focus trapping. There must
be no unreachable control, focus loss, hidden focus, or keyboard trap other
than the intentional modal Dialog cycle.

## Real-device and environmental sessions

Use the representative compositions and the family route that owns any defect:

- Safari on current macOS with keyboard, trackpad, 200 percent zoom, and 400
  percent zoom;
- Safari on a current iPhone with portrait and landscape orientation, touch,
  software keyboard, and text size increased;
- Chrome on a current Android phone with portrait and landscape orientation,
  touch, software keyboard, and increased font size;
- Windows high-contrast mode with keyboard; and
- one narrow 320 CSS-pixel reflow pass without horizontal page scrolling.

Check native form submission, reset, autofill where available, fixed and
sticky content, Dialog viewport fit and scroll locking, popup placement,
long-label Tabs, overflowing Table, focus after DOM removal, RTL layout, and
light/dark scheme changes.

## Close the release record

Attach the environment rows, per-task results, visual decisions, failures, and
links to the generated Phase 7.5 exit record. The release may claim a manual
profile only when all required rows for that profile passed on the exact wheel.
Multi-release upgrade and downgrade remain `unavailable` until two published
Citry UI releases exist.
