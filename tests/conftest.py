import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["MOCK_LLM"] = "true"
os.environ["DEMO_MODE"] = "true"

from app.config import settings
from app.db import init_db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(settings, "database_path", str(db_path))
    init_db()
    yield db_path


@pytest.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
