# Collections Voice Bot

Production-architecture voice bot for a loan collections company. Calls customers, collects Promise to Pay (PTP), and logs every outcome.

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 15 |
| API Layer | Java 17 + Spring Boot 3.x (Maven 3.9.6, project-local) |
| Dialogue Engine | Rasa 3.6.20 |
| Bot Orchestration | Python 3.10 + FastAPI + Uvicorn |
| Speech-to-Text | faster-whisper (tiny model, CPU) |
| Text-to-Speech | Piper TTS (ONNX, CPU) |
| HTTP Client | httpx (async) |

## Project Structure

```
collections-voice-bot/
├── README.md                          # This file
├── Requirements.txt                   # Full tech-stack documentation
├── .gitignore                         # Git ignore rules
├── .vscode/settings.json             # IDE configuration
│
├── api/                               # Spring Boot 3.x REST API
│   └── voice-bot-api/
│       ├── pom.xml                    # Maven build (Java 17)
│       └── src/main/
│           ├── java/com/collections/
│           │   ├── VoiceBotApiApplication.java
│           │   ├── api/
│           │   │   ├── controller/
│           │   │   │   ├── AccountController.java       # GET    /api/v1/accounts/{number}
│           │   │   │   ├── PromiseController.java       # POST   /api/v1/promise
│           │   │   │   ├── FollowupController.java      # POST   /api/v1/followup
│           │   │   │   ├── PromisePolicyController.java # GET    /api/v1/promise-policy
│           │   │   │   └── CallLogController.java       # POST   /api/v1/call-log
│           │   │   ├── dto/
│           │   │   │   ├── AccountDTO.java
│           │   │   │   ├── PromiseDTO.java
│           │   │   │   ├── PromiseRequest.java
│           │   │   │   ├── FollowupRequest.java
│           │   │   │   ├── CallLogRequest.java
│           │   │   │   └── CallLogDTO.java
│           │   │   └── repository/
│           │   │       ├── AccountRepository.java
│           │   │       ├── PromiseRepository.java
│           │   │       ├── FollowupRepository.java
│           │   │       ├── PromisePolicyRepository.java
│           │   │       └── CallLogRepository.java
│           │   └── entity/
│           │       ├── Account.java
│           │       ├── Promise.java
│           │       ├── Followup.java
│           │       ├── PromisePolicy.java
│           │       └── CallLog.java
│           └── resources/
│               └── application.properties
│
├── bot/                               # FastAPI voice bot server
│   ├── main.py                        # App factory + all endpoints + TTS + STT
│   ├── requirements.txt               # pip dependencies
│   ├── __init__.py
│   ├── test_bot.py                    # 13 unit tests (mocked, no services)
│   ├── test_audio.py                  # Lists available audio devices
│   ├── test_text.py                   # Text client simulator (terminal)
│   └── test_voice.py                  # Voice client simulator (mic + speaker)
│
├── rasa/                              # Rasa 3.6.20 dialogue engine
│   ├── domain.yml                     # Intents, slots, responses (en + hi)
│   ├── config.yml                     # NLU pipeline + TED/Memoization policies
│   ├── endpoints.yml                  # Action server URL (port 5055)
│   ├── data/
│   │   ├── nlu.yml                    # Training examples (English + Hindi)
│   │   ├── stories.yml                # Conversation flows
│   │   ├── rules.yml                  # Hard rules (dispute, callback, deny_ptp)
│   ├── actions/actions.py             # 3 custom actions:
│   │                                     action_fetch_account
│   │                                     action_validate_and_save_ptp
│   │                                     action_save_followup
│   └── models/                        # Trained model tarball
│
├── scripts/
│   ├── setup_db.ps1                   # Drops/recreates collections_dev DB
│   ├── train_rasa.ps1                 # Validates + trains Rasa model
│   ├── start_stack.ps1                # Start all services (one command)
│   └── stop_stack.ps1                 # Stop all services
│
├── tests/
│   └── e2e/
│       └── test_e2e.py                # 20 live integration tests (Spring Boot)
│
├── tools/
│   └── maven/
│       └── apache-maven-3.9.6/        # Project-local Maven (no global install needed)
│
└── venv310/                           # Python 3.10 virtualenv (project runtime)
```

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Java | 17+ | Spring Boot API |
| PostgreSQL | 15+ | Database |
| Python | 3.10 | Bot server + Rasa |

> **Maven is included in `tools/maven/`** — no global install required.

## One-Command Startup

### Start the entire stack

```powershell
.\scripts\start_stack.ps1
```

This starts all 5 services in order, checks health between each, and prints a status dashboard when ready.

```powershell
# Check current status
.\scripts\start_stack.ps1 -Status

# Stop everything
.\scripts\start_stack.ps1 -Stop

# Stop all processes on stack ports (force, including strays)
.\scripts\stop_stack.ps1 -All

# Partial starts
.\scripts\start_stack.ps1 -SkipRasa          # bot + Spring Boot only
.\scripts\start_stack.ps1 -BotOnly           # just the bot server
```

### What the script does

- Prerequisite checks (Java, Maven, PostgreSQL, venv310, Rasa, Spring JAR) — exits with a clear message if anything is missing
- Idempotent — skips services already running on their ports
- Waits up to 60-120s per service for health, with timeout and log-file pointer on failure
- Records PIDs to `.stack_pids.json` so `-Stop` only kills what *it* launched
- Final status dashboard: all 5 ports + bot `/health` endpoint + managed PID table

---

__3 Ways to Talk to the Voice Bot:__

