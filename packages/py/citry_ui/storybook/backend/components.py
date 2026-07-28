"""Private components used to compose Storybook scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from citry import ComponentLibrary, LibraryComponent


class CStorybookFragment(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        scenario_id: str
        content: object

    @dataclass(slots=True)
    class Slots:
        pass

    template = """
      <main
        class="citry-ui-storybook-frame"
        c-data-scenario-id="scenario_id"
      >
        {{ content }}
      </main>
    """

    css = """
      :where(.citry-ui-storybook-frame) {
        box-sizing: border-box;
        min-height: 12rem;
        padding: 1.5rem;
        color: CanvasText;
        font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      }
    """


class CStorybookPage(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        title: str
        scenario_id: str
        content: object

    @dataclass(slots=True)
    class Slots:
        pass

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <c-CStorybookFragment
            c-scenario_id="scenario_id"
            c-content="content"
          />
          <c-js />
        </body>
      </html>
    """


class CStaticTabsContent(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        pass

    template = """
      <c-CTabList aria_label="Account settings">
        <c-CTab value="account">
          Account
        </c-CTab>
        <c-CTab value="security">
          Security
        </c-CTab>
      </c-CTabList>
      <c-CTabPanel value="account">
        Account preferences
      </c-CTabPanel>
      <c-CTabPanel value="security">
        Security preferences
      </c-CTabPanel>
    """


class CReactiveCounterProbe(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        generation: str

    @dataclass(slots=True)
    class Slots:
        pass

    template = """
      <section
        class="citry-ui-readiness-probe"
        c-data-generation="generation"
        data-count="0"
        data-ready="loading"
      >
        <p>
          Generation:
          <strong>{{ generation }}</strong>
        </p>
        <button
          type="button"
          @click="increment()"
        >
          Increment
        </button>
        <output
          aria-live="polite"
          x-text="count"
        >
          0
        </output>
      </section>
    """

    js = """
      $component(({ els, data, scope, effect }) => {
        const root = els[0];
        const audit = globalThis.__citryUiReadiness ??= {
          active: 0,
          cleanups: [],
          clicks: [],
          events: [],
          inits: [],
        };
        const increment = () => {
          audit.events.push(data.generation);
          scope.count += 1;
        };
        scope.count = 0;
        scope.increment = () => {
          audit.clicks.push(data.generation);
          scope.count += 1;
        };
        audit.inits.push(data.generation);
        effect(() => {
          root.dataset.count = String(scope.count);
        });
        let active = false;
        let readinessTimer;
        const activate = () => {
          window.addEventListener("citry-ui-readiness-increment", increment);
          audit.active += 1;
          active = true;
          root.dataset.ready = "true";
        };
        if (data.generation === "delayed") {
          readinessTimer = window.setTimeout(activate, 800);
        } else if (data.generation !== "never") {
          activate();
        }
        return () => {
          window.clearTimeout(readinessTimer);
          if (active) {
            window.removeEventListener("citry-ui-readiness-increment", increment);
            audit.active -= 1;
          }
          audit.cleanups.push(data.generation);
        };
      });
    """

    css = """
      :where(.citry-ui-readiness-probe) {
        display: grid;
        gap: 0.75rem;
        max-width: 24rem;
        padding: 1rem;
        border: 2px solid rgb(37, 99, 235);
        border-radius: 0.75rem;
        background: rgb(219, 234, 254);
      }

      :where(.citry-ui-readiness-probe output) {
        font-variant-numeric: tabular-nums;
        font-weight: 700;
      }
    """

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:  # noqa: ARG002
        return {"generation": kwargs.generation}


STORYBOOK_COMPONENTS = ComponentLibrary(
    name="citry-ui-storybook-spike",
    components=(
        CStorybookFragment,
        CStorybookPage,
        CStaticTabsContent,
        CReactiveCounterProbe,
    ),
)


__all__ = [
    "STORYBOOK_COMPONENTS",
    "CReactiveCounterProbe",
    "CStaticTabsContent",
    "CStorybookFragment",
    "CStorybookPage",
]
