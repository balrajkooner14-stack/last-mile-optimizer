# Last-Mile Delivery Cost Optimizer — Project Memory

## What this is
A full-stack web application that solves the Vehicle Routing Problem (VRP) for small
business delivery routes in US cities. Users input a depot address and up to 25
delivery stop addresses, choose a city, vehicle type, and number of vehicles, and the app:
1. Geocodes all addresses using Nominatim (OpenStreetMap, free, no API key)
2. Builds a real driving distance matrix using the OSRM public demo API
3. Solves the VRP using Google OR-Tools to find the optimal multi-vehicle route
4. Compares optimized routes vs. naive sequential routes (before/after)
5. Calculates real dollar cost savings using BLS driver wage data and EIA fuel prices
6. Returns route geometry for Leaflet maps rendered in the Next.js frontend
7. Streams progress back to the frontend so the user sees live status updates

## Portfolio context
Masters in Business Analytics portfolio project. Target roles: Supply Chain Analyst,
Business Analyst, Consultant. Demonstrates operations research (VRP), real-world API
integration, geospatial analysis, full-stack development, and Vercel deployment.

## Architecture
- Backend: FastAPI (Python) in /api/index.py — Vercel serverless function
- Frontend: Next.js 14 (TypeScript, Tailwind) in /frontend/ — Vercel CDN
- Optimization: src/ modules called by the FastAPI backend
- Deployment: Single GitHub repo → Vercel auto-deploys both frontend and backend

## Tech stack
- FastAPI (backend API — pip install fastapi uvicorn python-multipart)
- Google OR-Tools (VRP solver — pip install ortools)
- OSRM public demo server: http://router.project-osrm.org (free, no key needed)
- Nominatim geocoding: https://nominatim.openstreetmap.org (free, no key needed)
- Next.js 14 + TypeScript + Tailwind CSS (frontend)
- Leaflet + react-leaflet (interactive maps, no API key)
- Recharts (cost breakdown charts)
- shadcn/ui (UI components)
- Pandas, NumPy (data handling)
- BLS driver wage data (CSV in /data/)
- EIA fuel price data (CSV in /data/)

## API endpoints (all served from api/index.py)
- GET  /api/health              → {status: "ok", version: "1.0.0"}
- GET  /api/scenarios           → list of available sample scenario names
- GET  /api/scenario/{name}     → {name, depot, stops[], metadata}
- POST /api/optimize            → streaming NDJSON: progress events then final result

## OSRM usage rules (DO NOT CHANGE)
- Use the public demo server: http://router.project-osrm.org
- Table service endpoint: /table/v1/driving/{coordinates}?annotations=distance,duration
- Route service endpoint: /route/v1/driving/{coordinates}?overview=full&geometries=geojson
- Always add 1.1 second delay between requests to respect rate limits
- Coordinates format: lon,lat (longitude FIRST, then latitude)

## OR-Tools VRP setup rules (DO NOT CHANGE)
- Distance callback uses the OSRM distance matrix (in meters)
- Number of vehicles: user-selectable 1-5
- Depot: index 0 in the locations list (always the first address entered)
- First solution strategy: PATH_CHEAPEST_ARC
- Local search metaheuristic: GUIDED_LOCAL_SEARCH
- Time limit: MUST be 55 seconds (Vercel free tier max is 60s — 5s buffer)
- Always return solution routes AND total distance in meters

## Cost calculation rules (DO NOT CHANGE)
- Driver cost = (route_time_hours) × bls_hourly_wage_for_city
- Fuel cost = (route_distance_miles) × (fuel_price_per_gallon / mpg)
- Vehicle MPG defaults: van=18, truck=12, car=28
- Total cost = driver_cost + fuel_cost
- Savings = naive_cost - optimized_cost
- Savings % = (savings / naive_cost) × 100
- Annual savings = daily_savings × 250 working days
- CO2 saved: van=0.89 lbs/mile, truck=1.45 lbs/mile, car=0.68 lbs/mile

## Streaming response format for POST /api/optimize (DO NOT CHANGE)
Each line of the NDJSON stream is one of:
  {"event": "progress", "step": 1, "total": 4, "message": "Geocoding addresses..."}
  {"event": "progress", "step": 2, "total": 4, "message": "Building driving distance matrix..."}
  {"event": "progress", "step": 3, "total": 4, "message": "Running VRP optimization..."}
  {"event": "progress", "step": 4, "total": 4, "message": "Calculating cost savings..."}
  {"event": "complete", "result": { naive, optimized, savings_report, locations, geocoding_failures }}
  {"event": "error", "message": "friendly error text"}

## Vercel deployment rules (DO NOT CHANGE)
- vercel.json routes /api/* to api/index.py and /* to frontend/
- pyproject.toml sets [tool.vercel] entrypoint = "api/index.py"
- functions.api/index.py.maxDuration = 60 in vercel.json
- Fluid Compute must be enabled in Vercel dashboard for the /api/optimize function
- All file reads in src/ must use pathlib.Path(__file__).parent.parent / "data"
  (relative to file location — hardcoded absolute paths will break on Vercel)
- Vercel uses Python 3.12 by default — requirements must be compatible with 3.12

## Frontend component structure (DO NOT CHANGE without asking)
app/page.tsx — main page, 4 sections:
  Section 1: AddressForm + ScenarioLoader + ProgressBar + results summary banner
  Section 2: RouteMap — side-by-side Leaflet maps (naive left, optimized right)
  Section 3: SavingsPanel — metrics grid + Recharts bar chart + pie chart + data table
  Section 4: HowItWorks — methodology explainer for non-technical viewers

## Key design decisions (DO NOT CHANGE)
- Dollar savings is the BIGGEST element on the results screen
- Stream progress so the user never sees a blank screen during optimization
- All Leaflet maps use OpenStreetMap tiles (free, no API key)
- Dark theme throughout (#0A0C10 background)
- Every result explainable in plain English for a non-technical hiring manager

## Deployment
- Platform: Vercel (Hobby free tier)
- GitHub repo: https://github.com/balrajkooner14-stack/last-mile-optimizer
- Live URL: https://last-mile-optimizer.vercel.app

## Sample scenarios (in /data/sample_scenarios/)
- chicago_florist.csv    — 15-stop flower delivery, Chicago IL
- austin_pharmacy.csv   — 12-stop pharmacy delivery, Austin TX
- brooklyn_grocery.csv  — 20-stop grocery delivery, Brooklyn NY

## Local development
- Backend: uvicorn api.index:app --reload --port 8000
- Frontend: cd frontend && npm run dev
- App: http://localhost:3000
- API health check: http://localhost:8000/api/health
