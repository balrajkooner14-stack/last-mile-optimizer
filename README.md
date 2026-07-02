# US Last-Mile Delivery Cost Optimizer

A full-stack web application that solves the **Vehicle Routing Problem (VRP)** for small-business delivery routes across US cities — and quantifies the dollar savings of optimization over naive sequential routing.

**Live demo:** https://last-mile-optimizer.vercel.app

---

## What it does

Enter a depot address and up to 25 delivery stops. The app:

1. **Geocodes** every address via OpenStreetMap Nominatim
2. **Builds a real driving-distance matrix** via the OSRM public routing API
3. **Solves the VRP** with Google OR-Tools (PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH)
4. **Compares** the optimized routes against a naive sequential baseline
5. **Calculates actual dollar costs** using BLS driver wage data and EIA fuel prices
6. **Streams live progress** to the browser so you never see a blank screen

Results include: cost saved today, projected annual savings, miles saved, CO₂ avoided, side-by-side Leaflet maps, and a full cost breakdown chart.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Vercel Platform                   │
│                                                      │
│  ┌──────────────────┐      ┌─────────────────────┐  │
│  │  Next.js 14      │      │  FastAPI (Python)   │  │
│  │  TypeScript      │ ───▶ │  api/index.py       │  │
│  │  Tailwind CSS    │      │  Streaming NDJSON   │  │
│  │  Leaflet Maps    │      │                     │  │
│  │  Recharts        │      │  src/               │  │
│  └──────────────────┘      │  ├─ geocoder.py     │  │
│                             │  ├─ distance_matrix │  │
│                             │  ├─ vrp_solver.py   │  │
│                             │  ├─ naive_router.py │  │
│                             │  ├─ cost_calculator │  │
│                             │  └─ route_visualizer│  │
│                             └─────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
  OpenStreetMap tiles         OSRM Route API
  (Leaflet, free)             Nominatim Geocoding
                              (both free, no key)
```

**Data sources:**
- BLS Occupational Employment Statistics — SOC 53-3031 (Light Truck Drivers), metro-level mean hourly wages, 2023
- EIA Weekly Retail Gasoline & Diesel Prices — state-level 2024 annual averages
- OpenStreetMap / OSRM — free public routing API, no key required

---

## Sample scenarios

| Scenario | City | Stops | Vehicles |
|---|---|---|---|
| Chicago Florist | Chicago, IL | 15 | 2 |
| Austin Pharmacy | Austin, TX | 12 | 2 |
| Brooklyn Grocery | Brooklyn, NY | 20 | 3 |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS v3 |
| Maps | Leaflet + react-leaflet v4, OpenStreetMap tiles |
| Charts | Recharts |
| UI components | shadcn/ui |
| Backend | FastAPI, Python 3.12 |
| Optimization | Google OR-Tools (VRP solver) |
| Geocoding | Nominatim (OpenStreetMap) |
| Routing | OSRM public demo server |
| Data | pandas, BLS OES CSV, EIA fuel prices CSV |
| Tests | pytest, unittest.mock |
| Deployment | Vercel (Hobby tier) |

---

## Local development

**Prerequisites:** Python 3.12+, Node.js 18+

### 1. Clone and install Python dependencies

```bash
git clone <repo-url>
cd last-mile-optimizer
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
```

### 3. Run both servers

**Terminal 1 — FastAPI backend (port 8001):**
```bash
python -m uvicorn api.index:app --port 8001 --reload
```

**Terminal 2 — Next.js frontend (port 3000):**
```bash
cd frontend && npm run dev
```

Open **http://localhost:3000**. The Next.js dev server proxies `/api/*` requests to the FastAPI backend automatically.

### 4. Run tests

```bash
python -m pytest tests/ -v
```

65 tests, ~2 minutes (the VRP solver tests use a 5-second time limit).

---

## Project structure

```
last-mile-optimizer/
├── api/
│   └── index.py              # FastAPI app — 4 endpoints, streaming NDJSON
├── src/
│   ├── geocoder.py           # Nominatim address → lat/lon
│   ├── distance_matrix.py    # OSRM N×N driving distance + duration matrix
│   ├── vrp_solver.py         # OR-Tools VRP solver
│   ├── naive_router.py       # Sequential baseline router
│   ├── cost_calculator.py    # BLS + EIA cost calculation
│   └── route_visualizer.py   # OSRM route geometry + Leaflet map payload
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Main page — streaming consumer + layout
│   │   ├── types.ts          # Shared TypeScript interfaces
│   │   └── components/
│   │       ├── ScenarioLoader.tsx
│   │       ├── AddressForm.tsx
│   │       ├── ProgressBar.tsx
│   │       ├── RouteMap.tsx  # Leaflet map (dynamic import, ssr: false)
│   │       ├── SavingsPanel.tsx
│   │       └── HowItWorks.tsx
│   └── next.config.mjs       # Dev proxy: /api/* → localhost:8001
├── data/
│   ├── bls_driver_wages.csv  # 20 US metros, SOC 53-3031 wages
│   ├── fuel_prices.csv       # 51 state-level 2024 fuel prices
│   └── sample_scenarios/     # chicago_florist, austin_pharmacy, brooklyn_grocery
├── tests/
│   ├── conftest.py
│   ├── test_geocoder.py
│   ├── test_distance_matrix.py
│   ├── test_vrp_solver.py
│   ├── test_cost_calculator.py
│   └── test_e2e.py
├── notebooks/
│   └── methodology.ipynb     # Step-by-step VRP walkthrough
├── vercel.json               # Vercel routing + 60s function timeout
└── requirements.txt
```

---

## How costs are calculated

```
driver_cost = route_duration_hours × bls_hourly_wage(city, state)
fuel_cost   = route_distance_miles × (fuel_price_per_gallon / vehicle_mpg)
total_cost  = driver_cost + fuel_cost

savings     = naive_total_cost − optimized_total_cost
annual      = savings × 250  (working days per year)
```

Vehicle MPG defaults: van = 18, truck = 12, car = 28.
CO₂ emission factors: van = 0.89 lbs/mile, truck = 1.45 lbs/mile, car = 0.68 lbs/mile.

---

## Deployment (Vercel)

The repo deploys automatically on push to `main`. Both the Python backend and Next.js frontend are served from a single Vercel project.

Key configuration in `vercel.json`:
- `/api/*` → `api/index.py` (FastAPI, maxDuration: 60s)
- `/*` → Next.js frontend

The VRP time limit is adaptive (`max(10, min(55, num_stops))` seconds) to stay within Vercel's 60-second serverless function cap.

---

## Portfolio context

Masters in Business Analytics project demonstrating:
- **Operations research** — Vehicle Routing Problem formulation and solution
- **Real-world API integration** — OSRM, Nominatim, BLS, EIA
- **Full-stack development** — FastAPI streaming + Next.js consumer
- **Geospatial analysis** — driving distance matrices, route geometry
- **Business framing** — translating route optimization into dollar savings a non-technical stakeholder can act on
