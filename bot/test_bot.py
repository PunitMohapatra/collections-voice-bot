"""
Bot Tests - Unit tests for the FastAPI voice bot server.
Tests health checks and message handling endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx

from bot.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_returns_status(self):
        """Health check should return JSON with service statuses."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "bot_server" in data
        assert "spring_api" in data
        assert "rasa_api" in data
        assert "whisper_loaded" in data
        assert "piper_available" in data
        assert data["bot_server"] is True


class TestCallStart:
    """Test /call/start endpoint."""

    @patch("bot.main.fetch_account", new_callable=AsyncMock)
    @patch("bot.main.set_tracker_slots", new_callable=AsyncMock)
    @patch("bot.main.synthesize_wav")
    def test_start_call_success(self, mock_synth, mock_slots, mock_fetch):
        """Successful call start returns WAV audio."""
        mock_fetch.return_value = {
            "accountId": 1,
            "accountNumber": "LN001",
            "customerName": "Rajesh Kumar",
            "overdueAmount": 12400,
            "charges": 500,
            "preferredLanguage": "hi",
            "lastEmiDate": "2025-02-01",
            "lastPaymentAmount": 5000,
            "lastPaymentDate": "2025-01-15",
        }
        mock_synth.return_value = b"fake-wav-bytes"

        response = client.post("/call/start?account_number=LN001")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        mock_fetch.assert_called_once_with("LN001")
        mock_synth.assert_called_once()

    @patch("bot.main.fetch_account", new_callable=AsyncMock)
    def test_start_call_account_not_found(self, mock_fetch):
        """Call start returns 404 when account doesn't exist."""
        from fastapi import HTTPException
        mock_fetch.side_effect = HTTPException(status_code=404, detail="Account not found")

        response = client.post("/call/start?account_number=INVALID")
        assert response.status_code == 404


class TestCallMessage:
    """Test /call/message/text endpoint."""

    @patch("bot.main.fetch_account", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    def test_text_message_success(self, mock_post, mock_fetch):
        """Text message returns bot response."""
        mock_fetch.return_value = {
            "accountId": 1,
            "preferredLanguage": "en",
            "customerName": "Priya Sharma",
            "overdueAmount": 8750,
            "charges": 250,
            "lastEmiDate": "2025-02-05",
            "lastPaymentAmount": 0,
            "lastPaymentDate": None,
            "accountNumber": "LN002",
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"text": "Your overdue amount is 8750 rupees."}]
        mock_post.return_value = mock_response

        response = client.post("/call/message/text?account_number=LN002&message=What is my balance?")

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

    @patch("bot.main.fetch_account", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    def test_text_message_empty_response(self, mock_post, mock_fetch):
        """Empty Rasa response returns default fallback text."""
        mock_fetch.return_value = {
            "accountId": 1,
            "preferredLanguage": "en",
            "customerName": "Test",
            "overdueAmount": 100,
            "charges": 0,
            "lastEmiDate": None,
            "lastPaymentAmount": 0,
            "lastPaymentDate": None,
            "accountNumber": "LN001",
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response

        response = client.post("/call/message/text?account_number=LN001&message=nonsense")
        assert response.status_code == 200
        assert "repeat" in response.json()["response"].lower() or len(response.json()["response"]) > 0

    def test_text_message_rasa_down(self):
        """Returns 502 when Rasa is unavailable."""
        import unittest.mock

        with unittest.mock.patch.object(
            httpx.AsyncClient, "post", side_effect=httpx.ConnectError("Connection refused")
        ):
            response = client.post("/call/message/text?account_number=LN001&message=hello")
        assert response.status_code == 502


class TestCallEnd:
    """Test /call/end endpoint."""

    @patch("httpx.AsyncClient.get")
    def test_end_call_no_active_call(self, mock_get):
        """Ending a call with no active call returns no_active_call status."""
        response = client.post("/call/end?account_number=LN999")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_active_call"


class TestLanguageNormalization:
    """Test language fallback logic."""

    def test_hindi_normalized(self):
        """Hindi language code stays 'hi'."""
        from bot.main import normalize_language
        assert normalize_language("hi") == "hi"

    def test_english_normalized(self):
        """English language code stays 'en'."""
        from bot.main import normalize_language
        assert normalize_language("en") == "en"

    def test_tamil_falls_back_to_english(self):
        """Unsupported language (Tamil) falls back to English."""
        from bot.main import normalize_language
        assert normalize_language("ta") == "en"

    def test_unknown_language_falls_back_to_english(self):
        """Unknown language code falls back to English."""
        from bot.main import normalize_language
        assert normalize_language("fr") == "en"


class TestBuildGreeting:
    """Test greeting generation in FastAPI."""

    def test_build_greeting_hindi(self):
        """Hindi greeting includes customer name and amounts."""
        from bot.main import build_greeting
        account = {
            "customerName": "Rajesh Kumar",
            "overdueAmount": 12400,
            "charges": 500,
            "preferredLanguage": "hi",
        }
        greeting = build_greeting(account)
        assert "Rajesh Kumar" in greeting
        assert "12400" in greeting
        assert "500" in greeting
        assert "Namaste" in greeting

    def test_build_greeting_english(self):
        """English greeting includes customer name and amounts."""
        from bot.main import build_greeting
        account = {
            "customerName": "Priya Sharma",
            "overdueAmount": 8750,
            "charges": 250,
            "preferredLanguage": "en",
        }
        greeting = build_greeting(account)
        assert "Priya Sharma" in greeting
        assert "8750" in greeting
        assert "250" in greeting
        assert "Hello" in greeting
