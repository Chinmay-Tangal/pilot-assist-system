# ✈️ Pilot Assistance System (PAS)

> An AI-powered cockpit assistance platform that automates ATC instruction parsing, contextual checklist retrieval, and real-time flight path visualization — reducing pilot monitoring workload and improving situational awareness.

---

## 🧭 Table of Contents

- [System Overview](#system-overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Module Breakdown](#module-breakdown)
- [Data Flow](#data-flow)
- [Flight Map & Journey Replay](#flight-map--journey-replay)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Roadmap](#roadmap)

---

## System Overview

The **Pilot Assistance System (PAS)** is designed to reduce the cognitive load of the **Pilot Monitoring (PM)** in a two-crew cockpit. It operates across three primary pillars:

| Pillar | What It Does |
|---|---|
| **ATC Audio Parser** | Captures live ATC audio, transcribes it, and extracts structured flight parameters (heading, altitude, speed, frequency, etc.) for display on the assistance dashboard |
| **Context Engine** | Ingests live flight data (FMS, avionics alerts), correlates with a checklist database, and surfaces the correct procedure automatically |
| **Flight Map & Replay** | Displays a real-time moving map with the flight path traced, and enables full journey replay to review how the system assisted throughout the flight |

---

## Core Features

- 🎙️ **Live ATC audio transcription** using speech-to-text with aviation-tuned language model
- 📋 **Structured parameter extraction** — heading, altitude, squawk, QNH, runway, frequency auto-parsed from ATC text
- 🗺️ **Real-time moving map** — aircraft position, route, waypoints, and path history
- ⚡ **Alert-triggered checklist retrieval** — ECAM/EICAS alerts piped to context engine → correct checklist served instantly
- 📡 **Flight data pipeline** — FMS, GPS, avionics feed into a central context engine
- 🔁 **Full flight journey replay** — mimic any flight from takeoff to landing with timestamped system actions overlaid
- 🖥️ **Pilot Monitoring Dashboard** — clean, glanceable UI designed for cockpit use

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        COCKPIT DATA SOURCES                         │
│   ATC Radio Audio    │   FMS / Avionics    │   ECAM / EICAS Alerts  │
└──────────┬───────────┴────────┬────────────┴──────────┬─────────────┘
           │                   │                        │
           ▼                   ▼                        ▼
┌──────────────────┐  ┌─────────────────┐   ┌─────────────────────┐
│  Audio Ingestion │  │ Flight Data Bus │   │   Alert Listener    │
│  Service         │  │ (ARINC 429 /    │   │   (ACARS / UDP)     │
│  (Whisper ASR)   │  │  UDP Bridge)    │   └────────┬────────────┘
└────────┬─────────┘  └────────┬────────┘            │
         │                    │                      │
         ▼                    ▼                      ▼
┌────────────────────────────────────────────────────────────────────┐
│                         CONTEXT ENGINE                             │
│                                                                    │
│   NLP Parameter Extractor   │   Alert Classifier   │  State Store  │
│   (ATC Intent Parser)       │   (ML / Rule-based)  │  (Redis)      │
└────────────────────────┬───────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────────┐
           ▼             ▼                 ▼
  ┌──────────────┐ ┌───────────┐  ┌──────────────────┐
  │  Dashboard   │ │ Checklist │  │  Flight Path DB  │
  │  API (REST / │ │ Database  │  │  (TimescaleDB /  │
  │  WebSocket)  │ │ (Postgres)│  │   InfluxDB)      │
  └──────┬───────┘ └───────────┘  └────────┬─────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────┐
│              PILOT MONITORING DASHBOARD             │
│                                                     │
│  ATC Parameters  │  Active Checklist  │  Map View   │
│  Panel           │  Panel             │  (Leaflet)  │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend

| Layer | Technology | Purpose |
|---|---|---|
| API Server | **FastAPI** (Python) | REST + WebSocket API for dashboard |
| Audio ASR | **OpenAI Whisper** (self-hosted or API) | ATC speech-to-text |
| NLP / Intent Parsing | **spaCy** + custom aviation grammar rules + **Claude API** | Extract structured parameters from ATC text |
| Alert Processing | **Python** rule engine + ML classifier | Match alerts to checklist triggers |
| Message Bus | **Apache Kafka** or **Redis Pub/Sub** | Real-time event streaming between modules |
| Checklist DB | **PostgreSQL** | Store all aircraft-type checklists with metadata |
| Flight Path Store | **TimescaleDB** (Postgres extension) | Time-series position data for map & replay |
| State Cache | **Redis** | Current flight state, active parameters |
| Task Queue | **Celery** | Async audio processing jobs |

### Frontend (Pilot Monitoring Dashboard)

| Layer | Technology | Purpose |
|---|---|---|
| Framework | **React** (TypeScript) | Component-based dashboard UI |
| Styling | **Tailwind CSS** | Dark cockpit-style theme |
| Real-time | **Socket.IO** | Push updates to dashboard without polling |
| Map | **Leaflet.js** + **React-Leaflet** | Flight path map, aircraft marker, waypoints |
| Tile Layer | **OpenStreetMap** or **Mapbox** | Base map tiles |
| Charts | **Recharts** | Altitude profile, speed trends |
| State Management | **Zustand** | Lightweight global state |

### Infrastructure & DevOps

| Component | Technology |
|---|---|
| Containerization | **Docker** + **Docker Compose** |
| Orchestration | **Kubernetes** (for production) |
| CI/CD | **GitHub Actions** |
| Monitoring | **Prometheus** + **Grafana** |
| Logging | **ELK Stack** (Elasticsearch, Logstash, Kibana) |
| Flight Hardware Bridge | **ARINC 429 / RS-232 adapter** + Python serial bridge (sim: X-Plane UDP) |

---

## Module Breakdown

### 1. Audio Ingestion Service

Captures audio from the VHF radio interface or a connected audio device.

- Input: Raw PCM audio stream (44.1kHz mono)
- Processing: VAD (Voice Activity Detection) → Whisper ASR → raw transcript
- Output: Raw ATC text pushed to Kafka topic `atc.raw_transcript`

```
services/audio_ingestion/
├── vad.py           # Silero VAD for speech segment detection
├── transcriber.py   # Whisper model inference
├── audio_capture.py # PortAudio / sounddevice capture
└── producer.py      # Kafka producer
```

### 2. NLP Parameter Extractor

Parses ATC transcript into structured instruction objects.

- Input: Raw ATC text (`"Speedbird 4 7 2, turn left heading 2 7 0, descend flight level 1 1 0, contact 128.6"`)
- Output: JSON parameter block

```json
{
  "callsign": "BAW472",
  "heading": 270,
  "altitude": "FL110",
  "frequency": "128.6",
  "instruction_type": "turn+descend+contact",
  "raw": "Speedbird 4 7 2, turn left heading 2 7 0..."
}
```

- Uses: spaCy NER + custom patterns, fallback to Claude API for ambiguous instructions

```
services/nlp_extractor/
├── patterns.py      # spaCy EntityRuler patterns (aviation vocabulary)
├── parser.py        # Main extraction logic
├── claude_fallback.py  # Claude API for complex/ambiguous ATC
└── schema.py        # Pydantic models for structured output
```

### 3. Context Engine

The brain of the system. Maintains current flight state and routes data to correct outputs.

- Subscribes to: `atc.parameters`, `flight.alerts`, `flight.position`
- Maintains: rolling flight state (altitude, heading, speed, phase of flight)
- On alert received: queries checklist DB → pushes to `checklist.active`
- On parameter update: pushes to `dashboard.atc_panel`

```
services/context_engine/
├── state_manager.py     # Flight state machine
├── alert_handler.py     # Alert → checklist resolver
├── checklist_client.py  # Postgres checklist query
├── router.py            # Route events to correct Kafka topics
└── flight_phase.py      # Phase detector (taxi, takeoff, cruise, etc.)
```

### 4. Checklist Database

Structured storage of all aircraft checklists (Normal, Abnormal, Emergency).

```sql
-- checklists table
CREATE TABLE checklists (
  id UUID PRIMARY KEY,
  aircraft_type VARCHAR(10),      -- e.g. 'A320', 'B737'
  phase VARCHAR(30),              -- e.g. 'BEFORE_START', 'EMERGENCY'
  trigger_alert VARCHAR(100),     -- ECAM/EICAS alert code
  title VARCHAR(200),
  items JSONB,                    -- array of checklist items
  priority INT                    -- 1=EMERGENCY, 2=ABNORMAL, 3=NORMAL
);
```

### 5. Flight Path Service

Records position data at fixed intervals and serves it for map display and replay.

- Input: GPS/FMS position over UDP or ARINC 429
- Storage: TimescaleDB hypertable (timestamp, lat, lon, alt, speed, heading)
- API: REST endpoint for path history + WebSocket for live position

```
services/flight_path/
├── position_listener.py  # UDP/serial listener
├── recorder.py           # Write to TimescaleDB
├── replay.py             # Replay engine with speed control
└── api.py                # FastAPI routes for path data
```

### 6. Pilot Monitoring Dashboard (Frontend)

```
frontend/src/
├── components/
│   ├── ATCPanel/          # Displays extracted ATC parameters
│   ├── ChecklistPanel/    # Active checklist with tick-off
│   ├── MapView/           # Leaflet map with flight path
│   ├── AlertBanner/       # Active alerts strip
│   └── ReplayControls/    # Play/pause/scrub for journey replay
├── hooks/
│   ├── useSocket.ts       # WebSocket connection
│   ├── useFlightState.ts  # Live flight state
│   └── useReplay.ts       # Replay engine hook
├── store/
│   └── flightStore.ts     # Zustand global state
└── App.tsx
```

---

## Data Flow

### ATC Instruction Flow

```
Radio Audio
    → Audio Capture (PortAudio)
    → VAD (speech segmentation)
    → Whisper ASR (transcription)
    → Kafka: atc.raw_transcript
    → NLP Extractor (parameter parsing)
    → Kafka: atc.parameters
    → Context Engine (state update)
    → WebSocket → Dashboard ATC Panel
```

### Alert → Checklist Flow

```
Avionics Alert (ECAM/EICAS)
    → Alert Listener (UDP/serial)
    → Kafka: flight.alerts
    → Context Engine (classify alert)
    → Checklist DB Query (PostgreSQL)
    → Kafka: checklist.active
    → WebSocket → Dashboard Checklist Panel
```

### Flight Path Flow

```
FMS / GPS Position
    → Position Listener (UDP)
    → TimescaleDB (recorded)
    → Kafka: flight.position
    → WebSocket → Dashboard Map View (live dot + path line)
```

---

## Flight Map & Journey Replay

The map module is central to mimicking a full flight journey.

### Live Map Features

- ✈️ **Aircraft marker** — rotates to match current heading
- 🛤️ **Path polyline** — drawn incrementally as flight progresses
- 📍 **Waypoints** — FMS route overlaid on map
- 🔴 **Alert markers** — timestamped pins where alerts were triggered
- 💬 **ATC event pins** — show what instruction was given at each point

### Replay Mode

The replay engine reads the TimescaleDB flight history and re-emits events at selectable playback speed (1x, 2x, 4x).

During replay:
- Aircraft marker animates along recorded path
- ATC panel updates with what was received at each timestamp
- Checklists re-surface at the moment they were triggered
- Alert timeline shown on a scrubber bar

```typescript
// Replay hook usage
const { play, pause, seek, speed, currentTime } = useReplay(flightId);
```

### Map Stack

```
Leaflet.js
  └── React-Leaflet (component wrapper)
       ├── TileLayer (Mapbox / OSM)
       ├── Polyline (flight path)
       ├── RotatedMarker (aircraft icon, heading-aware)
       ├── CircleMarker (waypoints)
       └── Popup (ATC/alert event details on click)
```

---

## Directory Structure

```
pilot-assistance-system/
│
├── services/
│   ├── audio_ingestion/
│   ├── nlp_extractor/
│   ├── context_engine/
│   ├── checklist_service/
│   ├── flight_path_service/
│   └── api_gateway/
│
├── frontend/
│   ├── src/
│   └── public/
│
├── database/
│   ├── migrations/
│   └── seeds/              # Sample checklist data (A320, B737)
│
├── simulation/
│   ├── xplane_bridge.py    # X-Plane 12 UDP position feed (for demo)
│   ├── atc_audio_samples/  # Sample ATC audio clips for testing
│   └── mock_flight.py      # Inject a full recorded flight for replay demo
│
├── infra/
│   ├── docker-compose.yml
│   ├── k8s/
│   └── prometheus/
│
├── docs/
│   ├── architecture.png
│   ├── data_schemas.md
│   └── checklist_format.md
│
└── README.md
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- (Optional) X-Plane 12 for live simulation feed

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/pilot-assistance-system.git
cd pilot-assistance-system
cp .env.example .env
# Edit .env with your keys (see Environment Variables)
```

### 2. Start Infrastructure

```bash
docker-compose up -d postgres redis kafka timescaledb
```

### 3. Run Database Migrations

```bash
cd database
python migrate.py
python seeds/load_checklists.py --aircraft A320
```

### 4. Start Backend Services

```bash
# Start all services
docker-compose up -d audio_ingestion nlp_extractor context_engine flight_path_service api_gateway
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 6. Inject a Demo Flight (Replay Mode)

```bash
cd simulation
python mock_flight.py --flight EGLL-EDDF-2024-03-15
# This injects a full recorded flight into the system for replay
```

---

## Environment Variables

```env
# ASR
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda           # or cpu

# Claude API (NLP fallback)
ANTHROPIC_API_KEY=your_key

# Databases
POSTGRES_URL=postgresql://pas:password@localhost:5432/pas_db
TIMESCALE_URL=postgresql://pas:password@localhost:5433/flight_path
REDIS_URL=redis://localhost:6379

# Kafka
KAFKA_BOOTSTRAP=localhost:9092

# Map
MAPBOX_TOKEN=your_mapbox_token   # optional, OSM works without

# Hardware (production)
ARINC_SERIAL_PORT=/dev/ttyUSB0  # for real avionics bridge
AUDIO_DEVICE_INDEX=2             # sounddevice device index

# Simulation
XPLANE_HOST=127.0.0.1
XPLANE_PORT=49000
```

---

## Roadmap

| Phase | Milestone | Status |
|---|---|---|
| 1 | Audio ingestion + Whisper ASR pipeline | 🔲 Planned |
| 2 | NLP parameter extractor (spaCy + patterns) | 🔲 Planned |
| 3 | Context engine + Kafka event bus | 🔲 Planned |
| 4 | Checklist database + alert resolver | 🔲 Planned |
| 5 | Pilot Monitoring Dashboard (React) | 🔲 Planned |
| 6 | Leaflet map with live position | 🔲 Planned |
| 7 | TimescaleDB flight recording | 🔲 Planned |
| 8 | Replay engine + journey mimic | 🔲 Planned |
| 9 | X-Plane 12 simulation integration | 🔲 Planned |
| 10 | Real avionics hardware bridge (ARINC 429) | 🔲 Future |

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). All avionics simulation and testing must be done in ground simulation environments only. This system is a research/assistance tool and is **not certified for operational flight use**.

---

## License

MIT License — see [LICENSE](./LICENSE)

---

> **Disclaimer:** PAS is a research prototype. It is not an approved avionics system and must not be used as a primary operational tool in certified flight operations.