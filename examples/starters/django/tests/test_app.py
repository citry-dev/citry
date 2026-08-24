from django.test import Client


def test_page_runtime_and_csrf_cookie_are_served() -> None:
    client = Client()

    page = client.get("/")
    runtime = client.get("/citry/citry.js")

    assert page.status_code == 200
    assert "Project Explorer" in page.content.decode()
    assert "Atlas" in page.content.decode()
    assert "csrftoken" in page.cookies
    assert runtime.status_code == 200
    assert runtime["Content-Type"].startswith("text/javascript")


def test_unknown_page_returns_not_found() -> None:
    assert Client().get("/missing").status_code == 404
