from app.citry_app import citry_app
from citry import Component, SlotInput


class PageShell(Component):
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
          <meta name="description" content="Search a small project catalog with Citry" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <a class="skip-link" href="#main-content">Skip to content</a>
          <header class="site-header">
            <div class="site-header__inner">
              <a class="brand" href="/">
                <span class="brand__name">Citry</span>
              </a>
              <span class="site-title">Project Explorer</span>
              <span class="mode-label">FastAPI starter</span>
            </div>
          </header>
          <main id="main-content" class="page-frame">
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
        --page-gutter: 1.5rem;
        --color-page: oklch(96.5% 0.005 250);
        --color-surface: oklch(94.5% 0.006 250);
        --color-input: oklch(99% 0.002 250);
        --color-text: oklch(25% 0.01 250);
        --color-muted: oklch(40% 0.01 250);
        --color-faint: oklch(50% 0.01 250);
        --color-border: oklch(88% 0.005 250);
        --color-border-subtle: oklch(92% 0.005 250);
        --color-input-border: oklch(65% 0.01 250);
        --color-accent: oklch(55% 0.13 195);
        --color-accent-hover: oklch(48% 0.13 195);
        --color-accent-ink: oklch(46% 0.13 195);
        --color-accent-soft: oklch(55% 0.13 195 / 10%);
        --color-link: oklch(52% 0.15 245);
        --color-link-hover: oklch(48% 0.15 245);
        --color-link-soft: oklch(55% 0.15 245 / 10%);
        --color-primary: oklch(48% 0.13 195);
        --color-primary-ink: #fff;
        --color-danger: oklch(50% 0.18 25);
        --color-focus: oklch(55% 0.13 195);
        color: var(--color-muted);
        background: var(--color-page);
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
        font-synthesis: none;
      }

      @media (min-width: 48rem) {
        :root { --page-gutter: 2rem; }
      }

      @media (min-width: 80rem) {
        :root { --page-gutter: 3rem; }
      }

      *, *::before, *::after { box-sizing: border-box; }

      html {
        min-width: 20rem;
        font-size: 90%;
        scroll-padding-top: 5rem;
      }

      [x-cloak] { display: none !important; }

      body {
        min-height: 100vh;
        margin: 0;
        color: var(--color-muted);
        background: var(--color-page);
        font-size: 1rem;
        line-height: 1.65;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }

      button, input { font: inherit; }

      button:focus-visible, input:focus-visible, a:focus-visible {
        outline: 2px solid var(--color-focus);
        outline-offset: 2px;
      }

      .skip-link {
        position: fixed;
        z-index: 30;
        top: 0.75rem;
        left: 0.75rem;
        padding: 0.45rem 0.7rem;
        border-radius: 0.375rem;
        color: var(--color-primary-ink);
        background: var(--color-primary);
        font-weight: 650;
        transform: translateY(-170%);
      }

      .skip-link:focus {
        transform: translateY(0);
      }

      .site-header {
        position: fixed;
        z-index: 20;
        top: 0;
        right: 0;
        left: 0;
        height: 4rem;
        border-bottom: 1px solid var(--color-border);
        background: var(--color-page);
      }

      .site-header__inner {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        width: min(80rem, 100%);
        height: 100%;
        margin-inline: auto;
        padding-inline: var(--page-gutter);
      }

      .brand {
        display: inline-flex;
        align-items: center;
        color: var(--color-text);
        text-decoration: none;
      }

      .brand__name {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.01em;
      }

      .site-title {
        margin-left: 0.3rem;
        padding-left: 0.9rem;
        border-left: 1px solid var(--color-border);
        color: var(--color-muted);
        font-size: 0.88rem;
      }

      .mode-label {
        margin-left: auto;
        color: var(--color-accent-ink);
        font-family: ui-monospace, "Cascadia Code", Menlo, monospace;
        font-size: 0.65rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .page-frame {
        width: min(68rem, calc(100% - (2 * var(--page-gutter))));
        margin-inline: auto;
        padding: 6.5rem 0 4rem;
      }

      .hero {
        display: grid;
        max-width: 45rem;
        gap: 0.75rem;
        margin-bottom: 2rem;
      }

      .eyebrow {
        margin: 0 0 0.15rem;
        color: var(--color-muted);
      }

      h1 {
        margin: 0;
        color: var(--color-text);
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        line-height: 1.3;
      }

      .hero__intro {
        max-width: 43rem;
        margin: 0;
        color: var(--color-muted);
        font-size: 1.05rem;
      }

      @media (max-width: 35rem) {
        .site-title { display: none; }

        .mode-label {
          max-width: 10rem;
          text-align: right;
        }

        .page-frame { padding-top: 6rem; }

        h1 { font-size: 2rem; }
      }
    """
