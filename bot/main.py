"""
Collections Voice Bot - FastAPI Server
=======================================
Orchestrates voice calls between customers and the Rasa dialogue engine.

Key Design Decisions:
1. FastAPI fetches account data from Spring Boot DIRECTLY (not Rasa)
2. Slots are set via Rasa tracker events API before conversation starts
3. Opening greeting is built in FastAPI from account data (Rasa not called)
4. Rasa tracker events record the greeting so dialogue state is correct
5. Call logging is sent to Spring Boot for audit/compliance

Endpoints:
    GET  /health              — status of all loaded models and services
    POST /call/start          — starts a call, returns WAV audio greeting
    POST /call/message        — receives WAV audio, returns WAV audio response
    POST /call/end            — ends a call, logs outcome to Spring Boot
"""

import asyncio
import io
import json
import logging
import os
import tempfile
import wave
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

# ---------------------------------------------------------------------------
# Optional imports — graceful degradation if models not installed
# ---------------------------------------------------------------------------
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    from piper import PiperVoice
except ImportError:
    PiperVoice = None

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("voice-bot")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
WHISPER_MODEL: Optional[Any] = None
VOICE_CACHE: Dict[str, Any] = {}
ACTIVE_CALLS: Dict[str, Dict[str, Any]] = {}  # track active call state

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SPRING_API_URL = os.getenv("SPRING_API_URL", "http://localhost:8080/api/v1")
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005")
BASE_DIR = Path(__file__).resolve().parent
VOICE_MODEL_PATHS: Dict[str, str] = {
    "hi": str(BASE_DIR / "models" / "hi" / "hi_IN" / "rohan" / "medium" / "hi_IN-rohan-medium.onnx"),
    "en": str(BASE_DIR / "models" / "en" / "en_US" / "amy" / "low" / "en_US-amy-low.onnx"),
}

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Collections Voice Bot",
    description="Voice bot for debt collection with Rasa NLU, Whisper STT, and Piper TTS",
    version="2.0.0",
)


# ===========================================================================
# Whisper STT
# ===========================================================================

def load_whisper_model() -> None:
    """Load the Whisper tiny model for speech-to-text on CPU.
    Uses 'tiny' for faster inference and lower memory on modest hardware."""
    global WHISPER_MODEL
    if WhisperModel is None:
        logger.warning("faster-whisper not installed. STT will be unavailable.")
        WHISPER_MODEL = None
        return

    try:
        logger.info("Loading Whisper 'tiny' model on CPU...")
        WHISPER_MODEL = WhisperModel("tiny", device="cpu")
        logger.info("Whisper model loaded successfully.")
    except Exception as exc:
        logger.error(f"Failed to load Whisper model: {exc}")
        WHISPER_MODEL = None


@app.on_event("startup")
async def startup_event() -> None:
    """Load heavy models in background thread on startup."""
    async def _load_whisper() -> None:
        try:
            await asyncio.to_thread(load_whisper_model)
        except Exception as exc:
            logger.error(f"[STARTUP] Whisper background load failed: {exc}")
            WHISPER_MODEL = None

    task = asyncio.create_task(_load_whisper())
    task.add_done_callback(lambda t: t.exception() and logger.error(f"[STARTUP] Whisper task error: {t.exception()}"))
    logger.info(f"Bot server starting. Spring API: {SPRING_API_URL}, Rasa: {RASA_URL}")


# ===========================================================================
# Piper TTS
# ===========================================================================

def normalize_language(language: str) -> str:
    """Normalize language code to supported values (hi/en).
    Tamil and other unsupported languages fall back to English with a warning."""
    if language == "hi":
        return "hi"
    if language not in ("en", "hi"):
        logger.warning(f"Unsupported language '{language}', falling back to English.")
    return "en"


def get_voice_model_path(language: str) -> str:
    """Get the Piper ONNX model path for the given language."""
    return VOICE_MODEL_PATHS.get(language, VOICE_MODEL_PATHS["en"])


