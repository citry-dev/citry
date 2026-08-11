from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class IconGroup:
    title: str
    names: tuple[str, ...]


class IconCatalog(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="icon-catalog">
        <c-for each="group in groups">
          <section>
            <h2>{{ group.title }}</h2>
            <ul>
              <c-for each="name in group.names">
                <li>
                  <c-CIcon c-name="name" size="lg" />
                  <code>{{ name }}</code>
                </li>
              </c-for>
            </ul>
          </section>
        </c-for>
      </section>
    """

    css = """
      :where(.icon-catalog) {
        display: grid;
        gap: 1.25rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-catalog h2) {
        margin: 0 0 0.6rem;
        color: light-dark(#285c36, #8bdd9f);
        font-size: 0.875rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.icon-catalog ul) {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
        gap: 0.35rem;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      :where(.icon-catalog li) {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        min-width: 0;
        padding: 0.55rem 0.65rem;
        border: 1px solid light-dark(#d9e2d4, #38513a);
        border-radius: 0.5rem;
        background: Canvas;
      }

      :where(.icon-catalog code) {
        overflow-wrap: anywhere;
        font-size: 0.75rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "groups": (
                IconGroup(
                    "Actions",
                    (
                        "check",
                        "close",
                        "copy",
                        "download",
                        "edit",
                        "plus",
                        "minus",
                        "refresh-cw",
                        "search",
                        "trash",
                        "upload",
                    ),
                ),
                IconGroup(
                    "Navigation",
                    (
                        "arrow-down",
                        "arrow-left",
                        "arrow-right",
                        "arrow-up",
                        "chevron-down",
                        "chevron-left",
                        "chevron-right",
                        "chevron-up",
                        "back",
                        "forward",
                        "prev",
                        "next",
                        "external-link",
                        "home",
                        "menu",
                        "more-horizontal",
                        "more-vertical",
                    ),
                ),
                IconGroup(
                    "Status and meaning",
                    (
                        "circle-check",
                        "circle-help",
                        "circle-info",
                        "circle-x",
                        "triangle-alert",
                        "success",
                        "info",
                        "warn",
                        "danger",
                        "expand",
                        "collapse",
                        "dropdown",
                        "clear",
                    ),
                ),
                IconGroup(
                    "Objects",
                    (
                        "calendar",
                        "clock",
                        "eye",
                        "eye-off",
                        "file",
                        "folder",
                        "heart",
                        "leaf",
                        "link",
                        "lock",
                        "mail",
                        "settings",
                        "star",
                        "unlock",
                        "user",
                        "x",
                    ),
                ),
            )
        }


preview = IconCatalog()

preview  # noqa: B018