1. __Text Simulator__ (easiest):

   ```powershell
   cd bot
   ..\venv310\Scripts\python.exe test_text.py
   ```

2. __Voice Simulator__ (real voice):

   ```powershell
   cd bot
   ..\venv310\Scripts\python.exe test_voice.py
   ```

3. __Direct API__ (developer):

   ```powershell
   curl -X POST "http://localhost:8000/call/mess
   ```


## Manual Setup (if needed)

### 1. Initialize the database

```powershell
# From the project root — drops, recreates, and seeds collections_dev
.\scripts\setup_db.ps1
```

Credentials match `api/voice-bot-api/src/main/resources/application.properties` (default: `postgres` / `all@1234`).

### 2. Build the Spring Boot API

```powershell
cd api\voice-bot-api
..\tools\maven\apache-maven-3.9.6\bin\mvn.cmd package -DskipTests
```

Produces `target/voice-bot-api-1.0.0.jar`.

### 3. Install Python dependencies

```powershell
python -m venv venv310
.\venv310\Scripts\pip install -r bot\requirements.txt
```

### 4. Train the Rasa model

```powershell
cd rasa
..\venv310\Scripts\rasa.exe train
```

---

## Services

| Service | Port | Command (manual) |
|---|---|---|
| PostgreSQL | 5432 | (system service) |
| Spring Boot API | 8080 | `java -jar api\voice-bot-api\target\voice-bot-api-1.0.0.jar` |
| Rasa Server | 5005 | `cd rasa; ..\venv310\Scripts\rasa.exe run --enable-api --cors "*" --port 5005` |
| Action Server | 5055 | `cd rasa; ..\venv310\Scripts\rasa.exe run actions --port 5055 --cors "*"` |
| Bot Server | 8000 | `cd bot; ..\venv310\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000` |

---

## API Reference

### Bot Server (FastAPI — port 8000)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check — status of all services and models |
| POST | `/call/start?account_number=LN001` | Start call — returns WAV greeting audio |
| POST | `/call/message?account_number=LN001` | Send WAV audio — returns WAV response |
| POST | `/call/message/text?account_number=LN001&message=hello` | Send text — returns JSON `{"response": "..."}` |
| POST | `/call/end?account_number=LN001` | End call — returns outcome with call_log |

### Spring Boot API (port 8080)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/accounts/{accountNumber}` | Fetch account details |
| GET | `/api/v1/promise-policy` | Fetch PTP business rules (max days, min %) |
| POST | `/api/v1/followup` | Save followup record `{accountId, remarks}` |
| POST | `/api/v1/promise` | Validate and save PTP `{accountId, followupId, promiseAmount, promiseDate}` |
| POST | `/api/v1/call-log` | Log call outcome (called by bot) |
| GET | `/api/v1/call-log/{accountId}` | Get call history for an account |

---

## Running Tests

### Unit tests (no external services needed)

```powershell
cd bot
..\venv310\Scripts\python.exe -m pytest test_bot.py -v
```

13 tests covering health checks, call start/end, message handling, Rasa-down fallback, language normalization, and greeting generation. All use mocked HTTP dependencies.

### E2E integration tests (requires Spring Boot on port 8080)

```powershell
cd .
.\venv310\Scripts\python.exe -m pytest tests\e2e\test_e2e.py -v
```

20 tests hitting the live Spring Boot API: account fetching, PTP validation within/exceeding limits, followup saving, multi-language support, complete flow, and error handling.

### All tests together

```powershell
.\venv310\Scripts\python.exe -m pytest bot\test_bot.py tests\e2e\test_e2e.py -v
```

---

## Client Simulators

### Text simulator (no audio hardware needed)

```powershell
cd bot
..\venv310\Scripts\python.exe test_text.py
```

Interactive terminal client. Sends text messages to `/call/message/text` and displays bot responses. Handles start call and end call.

### Voice simulator (requires microphone + headphones/speaker)

```powershell
cd bot
..\venv310\Scripts\python.exe test_voice.py
```

Records audio from your microphone, sends it to `/call/message`, plays back the bot's audio response. Uses `sounddevice` for audio I/O.

### List audio devices

```powershell
cd bot
..\venv310\Scripts\python.exe test_audio.py
```

Prints all available audio input/output device indices. Useful for configuring `MIC_DEVICE` and `HEADPHONE_DEVICE` constants in the simulators.

---

## Seeded Test Accounts

| Account | Customer | Language | Overdue | Charges |
|---|---|---|---|---|
| LN001 | Rajesh Kumar | Hindi (hi) | 12,400 | 500 |
| LN002 | Priya Sharma | English (en) | 8,750 | 250 |
| LN003 | Anand Rajan | Tamil (ta → en fallback) | 31,200 | 1,500 |

---

## How the PTP Flow Works

```
Customer call → /call/start (fetch account → set Rasa slots → build greeting → return WAV)
                                    ↓
Customer speaks → Whisper STT → transcript → Rasa NLU
                                    ↓
Rasa extracts intent + entities (amount, date)
       ↓
Rasa action_validate_and_save_ptp:
  1. Fetch promise-policy from Spring Boot
  2. Validate date ≤ maxPromiseDays (30)
  3. Validate amount ≥ minPromisePercent (25% of overdue)
  4. Create followup record
  5. Save promise → returns followupId
       ↓
       Bot synthesizes response via Piper TTS → returns WAV
                                    ↓
Call ends → /call/end reads Rasa tracker:
  - ptp_saved=True   → PTP_CAPTURED
  - last intent=dispute → ESCALATED
  - else             → COMPLETED
  Logs call_log with followupId linked
```

---

