"""Citry-owned components for the project landing page."""

from __future__ import annotations

import base64
import functools
import importlib
import itertools
import json
import re
from typing import TYPE_CHECKING, Any

from markupsafe import Markup, escape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from citry import Component
from docs_site._internal.project import current_docs_project
from docs_site._internal.util import flatten_for_markdown
from docs_site.snippets.landing.status_card import StatusCard

if TYPE_CHECKING:
    from collections.abc import Callable

# The walkthrough reads this file and marks the line ranges below. Line numbers
# are the one fragile part, so `test_walkthrough_stops_point_at_the_right_lines`
# checks that each range still contains the text it claims to explain.
_TOUR_PATH = "docs_site/snippets/landing/product_card.py"

# The editor demo reads ordinary source and layers its interactive symbols on
# top. Keeping the annotations here means the file stays useful as real Citry
# code, while a stale or ambiguous range fails the docs build.
_EDITOR_PATH = "docs_site/snippets/landing/editor_invite_panel.py"

_EDITOR_MARKS: tuple[dict[str, Any], ...] = (
    {
        "id": "member-type-definition",
        "needle": "class Member(TypedDict):",
        "symbol": "Member",
        "definition": "member-type",
        "signature": "class Member(TypedDict)",
        "language": "python",
        "provenance": "Python type",
        "description": "This JSON-safe shape follows members from Python into the browser.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "member-name-definition",
        "needle": "class Member(TypedDict):\n    name: str",
        "symbol": "name",
        "definition": "member-name",
        "signature": "(property) Member.name: str",
        "language": "python",
        "provenance": "Declared by Member",
        "description": "The field remains typed after Python data reaches Alpine.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "member-online-definition",
        "needle": "name: str\n    online: bool",
        "symbol": "online",
        "definition": "member-online",
        "signature": "(property) Member.online: bool",
        "language": "python",
        "provenance": "Declared by Member",
        "description": "Citry translates this bool to a JavaScript boolean.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "invite-type-definition",
        "needle": "class InviteIn(TypedDict):",
        "symbol": "InviteIn",
        "definition": "invite-type",
        "signature": "class InviteIn(TypedDict)",
        "language": "python",
        "provenance": "Python event payload",
        "description": "The event handler and browser call share this payload shape.",
        "docs": "/events/",
    },
    {
        "id": "member-chip-definition",
        "needle": "class MemberChip(Component):",
        "symbol": "MemberChip",
        "definition": "member-chip",
        "signature": "class MemberChip(Component)",
        "language": "python",
        "provenance": "Registered Citry component",
        "description": "Component tags navigate to the Python class that owns them.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "member-chip-name-definition",
        "needle": "class Kwargs:\n        name: str",
        "symbol": "name",
        "definition": "member-chip-name",
        "signature": "(property) MemberChip.Kwargs.name: str",
        "language": "python",
        "provenance": "Declared component input",
        "description": "The component accepts this required Python input.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "member-chip-status-definition",
        "needle": "name: str\n        status: CitryRender",
        "symbol": "status",
        "definition": "member-chip-status",
        "signature": "(property) MemberChip.Kwargs.status: CitryRender",
        "language": "python",
        "provenance": "Declared component input",
        "description": "The child accepts this rendered nested-template value.",
        "docs": "/syntax/nested-templates/",
    },
    {
        "id": "member-chip-online-definition",
        "needle": "props: { online: { type: Boolean } }",
        "symbol": "online",
        "definition": "member-chip-online",
        "signature": "(property) online: boolean",
        "language": "typescript",
        "provenance": "Declared by MemberChip.$component",
        "description": "The child exposes this client-side prop to its Alpine scope.",
        "docs": "/getting-started/client-props-and-handlers/",
    },
    {
        "id": "member-type-use",
        "needle": "members: list[Member]",
        "symbol": "Member",
        "target": "member-type",
        "signature": "class Member(TypedDict)",
        "language": "python",
        "provenance": "Type of each InvitePanel member",
        "description": "Go to Type Definition opens the TypedDict above.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "kwarg-title-definition",
        "needle": "class Kwargs:\n        title: str\n        members: list[Member]",
        "symbol": "title",
        "definition": "kwarg-title",
        "signature": "(property) InvitePanel.Kwargs.title: str",
        "language": "python",
        "provenance": "Declared component input",
        "description": "Every InvitePanel caller must provide this title.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "kwarg-members-definition",
        "needle": "title: str\n        members: list[Member]",
        "symbol": "members",
        "definition": "kwarg-members",
        "signature": "(property) InvitePanel.Kwargs.members: list[Member]",
        "language": "python",
        "provenance": "Declared component input",
        "description": "The server receives a typed list of members.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "event-definition",
        "needle": "def invite(self, data: InviteIn) -> None:",
        "symbol": "invite",
        "definition": "event-invite",
        "signature": "(method) InvitePanel.Events.invite(data: InviteIn) -> None",
        "language": "python",
        "provenance": "Python event handler",
        "description": "This method is callable from the component in the browser.",
        "docs": "/events/",
    },
    {
        "id": "invite-type-use",
        "needle": "data: InviteIn) -> None",
        "symbol": "InviteIn",
        "target": "invite-type",
        "signature": "class InviteIn(TypedDict)",
        "language": "python",
        "provenance": "Payload accepted by invite",
        "description": "Go to Type Definition opens the event payload declaration.",
        "docs": "/events/",
    },
    {
        "id": "template-title-definition",
        "needle": 'return {"title": kwargs.title}',
        "symbol": '"title"',
        "definition": "template-title",
        "signature": "(variable) title: str",
        "language": "python",
        "provenance": "Inferred from template_data()",
        "description": "Citry infers this template root directly from the returned dictionary.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "kwargs-title-use",
        "needle": "kwargs.title}",
        "symbol": "title",
        "target": "kwarg-title",
        "signature": "(property) InvitePanel.Kwargs.title: str",
        "language": "python",
        "provenance": "Declared by InvitePanel.Kwargs",
        "description": "Definition follows this access to the input declaration.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "js-members-definition",
        "needle": '"members": kwargs.members,',
        "symbol": '"members"',
        "definition": "js-members",
        "signature": "(variable) members: list[Member]",
        "language": "python",
        "provenance": "Inferred from js_data()",
        "description": "Citry serializes this inferred value into component JavaScript.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "kwargs-members-use",
        "needle": "kwargs.members,",
        "symbol": "members",
        "target": "kwarg-members",
        "signature": "(property) InvitePanel.Kwargs.members: list[Member]",
        "language": "python",
        "provenance": "Declared by InvitePanel.Kwargs",
        "description": "Definition follows this access to the input declaration.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "js-inviting-definition",
        "needle": '"inviting": False',
        "symbol": '"inviting"',
        "definition": "js-inviting",
        "signature": "(variable) inviting: bool",
        "language": "python",
        "provenance": "Inferred from js_data()",
        "description": "The literal False becomes a typed Alpine boolean.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "title-use",
        "needle": "<h2>{{ title }}</h2>",
        "symbol": "title",
        "target": "template-title",
        "placement": "below",
        "signature": "(variable) title: str",
        "language": "python",
        "provenance": "Inferred from template_data()",
        "description": "Go to Definition opens the exact returned dictionary key.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "member-binding",
        "needle": 'x-for="member in visibleMembers"',
        "symbol": "member",
        "signature": "(variable) member: Member",
        "language": "typescript",
        "provenance": "Introduced by x-for",
        "description": "This name exists only inside the repeated template subtree.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "visible-members-use",
        "needle": 'x-for="member in visibleMembers"',
        "symbol": "visibleMembers",
        "target": "visible-members",
        "signature": "(variable) visibleMembers: Member[]",
        "language": "typescript",
        "provenance": "Assigned by InvitePanel.$component",
        "description": "Go to Definition follows this name into component JavaScript.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "member-chip-use",
        "needle": "<c-MemberChip",
        "symbol": "MemberChip",
        "target": "member-chip",
        "signature": "class MemberChip(Component)",
        "language": "python",
        "provenance": "Registered Citry component",
        "description": "Go to Definition opens the component's Python class.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "member-chip-name-use",
        "needle": 'c-name="member.name"',
        "symbol": "c-name",
        "target": "member-chip-name",
        "signature": "(property) MemberChip.Kwargs.name: str",
        "language": "python",
        "provenance": "Input accepted by MemberChip",
        "description": "Go to Definition opens the child's Kwargs field.",
        "docs": "/ide/vscode/",
    },
    {
        "id": "member-name-use",
        "needle": 'member.name"',
        "symbol": "name",
        "target": "member-name",
        "signature": "(property) Member.name: string",
        "language": "typescript",
        "provenance": "Inferred from the x-for item",
        "description": "Go to Definition opens the TypedDict field.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "member-chip-status-use",
        "needle": 'c-status="<>',
        "symbol": "c-status",
        "target": "member-chip-status",
        "signature": "(property) MemberChip.Kwargs.status: CitryRender",
        "language": "python",
        "provenance": "Nested-template component input",
        "description": "Go to Definition opens the child input that receives this rendered fragment.",
        "docs": "/syntax/nested-templates/",
    },
    {
        "id": "nested-html-attribute",
        "needle": "c-title='title'",
        "symbol": "c-title",
        "signature": "(attribute) HTMLElement.title: string",
        "language": "typescript",
        "provenance": "HTML provider inside a nested template",
        "description": "Citry forwards native HTML completion, hover, and documentation into the fragment.",
        "docs": "/ide/vscode/#look-up-citry-syntax",
    },
    {
        "id": "nested-title-use",
        "needle": "='title'>",
        "symbol": "title",
        "target": "template-title",
        "signature": "(variable) title: str",
        "language": "python",
        "provenance": "Inferred from template_data()",
        "description": "Python-expression navigation remains available inside the nested template.",
        "docs": "/ide/vscode/#complete-template-roots",
    },
    {
        "id": "client-props",
        "needle": '$c-props="{',
        "symbol": "$c-props",
        "signature": "(attribute) $c-props: MemberChipProps",
        "language": "typescript",
        "provenance": "Checked against MemberChip",
        "description": "Unknown, missing, and mistyped child props are reported here.",
        "docs": "/getting-started/client-props-and-handlers/",
    },
    {
        "id": "member-chip-online-use",
        "needle": '$c-props="{ online:',
        "symbol": "online",
        "target": "member-chip-online",
        "signature": "(property) online: boolean",
        "language": "typescript",
        "provenance": "Client prop declared by MemberChip",
        "description": "Go to Definition opens the child's $component prop declaration.",
        "docs": "/getting-started/client-props-and-handlers/",
    },
    {
        "id": "member-online-use",
        "needle": "member.online }",
        "symbol": "online",
        "target": "member-online",
        "signature": "(property) Member.online: boolean",
        "language": "typescript",
        "provenance": "Inferred from the x-for item",
        "description": "Go to Definition opens the Python Member field.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "unknown-template-variable",
        "needle": "{{ missing_summary }}",
        "symbol": "missing_summary",
        "severity": "error",
        "code": "citry.template.unknown-variable",
        "signature": '"missing_summary" is not defined',
        "language": "python",
        "provenance": "Error · citry.template.unknown-variable",
        "description": "Template variable 'missing_summary' is not available in this template.",
        "docs": "/ide/diagnostics/#citry.template.unknown-variable",
    },
    {
        "id": "send-event",
        "needle": "@submit.prevent=\"$sendEvent('invite', { email })\"",
        "symbol": "$sendEvent",
        "signature": 'function $sendEvent(name: "invite", data: InviteIn): Promise<void>',
        "language": "typescript",
        "provenance": "Citry browser API",
        "description": "Calls a typed Python handler without leaving Alpine.",
        "docs": "/events/bindings/",
    },
    {
        "id": "event-name",
        "needle": "$sendEvent('invite', { email })",
        "symbol": "invite",
        "target": "event-invite",
        "signature": "(event) invite(data: InviteIn): void",
        "language": "typescript",
        "provenance": "Matches InvitePanel.Events.invite",
        "description": "Event names complete, validate, and navigate to Python.",
        "docs": "/events/bindings/",
    },
    {
        "id": "loading-magic",
        "needle": ":aria-busy=\"$loading('invite')\"",
        "symbol": "$loading",
        "signature": 'function $loading(event: "invite"): boolean',
        "language": "typescript",
        "provenance": "Citry browser API",
        "description": "Tracks the named Python event for this component instance.",
        "docs": "/events/bindings/#read-call-state-from-alpine",
    },
    {
        "id": "email-use",
        "needle": 'x-model="email"',
        "symbol": "email",
        "target": "scope-email",
        "signature": "(variable) email: string",
        "language": "typescript",
        "provenance": "Assigned by InvitePanel.$component",
        "description": "Go to Definition opens the direct scope assignment.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "inviting-use",
        "needle": ':disabled="inviting || queuedInvite"',
        "symbol": "inviting",
        "target": "js-inviting",
        "signature": "(variable) inviting: boolean",
        "language": "typescript",
        "provenance": "Inferred from js_data()",
        "description": "Go to Definition opens the exact returned dictionary key.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "unknown-alpine-variable",
        "needle": "inviting || queuedInvite",
        "symbol": "queuedInvite",
        "severity": "error",
        "code": "citry.alpine.unknown-variable",
        "signature": '"queuedInvite" is not defined',
        "language": "typescript",
        "provenance": "Error · citry.alpine.unknown-variable",
        "description": "Alpine variable 'queuedInvite' is not available in this component.",
        "docs": "/ide/diagnostics/#citry.alpine.unknown-variable",
    },
    {
        "id": "unknown-event",
        "needle": "$error('invte')",
        "symbol": "invte",
        "severity": "error",
        "code": "citry.browser.unknown-server-event",
        "signature": 'Server event "invte" is not declared',
        "language": "typescript",
        "provenance": "Error · citry.browser.unknown-server-event",
        "description": "Server event 'invte' is not declared by this component.",
        "docs": "/ide/diagnostics/#citry.browser.unknown-server-event",
    },
    {
        "id": "component-api",
        "needle": "$component({\n        props: { compact:",
        "symbol": "$component",
        "signature": "function $component(definition: ComponentDefinition): void",
        "language": "typescript",
        "provenance": "Citry component JavaScript API",
        "description": "Adds typed client props and setup to this component.",
        "docs": "/getting-started/client-props-and-handlers/",
    },
    {
        "id": "data-parameter",
        "needle": "init: ({ data, scope, props, effect }) => {",
        "symbol": "data",
        "signature": "(parameter) data: Readonly<InvitePanelData>",
        "language": "typescript",
        "provenance": "Inferred from js_data()",
        "description": "The callback sees the JSON-safe shape produced by Python.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "scope-parameter",
        "needle": "init: ({ data, scope, props, effect }) => {",
        "symbol": "scope",
        "signature": "(parameter) scope: AlpineScope",
        "language": "typescript",
        "provenance": "Citry $component context",
        "description": "Direct assignments become typed Alpine variables.",
        "docs": "/concepts/client-interactivity/",
    },
    {
        "id": "props-parameter",
        "needle": "init: ({ data, scope, props, effect }) => {",
        "symbol": "props",
        "signature": "(parameter) props: Readonly<{ compact?: boolean }>",
        "language": "typescript",
        "provenance": "Declared by InvitePanel.$component",
        "description": "The callback receives the component's validated client props.",
        "docs": "/getting-started/client-props-and-handlers/",
    },
    {
        "id": "effect-parameter",
        "needle": "init: ({ data, scope, props, effect }) => {",
        "symbol": "effect",
        "signature": "function effect(callback: () => void): CitryCleanup",
        "language": "typescript",
        "provenance": "Citry $component context",
        "description": "Runs a reactive effect and disposes it with the component.",
        "docs": "/getting-started/client-props-and-handlers/",
    },
    {
        "id": "email-definition",
        "needle": 'scope.email = "";',
        "symbol": "email",
        "definition": "scope-email",
        "signature": "(property) AlpineScope.email: string",
        "language": "typescript",
        "provenance": "Assigned during $component initialization",
        "description": "The direct scope write creates a typed Alpine variable.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "visible-members-definition",
        "needle": "scope.visibleMembers = props.compact",
        "symbol": "visibleMembers",
        "definition": "visible-members",
        "signature": "(property) AlpineScope.visibleMembers: Member[]",
        "language": "typescript",
        "provenance": "Assigned during $component initialization",
        "description": "The scope write is visible and typed in the template above.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "data-members-slice-use",
        "needle": "data.members.slice",
        "symbol": "members",
        "target": "js-members",
        "signature": "(property) InvitePanelData.members: Member[]",
        "language": "typescript",
        "provenance": "Inferred from js_data()",
        "description": "Go to Definition opens the exact returned dictionary key.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
    {
        "id": "data-members-fallback-use",
        "needle": ": data.members;",
        "symbol": "members",
        "target": "js-members",
        "signature": "(property) InvitePanelData.members: Member[]",
        "language": "typescript",
        "provenance": "Inferred from js_data()",
        "description": "Every use shares the Python key's inferred Member[] type.",
        "docs": "/ide/vscode/#complete-alpine-and-component-javascript",
    },
)

_EDITOR_NOTES: tuple[dict[str, str], ...] = (
    {
        "id": "typed-data",
        "label": "01 / Data is inferred",
        "title": "Returned dictionaries become typed editor data.",
        "text": "Citry follows template_data() and js_data() keys into template and Alpine expressions, without a duplicate schema.",
        "mark": "title-use",
    },
    {
        "id": "python-navigation",
        "label": "02 / Python stays connected",
        "title": "Types and fields navigate across the source.",
        "text": "Type Definition and Go to Definition follow TypedDicts, Kwargs fields, returned keys, and event payloads.",
        "mark": "member-type-use",
    },
    {
        "id": "child-contract",
        "label": "03 / Child contracts are joined",
        "title": "One component call connects three declarations.",
        "text": "The tag opens the Python class, c-name opens Kwargs, and $c-props opens the child's JavaScript prop.",
        "mark": "member-chip-use",
    },
    {
        "id": "nested-templates",
        "label": "04 / HTML enters attributes",
        "title": "Nested templates keep full editor intelligence.",
        "text": "Inside c-status, native HTML attributes retain documentation while template roots stay typed and navigable.",
        "mark": "nested-html-attribute",
    },
    {
        "id": "event-navigation",
        "label": "05 / Events cross languages",
        "title": "Browser event names open Python handlers.",
        "text": "$sendEvent is typed from the handler signature, while literal event names validate and navigate to Python.",
        "mark": "event-name",
    },
    {
        "id": "scope-seeding",
        "label": "06 / Setup feeds Alpine",
        "title": "Direct scope writes become typed variables.",
        "text": "email and visibleMembers navigate from template expressions to the exact assignments inside $component.",
        "mark": "email-use",
    },
    {
        "id": "diagnostics",
        "label": "07 / Mistakes explain themselves",
        "title": "Unknown names and event typos fail in place.",
        "text": "Red squiggles carry the same diagnostic code, message, and documentation link shown by the extension.",
        "mark": "unknown-alpine-variable",
    },
)

# A stop's ``text`` is markup, not plain prose: naming an attribute or a method
# reads better as code than in quotes, and the note is rendered as HTML.
_TOUR_STOPS: tuple[dict[str, Any], ...] = (
    {
        "id": "kwargs",
        "label": "Inputs",
        "lines": (4, 7),
        "anchor": "class Kwargs",
        "title": "Declared inputs",
        "text": (
            "Every input this component accepts, with its type and any default. "
            "Passing an unknown name, or leaving out a required one, is reported "
            "when the component renders rather than quietly producing a gap in "
            "the page."
        ),
    },
    {
        "id": "slots",
        "label": "Slots",
        "lines": (9, 11),
        "anchor": "class Slots",
        "title": "Openings the caller fills",
        "text": (
            "Named places a caller passes markup into. <code>body</code> is "
            "required and <code>footer</code> is optional, so the contract covers "
            "content as well as data."
        ),
    },
    {
        "id": "state",
        "label": "State",
        "lines": (13, 14),
        "anchor": "class State",
        "title": "State that survives a call",
        "text": (
            "Server-side state available across Python event handler calls. "
            "Travels between the server and the browser. "
            "Inheriting <code>Kwargs</code> makes the <code>State</code> "
            "carry the same fields."
        ),
    },
    {
        "id": "events",
        "label": "Events",
        "lines": (16, 21),
        "anchor": "class Events",
        "title": "Python that runs on interaction",
        "text": (
            "A public method here can be called from the browser "
            'using <code>@c-event="like"</code>. <code>like</code> '
            "reads the current state and renders the updated component, "
            "which the browser then displays."
        ),
    },
    {
        "id": "data",
        "label": "Data",
        "lines": (23, 33),
        "anchor": "def template_data",
        "title": "Use Python variables in templates, browser behavior, and CSS",
        "text": (
            "<code>template_data</code> prepares template variables, "
            "<code>js_data</code> seeds Alpine variables from JSON, and "
            "<code>css_data</code> creates CSS variables scoped to this "
            "one instance."
        ),
    },
    {
        "id": "alpine",
        "label": "Browser state",
        "lines": (36, 39),
        "anchor": "x-data",
        "title": "State that never leaves the page",
        "text": (
            "<code>x-data</code> holds what only the browser cares about. Opening "
            "and closing the card needs no server, so it never asks one."
        ),
    },
    {
        "id": "slot-body",
        "label": "Slot",
        "lines": (40, 40),
        "anchor": '<c-slot name="body"',
        "title": "Where filled content lands",
        "text": (
            "<code>&lt;c-slot&gt;</code> marks the spot the caller's content drops "
            "into, inside markup this component still controls."
        ),
    },
    {
        "id": "control",
        "label": "Control flow",
        "lines": (42, 51),
        "anchor": "c-for",
        "title": "A loop, a child, and the empty case",
        "text": (
            "<code>&lt;c-for&gt;</code> repeats a child component, "
            "while <code>&lt;c-empty&gt;</code> runs when there are no tags at all. "
            "The child component <code>&lt;c-Tag&gt;</code> receives "
            "<code>label</code> as Python value, and <code>highlight</code> "
            "as Alpine (browser) value through <code>$c-props</code>. "
            "You can listen to children's Alpine events with regular <code>@click</code>."
        ),
    },
    {
        "id": "handlers",
        "label": "Bindings",
        "lines": (53, 55),
        "anchor": "@c-click",
        "title": "Alpine and Python, side by side",
        "text": (
            "<code>@click</code> stays in the browser for instant feedback, while "
            "<code>@c-click</code> calls the Python handler set in the value, <code>like</code>."
        ),
    },
    {
        "id": "slot-footer",
        "label": "Fallback",
        "lines": (57, 59),
        "anchor": '<c-slot name="footer"',
        "title": "What shows when nobody fills it",
        "text": (
            "Content between the tags is the fallback for an optional slot, so a "
            "caller who skips it still gets something sensible."
        ),
    },
    {
        "id": "js",
        "label": "Script",
        "lines": (63, 68),
        "anchor": "$component",
        "title": "Advanced setup scoped to this component",
        "text": (
            "Templates use <code>js_data</code> values directly. Add "
            "<code>$component</code> when an imperative library or other setup "
            "needs this instance's elements and data."
        ),
    },
    {
        "id": "css",
        "label": "Style",
        "lines": (70, 78),
        "anchor": "var(--accent)",
        "title": "Styles reading Python values",
        "text": (
            "<code>var(--accent)</code> reads the custom property "
            "<code>css_data</code> produced, and it is scoped to this instance, so "
            "two cards on one page can differ without a second stylesheet."
        ),
    },
    {
        "id": "deps",
        "label": "Assets",
        "lines": (80, 82),
        "anchor": "class Dependencies",
        "title": "Third-party scripts and styles",
        "text": (
            "Libraries this component needs. Citry loads each script only once per page, "
            "however many components may use it."
        ),
    },
    {
        "id": "render",
        "label": "Render",
        "lines": (85, 88),
        "anchor": "str(ProductCard",
        "title": "Rendering is a function call",
        "text": (
            "Rendering returns ordinary HTML. This makes components "
            "easy to integrate with web frameworks, or test with plain Python."
        ),
    },
)


# One mounting example per supported host. Each names the adapter it calls, and
# `_check_host_entrypoints` confirms that callable still exists at build time, so
# a renamed adapter fails the page instead of publishing a dead instruction.
_HOST_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "fastapi",
        "label": "FastAPI",
        "blurb": "Also Starlette",
        "file": "main.py",
        "entrypoint": ("citry.contrib.fastapi", "mount"),
        "code": (
            "from contextlib import asynccontextmanager\n"
            "\n"
            "from fastapi import FastAPI\n"
            "\n"
            "from citry import citry\n"
            "from citry.contrib.fastapi import mount\n"
            "\n"
            "@asynccontextmanager\n"
            "async def lifespan(_app: FastAPI):\n"
            "    citry.initialize()\n"
            "    yield\n"
            "\n"
            "app = FastAPI(lifespan=lifespan)\n"
            "mount(app, citry)"
        ),
    },
    {
        "id": "flask",
        "label": "Flask",
        "blurb": "The same call shape",
        "file": "app.py",
        "entrypoint": ("citry.contrib.flask", "mount"),
        "code": (
            "from flask import Flask\n"
            "\n"
            "from citry import citry\n"
            "from citry.contrib.flask import mount\n"
            "\n"
            "app = Flask(__name__)\n"
            'mount(app, citry, prefix="/citry")\n'
            "citry.initialize()"
        ),
    },
    {
        "id": "django",
        "label": "Django",
        "blurb": "Added to your URL conf",
        "file": "urls.py",
        "entrypoint": ("citry.contrib.django", "urlpatterns"),
        "code": (
            "from django.urls import path\n"
            "\n"
            "from citry import citry\n"
            "from citry.contrib.django import urlpatterns as citry_urls\n"
            "\n"
            "urlpatterns = [\n"
            '    path("", home_view),\n'
            '    *citry_urls(citry, prefix="/citry"),\n'
            "]"
        ),
    },
    {
        "id": "asgi",
        "label": "Bare ASGI",
        "blurb": "No framework required",
        "file": "asgi.py",
        "entrypoint": ("citry.contrib.asgi", "asgi_app"),
        "code": (
            "from citry import citry\n"
            "from citry.contrib.asgi import asgi_app\n"
            "\n"
            "citry.initialize()\n"
            "app = asgi_app(citry)"
        ),
    },
    {
        "id": "wsgi",
        "label": "Bare WSGI",
        "blurb": "For synchronous stacks",
        "file": "wsgi.py",
        "entrypoint": ("citry.contrib.wsgi", "wsgi_app"),
        "code": (
            "from citry import citry\n"
            "from citry.contrib.wsgi import wsgi_app\n"
            "\n"
            "citry.initialize()\n"
            "application = wsgi_app(citry)"
        ),
    },
)


