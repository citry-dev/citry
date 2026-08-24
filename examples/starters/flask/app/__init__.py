from flask import Flask

from citry.contrib.flask import mount

from .citry_app import citry_app
from .components import ProjectPage
from .data import find_projects


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def home() -> str:
        return str(ProjectPage(projects=find_projects()))

    mount(app, citry_app, prefix="/citry")
    citry_app.initialize()
    return app
