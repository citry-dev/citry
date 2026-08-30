from django.apps import AppConfig


class ProjectExplorerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project_explorer"

    def ready(self) -> None:
        from project_explorer.citry_app import citry_app

        citry_app.initialize()
