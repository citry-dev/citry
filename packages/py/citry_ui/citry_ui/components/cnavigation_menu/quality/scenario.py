"""Shared NavigationMenu scenario used by repository quality tools."""

# ruff: noqa: E501

from __future__ import annotations

from citry import Citry, Component


def navigation_menu_states_component(app: Citry) -> type[Component]:
    class CitryUiNavigationMenuStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-navigation-menu-ready>
            <h1>NavigationMenu states</h1>
            <c-CNavigationMenu label="Primary navigation" value="products" variant="surface">
              <c-CNavigationMenuLink href="#home" c-current="True">Home</c-CNavigationMenuLink>
              <c-CNavigationMenuItem value="products"><c-fill name="label">Products</c-fill><c-fill name="default"><c-CGrid cols="2" gap="sm"><a href="#observe">Observe</a><a href="#coordinate">Coordinate</a></c-CGrid></c-fill></c-CNavigationMenuItem>
              <c-CNavigationMenuItem value="disabled" disabled><c-fill name="label">Disabled</c-fill><c-fill name="default">Unavailable</c-fill></c-CNavigationMenuItem>
            </c-CNavigationMenu>
            <div dir="rtl"><c-CNavigationMenu label="RTL navigation" size="lg"><c-CNavigationMenuLink href="#rtl-home">الرئيسية</c-CNavigationMenuLink><c-CNavigationMenuItem value="rtl-more"><c-fill name="label">المزيد</c-fill><c-fill name="default"><a href="#rtl-link">رابط</a></c-fill></c-CNavigationMenuItem></c-CNavigationMenu></div>
            <c-CNavigationMenu label="Vertical navigation" orientation="vertical" size="sm"><c-CNavigationMenuLink href="#profile">Profile</c-CNavigationMenuLink><c-CNavigationMenuItem value="teams"><c-fill name="label">Teams</c-fill><c-fill name="default"><a href="#research">Research</a></c-fill></c-CNavigationMenuItem></c-CNavigationMenu>
          </section>
        """

    return CitryUiNavigationMenuStates
