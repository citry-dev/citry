from citry import Component, SlotInput

from ..citry_app import citry_app


class AppShell(Component):
    citry = citry_app

    class Kwargs:
        title: str

    class Slots:
        header: SlotInput
        default: SlotInput

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"title": kwargs.title}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <meta
            name="description"
            content="A complete project board demo built with Citry"
          />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <header class="topbar">
            <a class="brand" href="#main-content">
              <span class="brand__mark" aria-hidden="true">C</span>
              <span>Northstar</span>
            </a>
            <div class="topbar__project">
              <span>Product</span>
              <strong>Launch workspace</strong>
            </div>
            <span class="avatar" title="Signed in as You" aria-label="Signed in as You">Y</span>
          </header>
          <main id="main-content">
            <c-slot name="header" />
            <c-slot />
          </main>
          <c-js />
        </body>
      </html>
    """

    css = """
      :root {
        color-scheme: light;
        font-family:
          Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
          "Segoe UI", sans-serif;
        color: #20231f;
        background: #e9e8e1;
        font-synthesis: none;
      }
      * { box-sizing: border-box; }
      [x-cloak] { display: none !important; }
      body { min-width: 20rem; min-height: 100vh; margin: 0; }
      button, input, select { font: inherit; }
      button, select { cursor: pointer; }
      button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible {
        outline: 3px solid #f58f5b;
        outline-offset: 3px;
      }
      .topbar {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 1rem;
        min-height: 4.75rem;
        padding: 0.75rem clamp(1rem, 3vw, 2.5rem);
        color: #f5f5f0;
        background: #202a25;
      }
      .brand {
        display: inline-flex;
        align-items: center;
        gap: 0.65rem;
        width: max-content;
        color: inherit;
        font-weight: 800;
        text-decoration: none;
      }
      .brand__mark, .avatar {
        display: grid;
        width: 2.2rem;
        height: 2.2rem;
        place-items: center;
        border-radius: 0.7rem;
        color: #202a25;
        background: #ffbf70;
        font-weight: 900;
      }
      .topbar__project { display: grid; gap: 0.1rem; text-align: center; }
      .topbar__project span { color: #aeb8b1; font-size: 0.72rem; text-transform: uppercase; }
      .avatar { justify-self: end; border-radius: 50%; background: #c9d7ce; }
      @media (max-width: 42rem) {
        .topbar { grid-template-columns: 1fr auto; }
        .topbar__project { display: none; }
      }
    """
