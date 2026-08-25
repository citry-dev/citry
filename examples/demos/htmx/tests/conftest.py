import pytest


@pytest.fixture(autouse=True)
def reset_demo_contacts():
    from app.data import reset_contacts

    reset_contacts()
    yield
    reset_contacts()
