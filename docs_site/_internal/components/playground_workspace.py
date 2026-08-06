"""Interactive workspace shown by the unversioned playground page."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from citry import Component

_STARTER_PATH = Path(__file__).parents[2] / "live_snippets" / "welcome.py"
_RUNTIME_PATH = Path(__file__).parents[2] / "static" / "playground" / "runtime.json"


class PlaygroundWorkspace(Component):
    """Two-panel editor and preview shell; browser behavior lives in playground.js."""

    transparent = True

    class Kwargs:
        help_html: Any = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        runtime = json.loads(_RUNTIME_PATH.read_text(encoding="utf-8"))
        return {
            "help_html": kwargs.help_html,
            "runtime_label": f"Citry {runtime['citry']['version']}",
            "starter_source": _STARTER_PATH.read_text(encoding="utf-8"),
        }

    template = """
      <main class="citry-playground" data-pagefind-body>
        <h1 class="citry-playground__title">Try Citry</h1>

        <div
          class="citry-playground__tabs"
          role="tablist"
          aria-label="Playground panels"
          data-pagefind-ignore
        >
          <button
            id="citry-playground-code-tab"
            class="citry-playground__tab is-active"
            type="button"
            role="tab"
            aria-selected="true"
            aria-controls="citry-playground-code-panel"
          >
            Code
          </button>
          <button
            id="citry-playground-result-tab"
            class="citry-playground__tab"
            type="button"
            role="tab"
            aria-selected="false"
            aria-controls="citry-playground-result-panel"
          >
            Result
          </button>
        </div>

        <div class="citry-playground__workspace" data-pagefind-ignore>
          <section
            id="citry-playground-code-panel"
            class="citry-playground__panel citry-playground__panel--code is-active"
            role="tabpanel"
            aria-labelledby="citry-playground-code-tab"
          >
            <header class="citry-playground__toolbar">
              <div class="citry-playground__toolbar-group">
                <div class="citry-playground__button-group" aria-label="Execution controls">
                  <button
                    id="citry-playground-run"
                    class="citry-playground__button citry-playground__button--primary"
                    type="button"
                    aria-label="Run Python"
                    title="Run Python (Ctrl+Enter)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </button>
                  <button
                    id="citry-playground-stop"
                    class="citry-playground__button citry-playground__button--stop"
                    type="button"
                    aria-label="Stop Python"
                    title="Stop Python"
                    disabled
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="6" y="6" width="12" height="12" rx="1" />
                    </svg>
                  </button>
                </div>
                <label class="citry-playground__toggle">
                  <input id="citry-playground-auto-run" type="checkbox">
                  <span>Auto-run</span>
                </label>
              </div>
              <div class="citry-playground__toolbar-group citry-playground__toolbar-group--secondary citry-playground__button-group">
                <button
                  id="citry-playground-copy-code"
                  class="citry-playground__button"
                  type="button"
                  aria-label="Copy code"
                  title="Copy code"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="9" y="9" width="11" height="11" rx="2" />
                    <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3" />
                  </svg>
                </button>
                <button
                  id="citry-playground-download-code"
                  class="citry-playground__button"
                  type="button"
                  aria-label="Download code"
                  title="Download code"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 3v12m0 0 5-5m-5 5-5-5M5 20h14" />
                  </svg>
                </button>
                <button
                  id="citry-playground-reset"
                  class="citry-playground__button"
                  type="button"
                  aria-label="Reset code"
                  title="Reset code"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M4 4v6h6M5.5 9A8 8 0 1 1 6 17" />
                  </svg>
                </button>
                <button
                  id="citry-playground-help"
                  class="citry-playground__button"
                  type="button"
                  aria-label="Playground help"
                  title="Playground help"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M9.8 9a2.4 2.4 0 1 1 3.6 2.1c-.9.5-1.4 1-1.4 2.1M12 17h.01" />
                  </svg>
                </button>
              </div>
            </header>

            <div class="citry-playground__editor-shell">
              <textarea
                id="citry-playground-editor-fallback"
                class="citry-playground__editor-fallback"
                aria-label="Citry Python module"
                spellcheck="false"
              >{{ starter_source }}</textarea>
              <div id="citry-playground-editor" class="citry-playground__editor" hidden></div>
            </div>

            <section
              id="citry-playground-python-diagnostic"
              class="citry-playground__diagnostic"
              aria-live="assertive"
              hidden
            >
              <div class="citry-playground__diagnostic-heading">
                <strong id="citry-playground-python-summary"></strong>
                <div class="citry-playground__button-group">
                  <button
                    id="citry-playground-copy-python-error"
                    class="citry-playground__button"
                    type="button"
                    aria-label="Copy Python diagnostic"
                    title="Copy Python diagnostic"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3" />
                    </svg>
                  </button>
                  <button
                    id="citry-playground-dismiss-python"
                    class="citry-playground__button"
                    type="button"
                    aria-label="Close Python diagnostic"
                    title="Close Python diagnostic"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M6 6l12 12M18 6 6 18" />
                    </svg>
                  </button>
                </div>
              </div>
              <pre id="citry-playground-python-details"></pre>
            </section>
          </section>

          <div
            id="citry-playground-divider"
            class="citry-playground__divider"
            role="separator"
            aria-label="Resize code and result panels"
            aria-orientation="vertical"
            aria-valuemin="30"
            aria-valuemax="70"
            aria-valuenow="50"
            tabindex="0"
          ></div>

          <section
            id="citry-playground-result-panel"
            class="citry-playground__panel citry-playground__panel--result"
            role="tabpanel"
            aria-labelledby="citry-playground-result-tab"
          >
            <header class="citry-playground__result-bar">
              <span id="citry-playground-status">Ready to run</span>
              <span id="citry-playground-stale" class="citry-playground__stale" hidden>Showing last successful result</span>
              <span id="citry-playground-runtime" class="citry-playground__runtime">{{ runtime_label }}</span>
            </header>
            <div class="citry-playground__preview-shell">
              <iframe
                id="citry-playground-preview"
                class="citry-playground__preview"
                title="Rendered Citry result"
                src="/static/playground/preview.html"
                sandbox="allow-forms allow-scripts"
              ></iframe>
              <div id="citry-playground-empty" class="citry-playground__empty">
                <p>Run the Python module to render its final expression.</p>
                <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
              </div>
            </div>
            <section
              id="citry-playground-preview-diagnostic"
              class="citry-playground__diagnostic citry-playground__diagnostic--preview"
              aria-live="assertive"
              hidden
            >
              <div class="citry-playground__diagnostic-heading">
                <strong id="citry-playground-preview-summary"></strong>
                <div class="citry-playground__button-group">
                  <button
                    id="citry-playground-copy-preview-error"
                    class="citry-playground__button"
                    type="button"
                    aria-label="Copy Result diagnostic"
                    title="Copy Result diagnostic"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3" />
                    </svg>
                  </button>
                  <button
                    id="citry-playground-dismiss-preview"
                    class="citry-playground__button"
                    type="button"
                    aria-label="Close Result diagnostic"
                    title="Close Result diagnostic"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M6 6l12 12M18 6 6 18" />
                    </svg>
                  </button>
                </div>
              </div>
              <pre id="citry-playground-preview-details"></pre>
            </section>
          </section>
        </div>

        <dialog
          id="citry-playground-help-dialog"
          class="citry-playground__help"
          aria-labelledby="citry-playground-help-title"
        >
          <div class="citry-playground__help-card">
            <header class="citry-playground__help-heading">
              <h2 id="citry-playground-help-title">Using the playground</h2>
              <button
                id="citry-playground-close-help"
                class="citry-playground__button citry-playground__help-close-icon"
                type="button"
                aria-label="Close playground help"
                title="Close playground help"
                data-citry-playground-close-help
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </button>
            </header>
            <article class="prose citry-playground__help-content">{{ help_html }}</article>
            <footer class="citry-playground__help-footer">
              <button
                id="citry-playground-close-help-footer"
                class="citry-playground__diagnostic-action citry-playground__help-close-action"
                type="button"
                data-citry-playground-close-help
              >
                Close
              </button>
            </footer>
          </div>
        </dialog>

        <div id="citry-playground-announcer" class="citry-playground__sr-only" aria-live="polite"></div>
      </main>
    """