# One answer per problem a product runs into once it is carrying real traffic,
# real rules, and more than one team. Each names the page that documents it,
# and `_check_depth_docs` confirms that page still exists at build time.
_DEPTH_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "cache",
        "label": "Caching",
        "blurb": "The same subtree, rebuilt on every request",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Two scopes, one backend. <code>Component.Cache</code> caches every call to a component class, while <code>&lt;c-cache&gt;</code> caches one named region inside a template, adding no wrapper element of its own.</p>"
            "<p>A miss always renders normally. Cache hit behaves the same in both the browser and server. <code>version</code> retires old entries on deploy.</p>"
            "</div>",
        ),
        "file": "product_card.py",
        "doc": "advanced/caching.md",
        "code": (
            "class ProductCard(Component):\n"
            "    class Kwargs:\n"
            "        product_id: int\n"
            "\n"
            "    class Slots:\n"
            "        pass\n"
            "\n"
            "    # Cache every time this component is called\n"
            "    class Cache:\n"
            "        enabled = True\n"
            "        ttl = 300\n"
            "        version = 1\n"
            "\n"
            '    template = """\n'
            "      <div>\n"
            "        {# Cache only this region #}\n"
            '        <c-cache key="expensive">\n'
            "          <c-ExpensiveUI />\n"
            "        </c-cache>\n"
            "      </div>\n"
            '    """\n'
        ),
    },
    {
        "id": "const",
        "label": "Const optimization",
        "blurb": "Don't re-render markup that never varies",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Most of a template does not change between renders. <code>Const</code> marks an input as fixed, so the markup that depends on it is rendered once and reused.</p>"
            "<p>A <code>Const</code> value works like the value it wraps in ordinary template expressions. Marking one is a promise that it will not change between renders.</p>"
            "</div>",
        ),
        "file": "dashboard.py",
        "doc": "advanced/const-optimization.md",
        "code": (
            "from citry import Const\n\n# The parts that never vary are rendered once and reused\nCard(cols=Const(3))"
        ),
    },
    {
        "id": "extensions",
        "label": "Extensions",
        "blurb": "Verify, modify, or extend all components at once",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>An extension installs on a <code>Citry</code> instance and sees every component through it, so a rule holds without editing each component or remembering to call anything.</p>"
            "<p>Hooks cover the render lifecycle, components' JS and CSS scripts, and more. An extension can also carry per-component config, store state for the duration of a render, and add its own URL endpoints and CLI commands.</p>"
            "</div>",
        ),
        "file": "timing.py",
        "doc": "advanced/extensions.md",
        "code": (
            "from citry import Citry, Extension\n"
            "\n"
            "\n"
            "class TimingExtension(Extension):\n"
            '    name = "timing"\n'
            "\n"
            "    def on_component_rendered(self, ctx):\n"
            "        record(type(ctx.component).__name__)\n"
            "        return None  # keep the original render\n"
            "\n"
            "\n"
            "app = Citry(extensions=[TimingExtension])"
        ),
    },
    {
        "id": "fragments",
        "label": "HTML fragments",
        "blurb": "Partial page updates. Works with HTMX.",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Easily integrate with HTMX. Instead of rendering a full page, render only small HTML to update one region.</p>"
            "<p>Fragments carry their own JS and CSS. Citry loads whatever that region needs. Duplicate assets are never loaded twice.</p>"
            "</div>",
        ),
        "file": "views.py",
        "doc": "advanced/html-fragments.md",
        "code": (
            'card = Card(title="Welcome")\n'
            "\n"
            "# The browser gets the markup and whatever JS and CSS it still needs\n"
            'card.render().serialize(deps_strategy="fragment")'
        ),
    },
    {
        "id": "libraries",
        "label": "Component libraries",
        "blurb": "Share and publish components across projects",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Share components across different projects as component libraries with <code>LibraryComponent</code>. An application installs the package's manifest into the <code>Citry</code> instance that should have it.</p>"
            "<p>Ideal for design systems or publishing to registries.</p>"
            "</div>",
        ),
        "file": "acme_ui/badge.py",
        "doc": "advanced/component-libraries.md",
        "code": (
            "from citry import (\n"
            "    ComponentLibrary,\n"
            "    LibraryComponent,\n"
            "    SlotInput,\n"
            "    citry,\n"
            ")\n"
            "\n"
            "# Define library components\n"
            "class AcmeBadge(LibraryComponent):\n"
            "    class Kwargs:\n"
            '        tone: str = "neutral"\n'
            "\n"
            "    class Slots:\n"
            "        default: SlotInput | None = None"
            "\n"
            "\n"
            "# Create Library\n"
            "acme_library = ComponentLibrary(\n"
            '    name="acme",\n'
            "    components=[AcmeBadge],\n"
            ")\n"
            "\n"
            "# Register library with Citry\n"
            "citry.register_library(acme_library)"
        ),
    },
)


