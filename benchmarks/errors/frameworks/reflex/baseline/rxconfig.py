import reflex as rx

config = rx.Config(
    app_name="board",
    # The page uses Radix Themes components, as `reflex init` sets up. It has
    # no Tailwind classes and needs no sitemap, so the config lists only the
    # Radix Themes plugin. Reflex adds the sitemap plugin unless the config
    # disables it, and warns until it does.
    plugins=[rx.plugins.RadixThemesPlugin()],
    disable_plugins=[rx.plugins.SitemapPlugin],
)
