from flask import Flask

from app.citry_app import citry_app
from app.components.project_page import ProjectPage
from app.data import find_projects
from citry.contrib.flask import mount


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def home() -> str:
        html = str(ProjectPage(projects=find_projects()))
        return html

    mount(app, citry_app, prefix="/citry")
    citry_app.initialize()
    return app