def _check_depth_docs() -> None:
    """Fail the build when a promoted capability lost the page that explains it."""
    for case in _DEPTH_CASES:
        page = current_docs_project().runtime.content_dir / case["doc"]
        if not page.is_file():
            message = f"Landing page promotes {case['label']!r}, but {case['doc']} is gone."
            raise RuntimeError(message)


def _check_host_entrypoints() -> None:
    """Fail the build when a host example names an adapter that moved."""
    for case in _HOST_CASES:
        module_name, attribute = case["entrypoint"]
        module = importlib.import_module(module_name)
        if not hasattr(module, attribute):
            message = f"Landing page names {module_name}.{attribute}, which no longer exists."
            raise RuntimeError(message)


def _as_markdown_block(html: str) -> Markup:
    """Wrap generated markup so the markdown pass leaves it alone."""
    return Markup(f"\n\n{flatten_for_markdown(html)}\n\n")  # noqa: S704 - generated in this module


class LandingPickerMarkup(Component):
    """
    A list of rows beside one panel each: the page's shared picker.

    Every panel ships in the HTML, so a reader without JavaScript gets all of
    them. Each case supplies a highlighted snippet, and ``extra`` adds anything
    that belongs under it, which is how the reliability section puts a real
    error message beneath its code.
    """

    transparent = True

    class Kwargs:
        cases: list

    class Slots:
        pass

    template = """
      <div class="landing-picker" data-landing-picker>
        <div
          c-for="case in cases"
          class="landing-picker__item"
        >
        <button
          class="landing-picker__row"
          type="button"
          c-data-picker-case="case['id']"
          c-aria-pressed="'true' if case['first'] else 'false'"
          c-class="{
            'landing-picker__row': True,
            'is-active': case['first'],
          }"
        >
          <span class="landing-picker__number">
            {{ case['number'] }}
          </span>
          <span>
            <strong>{{ case['label'] }}</strong>
            <br><span class="landing-picker__blurb">
              {{ case['blurb'] }}
            </span>
          </span>
          <svg
            class="landing-picker__caret"
            viewBox="0 0 16 16"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 6l4 4 4-4"/>
          </svg>
        </button>
        <div
          class="landing-picker__panel"
          c-data-picker-panel="case['id']"
        >
          {{ case['note'] }}
          <div class="landing-code landing-picker__code">
            <div class="landing-code__bar">
              <span class="landing-code__dot"></span>
              <span>{{ case['file'] }}</span>
            </div>
            {{ case['code'] }}
          </div>
          {{ case['extra'] }}
        </div>
        </div>
      </div>
    """


def _picker_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Number the rows and mark the one that opens first."""
    return [
        {
            **case,
            "number": f"{number:02d}",
            "first": number == 1,
            "note": case.get("note", Markup("")),
            "extra": case.get("extra", Markup("")),
        }
        for number, case in enumerate(cases, start=1)
    ]


class LandingHostsMarkup(Component):
    """One mounting example per host, switched by the list beside it."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        _check_host_entrypoints()
        return {
            "picker": Markup(  # noqa: S704 - markup from this module
                str(
                    LandingPickerMarkup(
                        cases=_picker_cases(
                            [
                                {
                                    "id": case["id"],
                                    "label": case["label"],
                                    "blurb": case["blurb"],
                                    "file": case["file"],
                                    "code": Markup(_highlight(case["code"])),  # noqa: S704
                                }
                                for case in _HOST_CASES
                            ],
                        ),
                    ),
                ),
            ),
        }

    template = """
      {{ picker }}
    """


class LandingDepthMarkup(Component):
    """The capabilities a team reaches for after the first version ships."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        _check_depth_docs()
        return {
            "picker": Markup(  # noqa: S704 - markup from this module
                str(
                    LandingPickerMarkup(
                        cases=_picker_cases(
                            [
                                {
                                    "id": case["id"],
                                    "label": case["label"],
                                    "blurb": case["blurb"],
                                    "file": case["file"],
                                    "note": case["note"],
                                    "code": Markup(_highlight(case["code"])),  # noqa: S704
                                }
                                for case in _DEPTH_CASES
                            ],
                        ),
                    ),
                ),
            ),
        }

    template = """
      {{ picker }}
    """


class LandingDepth(Component):
    """Place the advanced-capability picker into the page."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"depth": _as_markdown_block(str(LandingDepthMarkup()))}

    template = """
      {{ depth }}
    """


class LandingHosts(Component):
    """Place the host examples into the page, flushed left for the markdown pass."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        markup = _as_markdown_block(str(LandingHostsMarkup()))
        return {"hosts": markup}

    template = """
      {{ hosts }}
    """


class LandingTourMarkup(Component):
    """The annotated walkthrough: one component's source beside its explanations."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        source = (current_docs_project().runtime.repo_root / _TOUR_PATH).read_text(encoding="utf-8")
        return {
            "file_name": _TOUR_PATH.rsplit("/", 1)[-1],
            "code": Markup(_tour_code(source, _TOUR_STOPS)),  # noqa: S704 - pygments output
            # Each line is its own block so a highlight can span the full width,
            # which means the rendered text carries no newline characters. The
            # copy button reads the original source from here instead. It is
            # encoded because the markup this component emits passes through
            # whitespace handling that would otherwise rewrite the blank lines.
            "source": base64.b64encode(source.encode()).decode(),
            # A note names attributes and methods, which read better as code than
            # in quotes, so its text is markup written in this module.
            "stops": [
                {**stop, "text": Markup(stop["text"])}  # noqa: S704 - written above, not user input
                for stop in _TOUR_STOPS
            ],
        }

    template = """
      <p style="font-size: 0.85rem; margin-top: 3rem;">
        Point at any marked line below to see what it does:
      </p>
      <div class="landing-tour" data-landing-tour c-data-tour-source="source">
        <div class="landing-code landing-tour__code">
          <div class="landing-code__bar">
            <span class="landing-code__dot"></span>
            <span>{{ file_name }}</span>
          </div>
          {{ code }}
        </div>
        <div class="landing-tour__notes">
          <p class="landing-tour__hint" data-tour-hint>
            Point at a marked line to see what it does.
          </p>
          <div
            c-for="stop in stops"
            class="landing-tour__note"
            c-data-tour-note="stop['id']"
          >
            <span class="landing-tour__note-label">{{ stop['label'] }}</span>
            <strong>{{ stop['title'] }}</strong>
            <p>{{ stop['text'] }}</p>
          </div>
        </div>
      </div>
    """


class LandingTour(Component):
    """
    Place the annotated walkthrough into the page, flushed left.

    Every note is server-rendered, so a reader without JavaScript gets the whole
    explanation as a list under the code. The script then shows one note at a
    time as the reader moves across the source.
    """

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        markup = _as_markdown_block(str(LandingTourMarkup()))
        return {"tour": markup}

    template = """
      {{ tour }}
    """


def _editor_ranges(source: str, marks: tuple[dict[str, Any], ...]) -> list[tuple[int, int, dict[str, Any]]]:
    """Resolve exact demo symbols, failing when an annotation no longer names one place."""
    ranges: list[tuple[int, int, dict[str, Any]]] = []
    for mark in marks:
        needle = mark["needle"]
        if source.count(needle) != 1:
            message = f"Editor demo marker {mark['id']!r} needs one occurrence of {needle!r}."
            raise RuntimeError(message)
        if needle.count(mark["symbol"]) != 1:
            message = f"Editor demo marker {mark['id']!r} does not identify one symbol inside its source range."
            raise RuntimeError(message)
        start = source.index(needle) + needle.index(mark["symbol"])
        ranges.append((start, start + len(mark["symbol"]), mark))

    ranges.sort(key=lambda item: item[0])
    for previous, current in itertools.pairwise(ranges):
        if previous[1] > current[0]:
            message = f"Editor demo markers {previous[2]['id']!r} and {current[2]['id']!r} overlap."
            raise RuntimeError(message)
    return ranges


def _editor_symbol_open(mark: dict[str, Any]) -> str:
    """Open one exact symbol without changing the text Pygments highlighted."""
    if definition := mark.get("definition"):
        definition_id = escape(definition)
        return (
            '<span class="landing-editor__definition" '
            f'data-editor-annotation="{escape(mark["id"])}" '
            f'id="landing-editor-definition-{definition_id}" '
            f'data-editor-definition="{definition_id}" tabindex="-1">'
        )

    mark_id = escape(mark["id"])
    description = escape(f"{mark['symbol']}: {mark['signature']}")
    severity = mark.get("severity")
    classes = "landing-editor__symbol"
    if severity:
        classes += f" landing-editor__symbol--{severity}"
    signature_html = highlight(
        mark["signature"],
        get_lexer_by_name(mark["language"]),
        HtmlFormatter(nowrap=True),
    ).strip()
    attributes = [
        'type="button"',
        f'class="{classes}"',
        f'data-editor-annotation="{mark_id}"',
        f'data-editor-symbol="{mark_id}"',
        f'data-editor-signature="{escape(mark["signature"])}"',
        f'data-editor-signature-html="{escape(signature_html)}"',
        f'data-editor-language="{escape(mark["language"])}"',
        f'data-editor-provenance="{escape(mark["provenance"])}"',
        f'data-editor-description="{escape(mark["description"])}"',
        f'data-editor-docs="{escape(mark["docs"])}"',
        'aria-controls="landing-editor-hover"',
        'aria-expanded="false"',
        f'aria-label="{description}"',
    ]
    if severity:
        attributes.append(f'data-editor-severity="{escape(severity)}"')
    if code := mark.get("code"):
        attributes.append(f'data-editor-diagnostic="{escape(code)}"')
    if placement := mark.get("placement"):
        attributes.append(f'data-editor-placement="{escape(placement)}"')
    if target := mark.get("target"):
        attributes.append(f'data-editor-target="{escape(target)}"')
    return f"<button {' '.join(attributes)}>"


def _editor_symbol_close(mark: dict[str, Any]) -> str:
    """Close an inert definition destination or an interactive source symbol."""
    return "</span>" if mark.get("definition") else "</button>"


def _editor_code(source: str, marks: tuple[dict[str, Any], ...]) -> str:
    """Highlight source with the real Citry lexer and wrap only annotated symbols."""
    ranges = _editor_ranges(source, marks)
    boundaries = {position for start, end, _mark in ranges for position in (start, end)}
    starts = {start: mark for start, _end, mark in ranges}
    ends = {end: mark for _start, end, mark in ranges}
    formatter = HtmlFormatter()
    rendered: list[str] = ['<div class="highlight"><pre><span></span>']

    # Split lexer tokens at annotation boundaries. The original token type is
    # retained on every piece, so an interactive name has exactly the same
    # colour it would have in an ordinary Citry code block.
    lexer = get_lexer_by_name("citry")
    for offset, token_type, value in lexer.get_tokens_unprocessed(source):
        token_end = offset + len(value)
        cuts = [offset, *(point for point in boundaries if offset < point < token_end), token_end]
        cuts.sort()
        css_classes = formatter._get_css_classes(token_type)
        for start, end in itertools.pairwise(cuts):
            if mark := starts.get(start):
                rendered.append(_editor_symbol_open(mark))
            text = str(escape(value[start - offset : end - offset]))
            if css_classes and text:
                rendered.append(f'<span class="{css_classes}">{text}</span>')
            else:
                rendered.append(text)
            if mark := ends.get(end):
                rendered.append(_editor_symbol_close(mark))

    rendered.append("</pre></div>\n")
    return "".join(rendered)


class LandingEditorDemoMarkup(Component):
    """A server-rendered editor surface with exact, focusable symbol hovers."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        repo_root = current_docs_project().runtime.repo_root
        if repo_root is None:
            raise RuntimeError("The landing editor demo needs a repository root to load its source.")
        source = (repo_root / _EDITOR_PATH).read_text(encoding="utf-8")
        return {
            "file_name": _EDITOR_PATH.rsplit("/", 1)[-1],
            "code": Markup(_editor_code(source, _EDITOR_MARKS)),  # noqa: S704 - escaped Pygments output
            "notes": list(_EDITOR_NOTES),
        }

    template = """
      <p style="font-size: 0.85rem; margin-top: 3rem;">
        Hover or focus any dotted symbol below. <b>Ctrl-click</b> / <b>⌘-click</b>
        on a symbol to go to its definition.
      </p>
      <div class="landing-editor" data-editor-showcase>
        <div class="landing-code landing-editor__code" data-editor-code>
          <div class="landing-code__bar landing-editor__bar">
            <span class="landing-code__dot"></span>
            <span>{{ file_name }}</span>
            <span class="landing-editor__mode">Citry</span>
          </div>
          <div class="landing-editor__hover-layer">
            <div
              id="landing-editor-hover"
              class="landing-editor__hover"
              role="dialog"
              aria-label="Type information"
              data-editor-hover
              hidden
            >
              <div class="landing-editor__hover-signature">
                <code data-editor-hover-signature></code>
              </div>
              <strong data-editor-hover-provenance></strong>
              <p data-editor-hover-description></p>
              <div class="landing-editor__hover-actions">
                <a
                  href="/ide/vscode/"
                  target="_blank"
                  rel="noopener"
                  data-editor-hover-docs
                >
                  Open Citry docs
                </a>
                <a href="#" data-editor-jump hidden>
                  Go to definition
                </a>
              </div>
              <small data-editor-jump-hint hidden>
                <kbd>Ctrl</kbd>/<kbd>⌘</kbd> + click also jumps
              </small>
            </div>
          </div>
          {{ code }}
          <p class="landing-editor__status" data-editor-status aria-live="polite"></p>
        </div>

        <div class="landing-editor__notes">
          <button
            c-for="note in notes"
            class="landing-editor__note"
            type="button"
            c-data-editor-note="note['mark']"
          >
            <span>{{ note['label'] }}</span>
            <strong>{{ note['title'] }}</strong>
            <small>{{ note['text'] }}</small>
          </button>
        </div>
      </div>
    """


class LandingEditorDemo(Component):
    """Place the editor showcase into a markdown page without rewriting its code."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"demo": _as_markdown_block(str(LandingEditorDemoMarkup()))}

    template = """
      {{ demo }}
    """


