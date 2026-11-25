# Project 07: Red – Network Operator Analytics
## Production Architecture, Modern React Frontend & Verification Manual

### Overview
**Project 07: Network Operator Analytics** (CYBER-N201 Graduation Project, Team 10) is a centralized, real-time cyber operations analysis and telemetry consolidation engine. It correlates and visualizes multi-campaign red-team operations across three simulated external source feeds:
* **Project 04 (C2 Framework):** C2 registration, periodic heartbeat check-ins, multi-agent task execution, and host discovery.
* **Project 05 (Interactive Shells):** Reverse/bind shells across TCP, HTTPS, DNS, and ICMP/UDP, command execution, and session management.
* **Project 06 (Covert Exfiltration):** Steganographic and chunked data movement over DNS tunneling, ICMP Echo, and HTTPS beaconing.
* **Project 07 (Analytics Platform Engine):** Canonical SHA-256 event deduplication, thread-safe in-memory repository, lifecycle entity correlation, watchdog stall detection, automated incident synthesis, and an executive React dashboard built using the **Option 2: Glassmorphism Dashboard** design specification.

---

## 1. System Architecture

```
Project Root
├── schemas/
│   └── event.schema.json               # Monolithic JSON Schema Draft 2020-12 (Phase 3 Sealed)
├── models/                             # Pydantic v2 Canonical Validation Models (Phase 3 Sealed)
│   ├── base.py                         # Reusable envelope sub-models (Host, Destination, Technique, Correlation)
│   ├── enums.py                        # Centralized String Enums
│   ├── envelope.py                     # Root CommonEventEnvelope with discriminated detail dispatch
│   └── details/                        # P4, P5, P6, and P7 detail schemas
├── api/                                # FastAPI Backend Application
│   ├── app.py                          # FastAPI factory with Lifespan background scheduler & SPA mount
│   ├── config.py                       # IngestionSettings with production and environment security rules
│   ├── dependencies.py                 # Dependency injection wiring (Repository, Tracker, Watchdogs)
│   ├── hashing.py                      # SHA-256 deterministic canonical payload hashing
│   ├── responses.py                    # API response contracts (Liveness, Readiness, Ingestion, Batch)
│   ├── routes/                         # API Routers
│   │   ├── health.py                   # GET /api/v1/health/live & /ready
│   │   ├── events.py                   # POST /api/v1/events, /batch, GET /events, /{id}
│   │   └── analytics.py                # Overview, Campaigns, Entities, Alerts, Reports, Watchdogs, Demo
│   └── storage/                        # Thread-Safe In-Memory Storage
│       ├── interface.py                # IEventRepository abstract interface & IngestionOutcome
│       └── memory.py                   # Atomic save_if_absent with concurrency locks
├── engine/                             # Core Analytics & Lifecycle Correlation
│   ├── clock.py                        # IClock abstraction (SystemClock & VirtualClock)
│   ├── tracker.py                      # Thread-safe entity lifecycle, recovery, and alert history
│   └── watchdog.py                     # WatchdogEngine with deduplication lock & campaign scoping
├── synthetic/                          # Synthetic Telemetry Generators
│   ├── base.py                         # Generator base class
│   ├── p4_generator.py                 # Project 04 C2 synthetic event builder
│   ├── p5_generator.py                 # Project 05 Interactive Shell synthetic event builder
│   ├── p6_generator.py                 # Project 06 Covert Exfiltration synthetic event builder
│   ├── scenarios.py                    # Pre-packaged end-to-end operational scenarios
│   └── runner.py                       # Automated scenario execution harness
├── frontend/                           # Modernized React + TypeScript + Vite Console
│   ├── src/
│   │   ├── components/                 # Sidebar, Header, EventModal
│   │   ├── pages/                      # Overview, Campaigns, Events, Entities, Alerts, Analytics, Reports
│   │   ├── services/                   # Typed API client
│   │   ├── types/                      # Frontend TypeScript models
│   │   ├── App.tsx                     # Main application layout and polling state
│   │   └── index.css                   # Tactical dark cyber-operations design system
│   ├── package.json                    # Frontend package dependencies (React 18, Vite, Lucide)
│   └── vite.config.ts                  # Vite bundler configuration
├── tests/                              # Comprehensive Automated Test Suite (107 Tests)
├── scripts/                            # Verification & Automation Scripts
│   └── verify_e2e.py                   # Automated 12-step end-to-end acceptance verification
└── README.md
```

---

## 2. Watchdog Engine, Concurrency & Campaign Scoping

### Automatic Periodic Scheduler
* Configured in `api/config.py` via `P7_WATCHDOG_AUTO_EVALUATE` (default `True` in development/production) and `P7_WATCHDOG_INTERVAL_SEC` (default `1.0s`).
* Integrated into FastAPI's startup/shutdown lifespan cycle: a non-blocking background `asyncio` task evaluates watchdogs and shuts down cleanly on server exit.
* Deterministic unit tests automatically disable background scheduling (`ENVIRONMENT=testing`) while preserving full access to manual evaluation.

