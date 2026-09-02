"""
Tests for rules endpoints — /api/upload-csv and /api/rules.
"""

import io
import pytest
from httpx import AsyncClient


def make_csv(content: str) -> io.BytesIO:
    """Create a file-like CSV for upload."""
    return io.BytesIO(content.encode("utf-8"))


@pytest.mark.asyncio
async def test_upload_csv_success(client: AsyncClient, auth_headers: dict):
    """Uploading a valid CSV imports rules."""
    csv_content = (
        "id,type,description\n"
        "1,formatting,Use consistent indentation\n"
        "2,security,Never hardcode credentials\n"
        "3,performance,Cache expensive computations\n"
    )

    response = await client.post(
        "/api/upload-csv",
        headers=auth_headers,
        files={"file": ("rules.csv", make_csv(csv_content), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert "Imported 3 rules" in data["message"]


@pytest.mark.asyncio
async def test_upload_csv_skips_invalid_rows(client: AsyncClient, auth_headers: dict):
    """CSV rows with missing type or description are skipped."""
    csv_content = (
        "id,type,description\n"
        "1,formatting,Good rule\n"
        "2,,Missing type\n"
        "3,security,\n"
        "4,performance,Valid rule\n"
    )

    response = await client.post(
        "/api/upload-csv",
        headers=auth_headers,
        files={"file": ("rules.csv", make_csv(csv_content), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # Only rows 1 and 4 are valid
    assert "skipped" in data["message"].lower()


@pytest.mark.asyncio
async def test_upload_csv_missing_columns(client: AsyncClient, auth_headers: dict):
    """CSV missing required columns returns 400."""
    csv_content = "name,value\nfoo,bar\n"

    response = await client.post(
        "/api/upload-csv",
        headers=auth_headers,
        files={"file": ("bad.csv", make_csv(csv_content), "text/csv")},
    )
    assert response.status_code == 400
    assert "missing" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_csv_empty_file(client: AsyncClient, auth_headers: dict):
    """Uploading an empty CSV returns 400."""
    response = await client.post(
        "/api/upload-csv",
        headers=auth_headers,
        files={"file": ("empty.csv", make_csv(""), "text/csv")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_rules_after_upload(client: AsyncClient, auth_headers: dict):
    """Rules endpoint returns uploaded rules."""
    # Upload first
    csv_content = (
        "id,type,description\n"
        "1,formatting,Indent with 4 spaces\n"
        "2,best-practice,Add type hints\n"
    )
    await client.post(
        "/api/upload-csv",
        headers=auth_headers,
        files={"file": ("rules.csv", make_csv(csv_content), "text/csv")},
    )

    # Fetch rules
    response = await client.get("/api/rules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["rules"]) == 2
    assert data["rules"][0]["type"] == "formatting"
    assert "id" in data["rules"][0]


@pytest.mark.asyncio
async def test_get_rules_empty(client: AsyncClient, auth_headers: dict):
    """Rules endpoint returns empty list when no rules exist."""
    response = await client.get("/api/rules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["rules"] == []