class LandingDiagnosticMarkup(Component):
    """
    Every captured error, its snippet, and the row that selects it.

    The rows and the panels come from one list, so the page cannot name a case
    it does not show. Each panel carries the real message under its code.
    """

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        cases = []
        for case in json.loads(_render_diagnostics()):
            message = (
                '<div class="landing-diagnostic">'
                f'<p class="landing-diagnostic__mutation"><span>{escape(case["blurb"])}</span></p>'
                f'<span class="landing-diagnostic__type">{escape(case["type"])}</span>'
                f"<pre>{escape(case['message'])}</pre>"
                "</div>"
            )
            cases.append(
                {
                    "id": case["id"],
                    "label": case["label"],
                    "blurb": case["blurb"],
                    "file": f"{case['id']}.py",
                    "code": Markup(case["code"]),  # noqa: S704 - pygments output
                    "extra": Markup(message),  # noqa: S704 - escaped above
                },
            )
        return {
            "picker": Markup(str(LandingPickerMarkup(cases=_picker_cases(cases)))),  # noqa: S704
        }

    template = """
      {{ picker }}
    """


class LandingDiagnostic(Component):
    """
    Place every captured error into the page, server-rendered.

    The panels are flushed left because they land inside a markdown block:
    indented HTML there is read as a code block and printed as source instead
    of rendered. Each error message sits in a ``<pre>``, so the carets Citry
    draws under the offending token keep their columns.
    """

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        panel = _as_markdown_block(str(LandingDiagnosticMarkup()))
        return {"panel": panel}

    template = """
      {{ panel }}
    """


# Each case is one mistake a reader can recognise, paired with the smallest code
# that causes it. The build runs this exact source, so the snippet on the page
# and the message under it can never describe different things.
_ERROR_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "input",
        "label": "Missing input",
        "blurb": "Rejected as the component is called",
        "code": (
            "card = StatusCard(\n"
            "    complete=18,\n"
            "    total=25,\n"
            ")\n"
            "\n"
            "# Rendering is where the component's inputs are checked\n"
            "str(card)"
        ),
        "expected": TypeError,
        "contains": "missing 1 required positional argument: 'title'",
    },
    {
        "id": "misspelled",
        "label": "Misspelled input",
        "blurb": "Rejected, and the name you meant is offered",
        "code": ('card = StatusCard(\n    titel="Deploy preview",\n    complete=18,\n    total=25,\n)\n\nstr(card)'),
        "expected": TypeError,
        "contains": "Did you mean 'title'?",
    },
    {
        "id": "template",
        "label": "Unknown template value",
        "blurb": "Pointed at the line that asked for it",
        "code": (
            "class Greeting(Component):\n"
            "    class Kwargs:\n"
            "        name: str\n"
            "\n"
            "    def template_data(self, kwargs, slots):\n"
            '        return {"name": kwargs.name}\n'
            "\n"
            '    template = "<p>Hello, {{ naem }}!</p>"\n'
            "\n"
            'str(Greeting(name="Ada"))'
        ),
        "expected": KeyError,
        "contains": "naem",
    },
    {
        "id": "isolation",
        "label": "Data stays in its component",
        "blurb": "A child never inherits the parent's variables",
        "code": (
            "class Child(Component):\n"
            '    template = "<span>{{ user_name }}</span>"\n'
            "\n"
            "class Parent(Component):\n"
            "    def template_data(self, kwargs, slots):\n"
            '        return {"user_name": "Ada"}\n'
            "\n"
            '    template = "<div>{{ user_name }}<c-child /></div>"\n'
            "\n"
            "str(Parent())"
        ),
        "expected": KeyError,
        "contains": "user_name",
    },
    {
        "id": "unknown",
        "label": "Unknown component",
        "blurb": "Named at the tag that asked for it",
        "code": (
            "class Page(Component):\n"
            '    template = """\n'
            '      <c-StatusCrad title="Deploy preview" />\n'
            '    """\n'
            "\n"
            "str(Page())"
        ),
        "expected": Exception,
        "contains": "statuscrad",
    },
    {
        "id": "mismatched",
        "label": "Mismatched tags",
        "blurb": "The parser names the tag it expected to close",
        "code": ('class Broken(Component):\n    template = "<div><span>Deploy preview</div>"\n\nstr(Broken())'),
        "expected": SyntaxError,
        "contains": "Mismatched tags",
    },
    {
        "id": "unsafe",
        "label": "Unsafe expression",
        "blurb": "Template expressions cannot reach the interpreter",
        "code": (
            "class Danger(Component):\n    template = \"<i>{{ __import__('os').system('ls') }}</i>\"\n\nstr(Danger())"
        ),
        "expected": Exception,
        "contains": "unsafe",
    },
)


def _tour_code(source: str, stops: tuple[dict[str, Any], ...]) -> str:
    """
    Highlight the walkthrough source and tag each line with the stop it belongs to.

    Pygments' ``linespans`` wraps every rendered line in its own span, which is
    what makes this possible: a triple-quoted template is one token spanning
    many lines, so splitting the highlighted HTML by newline would cut tags in
    half. The line spans are added by the formatter, after tokenizing, so they
    always land between lines rather than inside a token.
    """
    html = highlight(source, get_lexer_by_name("citry"), HtmlFormatter(linespans="tourline"))
    line_to_stop: dict[int, tuple[str, bool]] = {}
    for stop in stops:
        first, last = stop["lines"]
        for number in range(first, last + 1):
            line_to_stop[number] = (stop["id"], number == first)

    def tag(match: re.Match[str]) -> str:
        number = int(match.group(1))
        found = line_to_stop.get(number)
        if found is None:
            # Every line becomes a block, marked or not, so the block layout is
            # what breaks lines. A mix of block and inline lines would run the
            # inline ones together once their newlines are gone.
            return f'<span id="tourline-{number}" class="landing-tour__line">'
        stop_id, is_first = found
        start = ' data-tour-start=""' if is_first else ""
        return f'<span id="tourline-{number}" class="landing-tour__line is-marked" data-tour="{stop_id}"{start}>'

    html = re.sub(r'<span id="tourline-(\d+)">', tag, html)
    # Pygments keeps each line's newline inside its span. A block-level line
    # already ends its own row, so the newline is dropped rather than moved:
    # left anywhere in the flow it renders as a second, empty row.
    return html.replace("\n</span>", "</span>")


def _clean(message: str) -> str:
    """
    Drop build-machine detail a reader cannot act on.

    A component defined inside one of these snippets has no source file, so the
    location Citry names for it points at the interpreter rather than anything
    the reader could open.
    """
    text = message.replace(str(current_docs_project().runtime.repo_root) + "/", "")
    # Citry names a component's location two ways: in parentheses after the
    # template's name, and inline for a parse error. Both point at the
    # interpreter for a class defined in one of these snippets.
    text = re.sub(r"\s*\((?:builtins|<string>)::[^)]+\)", "", text)
    return re.sub(r"(?:builtins|<string>)::", "", text)


def _highlight(code: str) -> str:
    """Colour one snippet with the same lexer the page's code blocks use."""
    return highlight(code, get_lexer_by_name("citry"), HtmlFormatter())


def _capture(render: Callable[[], object], expected: type[Exception], contains: str) -> tuple[str, str]:
    """
    Run a deliberately broken render and return the real error class and text.

    The page tells readers that a mistake which stops being reported fails this
    build, so checking that *something* raised is not enough: a different error,
    or the same error with its guidance dropped, would still publish a label
    that no longer matches the message. The build fails unless the expected
    error arrives carrying the words the page promises.
    """
    try:
        render()
    except expected as error:
        # KeyError stringifies as the repr of its argument, which would show the
        # message's newlines and carets as literal escapes. Read the text itself.
        text = error.args[0] if isinstance(error, KeyError) and error.args else str(error)
        text = str(text)
        if contains not in text:
            message = (
                f"Landing page diagnostic lost its detail: expected {contains!r} "
                f"in the {expected.__name__} Citry raised, got:\n{text}"
            )
            raise RuntimeError(message) from error
        return type(error).__name__, text
    message = (
        f"Landing page diagnostic no longer raises {expected.__name__}; the reliability claim on the page is stale."
    )
    raise RuntimeError(message)


@functools.cache
def _render_diagnostics() -> str:
    """Run every listed mistake and collect the error Citry raised for it."""
    captured = []
    for case in _ERROR_CASES:
        code = case["code"]
        # The snippet is a constant written above, and running it is the whole
        # point: the reader is looking at the source that produced the message.
        namespace: dict[str, Any] = {"Component": Component, "StatusCard": StatusCard}
        error_type, message = _capture(
            lambda code=code, namespace=namespace: exec(code, namespace),  # noqa: S102
            case["expected"],
            case["contains"],
        )
        captured.append(
            {
                "id": case["id"],
                "label": case["label"],
                "blurb": case["blurb"],
                "code": _highlight(code),
                "type": error_type,
                # A build machine's checkout path is not useful to a reader, and
                # a snippet defined here has no file of its own to point at.
                "message": _clean(message),
            },
        )
    return json.dumps(captured, separators=(",", ":"))


