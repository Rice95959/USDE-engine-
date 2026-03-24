# USDE v7.6 — Clarity Engine

A structured reasoning engine that analyzes competing explanations, identifies the strongest path, exposes the weakest, and recommends action. Powered by Mistral AI.

## Architecture

```
Frontend (HTML/React)  →  FastAPI Backend  →  Mistral API
                                ↓
                     Python USDE v6.2 Engine
                     (local sensor telemetry)
```

- **Frontend**: Single-page React app served as static HTML
- **Backend**: FastAPI with async Mistral client + local Python engine
- **LLM**: Mistral Large (v7.6 prompt architecture)
- **Engine**: Rule-based NLP sensor layer (1,941 lines, 115 tests, stdlib-only)

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/usde-clarity-engine.git
cd usde-clarity-engine

# 2. Set up environment
cp .env.example .env
# Edit .env and add your Mistral API key

# 3. Install Python dependencies
cd backend
pip install -r requirements.txt

# 4. Run
MISTRAL_API_KEY=your_key uvicorn app:app --host 0.0.0.0 --port 10000

# 5. Open http://localhost:10000
```

## Deploy to Render

### Option A: One-Click (render.yaml)

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint** → connect your repo
4. Render reads `render.yaml` and creates the service
5. Add `MISTRAL_API_KEY` in Environment Variables
6. Deploy

### Option B: Manual

1. Push to GitHub
2. Render → **New** → **Web Service**
3. Connect repo, select **Docker** runtime
4. Set environment variables:
   - `MISTRAL_API_KEY` = your Mistral API key
   - `MISTRAL_MODEL` = `mistral-large-latest` (or `mistral-small-latest` for lower cost)
5. Deploy

### Option C: Docker Local

```bash
docker build -t usde-clarity-engine .
docker run -p 10000:10000 -e MISTRAL_API_KEY=your_key usde-clarity-engine
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check + config status |
| `/api/analyze` | POST | Run v7.6 analysis via Mistral |
| `/` | GET | Frontend UI |

### POST /api/analyze

```json
{
  "text": "Your text to analyze...",
  "mode": "full"
}
```

Modes:
- `full` — Mistral v7.6 analysis (default)
- `engine` — Local Python sensor telemetry only
- `both` — Both Mistral + local engine

### Response

```json
{
  "mode_used": "full",
  "analysis": {
    "trust_score": 72,
    "status": "fragile",
    "mode": "empirical",
    "decision": { "action": "challenge specific claim", ... },
    "dominant_chain": { ... },
    "invalid_chain": { ... },
    "counterfactuals": { ... },
    "basin_competition": { ... },
    ...
  }
}
```

## Project Structure

```
usde-clarity-engine/
├── backend/
│   ├── app.py              # FastAPI server
│   ├── mistral_client.py   # Async Mistral API client
│   ├── usde_engine.py      # Python v6.2 sensor engine (1,941 lines)
│   ├── system_prompt.txt   # v7.6 LLM prompt architecture
│   └── requirements.txt
├── frontend/
│   └── index.html          # Full v7.6 React UI
├── Dockerfile
├── render.yaml             # Render blueprint
├── .env.example
├── .gitignore
└── README.md
```

## Mistral Models

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `mistral-large-latest` | Slower | Best for v7.6 schema | Higher |
| `mistral-small-latest` | Faster | Good for simple texts | Lower |

Set via `MISTRAL_MODEL` environment variable.

## What the Engine Does

1. **Parses** text into claims with evidence types and domain tags
2. **Builds** a causal graph of competing explanations
3. **Expands** the adjacency field to find nearby structures (v7.6)
4. **Competes** multiple interpretive basins before collapsing (v7.6)
5. **Selects** the dominant chain and shows where the broken chain fails
6. **Tests** the dominant chain against counterfactual alternatives
7. **Decomposes** uncertainty into evidence, mechanism, sequence, and downstream axes
8. **Recommends** one action with concrete next steps
9. **Self-diagnoses** when its own architecture underperformed

## License

MIT
