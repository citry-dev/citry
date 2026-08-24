import os

import pytest

os.environ.setdefault("CITRY_SECRET", "test-only-citry-secret")


@pytest.fixture(autouse=True)
def reset_demo_tasks():
    from app.store import reset_tasks

    reset_tasks()
    yield
    reset_tasks()