class LandingPage(Component):
    """Purpose-built landing layout with a component-generated canvas field."""

    class Kwargs:
        content_html: Any
        searchable: bool = True
        pagefind_weight: Any = None
        repo_url: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "content_html": kwargs.content_html,
            "searchable": kwargs.searchable,
            "pagefind_weight": kwargs.pagefind_weight,
            "repo_url": kwargs.repo_url,
        }

    template = """
      <div class="landing-shell" data-landing-root>
        <a class="landing-skip" href="#landing-main">Skip to content</a>
        <main id="landing-main" class="landing-main">
          <article
            class="landing-content"
            c-data-pagefind-body="searchable"
            c-data-pagefind-weight="pagefind_weight"
          >
            {{ content_html }}
          </article>
        </main>
        <footer class="landing-footer">
          <span>Citry is free and open source under the
          <a href="/community/license/">MIT license</a>.</span>
          <span class="landing-footer__links">
            <!-- The footer is not a markdown context, so it takes the row
                 directly rather than the wrapped-for-markdown form. -->
            <c-social-links-markup variant="landing-social--footer" />
          </span>
        </footer>
      </div>
    """

    css = """
      .citry-landing-page {
        overflow-x: hidden;
      }

      .citry-landing__nav-drawer {
        display: none;
      }

      .landing-shell {
        --landing-bg: #f4f8fc;
        --landing-bg-deep: #e5eef8;
        --landing-ink: #0b1729;
        --landing-muted: #4e6076;
        --landing-faint: #70849c;
        --landing-line: rgb(21 69 112 / 14%);
        --landing-panel: rgb(255 255 255 / 100%);
        --landing-panel-solid: #f9fbfe;
        --landing-blue: #276df2;
        --landing-cyan: #00a9a6;
        --landing-violet: #7457ef;
        --landing-warm: #df6d46;
        min-height: 100vh;
        background:
          radial-gradient(circle at 16% 12%, rgb(39 109 242 / 12%), transparent 28rem),
          radial-gradient(circle at 86% 28%, rgb(0 169 166 / 9%), transparent 34rem),
          var(--landing-bg);
        color: var(--landing-ink);
      }

      [data-theme="dark"] .landing-shell {
        --landing-bg: #050914;
        --landing-bg-deep: #0a1122;
        --landing-ink: #f3f7ff;
        --landing-muted: #a7b6cc;
        --landing-faint: #7588a5;
        --landing-line: rgb(127 181 255 / 15%);
        --landing-panel: rgb(11 19 36 / 100%);
        --landing-panel-solid: #0b1324;
        --landing-blue: #6d9eff;
        --landing-cyan: #4de0d5;
        --landing-violet: #a18aff;
        --landing-warm: #ff9776;
      }

      @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) .landing-shell {
          --landing-bg: #050914;
          --landing-bg-deep: #0a1122;
          --landing-ink: #f3f7ff;
          --landing-muted: #a7b6cc;
          --landing-faint: #7588a5;
          --landing-line: rgb(127 181 255 / 15%);
          --landing-panel: rgb(11 19 36 / 100%);
          --landing-panel-solid: #0b1324;
          --landing-blue: #6d9eff;
          --landing-cyan: #4de0d5;
          --landing-violet: #a18aff;
          --landing-warm: #ff9776;
        }
      }

      .landing-skip {
        position: fixed;
        top: 0.75rem;
        left: 0.75rem;
        z-index: 100;
        padding: 0.65rem 0.9rem;
        border-radius: 0.5rem;
        background: var(--landing-ink);
        color: var(--landing-bg);
        transform: translateY(-160%);
      }

      .landing-skip:focus {
        transform: translateY(0);
      }

      .landing-main {
        position: relative;
        padding-top: 4rem;
      }

      .landing-content {
        position: relative;
        z-index: 2;
      }

      /* A class that sets `display` beats the [hidden] default, which would
         otherwise leave every panel on screen once the script hides one. */
      .landing-shell [hidden] {
        display: none !important;
      }

      .landing-content a {
        color: inherit;
        text-underline-offset: 0.2em;
      }

      .landing-content .heading-anchor,
      .landing-content .heading-anchor:visited {
        color: inherit;
        text-decoration: none;
      }

      .landing-hero,
      .landing-section,
      .landing-final {
        width: min(76rem, calc(100% - 3rem));
        margin-inline: auto;
      }

      .landing-hero {
        position: relative;
        min-height: min(54rem, calc(100svh - 4rem));
        display: grid;
        align-content: center;
        padding: clamp(4.5rem, 10vh, 8rem) 0 6rem;
      }

      /* A blueprint grid behind the hero, drawn entirely in CSS: two repeating
         line gradients and one accent glow, with no payload and no script. It
         bleeds past the page column to reach the window edges, and the mask
         fades it out before it reaches the copy, so contrast is never the
         reader's problem. */
      .landing-hero::before {
        content: "";
        position: absolute;
        z-index: -1;
        inset: -8rem -50vw -6rem;
        background:
          radial-gradient(
            circle at 14% 6%,
            color-mix(in srgb, var(--landing-blue), transparent 76%),
            transparent 42%
          ),
          repeating-linear-gradient(
            90deg,
            transparent 0 2.25rem,
            var(--landing-line) 2.25rem calc(2.25rem + 1px)
          ),
          repeating-linear-gradient(
            180deg,
            transparent 0 2.25rem,
            var(--landing-line) 2.25rem calc(2.25rem + 1px)
          );
        mask-image: radial-gradient(
          130% 105% at 6% 0%,
          rgb(0 0 0 / 90%) 0%,
          rgb(0 0 0 / 40%) 46%,
          transparent 76%
        );
        pointer-events: none;
      }

      .landing-hero__grid {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
        gap: clamp(2rem, 5vw, 4.5rem);
        align-items: start;
      }

      .landing-hero__copy {
        min-width: 0;
      }

      .landing-hero__code {
        min-width: 0;
        margin-top: -2.5rem;
      }

      .landing-hero__code pre {
        max-height: 35rem;
        font-size: 0.72rem;
      }

      .landing-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        margin: 0 0 1.4rem;
        padding: 0.45rem 0.75rem;
        border: 1px solid var(--landing-line);
        border-radius: 999px;
        background: var(--landing-panel);
        color: var(--landing-muted);
        font-family: var(--font-mono);
        font-size: 0.75rem;
        letter-spacing: 0.055em;
        text-transform: uppercase;
      }

      .landing-eyebrow::before {
        content: "";
        width: 0.48rem;
        height: 0.48rem;
        border-radius: 50%;
        background: var(--landing-cyan);
        box-shadow: 0 0 1rem var(--landing-cyan);
      }

      /* Sized for a sentence rather than a phrase: the cap holds it to three
         lines beside the code panel instead of stacking one word per row. */
      .landing-content .landing-hero h1 {
        max-width: 15ch;
        margin: 0;
        font-size: clamp(2.9rem, 5.6vw, 4.6rem);
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.03em;
        text-wrap: balance;
      }

      .landing-hero__lede {
        max-width: 43rem;
        margin: 2rem 0 0;
        color: var(--landing-muted);
        font-size: clamp(1.12rem, 2vw, 1.4rem);
        line-height: 1.62;
      }

      .landing-hero__lede strong {
        color: var(--landing-ink);
        font-weight: 620;
      }

      .landing-actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        margin-top: 2rem;
      }

      /* Two weights, not two boxes. The primary action is a solid, slightly
         raised control; the secondary is quiet until the pointer reaches it, so
         the pair reads as a decision rather than a toolbar. */
      .landing-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        height: 3rem;
        padding: 0 1.15rem;
        border: 1px solid transparent;
        border-radius: 0.55rem;
        background: transparent;
        color: var(--landing-muted);
        font-size: 0.95rem;
        font-weight: 550;
        letter-spacing: -0.01em;
        text-decoration: none;
        transition: color 140ms ease, background 140ms ease, box-shadow 140ms ease;
      }

      .landing-content .landing-button:hover,
      .landing-content .landing-button:focus-visible {
        background: color-mix(in srgb, var(--landing-ink), transparent 94%);
        color: var(--landing-ink);
      }

      .landing-button:focus-visible {
        outline: 2px solid var(--landing-blue);
        outline-offset: 2px;
      }

      /* The arrow leans forward on hover, so the button answers the pointer
         without the whole control jumping under it. */
      .landing-button__arrow {
        width: 0.85rem;
        height: 0.85rem;
        flex: none;
        transition: transform 160ms ease;
      }

      .landing-button:hover .landing-button__arrow,
      .landing-button:focus-visible .landing-button__arrow {
        transform: translateX(0.15rem);
      }

      .landing-content .landing-button--primary {
        padding: 0 1.35rem;
        background: var(--landing-blue);
        color: #fff;
        font-weight: 600;
        /* A hairline of light along the top edge and a shadow tinted with the
           button's own colour, so it sits on the page rather than on top of it. */
        box-shadow:
          inset 0 1px 0 rgb(255 255 255 / 22%),
          0 6px 16px -8px color-mix(in srgb, var(--landing-blue), transparent 25%);
        transition: 0.2s;
      }

      .landing-content .landing-button--primary:hover,
      .landing-content .landing-button--primary:focus-visible {
        background: color-mix(in srgb, var(--landing-blue), #000 12%);
        color: #fff;
        box-shadow:
          inset 0 1px 0 rgb(255 255 255 / 22%),
          0 10px 12px -10px color-mix(in srgb, var(--landing-blue), transparent 10%);
      }

      [data-theme="dark"] .landing-content .landing-button--primary:hover,
      [data-theme="dark"] .landing-content .landing-button--primary:focus-visible {
        background: color-mix(in srgb, var(--landing-blue), #fff 12%);
      }

      /* The channels the project actually lives on, under the install line. */
      .social-links {
        display: flex;
        align-items: center;
        gap: 0.25rem;
      }

      .landing-social {
        margin-top: 0.9rem;
        margin-left: -0.5rem;
      }

      .social-links__link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.25rem;
        height: 2.25rem;
        border-radius: 0.5rem;
        color: var(--landing-faint);
        transition: color 140ms ease, background 140ms ease;
      }

      .landing-content .social-links__link:hover,
      .landing-content .social-links__link:focus-visible {
        background: color-mix(in srgb, var(--landing-ink), transparent 94%);
        color: var(--landing-ink);
      }

      .landing-social--footer {
        margin-left: 0.25rem;
      }

      .landing-social--footer .social-links__link {
        width: 1.9rem;
        height: 1.9rem;
      }

      /* Reads as a terminal line rather than a form field: a prompt mark, the
         command, and a copy control that only colours in on hover. */
      .landing-install {
        display: flex;
        width: fit-content;
        max-width: 100%;
        align-items: center;
        gap: 0.9rem;
        margin-top: 1.1rem;
        padding: 0 0.5rem 0 1rem;
        min-height: 3.25rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.6rem;
        background: var(--landing-panel-solid);
      }

      .landing-install code {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        min-width: 0;
        overflow-x: auto;
        color: var(--landing-ink);
        font-family: var(--font-mono);
        font-size: 0.92rem;
        white-space: nowrap;
      }

      .landing-install code::before {
        content: "$";
        color: var(--landing-blue);
        user-select: none;
      }

      .landing-copy {
        display: inline-flex;
        align-items: center;
        flex: none;
        min-height: 2.25rem;
        padding: 0 0.7rem;
        border: 0;
        border-radius: 0.4rem;
        background: transparent;
        color: var(--landing-faint);
        cursor: pointer;
        font: inherit;
        font-size: 0.78rem;
        transition: background 140ms ease, color 140ms ease;
      }

      .landing-copy:hover,
      .landing-copy:focus-visible {
        background: color-mix(in srgb, var(--landing-blue), transparent 90%);
        color: var(--landing-ink);
      }

      .landing-sponsors {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem 1.5rem;
        margin: 1.5rem 0 0;
        padding: 0;
        list-style: none;
      }

      .landing-sponsors a {
        color: var(--landing-ink);
        font-size: 1.05rem;
        font-weight: 640;
        text-decoration: none;
      }

      .landing-sponsors a:hover {
        color: var(--landing-blue);
      }

      .landing-section {
        padding: clamp(5rem, 10vw, 9rem) 0;
        border-top: 1px solid var(--landing-line);
      }

      /* A full-width band on the deeper surface. Breaking out of the page
         column stops every section from arriving at the same width and tone;
         the page hides sideways overflow, so the viewport-width trick here
         cannot introduce a horizontal scrollbar. */
      .landing-section--band {
        width: auto;
        margin-inline: calc(50% - 50vw);
        padding-inline: max(1.5rem, calc(50vw - 38rem));
        border-top: 0;
        background: var(--landing-bg-deep);
      }

      /* The facts section is deliberately the quietest one on the page. */
      .landing-section--plain {
        padding: clamp(3.5rem, 7vw, 5.5rem) 0;
      }

      .landing-content .landing-section--plain h2 {
        max-width: 34ch;
        font-size: clamp(1.4rem, 2.2vw, 1.9rem);
        letter-spacing: -0.015em;
      }

      .landing-section--plain .landing-trust-grid {
        margin-top: 2rem;
        gap: clamp(1.5rem, 4vw, 3rem);
        align-items: start;
      }

      .landing-section__kicker {
        margin: 0 0 1rem;
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.76rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .landing-content .landing-section h2,
      .landing-content .landing-final h2 {
        max-width: 18ch;
        margin: 0;
        color: var(--landing-ink);
        font-size: clamp(2.1rem, 3.6vw, 3.5rem);
        line-height: 1.06;
        letter-spacing: -0.025em;
        text-wrap: balance;
      }

      .landing-content .headerlink {
        color: var(--landing-faint);
        font-size: 0.4em;
        text-decoration: none;
        vertical-align: middle;
        opacity: 0;
      }

      .landing-content h2:hover .headerlink,
      .landing-content .headerlink:focus-visible {
        opacity: 1;
      }

      .landing-section__intro {
        max-width: 42rem;
        margin: 1.4rem 0 0;
        color: var(--landing-muted);
        font-size: 1.1rem;
        line-height: 1.7;
      }

      .landing-proof-grid,
      .landing-error-grid,
      .landing-human-grid,
      .landing-trust-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(17rem, 0.85fr);
        gap: clamp(2rem, 6vw, 5.5rem);
        align-items: start;
        margin-top: 3rem;
      }

      .landing-proof-grid > *,
      .landing-error-grid > *,
      .landing-human-grid > *,
      .landing-trust-grid > * {
        min-width: 0;
      }

      .landing-code {
        overflow: hidden;
        min-width: 0;
        max-width: 100%;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel-solid);
        box-shadow: 0 2rem 6rem rgb(18 48 84 / 10%);
      }

      .landing-code__bar {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.7rem 0.9rem;
        border-bottom: 1px solid var(--landing-line);
        color: var(--landing-faint);
        font-family: var(--font-mono);
        font-size: 0.6rem;
      }

      .landing-code__dot {
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 2px;
        background: var(--landing-blue);
      }

      .landing-code__bar span:last-child {
        margin-left: 0.15rem;
      }

      .landing-code .highlight,
      .landing-code pre {
        margin: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
      }

      .landing-code pre {
        overflow: auto;
        padding: 1.25rem;
        font-size: 0.78rem;
        line-height: 1.65;
      }

      .landing-error-list {
        display: grid;
        gap: 0.6rem;
      }

      /* The caret only means something where a row opens its own panel, so it
         is absent from the layout until the list becomes an accordion. */
      .landing-picker__caret {
        display: none;
        width: 1rem;
        height: 1rem;
        align-self: center;
        color: var(--landing-faint);
        transition: transform 160ms ease;
      }

      .landing-picker__row {
        user-select: text;
        display: grid;
        grid-template-columns: 1.75rem 1fr;
        gap: 0.7rem;
        width: 100%;
        padding: 0.5rem 0.85rem;
        border: 1px solid transparent;
        border-radius: 0.7rem;
        background: transparent;
        color: var(--landing-muted);
        cursor: pointer;
        font: inherit;
        text-align: left;
      }

      .landing-picker__row:hover,
      .landing-picker__row:focus-visible,
      .landing-picker__row.is-active {
        border-color: var(--landing-line);
        background: var(--landing-panel);
        color: var(--landing-ink);
      }

      .landing-picker__number {
        color: var(--landing-warm);
        font-family: var(--font-mono);
        font-size: 0.76rem;
      }

      .landing-picker__blurb {
        font-size: 0.85rem;
      }

      /* The editor leads so this section changes the page's visual rhythm;
         the compact capability index stays visible beside the long source. */
      .landing-editor {
        display: grid;
        grid-template-columns: minmax(0, 1.42fr) minmax(15rem, 0.58fr);
        gap: clamp(1.5rem, 4vw, 3rem);
        align-items: start;
      }

      .landing-editor__notes {
        position: sticky;
        top: 5.5rem;
        display: grid;
        gap: 0.7rem;
        min-width: 0;
      }

      .landing-editor__hint {
        margin: 0 0 0.25rem;
        color: var(--landing-faint);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .landing-editor__note {
        display: grid;
        gap: 0.4rem;
        width: 100%;
        padding: 0.9rem 1rem;
        border: 1px solid transparent;
        border-radius: 0.8rem;
        background: transparent;
        color: var(--landing-muted);
        cursor: pointer;
        font: inherit;
        text-align: left;
        transition: 140ms ease;
        transition-property: border-color, background, color, transform;
      }

      .landing-editor__note:hover,
      .landing-editor__note:focus-visible,
      .landing-editor__note.is-active {
        border-color: var(--landing-line);
        background: var(--landing-panel);
        color: var(--landing-ink);
        transform: translateX(-0.2rem);
      }

      .landing-editor__note span {
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }

      .landing-editor__note strong {
        font-size: 0.92rem;
        line-height: 1.35;
      }

      .landing-editor__note small {
        color: var(--landing-muted);
        font-size: 0.79rem;
        line-height: 1.5;
      }

      .landing-editor__code {
        position: relative;
        overflow: visible;
        min-width: 0;
        isolation: isolate;
      }

      .landing-editor__code > .highlight {
        overflow: hidden;
        border-radius: 0 0 0.9rem 0.9rem;
      }

      .landing-editor__bar {
        background: color-mix(in srgb, var(--landing-panel-solid), var(--landing-bg) 22%);
      }

      .landing-editor__mode {
        margin-left: auto !important;
        color: var(--landing-blue);
        text-transform: uppercase;
      }

      .landing-editor__code > .highlight > pre {
        max-height: 46rem;
        padding: 1.2rem 1.35rem 2.5rem;
        font-size: 0.76rem;
        line-height: 1.62;
      }

      /* Buttons retain the lexer spans inside them, so resetting their chrome
         keeps the exact syntax colours and adds only the discoverable underline. */
      .landing-editor__symbol {
        display: inline;
        margin: 0;
        padding: 0 0 0.04em;
        border: 0;
        border-bottom: 1px dotted color-mix(in srgb, var(--landing-blue), transparent 18%);
        border-radius: 0;
        background: transparent;
        color: inherit;
        cursor: help;
        font: inherit;
        letter-spacing: inherit;
        line-height: inherit;
        text-align: inherit;
      }

      .landing-editor__symbol:hover,
      .landing-editor__symbol:focus-visible,
      .landing-editor__symbol.is-active {
        outline: 0;
        background: color-mix(in srgb, var(--landing-blue), transparent 80%);
        box-shadow: 0 0 0 0.13rem color-mix(in srgb, var(--landing-blue), transparent 80%);
      }

      .landing-editor__symbol--error {
        border-bottom: 0;
        text-decoration-line: underline;
        text-decoration-style: wavy;
        text-decoration-color: #f14c4c;
        text-decoration-thickness: 1.5px;
        text-underline-offset: 0.16em;
      }

      .landing-editor__symbol--error:hover,
      .landing-editor__symbol--error:focus-visible,
      .landing-editor__symbol--error.is-active {
        background: rgb(241 76 76 / 12%);
        box-shadow: 0 0 0 0.13rem rgb(241 76 76 / 12%);
      }

      .landing-editor__definition:focus {
        outline: 0;
      }

      .landing-editor__definition.is-definition-flash {
        animation: landing-editor-definition 1.15s ease-out;
      }

      @keyframes landing-editor-definition {
        0%, 35% {
          background: color-mix(in srgb, var(--landing-cyan), transparent 55%);
          box-shadow: 0 0 0 0.28rem color-mix(in srgb, var(--landing-cyan), transparent 72%);
        }
        100% {
          background: transparent;
          box-shadow: none;
        }
      }

      .landing-editor__hover-layer {
        position: absolute;
        inset: 0;
        z-index: 8;
        overflow: visible;
        pointer-events: none;
      }

      .landing-editor__hover {
        position: absolute;
        width: min(29rem, calc(100% - 1.5rem));
        padding: 0.8rem 0.9rem;
        border: 1px solid #555;
        border-radius: 0.28rem;
        background: #202020;
        box-shadow: 0 0.8rem 2.2rem rgb(0 0 0 / 42%);
        color: #d4d4d4;
        font-family: var(--font-sans);
        font-size: 0.78rem;
        line-height: 1.45;
        pointer-events: auto;
      }

      .landing-editor__hover.is-error {
        border-color: #a1260d;
      }

      .landing-editor__hover.is-error .landing-editor__hover-signature {
        border-bottom-color: #6e342c;
        box-shadow: inset 0.2rem 0 #f14c4c;
      }

      .landing-editor__hover.is-error > strong {
        color: #f48771;
      }

      .landing-editor__hover-signature {
        margin: -0.8rem -0.9rem 0.75rem;
        padding: 0.7rem 0.9rem;
        border-bottom: 1px solid #3d3d3d;
        background: #181818;
        color: #d4d4d4;
        font-size: 0.76rem;
        line-height: 1.55;
        white-space: pre-wrap;
      }

      .landing-editor__hover-signature code {
        padding: 0;
        background: transparent;
        color: inherit;
        font-family: var(--font-mono);
        font-size: inherit;
        line-height: inherit;
        white-space: inherit;
      }

      /* These mirror the restrained VS Code dark-theme palette used by the
         reference hover while preserving Pygments' language-aware tokens. */
      .landing-editor__hover-signature :is(.n, .nx, .nv) { color: #9cdcfe; }
      .landing-editor__hover-signature :is(.nb, .kt, .nc) { color: #4ec9b0; }
      .landing-editor__hover-signature :is(.k, .kd, .kn, .ow) { color: #c586c0; }
      .landing-editor__hover-signature :is(.nf, .fm) { color: #dcdcaa; }
      .landing-editor__hover-signature :is(.s, .s1, .s2) { color: #ce9178; }
      .landing-editor__hover-signature :is(.mi, .mf) { color: #b5cea8; }
      .landing-editor__hover-signature :is(.p, .o) { color: #d4d4d4; }

      .landing-editor__hover strong {
        display: block;
        color: #f2f2f2;
        font-size: 0.78rem;
      }

      .landing-editor__hover p {
        margin: 0.35rem 0 0;
        color: #b8b8b8;
      }

      .landing-editor__hover-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
        margin-top: 0.65rem;
      }

      .landing-editor__hover a {
        color: #75beff;
        font-size: 0.74rem;
        text-decoration: none;
      }

      .landing-editor__hover a:hover,
      .landing-editor__hover a:focus-visible {
        text-decoration: underline;
      }

      .landing-editor__hover > small {
        display: block;
        margin-top: 0.5rem;
        color: #929292;
        font-size: 0.68rem;
      }

      .landing-editor__hover kbd {
        padding: 0.05rem 0.2rem;
        border: 1px solid #555;
        border-radius: 0.2rem;
        background: #2d2d2d;
        color: #ddd;
        font-family: var(--font-mono);
        font-size: 0.64rem;
      }

      .landing-editor__status {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip-path: inset(50%);
        white-space: nowrap;
      }

      /* The annotated walkthrough: source on the left, one explanation on the
         right. Marked lines carry a dot in the gutter so a reader can see where
         there is something to point at. */
      .landing-tour {
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(16rem, 0.65fr);
        gap: clamp(1.5rem, 4vw, 3rem);
        align-items: start;
      }

      .landing-tour__code {
        min-width: 0;
      }

      .landing-tour__code pre {
        max-height: none;
        padding-left: 1.9rem;
        font-size: 0.78rem;
      }

      .landing-tour__line {
        position: relative;
        display: block;
        min-height: 1.2rem;
        cursor: help;
        transition: background 140ms ease;
      }

      .landing-tour__line:hover,
      .landing-tour__line.is-active {
        background: color-mix(in srgb, var(--landing-blue), transparent 88%);
        box-shadow: inset 2px 0 0 var(--landing-blue);
      }

      .landing-tour__line[data-tour-start]::before {
        content: "";
        position: absolute;
        left: -1.15rem;
        top: 0.52em;
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 50%;
        background: var(--landing-blue);
        box-shadow: 0 0 0 0 color-mix(in srgb, var(--landing-blue), transparent 40%);
        animation: landing-tour-pulse 2.6s ease-out infinite;
      }

      @keyframes landing-tour-pulse {
        0%, 70% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--landing-blue), transparent 40%); }
        100% { box-shadow: 0 0 0 0.42rem color-mix(in srgb, var(--landing-blue), transparent 100%); }
      }

      .landing-tour__notes {
        position: sticky;
        top: 5.5rem;
        display: grid;
        gap: 0.9rem;
        min-width: 0;
      }

      .landing-tour__hint {
        margin: 0;
        color: var(--landing-faint);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .landing-tour__note {
        padding: 1.1rem 1.2rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel-solid);
        box-shadow: 0 1rem 2.5rem rgb(12 30 56 / 14%);
      }

      [data-theme="dark"] .landing-tour__note {
        box-shadow: 0 1rem 2.5rem rgb(0 0 0 / 45%);
      }

      .landing-tour__note-label {
        display: block;
        margin-bottom: 0.5rem;
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      .landing-tour__note strong {
        display: block;
        font-size: 1.02rem;
      }

      .landing-tour__note p {
        margin: 0.5rem 0 0;
        color: var(--landing-muted);
        font-size: 0.88rem;
        line-height: 1.6;
      }

      .landing-tour__note code {
        padding: 0.08em 0.32em;
        border-radius: 0.3rem;
        background: color-mix(in srgb, var(--landing-blue), transparent 88%);
        color: var(--landing-ink);
        font-family: var(--font-mono);
        font-size: 0.85em;
        white-space: nowrap;
      }

      /* A panel belongs to the row above it on a small screen and to a column
         beside the list on a large one. The markup keeps each panel next to its
         own row either way; here the panels are lifted out of the flow so the
         rows stay stacked tight against each other. A panel left in the grid
         would span every row and hand its height back to them as gaps. */
      .landing-picker {
        --landing-picker-rail: 20rem;
        --landing-picker-gutter: clamp(1.5rem, 4vw, 3rem);
        /* Held as one value: a minifier may drop the space between a var() and
           a following function, which would make the declaration invalid. */
        --landing-picker-columns: 20rem minmax(0, 1fr);
        position: relative;
        display: grid;
        grid-template-columns: var(--landing-picker-columns);
        gap: 0.4rem var(--landing-picker-gutter);
        align-content: start;
        /* Room for the tallest panel before the script measures the real one. */
        min-height: 26rem;
        margin-top: 3rem;
      }

      .landing-picker__item {
        display: contents;
      }

      .landing-picker .landing-picker__row {
        grid-column: 1;
      }

      .landing-picker .landing-picker__panel {
        position: absolute;
        top: 0;
        left: calc(var(--landing-picker-rail) + var(--landing-picker-gutter));
        right: 0;
      }

      .landing-diagnostics {
        display: grid;
        gap: 1rem;
        /* Both the wrapper and each panel need this. A grid item defaults to
           min-width:auto, which grows to the widest line of the error text and
           pushes the whole card past the right edge of the page instead of
           letting the message scroll inside it. */
        min-width: 0;
      }

      .landing-diagnostic {
        min-width: 0;
        padding: 1.2rem;
        border: 1px solid color-mix(in srgb, var(--landing-warm), transparent 60%);
        border-radius: 0.85rem;
        background: color-mix(in srgb, var(--landing-warm), transparent 92%);
        font-family: var(--font-mono);
        font-size: 0.78rem;
        line-height: 1.65;
      }

      .landing-diagnostic__type {
        display: block;
        margin-bottom: 0.7rem;
        color: var(--landing-warm);
        font-weight: 700;
      }

      .landing-diagnostic__mutation {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0 0 1rem;
        padding-bottom: 0.9rem;
        border-bottom: 1px solid color-mix(in srgb, var(--landing-warm), transparent 75%);
        color: var(--landing-faint);
        font-size: 0.72rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }

      .landing-diagnostic__blurb {
        margin-left: auto;
        color: var(--landing-muted);
        letter-spacing: 0;
        text-transform: none;
      }

      /* The snippet sits above its error as its own card, styled like every
         other code block on the page. */
      .landing-picker__panel {
        display: grid;
        min-width: 0;
      }

      /* Context for the snippet under it: what the capability is and what it
         does not promise, before the reader gets to the code. */
      .landing-picker__note {
        margin-bottom: 0.6rem;
        padding: 1.1rem 1.2rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel);
      }

      .landing-picker__note p {
        margin: 0;
        color: var(--landing-muted);
        font-size: 0.9rem;
        line-height: 1.65;
      }

      .landing-picker__note p + p {
        margin-top: 0.7rem;
      }

      .landing-picker__note code {
        padding: 0.08em 0.32em;
        border-radius: 0.3rem;
        background: color-mix(in srgb, var(--landing-blue), transparent 88%);
        color: var(--landing-ink);
        font-family: var(--font-mono);
        font-size: 0.85em;
        white-space: nowrap;
      }

      .landing-picker__code {
        min-width: 0;
      }

      /* The real message carries its own line breaks and carets, so it keeps
         its whitespace and scrolls sideways rather than rewrapping. */
      .landing-diagnostic pre {
        overflow-x: auto;
        margin: 0;
        padding: 0;
        border: 0;
        background: transparent;
        color: var(--landing-ink);
        font-size: 0.72rem;
        line-height: 1.6;
        tab-size: 2;
      }

      .landing-flow {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0;
        margin: 3rem 0 0;
        padding: 0;
        list-style: none;
      }

      .landing-flow li {
        position: relative;
        min-height: 10rem;
        padding: 1.2rem;
        border: 1px solid var(--landing-line);
        background: var(--landing-panel);
      }

      .landing-flow li:nth-child(n + 2) {
        border-left: 0;
      }

      .landing-flow li:first-child {
        border-radius: 0.9rem 0 0 0.9rem;
      }

      .landing-flow li:last-child {
        border-radius: 0 0.9rem 0.9rem 0;
      }

      .landing-flow__step {
        display: block;
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.7rem;
      }

      .landing-flow strong {
        display: block;
        margin-top: 1.6rem;
        font-size: 1.15rem;
      }

      .landing-flow p {
        margin: 0.55rem 0 0;
        color: var(--landing-muted);
        font-size: 0.88rem;
        line-height: 1.55;
      }

      .landing-capabilities {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        margin: 3rem 0 0;
        padding: 0;
        border-top: 1px solid var(--landing-line);
        list-style: none;
      }

      .landing-capabilities li {
        padding: 1.35rem 1.35rem 1.35rem 0;
        border-bottom: 1px solid var(--landing-line);
      }

      .landing-capabilities li + li {
        padding-left: 1.35rem;
        border-left: 1px solid var(--landing-line);
      }

      .landing-capabilities strong {
        display: block;
        color: var(--landing-ink);
      }

      .landing-capabilities span {
        display: block;
        margin-top: 0.65rem;
        color: var(--landing-muted);
        font-size: 0.88rem;
        line-height: 1.55;
      }

      .landing-composer {
        --composer-line: color-mix(in srgb, var(--landing-line) 86%, transparent);
        --composer-panel: color-mix(in srgb, var(--landing-panel) 94%, var(--landing-blue) 6%);
        --composer-stage-start: color-mix(in srgb, var(--landing-blue) 22%, var(--landing-bg-deep));
        --composer-stage-end: color-mix(in srgb, var(--landing-violet) 18%, var(--landing-bg-deep));
        overflow: clip;
        margin-top: 2.25rem;
        border: 1px solid var(--composer-line);
        border-radius: 1.15rem;
        background: var(--landing-panel);
        box-shadow: 0 1.5rem 4rem rgb(6 18 38 / 10%);
        color: var(--landing-ink);
      }

      .landing-composer button {
        font: inherit;
      }

      .landing-composer button {
        touch-action: manipulation;
      }

      .landing-composer button:focus-visible {
        outline: 3px solid color-mix(in srgb, var(--landing-blue) 42%, transparent);
        outline-offset: 2px;
      }

      .landing-composer__bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
      }

      .landing-composer__bar {
        padding: 0.85rem 1rem;
        border-bottom: 1px solid var(--composer-line);
        background: color-mix(in srgb, var(--landing-panel) 96%, var(--landing-blue) 4%);
      }

      .landing-composer__bar-copy {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        gap: 0.2rem 0.35rem;
      }

      .landing-composer__bar p {
        margin: 0;
        color: var(--landing-muted);
        font-size: 0.82rem;
      }

      .landing-composer__bar h3 {
        margin: 0;
        color: var(--landing-ink);
        font-size: 0.95rem;
      }

      .landing-composer__reset,
      .landing-composer__palette button {
        min-height: 2rem;
        padding: 0.35rem 0.65rem;
        border: 1px solid var(--composer-line);
        border-radius: 0.5rem;
        background: var(--landing-panel);
        color: var(--landing-ink);
        font-size: 0.75rem;
        font-weight: 650;
        line-height: 1.2;
        text-decoration: none;
        cursor: pointer;
      }

      .landing-composer button:disabled {
        opacity: 0.45;
        cursor: not-allowed;
      }

      .landing-composer__layout {
        display: grid;
        grid-template-columns: minmax(18rem, 0.95fr) minmax(20rem, 1.65fr);
        height: 38rem;
        min-height: 31rem;
      }

      .landing-composer__palette {
        overflow: auto;
        min-width: 0;
        padding: 0.75rem;
        border-right: 1px solid var(--composer-line);
        background: var(--composer-panel);
      }

      .landing-composer__palette-group {
        margin-top: 0.65rem;
      }

      .landing-composer__palette-group:first-child {
        margin-top: 0;
      }

      .landing-composer__palette-group h4 {
        margin: 0 0 0.3rem;
        color: var(--landing-muted);
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .landing-composer__palette-group ul {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.3rem;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      .landing-composer__palette-group li {
        min-width: 0;
      }

      .landing-composer__palette-item {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        align-items: center;
        gap: 0.35rem;
        width: 100%;
        min-height: 2.15rem !important;
        padding: 0.28rem 0.45rem !important;
        text-align: left;
        touch-action: pan-y !important;
        transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
      }

      .landing-composer__palette-item:hover {
        border-color: color-mix(in srgb, var(--landing-blue) 45%, var(--composer-line));
        box-shadow: 0 0.35rem 1rem rgb(6 18 38 / 8%);
      }

      .landing-composer__palette-group li.is-drag-pending .landing-composer__palette-item,
      .landing-composer__palette-group li.is-drag-source .landing-composer__palette-item {
        border-color: var(--landing-blue);
        background: color-mix(in srgb, var(--landing-blue) 10%, var(--landing-panel));
        box-shadow: 0 0.9rem 2rem rgb(6 18 38 / 20%);
        transform: scale(1.035) rotate(-1deg);
      }

      .landing-composer__palette-group li.is-drag-source .landing-composer__palette-item {
        opacity: 0.72;
      }

      .landing-composer__grip {
        display: grid;
        place-items: center;
        width: 1rem;
        min-height: 1.5rem;
        color: var(--landing-faint);
        cursor: grab;
        user-select: none;
      }

      .landing-composer__palette-item strong {
        overflow: hidden;
        font-size: 0.8rem;
        font-weight: bold;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .landing-composer__workspace {
        display: flex;
        overflow: hidden;
        flex-direction: column;
        min-width: 0;
        background:
          radial-gradient(circle at 14% 10%, color-mix(in srgb, var(--landing-cyan) 24%, transparent), transparent 36%),
          radial-gradient(circle at 88% 92%, color-mix(in srgb, var(--landing-violet) 20%, transparent), transparent 40%),
          radial-gradient(rgb(255 255 255 / 28%) 0.7px, transparent 0.7px),
          linear-gradient(145deg, var(--composer-stage-start), var(--composer-stage-end));
        background-size: auto, auto, 14px 14px, auto;
        box-shadow: inset 0 0 0 1px rgb(255 255 255 / 20%);
      }

      .landing-composer__board {
        zoom: 0.8;
        position: relative;
        overflow: auto;
        flex: 1 1 auto;
        min-height: 0;
        padding: clamp(1.35rem, 3.8vw, 2.8rem);
        overflow-anchor: none;
        scrollbar-gutter: stable;
      }

      .landing-composer__canvas {
        display: grid;
        align-content: start;
        min-height: 100%;
        padding: clamp(0.75rem, 2vw, 1.25rem);
        border: 1px solid color-mix(in srgb, white 48%, var(--composer-line));
        border-radius: 0.9rem;
        background: Canvas;
        box-shadow:
          0 2rem 4.5rem rgb(5 15 38 / 28%),
          0 0.35rem 1rem rgb(5 15 38 / 18%),
          inset 0 0 0 1px rgb(255 255 255 / 42%);
        color: CanvasText;
      }

      .landing-composer__rendered-recipe {
        display: contents;
      }

      .landing-composer__rendered-recipe.is-just-placed > * {
        animation: landing-composer-arrive 220ms ease-out;
      }

      .landing-composer__canvas :where([data-citry-ui-part]) {
        max-inline-size: 100%;
      }

      .landing-composer__canvas [data-composer-inert-control] {
        cursor: default !important;
      }

      @keyframes landing-composer-arrive {
        from {
          opacity: 0;
          transform: translateY(0.45rem) scale(0.985);
        }

        to {
          opacity: 1;
          transform: none;
        }
      }

      .landing-composer__drop {
        display: grid;
        place-items: center;
        gap: 0.2rem;
        width: 100%;
        min-width: min(100%, 7rem);
        min-height: 4.5rem;
        margin-block: 0.55rem;
        padding: 0.75rem;
        border: 1px dashed color-mix(in srgb, var(--landing-blue) 38%, var(--composer-line)) !important;
        border-radius: 0.65rem;
        border-color: color-mix(in srgb, var(--landing-blue) 38%, var(--composer-line)) !important;
        background: color-mix(in srgb, var(--landing-blue) 4%, var(--landing-panel)) !important;
        color: var(--landing-muted) !important;
        cursor: pointer !important;
        transition: background 140ms ease, border-color 140ms ease, box-shadow 140ms ease, opacity 140ms ease;
        font-size: 1rem;
      }

      .landing-composer__drop > strong {
        color: var(--landing-ink);
        font-size: 1.2rem;
      }

      .landing-composer__drop > small {
        max-width: 26rem;
        color: var(--landing-muted);
        font-size: 1rem;
        line-height: 1.45;
      }

      .landing-composer__drop--root {
        min-height: clamp(15rem, 45vh, 22rem);
        margin: 0;
      }

      .landing-composer__drop--flow {
        overflow: hidden;
        min-width: 0;
        min-height: 0;
        max-height: 0;
        margin: 0;
        padding: 0;
        border-width: 0 !important;
        opacity: 0;
        pointer-events: none !important;
        transition:
          max-height 180ms ease,
          min-height 180ms ease,
          margin 180ms ease,
          padding 180ms ease,
          opacity 120ms ease,
          flex-basis 180ms ease,
          inline-size 180ms ease;
      }

      .landing-composer__drop--flow[data-composer-drop-axis="inline"] {
        flex: 0 0 0;
        inline-size: 0;
        max-inline-size: 0;
      }

      .landing-composer[data-composer-dragging]
        .landing-composer__drop--flow.is-drag-near,
      .landing-composer__drop--flow:focus-visible {
        min-height: 4rem;
        max-height: 5rem;
        margin-block: 0.4rem;
        padding: 0.65rem;
        border-width: 2px !important;
        opacity: 1;
        pointer-events: auto !important;
      }

      .landing-composer[data-composer-dragging]
        .landing-composer__drop--flow[data-composer-drop-axis="inline"].is-drag-near,
      .landing-composer__drop--flow[data-composer-drop-axis="inline"]:focus-visible {
        flex-basis: clamp(4.5rem, 18%, 7rem);
        min-width: 4.5rem;
        min-height: 3rem;
        max-width: 7rem;
        max-height: 5rem;
        margin: 0 0.3rem;
      }

      .landing-composer__drop.is-selected,
      .landing-composer__drop[aria-pressed="true"] {
        border-color: color-mix(in srgb, var(--landing-blue) 55%, var(--composer-line)) !important;
        background: color-mix(in srgb, var(--landing-blue) 7%, var(--landing-panel)) !important;
        color: var(--landing-ink) !important;
      }

      .landing-composer[data-composer-dragging] .landing-composer__board {
        background: color-mix(in srgb, var(--landing-blue) 5%, transparent);
        box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--landing-blue) 32%, transparent);
      }

      .landing-composer__drop.is-drag-available:not(.landing-composer__drop--flow),
      .landing-composer__drop--flow.is-drag-near {
        border-width: 2px !important;
        border-color: var(--landing-blue) !important;
        background: color-mix(in srgb, var(--landing-blue) 12%, var(--landing-panel)) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--landing-blue) 12%, transparent);
        color: var(--landing-ink) !important;
      }

      .landing-composer__drop.is-drag-target {
        background: color-mix(in srgb, var(--landing-blue) 23%, var(--landing-panel)) !important;
        box-shadow: 0 0 0 5px color-mix(in srgb, var(--landing-blue) 22%, transparent);
        transform: scale(1.01);
      }

      .landing-composer__drop.is-drag-unavailable {
        opacity: 0.32;
      }

      .landing-composer__drag-cue {
        position: sticky;
        z-index: 4;
        top: 0;
        width: fit-content;
        max-height: 0;
        margin: 0 auto;
        padding: 0rem 0.8rem;
        border-radius: 999px;
        background: var(--landing-blue);
        box-shadow: 0 0.7rem 1.6rem rgb(6 18 38 / 22%);
        color: white;
        font-size: 1rem;
        font-weight: 750;
        opacity: 0;
        transform: translateY(-0.8rem);
        transition: opacity 120ms ease, transform 120ms ease;
        pointer-events: none;
      }

      .landing-composer[data-composer-dragging] .landing-composer__drag-cue {
        max-height: 3rem;
        opacity: 1;
        transform: translateY(0);
        padding: 0.5rem 0.8rem;
      }

      .landing-composer__drag-ghost {
        position: fixed;
        z-index: 1000;
        top: 0;
        left: 0;
        display: grid;
        grid-template-columns: auto minmax(7rem, 1fr);
        column-gap: 0.55rem;
        align-items: center;
        min-width: 11rem;
        max-width: 17rem;
        padding: 0.7rem 0.85rem;
        border: 2px solid var(--landing-blue);
        border-radius: 0.7rem;
        background: var(--landing-panel);
        box-shadow: 0 1.1rem 2.7rem rgb(6 18 38 / 28%);
        color: var(--landing-ink);
        font-size: 0.72rem;
        pointer-events: none;
      }

      .landing-composer__drag-ghost-grip {
        grid-row: 1 / span 2;
        color: var(--landing-blue);
        font-size: 1rem;
      }

      .landing-composer__drag-ghost strong {
        font-size: 0.78rem;
      }

      .landing-composer__drag-ghost small {
        margin-top: 0.1rem;
        color: var(--landing-muted);
        font-size: 0.62rem;
      }

      @media (max-width: 64rem) {
        .landing-composer__layout {
          grid-template-columns: minmax(15rem, 0.8fr) minmax(20rem, 1.4fr);
        }
      }

      @media (max-width: 44rem) {
        .landing-composer__bar {
          align-items: stretch;
          flex-direction: column;
        }

        .landing-composer__layout {
          display: block;
          height: auto;
        }

        .landing-composer__palette {
          overflow: visible;
          border-right: 0;
          border-bottom: 1px solid var(--composer-line);
        }

        .landing-composer__workspace {
          min-height: 28rem;
          max-height: 38rem;
        }

        .landing-composer__board {
          min-height: 24rem;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .landing-composer__palette-item,
        .landing-composer__drop,
        .landing-composer__drag-cue {
          transition: none;
        }

        .landing-composer__rendered-recipe.is-just-placed > * {
          animation: none;
        }
      }

      @media (forced-colors: active) {
        .landing-composer,
        .landing-composer__canvas,
        .landing-composer__palette-item {
          border-color: CanvasText;
        }

        .landing-composer__workspace,
        .landing-composer__canvas {
          background: Canvas;
          box-shadow: none;
        }

        .landing-composer__drop[aria-pressed="true"],
        .landing-composer__drop.is-drag-target,
        .landing-composer__drop.is-drag-available:not(.landing-composer__drop--flow),
        .landing-composer__drop--flow.is-drag-near,
        .landing-composer__palette-group li.is-drag-source .landing-composer__palette-item {
          outline: 2px solid Highlight;
          outline-offset: 1px;
        }
      }

      .landing-human-note,
      .landing-trust-card {
        height: 100%;
        padding: 1.4rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel);
      }

      .landing-trust-card h3 {
        margin: 0;
        font-size: 1rem;
      }

      .landing-trust-card ul {
        margin: 1rem 0 0;
        padding-left: 1.1rem;
        color: var(--landing-muted);
      }

      .landing-trust-card li {
        margin-top: 0.65rem;
        line-height: 1.55;
      }

      .landing-human-note blockquote {
        margin: 0;
        color: var(--landing-ink);
        font-size: clamp(1.25rem, 2.5vw, 1.8rem);
        line-height: 1.4;
        letter-spacing: -0.025em;
      }

      .landing-human-note footer {
        margin-top: 1.4rem;
        color: var(--landing-muted);
        font-size: 0.84rem;
      }

      /* The acknowledgment grid reads as one texture of faces, so the portraits
         are much smaller here than on the People page and sit close together. */
      .landing-shell .user-list {
        gap: 0.55rem;
        margin-top: 1.5rem;
      }

      .landing-shell .user .avatar-wrapper {
        width: 2.4em;
        height: 2.4em;
      }

      .landing-shell .user .avatar-wrapper img {
        filter: saturate(0.85);
      }

      .landing-human-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1.2rem;
        margin-top: 1.5rem;
        color: var(--landing-muted);
        font-size: 0.88rem;
      }

      .landing-final {
        padding: clamp(7rem, 14vw, 13rem) 0;
        text-align: center;
      }

      .landing-content .landing-final h2 {
        max-width: 13ch;
        margin-inline: auto;
      }

      .landing-final p {
        max-width: 38rem;
        margin: 1.3rem auto 0;
        color: var(--landing-muted);
        font-size: 1.08rem;
        line-height: 1.7;
      }

      .landing-final .landing-actions,
      .landing-final .landing-install {
        justify-content: center;
        margin-inline: auto;
      }

      .landing-footer {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        width: min(76rem, calc(100% - 3rem));
        margin-inline: auto;
        padding: 1.5rem 0 2.5rem;
        border-top: 1px solid var(--landing-line);
        color: var(--landing-faint);
        font-size: 0.78rem;
      }

      .landing-footer__links {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
      }

      @media (max-width: 900px) {
        .landing-editor {
          grid-template-columns: 1fr;
        }

        /* The interaction itself leads on a small screen; the six summaries
           then remain available below it without shrinking the source. */
        .landing-editor__code {
          grid-row: 1;
        }

        .landing-editor__notes {
          position: static;
          grid-row: 2;
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .landing-tour {
          grid-template-columns: 1fr;
          position: relative;
        }

        .landing-tour__notes {
          position: static;
        }

        /* On a narrow screen the note follows the line it explains, so the
           reader never has to scroll away from the code to read it. */
        .landing-tour__notes.is-floating {
          position: absolute;
          left: 0;
          right: 0;
          z-index: 3;
          pointer-events: none;
        }

        .landing-tour__notes.is-floating .landing-tour__hint {
          display: none;
        }

        .landing-tour__notes.is-floating .landing-tour__note {
          box-shadow: 0 1rem 2.5rem rgb(6 18 38 / 28%);
        }

        /* The code panel keeps its place beside the copy, just smaller, until
           the columns get too narrow to read either of them. */
        .landing-hero__grid {
          grid-template-columns: minmax(0, 1fr) minmax(0, 0.85fr);
          gap: 1.5rem;
        }

        .landing-hero__code pre {
          padding: 0.9rem;
          font-size: 0.7rem;
          line-height: 1.5;
        }

        .landing-proof-grid,
        .landing-error-grid,
          .landing-human-grid,
        .landing-trust-grid {
          grid-template-columns: 1fr;
        }

        .landing-flow {
          grid-template-columns: 1fr;
        }

        .landing-flow li:nth-child(n + 2) {
          border-top: 0;
          border-left: 1px solid var(--landing-line);
        }

        .landing-flow li:first-child {
          border-radius: 0.9rem 0.9rem 0 0;
        }

        .landing-flow li:last-child {
          border-radius: 0 0 0.9rem 0.9rem;
        }

        .landing-capabilities {
          grid-template-columns: repeat(2, 1fr);
        }

        .landing-capabilities li:nth-child(3) {
          padding-left: 0;
          border-left: 0;
        }
      }

      @media (max-width: 720px) {
        .landing-hero__grid {
          grid-template-columns: 1fr;
        }

        .landing-hero__code {
          display: none;
        }
      }

      @media (max-width: 600px) {
        .landing-editor__notes {
          grid-template-columns: 1fr;
        }

        .landing-editor__code > .highlight > pre {
          padding-inline: 1rem;
          font-size: 0.7rem;
        }

        .landing-editor__hover {
          width: calc(100% - 1rem);
        }

        /* One column, and each panel sits under its own row, so a reader never
           has to look elsewhere on the page for the answer. */
        .landing-picker {
          grid-template-columns: 1fr;
          min-height: 0;
        }

        .landing-picker__item {
          display: block;
        }

        /* Back into the flow, directly under the row that opened it. */
        .landing-picker .landing-picker__panel {
          position: static;
          margin: 0.6rem 0 1.2rem;
        }

        .landing-picker .landing-picker__row {
          grid-template-columns: 1.75rem 1fr auto;
        }

        .landing-picker .landing-picker__caret {
          display: block;
        }

        .landing-picker .landing-picker__row.is-active .landing-picker__caret {
          transform: rotate(180deg);
          color: var(--landing-blue);
        }

        .landing-hero,
        .landing-section,
        .landing-final,
        .landing-footer {
          width: min(100% - 2rem, 76rem);
        }

        .landing-hero {
          min-height: 42rem;
          padding-top: 4rem;
        }

        .landing-hero__copy {
          width: 100%;
        }

        .landing-content .landing-hero h1 {
          font-size: clamp(2.6rem, 11vw, 3.6rem);
        }

        .landing-actions {
          align-items: stretch;
        }

        .landing-button {
          flex: 1 1 100%;
        }

        .landing-install {
          width: 100%;
          justify-content: space-between;
        }

        .landing-capabilities {
          grid-template-columns: 1fr;
        }

        .landing-capabilities li + li,
        .landing-capabilities li:nth-child(3) {
          padding-left: 0;
          border-left: 0;
        }

        .landing-footer {
          flex-direction: column;
        }

      }

      @media (max-width: 768px) {
        .citry-landing__nav-drawer {
          display: block;
          position: fixed;
          top: 0;
          left: 0;
          bottom: 0;
          z-index: 70;
          transform: translateX(-100%);
        }

        body.djc-drawer-open .citry-landing__nav-drawer {
          transform: translateX(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .landing-shell *,
        .landing-shell *::before,
        .landing-shell *::after {
          scroll-behavior: auto !important;
          transition-duration: 0.01ms !important;
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
        }
      }
    """

    js = """
      $component(({ els }) => {
        const root = els[0];
        root.querySelectorAll('[data-copy-install]').forEach((button) => {
          button.addEventListener('click', async () => {
            try {
              await navigator.clipboard.writeText('pip install citry');
              button.textContent = 'Copied';
              window.setTimeout(() => { button.textContent = 'Copy'; }, 1400);
            } catch (_error) {
              button.textContent = 'Select command';
            }
          });
        });

        // Every picker on the page works the same way: a list of rows, and one
        // panel per row. All the panels ship in the HTML, so without this script
        // a reader still gets every one of them; with it, they get one at a time.
        // Below the stacked breakpoint each panel sits under its own row, so the
        // list behaves as an accordion and a second tap on an open row closes it.
        const stacked = window.matchMedia('(max-width: 600px)');

        root.querySelectorAll('[data-landing-picker]').forEach((picker) => {
          const rows = Array.from(picker.querySelectorAll('[data-picker-case]'));
          const panels = Array.from(picker.querySelectorAll('[data-picker-panel]'));
          if (!rows.length || !panels.length) return;
          let openCase = rows[0].dataset.pickerCase;

          function show(id) {
            openCase = id;
            panels.forEach((panel) => {
              panel.hidden = panel.dataset.pickerPanel !== id;
            });
            rows.forEach((row) => {
              const selected = row.dataset.pickerCase === id;
              row.classList.toggle('is-active', selected);
              row.setAttribute('aria-pressed', selected ? 'true' : 'false');
            });
            // Beside the list a panel is out of the flow, so the container has
            // to be told how much room the visible one needs.
            const shown = panels.find((panel) => !panel.hidden);
            picker.style.minHeight = shown && !stacked.matches ? `${shown.offsetHeight}px` : '';
          }

          show(openCase);
          rows.forEach((row) => {
            const id = row.dataset.pickerCase;
            row.addEventListener('click', () => {
              // Closing is only useful where the panel covers the next row.
              if (stacked.matches && openCase === id) show(null);
              else show(id);
            });
            row.addEventListener('mouseenter', () => {
              if (!stacked.matches) show(id);
            });
            row.addEventListener('focus', () => {
              if (!stacked.matches) show(id);
            });
          });
          stacked.addEventListener('change', () => {
            if (!stacked.matches && !openCase) show(rows[0].dataset.pickerCase);
            else show(openCase);
          });
        });

        // The walkthrough. Every note is already in the page; pointing at a
        // marked line narrows them to the one that explains it.
        const tourRoot = root.querySelector('[data-landing-tour]');
        if (tourRoot) {
          // The shared copy button reads textContent, and the walkthrough has no
          // newlines left in its markup, so it answers with the real source.
          tourRoot.addEventListener('click', (event) => {
            const button = event.target.closest && event.target.closest('.djc-code-copy');
            if (!button) return;
            event.stopPropagation();
            const encoded = tourRoot.dataset.tourSource || '';
            const bytes = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
            navigator.clipboard.writeText(new TextDecoder().decode(bytes));
          }, true);
        }

        const tour = root.querySelector('[data-landing-tour]');
        if (tour) {
          const lines = Array.from(tour.querySelectorAll('[data-tour]'));
          const notes = Array.from(tour.querySelectorAll('[data-tour-note]'));
          const hint = tour.querySelector('[data-tour-hint]');

          function showStop(id) {
            notes.forEach((note) => {
              note.hidden = note.dataset.tourNote !== id;
            });
            lines.forEach((line) => {
              line.classList.toggle('is-active', line.dataset.tour === id);
            });
            if (hint) hint.hidden = Boolean(id);
          }

          // Below the two-column layout the notes would sit under the code,
          // off screen from the line they explain, so they follow the line as a
          // floating card instead.
          const narrow = window.matchMedia('(max-width: 900px)');
          const notesBox = tour.querySelector('.landing-tour__notes');

          function placeNotes(line) {
            if (!notesBox) return;
            if (!narrow.matches) {
              notesBox.classList.remove('is-floating');
              notesBox.style.removeProperty('top');
              return;
            }
            notesBox.classList.add('is-floating');
            const code = tour.querySelector('.landing-tour__code');
            const top = line.offsetTop + line.offsetHeight - (code ? code.scrollTop : 0);
            notesBox.style.top = `${Math.max(0, top)}px`;
          }

          let openStop = null;

          function activate(line, fromTap) {
            const id = line.dataset.tour;
            // On a narrow screen the note covers the text under it, so tapping
            // the same line again puts it away.
            if (fromTap && narrow.matches && openStop === id && notesBox
                && notesBox.classList.contains('is-floating')) {
              notesBox.classList.remove('is-floating');
              openStop = null;
              return;
            }
            openStop = id;
            showStop(id);
            placeNotes(line);
          }

          if (lines.length && notes.length) {
            showStop(lines[0].dataset.tour);
            lines.forEach((line) => {
              line.setAttribute('tabindex', '0');
              line.addEventListener('mouseenter', () => activate(line, false));
              line.addEventListener('focus', () => activate(line, false));
              // Touch has no hover, so a tap has to do the same thing.
              line.addEventListener('click', () => activate(line, true));
            });
            narrow.addEventListener('change', () => {
              if (!narrow.matches && notesBox) {
                notesBox.classList.remove('is-floating');
                notesBox.style.removeProperty('top');
              }
            });
            // Tapping away from the code puts the notes back out of the way.
            document.addEventListener('click', (event) => {
              if (!narrow.matches || !notesBox) return;
              if (!tour.contains(event.target)) notesBox.classList.remove('is-floating');
            });
          }
        }

        // The editor sample keeps the original highlighted source in the DOM.
        // Exact symbol buttons fill one hover card from server-rendered data,
        // and modified clicks follow the same targets its definition link uses.
        const editor = root.querySelector('[data-editor-showcase]')
          || document.querySelector('[data-editor-showcase]');
        if (editor) {
          const code = editor.querySelector('[data-editor-code]');
          const scroller = editor.querySelector('.highlight pre');
          const symbols = Array.from(editor.querySelectorAll('[data-editor-symbol]'));
          const card = editor.querySelector('[data-editor-hover]');
          const signature = editor.querySelector('[data-editor-hover-signature]');
          const provenance = editor.querySelector('[data-editor-hover-provenance]');
          const description = editor.querySelector('[data-editor-hover-description]');
          const docs = editor.querySelector('[data-editor-hover-docs]');
          const jump = editor.querySelector('[data-editor-jump]');
          const jumpHint = editor.querySelector('[data-editor-jump-hint]');
          const notes = Array.from(editor.querySelectorAll('[data-editor-note]'));
          const status = editor.querySelector('[data-editor-status]');
          let activeSymbol = null;
          let clickedSymbol = null;

          function placeHover(symbol, card) {
            if (!code || !symbol || !card) return;
            const codeRect = code.getBoundingClientRect();
            const symbolRect = symbol.getBoundingClientRect();
            const inset = 8;
            const width = card.offsetWidth;
            const height = card.offsetHeight;
            let left = symbolRect.left - codeRect.left;
            const preferredTop = symbol.dataset.editorPlacement === 'below'
              ? symbolRect.bottom - codeRect.top + inset
              : symbolRect.top - codeRect.top - height - inset;
            const bar = code.querySelector('.landing-editor__bar');
            const minimumTop = (bar ? bar.offsetHeight : 0) + inset;
            const maximumTop = Math.max(
              minimumTop,
              code.clientHeight - height - inset,
            );
            const top = Math.max(minimumTop, Math.min(preferredTop, maximumTop));
            left = Math.max(inset, Math.min(left, code.clientWidth - width - inset));
            card.style.left = `${left}px`;
            card.style.top = `${top}px`;
          }

          function showEditorHover(symbol) {
            if (!symbol || !card) return;
            const id = symbol.dataset.editorSymbol;
            if (activeSymbol !== symbol) clickedSymbol = null;
            activeSymbol = symbol;
            // Pygments produced and escaped this module-owned signature on the
            // server; retaining its spans gives the hover editor-like colour.
            if (signature) signature.innerHTML = symbol.dataset.editorSignatureHtml || '';
            if (provenance) provenance.textContent = symbol.dataset.editorProvenance || '';
            if (description) description.textContent = symbol.dataset.editorDescription || '';
            if (docs) docs.href = symbol.dataset.editorDocs || '/ide/vscode/';
            const target = symbol.dataset.editorTarget;
            if (jump) {
              jump.hidden = !target;
              jump.dataset.editorJump = target || '';
              jump.href = target ? `#landing-editor-definition-${target}` : '#';
            }
            if (jumpHint) jumpHint.hidden = !target;
            const isError = symbol.dataset.editorSeverity === 'error';
            card.classList.toggle('is-error', isError);
            card.setAttribute(
              'aria-label',
              `${isError ? 'Diagnostic' : 'Type information'} for ${symbol.textContent}`,
            );
            card.hidden = false;
            symbols.forEach((item) => {
              const selected = item === symbol;
              item.classList.toggle('is-active', selected);
              item.setAttribute('aria-expanded', selected ? 'true' : 'false');
            });
            notes.forEach((note) => {
              note.classList.toggle('is-active', note.dataset.editorNote === id);
            });
            requestAnimationFrame(() => placeHover(symbol, card));
          }

          function hideEditorHover() {
            activeSymbol = null;
            clickedSymbol = null;
            if (card) card.hidden = true;
            symbols.forEach((symbol) => {
              symbol.classList.remove('is-active');
              symbol.setAttribute('aria-expanded', 'false');
            });
            notes.forEach((note) => note.classList.remove('is-active'));
          }

          function jumpToDefinition(target) {
            const definition = editor.querySelector(
              `[data-editor-definition="${CSS.escape(target)}"]`,
            );
            if (!definition) return;
            hideEditorHover();
            definition.scrollIntoView({ block: 'center', inline: 'nearest' });
            definition.focus({ preventScroll: true });
            definition.classList.remove('is-definition-flash');
            requestAnimationFrame(() => definition.classList.add('is-definition-flash'));
            if (status) status.textContent = `Opened definition for ${definition.textContent}`;
          }

          symbols.forEach((symbol) => {
            symbol.addEventListener('mouseenter', () => showEditorHover(symbol));
            symbol.addEventListener('focus', () => showEditorHover(symbol));
            symbol.addEventListener('click', (event) => {
              const target = symbol.dataset.editorTarget;
              // A keyboard-generated button click has detail 0. It follows the
              // target directly, while an ordinary pointer click opens hover.
              if (target && (event.ctrlKey || event.metaKey || event.detail === 0)) {
                event.preventDefault();
                jumpToDefinition(target);
                return;
              }
              if (clickedSymbol === symbol && activeSymbol === symbol && !card.hidden) {
                hideEditorHover();
                return;
              }
              showEditorHover(symbol);
              clickedSymbol = symbol;
            });
          });

          notes.forEach((note) => {
            note.addEventListener('click', () => {
              const symbol = symbols.find(
                (item) => item.dataset.editorSymbol === note.dataset.editorNote,
              );
              if (!symbol) return;
              symbol.scrollIntoView({ block: 'center', inline: 'nearest' });
              requestAnimationFrame(() => showEditorHover(symbol));
            });
          });

          if (jump) {
            jump.addEventListener('click', (event) => {
              event.preventDefault();
              jumpToDefinition(jump.dataset.editorJump);
            });
          }

          document.addEventListener('click', (event) => {
            const target = event.target;
            const staysOpen = target && typeof target.closest === 'function'
              ? target.closest('[data-editor-symbol], [data-editor-note], [data-editor-hover]')
              : null;
            if (!staysOpen) hideEditorHover();
          });
          document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && activeSymbol) hideEditorHover();
          });

          if (scroller) {
            scroller.addEventListener('scroll', () => {
              if (!activeSymbol) return;
              placeHover(activeSymbol, card);
            }, { passive: true });
          }
          window.addEventListener('resize', () => {
            if (!activeSymbol) return;
            placeHover(activeSymbol, card);
          });

          // Opening one representative hover makes the interaction visible
          // without requiring the reader to guess which dotted name to try.
          const first = symbols.find(
            (symbol) => symbol.dataset.editorSymbol === 'member-chip-use',
          );
          if (first) showEditorHover(first);
        }

      });
    """
