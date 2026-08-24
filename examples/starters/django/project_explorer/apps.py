from django.apps import AppConfig


class ProjectExplorerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project_explorer"

    def ready(self) -> None:
        # Import all components before freezing startup-time registration.
        from . import components  # noqa: F401
        from .citry_app import citry_app

        citry_app.initialize()
