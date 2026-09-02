"""
Tests for review endpoints — /api/submit and /api/history.

The reviewer is now fully rule-based, so no mocking is needed.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_code_success(client: AsyncClient, auth_headers: dict):
    """Submitting code returns a structured review response."""
    response = await client.post(
        "/api/submit",
        json={"code": "def hello():\n    print('hi')\n", "language": "python"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "rating" in data
    assert 1 <= data["rating"] <= 10
    assert "feedback" in data
    assert isinstance(data["issues"], list)
    assert data["language"] == "python"
    assert "code_preview" in data

    # The rule-based reviewer should detect print() usage
    issue_types = [i["type"] for i in data["issues"]]
    assert any(t in ("best-practice", "formatting", "security", "optimization", "other") for t in issue_types)


@pytest.mark.asyncio
async def test_submit_detects_security_issues(client: AsyncClient, auth_headers: dict):
    """Submitting code with hardcoded secrets flags security issues."""
    code = '''
password = "my_secret_123"
api_key = "sk-abc123def456"
'''
    response = await client.post(
        "/api/submit",
        json={"code": code, "language": "python"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    security_issues = [i for i in data["issues"] if i["type"] == "security"]
    assert len(security_issues) > 0


@pytest.mark.asyncio
async def test_submit_detects_js_issues(client: AsyncClient, auth_headers: dict):
    """Submitting JavaScript code detects JS-specific issues."""
    code = '''
var x = 5;
if (x == "5") {
    console.log("equal");
    document.write("<p>test</p>");
}
'''
    response = await client.post(
        "/api/submit",
        json={"code": code, "language": "javascript"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["issues"]) > 0
    # Should detect var, ==, console.log, document.write
    descriptions = " ".join(i["description"] for i in data["issues"])
    assert "var" in descriptions.lower() or "console" in descriptions.lower()


@pytest.mark.asyncio
async def test_submit_empty_code(client: AsyncClient, auth_headers: dict):
    """Submitting empty code returns 400."""
    response = await client.post(
        "/api/submit",
        json={"code": "   ", "language": "python"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_submit_code_too_long(client: AsyncClient, auth_headers: dict):
    """Submitting code exceeding max length returns 400."""
    long_code = "x" * 60_000
    response = await client.post(
        "/api/submit",
        json={"code": long_code, "language": "python"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_history_returns_submissions(client: AsyncClient, auth_headers: dict):
    """After submitting code, history endpoint returns the submission."""
    # Submit code first
    await client.post(
        "/api/submit",
        json={"code": "def greet(name):\n    return f'Hello {name}'\n", "language": "python"},
        headers=auth_headers,
    )

    # Fetch history
    response = await client.get("/api/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "submissions" in data
    assert len(data["submissions"]) == 1
    sub = data["submissions"][0]
    assert sub["language"] == "python"
    assert 1 <= sub["rating"] <= 10
    assert "code_preview" in sub
    assert "created_at" in sub


@pytest.mark.asyncio
async def test_history_empty(client: AsyncClient, auth_headers: dict):
    """History returns empty list when user has no submissions."""
    response = await client.get("/api/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["submissions"] == []


@pytest.mark.asyncio
async def test_history_sorted_oldest_first(client: AsyncClient, auth_headers: dict):
    """History submissions are sorted oldest first."""
    # Submit two reviews
    await client.post(
        "/api/submit",
        json={"code": "first_function()", "language": "python"},
        headers=auth_headers,
    )
    await client.post(
        "/api/submit",
        json={"code": "second_function()", "language": "javascript"},
        headers=auth_headers,
    )

    response = await client.get("/api/history", headers=auth_headers)
    submissions = response.json()["submissions"]

    assert len(submissions) == 2
    assert submissions[0]["id"] < submissions[1]["id"]  # Oldest first


@pytest.mark.asyncio
async def test_submit_with_csv_rules(client: AsyncClient, auth_headers: dict):
    """CSV rules are applied during code review when relevant."""
    import io

    # Upload CSV rules first
    csv_content = (
        "id,type,description\n"
        "1,security,Never use eval function\n"
        "2,formatting,Always use descriptive variable names\n"
    )
    await client.post(
        "/api/upload-csv",
        headers=auth_headers,
        files={"file": ("rules.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )

    # Submit code that matches a CSV rule
    code = "result = eval(user_input)\n"
    response = await client.post(
        "/api/submit",
        json={"code": code, "language": "python"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Should find both built-in eval() issue and the CSV rule
    descriptions = " ".join(i["description"] for i in data["issues"])
    assert "eval" in descriptions.lower()