### Deduplication Lock & Concurrency Protection
* `WatchdogEngine` evaluation is guarded by a `threading.Lock()` preventing race conditions during simultaneous manual API triggers and periodic scheduler execution.
* Transitions from `running` to `stalled` and `stalled` to `timeout` are atomic.
* Once an entity enters `stalled`, subsequent watchdog cycles only evaluate grace period expiration, guaranteeing that duplicate `beacon_missed`, `task_stalled`, `session_stalled`, or `transfer_stalled` events are never emitted for the same stall episode.
* If an entity recovers via fresh telemetry and stalls again later, a new legitimate incident is generated.

### Campaign & Run Scoping
* `WatchdogEngine.check_watchdogs(campaign_id=..., run_id=...)` supports optional scoping:
  * Providing both limits evaluation strictly to that specific campaign and run.
  * Providing only `campaign_id` evaluates all runs within that campaign.
  * Omitting both evaluates all active entities across campaigns.
* Every synthesized P7 event retains the entity's exact `campaign_id` and `run_id`.

---

## 3. Dedicated Alert Center

The system tracks all operational incidents via `GET /api/v1/analytics/alerts`, segregating telemetry into three distinct operational states:
1. **Active Stalls (`active`):** Entities currently exceeding their heartbeat, idle, chunk, or task deadline whose grace periods are currently running.
2. **Resolved Recoveries (`resolved`):** Entities that stalled but received valid activity prior to grace period expiration. Retains recovery timestamps and recovery messages.
3. **Terminal Timeouts (`historical`):** Entities that failed to recover before grace expiration or suffered direct handshake timeouts.

---

## 4. Setup and Quick Start

### Prerequisites
* **Python:** Python 3.10.x
* **Node.js:** Node v18+ or v20+ and npm

### Backend Setup
```powershell
# 1. Navigate to project root
cd C:\Project07_Red_Analytics

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the FastAPI server (serves API and compiled React frontend)
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Development Workflow
```powershell
# In a separate terminal:
cd C:\Project07_Red_Analytics\frontend

# Install dependencies
npm install

# Run Vite dev server with proxy to FastAPI
npm run dev
# Vite runs at http://localhost:3000 and proxies /api to http://127.0.0.1:8000
```

### Production Build & Single-Port Serving
```powershell
# Build production bundle into frontend/dist
cd C:\Project07_Red_Analytics\frontend
npm run build

# Start FastAPI to serve everything from http://127.0.0.1:8000
cd C:\Project07_Red_Analytics
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```
Open **http://127.0.0.1:8000** in your browser to access the full operational console.

---

## 5. Verification Commands

### Execute Full Backend Test Suite (113 Tests)
```powershell
cd C:\Project07_Red_Analytics
python -m pytest tests/ -v
```
* **Coverage:** JSON Schema compliance, Pydantic model cross-field validation, schema parity, lifecycle invariants, API key authentication, SHA-256 canonical hashing, single/batch ingestion idempotency, health probes, watchdog scoping, alert state transitions, concurrency deduplication, all 7 synthetic demo scenarios, and multi-run comparison.

---

## 6. Git Synchronization Guide

To push this repository to your target remote (`https://github.com/Ibrahimhussein711/Network-operator-analytics-`):

```powershell
# 1. Initialize git repository (if not already initialized)
cd C:\Project07_Red_Analytics
git init

# 2. Stage all project files (ignoring caches, virtual environments, and node_modules)
git add .

# 3. Commit the implementation
git commit -m "feat: complete Project 07 MVP with Option 2 Glassmorphism Dashboard, Watchdog scoping, and 100% test pass"

# 4. Set main branch and remote
git branch -M main
git remote add origin https://github.com/Ibrahimhussein711/Network-operator-analytics-.git

# 5. Push to GitHub
git push -u origin main
```

### Execute End-to-End Acceptance Verification
```powershell
cd C:\Project07_Red_Analytics
python scripts/verify_e2e.py
```
* **Verifies:**
  1. Liveness probe (`GET /api/v1/health/live`)
  2. Readiness probe (`GET /api/v1/health/ready`)
  3. Dashboard serving (`GET /` and `GET /dashboard`)
  4. Synthetic P4 C2 ingestion (`agent_registered`, `beacon_checkin`)
  5. Synthetic P5 Shell ingestion (`connection_requested`, `established`, `activity`)
  6. Synthetic P6 Exfiltration ingestion (`transfer_started`, `chunked progress`)
  7. Idempotent duplicate ingestion (HTTP 200 deduplicated)
  8. Payload conflict detection (HTTP 409 Conflict)
  9. External P7 submission rejection (HTTP 422 Unprocessable)
  10. Watchdog timeout evaluation & P7 event generation
  11. Multi-campaign and multi-run isolation
  12. Executive campaign reporting and metrics generation

---

## 6. Troubleshooting Common Issues

* **Registry Permission Warning on Windows:** Handled automatically in `api/app.py` via `mimetypes._mimetypes_read_windows_registry = None`.
* **Path Portability:** All paths derive dynamically from `Path(__file__).resolve().parent.parent`. The project can be relocated to any directory or drive without breaking.
* **Vite Proxy:** In development mode (`npm run dev`), Vite proxies all `/api` traffic to `http://127.0.0.1:8000`. Ensure the FastAPI server is running.
