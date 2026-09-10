# FLARE — Flight Airfare Real-Time Economic Index Platform

**FLARE** is an airfare price intelligence and indexing platform built for the **Smart India Hackathon (SIH)**. It tracks, normalizes, and analyzes domestic airfares across India in real time, breaking down ticket costs and modeling airfare inflation against official **MoSPI Consumer Price Index (CPI)** benchmarks.

---

## ✈️ Key Features

- **Multi-Source Fare Ingestion**: Ingests real-time flight pricing across major Indian OTAs (MakeMyTrip, Goibibo, EaseMyTrip, Cleartrip, Ixigo, Yatra), direct airline portals (IndiGo, Air India), and GDS/metasearch feeds.
- **Itemized Fare Decomposition**: Breaks down ticket prices into Base Rate, Taxes & GST, and OTA Convenience Fees.
- **MAD Outlier Filtering**: Sanitizes abnormal fare spikes using Median Absolute Deviation (MAD) statistical filtering.
- **Laspeyres Airfare Price Index**: Computes weighted domestic airfare index series to monitor inflation in air transport.
- **MoSPI CPI Integration**: Benchmarks airfare trends against official Ministry of Statistics and Programme Implementation (MoSPI) transport CPI metrics.
- **Interactive GIS Corridor Map**: Visualizes domestic flight routes, hubs, and price corridors on an interactive Leaflet map.
- **Live Search & Analytics Dashboard**: Explore live fares, historical trends, price distributions, and carrier breakdowns.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | [Next.js](https://nextjs.org/) (App Router), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Tailwind CSS](https://tailwindcss.com/), [Leaflet](https://leafletjs.com/), [Recharts](https://recharts.org/), Lucide Icons |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/), [Python 3.12+](https://www.python.org/), [Uvicorn](https://www.uvicorn.org/), [Pydantic v2](https://docs.pydantic.dev/) |
| **Database & Cache** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/), SQLite / [PostgreSQL](https://www.postgresql.org/), [Redis](https://redis.io/) |
| **Background Tasks** | [Celery](https://docs.celeryq.dev/) / APScheduler |
| **Data Ingestion** | Scrape.do, Firecrawl, Apify, Amadeus GDS, Beautiful Soup |

---

## 📁 Project Structure

```text
SIH/
├── backend/                  # FastAPI REST API & Ingestion Engine
│   ├── app/
│   │   ├── api/              # Routers (fares, search, airports, cpi, index)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic data schemas
│   │   ├── services/         # Scrapers, CPI service, DB connection
│   │   └── main.py           # Application entrypoint & table auto-seeding
│   ├── requirements.txt      # Python dependencies
│   └── seed_and_migrate.py   # Seeding & DB migration script
├── frontend/                 # Next.js Web Dashboard
│   ├── src/
│   │   ├── app/              # App router pages (search, explorer, cpi, economic)
│   │   ├── components/       # UI components & Leaflet route map
│   │   └── lib/              # API clients & utilities
│   └── package.json          # Node.js dependencies & scripts
├── database/                 # Database schema & initialization scripts
├── docker-compose.yml        # Multi-container orchestration (DB, Redis, Backend, Frontend)
└── .env.example              # Environment variables template
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** & **npm**
- *(Optional)* **Docker** & **Docker Compose**

---

### Option A: Local Development Setup

#### 1. Configure Environment Variables
Copy the example configuration file:
```bash
cp .env.example .env
```

#### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
# Windows:
python -m venv venv
.\venv\Scripts\activate
# Linux/macOS:
# python3 -m venv venv
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
> The API will be live at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`. Database tables and Indian airports are seeded automatically on first startup.

#### 3. Frontend Setup
In a new terminal:
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
> The web application will be accessible at `http://localhost:3000`.

---

### Option B: Docker Compose

To start the full stack (PostgreSQL, Redis, Backend, Celery Worker/Scheduler, and Frontend) in containers:

```bash
docker-compose up --build
```

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/search` | Search live and cached flight fares |
| `GET` | `/api/v1/airports` | List supported Indian airports and coordinates |
| `GET` | `/api/v1/fares` | Retrieve itemized fare observations |
| `GET` | `/api/v1/index` | Query Laspeyres airfare price index metrics |
| `GET` | `/api/v1/inflation` | Airfare inflation rates and month-over-month trends |
| `GET` | `/api/v1/cpi` | MoSPI official CPI benchmarks and correlation data |

---

## 👥 Team

Developed for the **Smart India Hackathon (SIH)**.
