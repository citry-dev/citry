"""Browser evidence for every registered CommandPalette docs preview."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from docs_site._internal.project import load_docs_project
from docs_site._internal.ui_previews import discover_ui_previews

pytestmark = pytest.mark.e2e


def test_every_command_palette_preview_loads_through_the_actual_docs_path(page: Any, docs_site_url: str) -> None:
    project = load_docs_project()
    previews = tuple(
        preview
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "command-palette"
    )
    assert previews

    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    for preview in previews:
        console_errors.clear()
        page_errors.clear()
        page.goto(docs_site_url + preview.public_path, wait_until="networkidle")
        ready_script = """() => {
              const roots = [];
              const visit = owner => {
                roots.push(...owner.querySelectorAll('[data-citry-command-palette-host]'));
                for (const element of owner.querySelectorAll('*')) {
                  if (element.shadowRoot) visit(element.shadowRoot);
                }
              };
              visit(document);
              return roots.length > 0 && roots.every(
                root => root.hasAttribute('data-citry-command-palette-initialized'),
              );
            }"""
        try:
            page.wait_for_function(ready_script, timeout=10_000)
        except Exception as error:  # noqa: BLE001 - retain exact cross-root preview diagnostics
            diagnostic = page.evaluate(
                """() => {
                  const roots = [];
                  const visit = owner => {
                    roots.push(...owner.querySelectorAll('[data-citry-command-palette-host]'));
                    for (const element of owner.querySelectorAll('*')) {
                      if (element.shadowRoot) visit(element.shadowRoot);
                    }
                  };
                  visit(document);
                  return roots.map(root => ({
                    ready: root.hasAttribute('data-citry-command-palette-initialized'),
                    connected: root.isConnected,
                    label: root.querySelector('dialog')?.getAttribute('aria-label') ?? null,
                  }));
                }"""
            )
            pytest.fail(
                f"Preview {preview.name!r} did not settle: {diagnostic}; "
                f"console={console_errors}; page={page_errors}; error={error}"
            )
        anatomy = page.evaluate(
            """() => {
              const roots = [];
              const visit = owner => {
                roots.push(...owner.querySelectorAll('[data-citry-command-palette-host]'));
                for (const element of owner.querySelectorAll('*')) {
                  if (element.shadowRoot) visit(element.shadowRoot);
                }
              };
              visit(document);
              return roots.map(root => ({
                dialog: Boolean(root.querySelector('[data-citry-ui-part=command-palette]')),
                input: Boolean(root.querySelector('[data-citry-ui-part=command-palette-input]')),
                listbox: Boolean(root.querySelector('[data-citry-ui-part=command-palette-listbox]')),
              }));
            }"""
        )
        assert all(value == {"dialog": True, "input": True, "listbox": True} for value in anatomy), preview.name
        assert console_errors == [], preview.name
        assert page_errors == [], preview.name
