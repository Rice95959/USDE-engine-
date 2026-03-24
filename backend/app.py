"""
USDE Clarity Engine — Backend Server
FastAPI application serving:
  - /api/analyze    → Mistral-powered v7.6 analysis
  - /api/engine     → Local Python v6.2 sensor telemetry
  - /api/health     → Health check
  - /                → Static frontend
"""

import os
import json
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from mistral_client import MistralClient
from usde_engine import CouncilOfOmegas

app = FastAPI(title="USDE Clarity Engine", version="7.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Clients ──
mistral = MistralClient(api_key=os.environ.get("MISTRAL_API_KEY", ""))
council = CouncilOfOmegas()


class AnalyzeRequest(BaseModel):
    text: str
    mode: str = "full"  # "full" = Mistral v7.6, "engine" = Python only


class HealthResponse(BaseModel):
    status: str
    version: str
    mistral_configured: bool


# ── System prompt (v7.6 schema) ──
SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(__file__), "system_prompt.txt"), "r"
).read()


@app.get("/api/health")
async def health():
    return HealthResponse(
        status="ok",
        version="7.6.0",
        mistral_configured=bool(os.environ.get("MISTRAL_API_KEY")),
    )


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.text or len(req.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text too short")

    # Sanitize
    text = req.text
    for old, new in [
        ("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'),
        ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " "), ("\u2026", "..."),
    ]:
        text = text.replace(old, new)

    # Truncate
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000]) + "\n[Truncated]"

    result = {"mode_used": req.mode}

    # Run local Python engine if requested
    if req.mode in ("engine", "both"):
        try:
            engine_result = council.analyze(text)
            result["engine"] = engine_result
        except Exception as e:
            result["engine_error"] = str(e)[:200]

    # Run Mistral v7.6 analysis
    if req.mode in ("full", "both"):
        if not os.environ.get("MISTRAL_API_KEY"):
            raise HTTPException(status_code=503, detail="MISTRAL_API_KEY not configured")

        try:
            user_msg = f"Analyze this text. Return ONLY a single JSON object, no markdown fences, no commentary:\n\n{text}"
            raw = await mistral.chat(
                system=SYSTEM_PROMPT,
                user=user_msg,
                model=os.environ.get("MISTRAL_MODEL", "mistral-large-latest"),
                max_tokens=16000,
            )

            # Extract JSON
            raw = raw.replace("```json", "").replace("```", "").strip()
            i0, i1 = raw.find("{"), raw.rfind("}")
            if i0 < 0 or i1 <= i0:
                raise ValueError(f"No JSON in response: {raw[:150]}")

            parsed = json.loads(raw[i0 : i1 + 1])
            result["analysis"] = parsed

        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"JSON parse error: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Mistral API error: {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)[:300])

    return JSONResponse(content=result)


# ── Serve frontend ──
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets") if os.path.isdir(os.path.join(frontend_dir, "assets")) else frontend_dir), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
