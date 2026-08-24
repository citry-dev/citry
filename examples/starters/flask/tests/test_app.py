from app import create_app


def test_page_and_citry_runtime_are_served() -> None:
    client = create_app().test_client()

    page = client.get("/")
    runtime = client.get("/citry/citry.js")

    assert page.status_code == 200
    assert "Project Explorer" in page.text
    assert "Atlas" in page.text
    assert runtime.status_code == 200
    assert runtime.content_type.startswith("text/javascript")


def test_prefix_lookalike_is_left_to_flask() -> None:
    assert create_app().test_client().get("/citryx").status_code == 404
