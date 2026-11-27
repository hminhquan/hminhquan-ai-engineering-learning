import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError, InternalServerError, RateLimitError

from app.main import app
from app.schemas import MeetingAnalysis
from app.services import llm

client = TestClient(app)

RESPONSE = {
    "summary": "Lan agreed to update the guide.",
    "decisions": [],
    "actions": [{"owner": "Lan", "action": "Update the guide", "due_date": None}],
}
REQUEST = {"meeting_text": "Lan agreed to update the guide."}


def test_analyze_meeting(monkeypatch):
    def analyze(text):
        assert text == REQUEST["meeting_text"]
        return MeetingAnalysis.model_validate(RESPONSE)

    monkeypatch.setattr(llm, "analyze_meeting", analyze)
    response = client.post("/analyze-meeting", json=REQUEST)
    assert response.status_code == 200
    assert response.json() == RESPONSE
    assert "/analyze-meeting" in client.get("/openapi.json").json()["paths"]


def test_invalid_payload_never_calls_model(monkeypatch):
    def analyze(_text):
        pytest.fail("Invalid request reached the model")

    monkeypatch.setattr(llm, "analyze_meeting", analyze)
    assert client.post("/analyze-meeting", json={"meeting_text": " "}).status_code == 422


upstream_request = httpx.Request("POST", "https://example.test")


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (APITimeoutError(upstream_request), 504),
        (RateLimitError("private upstream data", response=httpx.Response(429, request=upstream_request), body=None), 429),
        (InternalServerError("private upstream data", response=httpx.Response(500, request=upstream_request), body=None), 502),
    ],
)
def test_upstream_failure_is_sanitized(monkeypatch, error, expected_status):
    def analyze(_text):
        raise error

    monkeypatch.setattr(llm, "analyze_meeting", analyze)
    response = client.post("/analyze-meeting", json=REQUEST)
    assert response.status_code == expected_status
    assert "private upstream data" not in response.text


def test_malformed_model_output(monkeypatch):
    def analyze(_text):
        return MeetingAnalysis.model_validate_json("private upstream data")

    monkeypatch.setattr(llm, "analyze_meeting", analyze)
    response = client.post("/analyze-meeting", json=REQUEST)
    assert response.status_code == 502
    assert "private upstream data" not in response.text