def load_piper_voice(language: str) -> Any:
    """Load and cache a Piper TTS voice model."""
    if PiperVoice is None:
        raise RuntimeError("Piper is not installed. Install piper-tts to synthesize audio.")

    if language in VOICE_CACHE:
        return VOICE_CACHE[language]

    model_path = get_voice_model_path(language)
    config_path = f"{model_path}.json"
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Voice model file not found: {model_path}")
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Voice model config file not found: {config_path}")

    logger.info(f"Loading Piper voice model: {model_path}")
    voice = PiperVoice.load(model_path, config_path=config_path)
    VOICE_CACHE[language] = voice
    return voice


def synthesize_wav(text: str, language: str) -> bytes:
    """Synthesize text to WAV audio bytes using Piper TTS."""
    voice = load_piper_voice(language)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file, set_wav_format=True)

    buffer.seek(0)
    return buffer.read()


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe WAV audio to text using faster-whisper."""
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        load_whisper_model()
        if WHISPER_MODEL is None:
            raise RuntimeError(
                "faster-whisper is not installed or failed to load. "
                "Install faster-whisper and ensure the Whisper model loads successfully."
            )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name

    try:
        segments, _ = WHISPER_MODEL.transcribe(tmp_path, beam_size=5, word_timestamps=False)
        transcript = " ".join([segment.text for segment in segments])
        return transcript.strip()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ===========================================================================
# Spring Boot API calls
# ===========================================================================

async def fetch_account(account_number: str) -> Dict[str, Any]:
    """Fetch account details from the Spring Boot API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{SPRING_API_URL}/accounts/{account_number}")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Account '{account_number}' not found")
        raise HTTPException(status_code=502, detail="Unable to fetch account from API")


async def log_call_to_api(call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Log a call event to the Spring Boot call-log endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{SPRING_API_URL}/call-log", json=call_data)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Call log API returned {response.status_code}: {response.text}")
    except httpx.RequestError as exc:
        logger.warning(f"Failed to log call: {exc}")
    return None


# ===========================================================================
# Rasa integration
# ===========================================================================

def build_greeting(account: Dict[str, Any]) -> str:
    """Build the opening greeting message from account data.
    Greeting is built directly in FastAPI — Rasa is NOT called for this."""
    name = account.get("customerName", "customer")
    overdue = account.get("overdueAmount", 0)
    charges = account.get("charges", 0)
    language = account.get("preferredLanguage", "en")

    if language == "hi":
        return (
            f"Namaste, kya main {name} ji se baat kar sakta hoon? "
            f"Aapke loan account par {overdue} rupaye baaki hain aur {charges} rupaye ke charges hain. "
            f"Aap kab tak payment kar sakte hain?"
        )

    return (
        f"Hello, am I speaking with {name}? "
        f"Your loan account has an overdue amount of {overdue} rupees "
        f"with additional charges of {charges} rupees. "
        f"When would you be able to make this payment?"
    )


