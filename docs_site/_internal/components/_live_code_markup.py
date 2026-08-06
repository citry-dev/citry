"""Shared Citry components for the inline live-code runtime."""

from __future__ import annotations

from citry import Component


class LiveActivationControls(Component):
    """Render the progressively enhanced activation controls."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
          <button
            class="citry-live-code__activate"
            type="button"
            data-live-activate
            hidden
          >
            Try live
          </button>
          <span
            class="citry-live-code__draft"
            data-live-draft
            hidden
          >
            Draft saved
          </span>
    """


class LiveWorkspace(Component):
    """Render the editor and result workspace expected by the browser runtime."""

    transparent = True

    class Kwargs:
        identifier: str
        title: str

    class Slots:
        pass

    template = """
          <div
            class="citry-live-code__workspace"
            data-live-workspace
            data-pagefind-ignore
            hidden
          >
            <div
              class="citry-live-code__tabs"
              role="tablist"
              c-aria-label="title + ' panels'"
            >
              <button
                c-id="identifier + '-code-tab'"
                type="button"
                role="tab"
                aria-selected="true"
                c-aria-controls="identifier + '-code-panel'"
                data-live-tab="code"
              >
                Code
              </button>
              <button
                c-id="identifier + '-result-tab'"
                type="button"
                role="tab"
                aria-selected="false"
                c-aria-controls="identifier + '-result-panel'"
                data-live-tab="result"
                tabindex="-1"
              >
                Result
              </button>
            </div>
            <div class="citry-live-code__toolbar">
              <div
                class="citry-live-code__button-group"
                aria-label="Execution controls"
              >
                <button
                  type="button"
                  class="citry-live-code__icon citry-live-code__icon--primary"
                  data-live-run
                  aria-label="Run Python"
                  title="Run Python (Ctrl+Enter)"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="citry-live-code__icon"
                  data-live-stop
                  aria-label="Stop Python"
                  title="Stop Python"
                  disabled
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="6" y="6" width="12" height="12" rx="1" />
                  </svg>
                </button>
              </div>
              <label class="citry-live-code__toggle">
                <input
                  type="checkbox"
                  data-live-auto-run
                  checked
                />
                <span>Auto-run</span>
              </label>
              <span class="citry-live-code__status" data-live-status>
                Ready
              </span>
              <span class="citry-live-code__stale" data-live-stale hidden>
                Showing last result
              </span>
              <div class="citry-live-code__button-group citry-live-code__toolbar-end">
                <button
                  type="button"
                  class="citry-live-code__icon"
                  data-live-reset
                  aria-label="Reset code"
                  title="Reset code"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M4 4v6h6M5.5 9A8 8 0 1 1 6 17" />
                  </svg>
                </button>
                <button
                  type="button"
                  class="citry-live-code__icon"
                  data-live-close
                  aria-label="Close live editor"
                  title="Close live editor"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 6l12 12M18 6 6 18" />
                  </svg>
                </button>
              </div>
            </div>
            <section
              c-id="identifier + '-code-panel'"
              class="citry-live-code__panel is-active"
              role="tabpanel"
              c-aria-labelledby="identifier + '-code-tab'"
              data-live-panel="code"
            >
              <div class="citry-live-code__editor-shell">
                <textarea
                  class="citry-live-code__fallback"
                  data-live-fallback
                  aria-label="Citry Python module"
                  spellcheck="false"
                ></textarea>
                <div
                  class="citry-live-code__editor"
                  data-live-editor
                  hidden
                ></div>
              </div>
              <section
                class="citry-live-code__diagnostic"
                data-live-python-diagnostic
                aria-live="assertive"
                hidden
              >
                <div class="citry-live-code__diagnostic-heading">
                  <strong data-live-python-summary></strong>
                  <div class="citry-live-code__button-group">
                    <button
                      type="button"
                      class="citry-live-code__icon"
                      data-live-copy-python
                      aria-label="Copy Python diagnostic"
                      title="Copy Python diagnostic"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <rect x="9" y="9" width="11" height="11" rx="2" />
                        <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="citry-live-code__icon"
                      data-live-dismiss-python
                      aria-label="Close Python diagnostic"
                      title="Close Python diagnostic"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M6 6l12 12M18 6 6 18" />
                      </svg>
                    </button>
                  </div>
                </div>
                <pre data-live-python-details></pre>
              </section>
            </section>
            <section
              c-id="identifier + '-result-panel'"
              class="citry-live-code__panel"
              role="tabpanel"
              c-aria-labelledby="identifier + '-result-tab'"
              data-live-panel="result"
              hidden
            >
              <div
                class="citry-live-code__preview-shell"
                data-live-preview-shell
              >
                <div class="citry-live-code__empty" data-live-empty>
                  Preparing the result…
                </div>
              </div>
              <section
                class="citry-live-code__diagnostic citry-live-code__diagnostic--result"
                data-live-preview-diagnostic
                aria-live="assertive"
                hidden
              >
                <div class="citry-live-code__diagnostic-heading">
                  <strong data-live-preview-summary></strong>
                  <div class="citry-live-code__button-group">
                    <button
                      type="button"
                      class="citry-live-code__icon"
                      data-live-copy-preview
                      aria-label="Copy Result diagnostic"
                      title="Copy Result diagnostic"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <rect x="9" y="9" width="11" height="11" rx="2" />
                        <path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3" />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="citry-live-code__icon"
                      data-live-dismiss-preview
                      aria-label="Close Result diagnostic"
                      title="Close Result diagnostic"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M6 6l12 12M18 6 6 18" />
                      </svg>
                    </button>
                  </div>
                </div>
                <pre data-live-preview-details></pre>
              </section>
            </section>
            <p
              class="citry-live-code__sr-only"
              data-live-announcer
              aria-live="polite"
            ></p>
          </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, str]:
        return {
            "identifier": str(kwargs.identifier),
            "title": str(kwargs.title),
        }


__all__ = ["LiveActivationControls", "LiveWorkspace"]
