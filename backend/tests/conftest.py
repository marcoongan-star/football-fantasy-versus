from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        auth_mode="development",
        create_schema=True,
    )
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(user_number: int, name: str | None = None) -> dict[str, str]:
    return {
        "x-ffv-user-id": f"google-subject-{user_number}",
        "x-ffv-user-email": f"manager{user_number}@example.com",
        "x-ffv-user-name": name or f"Manager {user_number}",
    }