async def set_tracker_slots(account_number: str, account: Dict[str, Any]) -> None:
    """Set all account slots in Rasa tracker via events API.
    Also records the greeting as having happened so dialogue state is correct."""
    lang = normalize_language(account.get("preferredLanguage", "en"))

    events = [
        {"event": "slot", "name": "account_number", "value": account.get("accountNumber")},
        {"event": "slot", "name": "account_id", "value": account.get("accountId")},
        {"event": "slot", "name": "customer_name", "value": account.get("customerName")},
        {"event": "slot", "name": "overdue_amount", "value": account.get("overdueAmount")},
        {"event": "slot", "name": "charges", "value": account.get("charges")},
        {"event": "slot", "name": "last_emi_date", "value": account.get("lastEmiDate")},
        {"event": "slot", "name": "last_payment_amount", "value": account.get("lastPaymentAmount")},
        {"event": "slot", "name": "last_payment_date", "value": account.get("lastPaymentDate")},
        {"event": "slot", "name": "preferred_language", "value": lang},
        {
            "event": "user",
            "text": "greet",
            "parse_data": {
                "intent": {"name": "greet", "confidence": 1.0},
                "entities": [],
            },
        },
        {"event": "action", "name": "utter_greet"},
        {"event": "action", "name": "action_listen"},
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(f"{RASA_URL}/conversations/{account_number}/tracker/events", json=events)


# ===========================================================================
# API Endpoints
# ===========================================================================

@app.get("/health")
async def health():
    """Health check — reports status of all services and models."""
    status = {
        "bot_server": True,
        "spring_api": False,
        "rasa_api": False,
        "whisper_loaded": WHISPER_MODEL is not None,
        "whisper_available": WhisperModel is not None,
        "piper_available": PiperVoice is not None,
        "piper_voices": list(VOICE_CACHE.keys()),
        "active_calls": len(ACTIVE_CALLS),
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            spring_resp = await client.get(f"{SPRING_API_URL}/accounts/LN001")
            status["spring_api"] = spring_resp.status_code in (200, 404)
        except httpx.RequestError:
            status["spring_api"] = False

        try:
            rasa_resp = await client.get(f"{RASA_URL}/status")
            status["rasa_api"] = rasa_resp.status_code == 200
        except httpx.RequestError:
            status["rasa_api"] = False

    return status


@app.post("/call/start")
async def start_call(account_number: str = Query(..., alias="account_number")):
    """Start a new collection call.

    1. Fetches account from Spring Boot API
    2. Sets all slots in Rasa tracker via events
    3. Builds greeting text directly (not via Rasa)
    4. Logs call start to Spring Boot
    5. Synthesizes greeting to WAV and returns audio
    """
    logger.info(f"[CALL START] account={account_number}")

    # Fetch account data
    account = await fetch_account(account_number)
    language = normalize_language(account.get("preferredLanguage", "en"))

    # Set slots in Rasa tracker (non-blocking — continue even if Rasa is down)
    try:
        await set_tracker_slots(account_number, account)
    except httpx.ConnectError:
        logger.warning("Rasa unavailable — skipped tracker slot initialization")

    # Build greeting
    greeting = build_greeting(account)
    logger.info(f"[GREETING] lang={language}, text={greeting[:80]}...")

    # Track active call
    call_start_time = datetime.now().isoformat()
    ACTIVE_CALLS[account_number] = {
        "account_id": account.get("accountId"),
        "call_start_time": call_start_time,
        "language": language,
    }

    # Log call start to Spring Boot
    await log_call_to_api({
        "accountId": account.get("accountId"),
        "callStartTime": call_start_time,
        "callStatus": "IN_PROGRESS",
        "languageUsed": language,
        "ptpCaptured": False,
        "escalated": False,
    })

    # Synthesize greeting to audio
    try:
        wav_bytes = await asyncio.to_thread(synthesize_wav, greeting, language)
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as exc:
        logger.error(f"[TTS ERROR] {exc}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(exc)}")


@app.post("/call/message")
async def handle_message(
    account_number: str = Query(..., alias="account_number"),
    file: UploadFile = File(...),
):
    """Process a customer voice message during an active call.

    1. Transcribes WAV audio to text via Whisper
    2. Sends transcript to Rasa for dialogue processing
    3. Fetches response language from account
    4. Synthesizes Rasa response to WAV and returns audio
    """
    logger.info(f"[MESSAGE] account={account_number}")

    # Transcribe audio
    audio_bytes = await file.read()
    transcript = await asyncio.to_thread(transcribe_audio, audio_bytes)
    logger.info(f"[TRANSCRIPT] account={account_number}: \"{transcript}\"")

    if not transcript.strip():
        logger.warning(f"[EMPTY TRANSCRIPT] account={account_number}")
        transcript = "hello"

    # Send to Rasa
    async with httpx.AsyncClient(timeout=15.0) as client:
        rasa_resp = await client.post(
            f"{RASA_URL}/webhooks/rest/webhook",
            json={"sender": account_number, "message": transcript},
        )

    if rasa_resp.status_code != 200:
        logger.error(f"[RASA ERROR] status={rasa_resp.status_code}, body={rasa_resp.text}")
        raise HTTPException(status_code=502, detail="Rasa failed to process the message")

    response_payload = rasa_resp.json()
    if isinstance(response_payload, dict):
        response_payload = [response_payload]
    if not isinstance(response_payload, list):
        response_payload = []

    response_text = " ".join(item.get("text", "") for item in response_payload if isinstance(item, dict) and item.get("text"))
    if not response_text:
        response_text = "Sorry, I could not understand that. Could you please repeat?"

    logger.info(f"[RASA RESPONSE] account={account_number}: \"{response_text[:100]}\"")

    # Get language for TTS
    account = await fetch_account(account_number)
    language = normalize_language(account.get("preferredLanguage", "en"))

    # Synthesize response to audio
    try:
        wav_bytes = await asyncio.to_thread(synthesize_wav, response_text, language)
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as exc:
        logger.error(f"[TTS ERROR] {exc}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(exc)}")


@app.post("/call/message/text")
async def handle_text_message(
    account_number: str = Query(..., alias="account_number"),
    message: str = Query(..., alias="message"),
):
    """Process a customer text message during an active call.

    1. Sends transcript to Rasa for dialogue processing
    2. Returns Rasa response text as JSON
    """
    logger.info(f"[TEXT MESSAGE] account={account_number}: \"{message}\"")

    if not message.strip():
        message = "hello"

    # Send to Rasa
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            rasa_resp = await client.post(
                f"{RASA_URL}/webhooks/rest/webhook",
                json={"sender": account_number, "message": message},
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Rasa is unavailable")

    if rasa_resp.status_code != 200:
        logger.error(f"[RASA ERROR] status={rasa_resp.status_code}, body={rasa_resp.text}")
        raise HTTPException(status_code=502, detail="Rasa failed to process the message")

    response_payload = rasa_resp.json()
    if isinstance(response_payload, dict):
        response_payload = [response_payload]
    if not isinstance(response_payload, list):
        response_payload = []

    response_text = " ".join(item.get("text", "") for item in response_payload if isinstance(item, dict) and item.get("text"))
    if not response_text:
        response_text = "Sorry, I could not understand that. Could you please repeat?"

    logger.info(f"[RASA RESPONSE] account={account_number}: \"{response_text[:100]}\"")
    return {"response": response_text}


@app.post("/call/end")
async def end_call(account_number: str = Query(..., alias="account_number")):
    """End an active call and log the outcome to Spring Boot.

    Checks Rasa tracker for PTP and escalation status, then creates
    a final call log entry with the complete call information.
    """
    logger.info(f"[CALL END] account={account_number}")

    call_info = ACTIVE_CALLS.pop(account_number, None)
    if call_info is None:
        logger.warning(f"[CALL END] No active call found for {account_number}")
        return {"status": "no_active_call", "account_number": account_number}

    # Check Rasa tracker for call outcome
    ptp_captured = False
    escalated = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tracker_resp = await client.get(f"{RASA_URL}/conversations/{account_number}/tracker")
            if tracker_resp.status_code == 200:
                tracker = tracker_resp.json()
                slots = tracker.get("slots", {})
                ptp_captured = bool(slots.get("ptp_saved", False))
                # Check if last intent was dispute
                events = tracker.get("events", [])
                for event in reversed(events):
                    if event.get("event") == "user":
                        intent = event.get("parse_data", {}).get("intent", {}).get("name", "")
                        if intent == "dispute":
                            escalated = True
                        break
    except httpx.RequestError as exc:
        logger.warning(f"Failed to check Rasa tracker: {exc}")

    # Log final call outcome
    call_end_time = datetime.now().isoformat()
    call_status = "COMPLETED"
    if escalated:
        call_status = "ESCALATED"
    elif ptp_captured:
        call_status = "PTP_CAPTURED"

    # Resolve followup_id: try tracker first, then lookup the latest promise
    followup_id = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tracker_resp = await client.get(f"{RASA_URL}/conversations/{account_number}/tracker")
            if tracker_resp.status_code == 200:
                slots = tracker_resp.json().get("slots", {})
                followup_id = slots.get("followup_id")
    except httpx.RequestError:
        pass

    result = await log_call_to_api({
        "accountId": int(call_info["account_id"]) if call_info.get("account_id") is not None else None,
        "callStartTime": call_info["call_start_time"],
        "callEndTime": call_end_time,
        "callStatus": call_status,
        "languageUsed": call_info.get("language", "en"),
        "ptpCaptured": ptp_captured,
        "escalated": escalated,
        "followupId": int(followup_id) if followup_id is not None else None,
    })

    logger.info(f"[CALL END] account={account_number}, status={call_status}, ptp={ptp_captured}, escalated={escalated}")

    return {
        "status": call_status,
        "account_number": account_number,
        "ptp_captured": ptp_captured,
        "escalated": escalated,
        "call_log": result,
    }
