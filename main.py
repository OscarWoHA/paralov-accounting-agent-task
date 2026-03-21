import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

AGENT_VERSION = os.getenv("AGENT_VERSION", "v3")

if AGENT_VERSION == "v3":
    from agent_v3 import run_agent
elif AGENT_VERSION == "v2":
    from agent_v2 import run_agent
else:
    from agent import run_agent

load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUESTS_DIR = os.path.join(PROJECT_DIR, "requests")
SESSIONS_DIR = os.path.join(PROJECT_DIR, "sessions")
os.makedirs(REQUESTS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tripletex AI Accounting Agent")


def save_request(body: dict) -> str:
    """Save the raw request body to a timestamped JSON file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = os.path.join(REQUESTS_DIR, f"{ts}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=2)
    return filepath


@app.post("/solve")
async def solve(request: Request):
    raw_body = await request.body()
    logger.info(f"Received {len(raw_body)} bytes")

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON ({e}). Raw body (first 500 chars): {raw_body[:500]}")
        return JSONResponse({"status": "completed"}, status_code=200)

    prompt = body.get("prompt")
    if not prompt:
        logger.error(f"No prompt in request body. Keys: {list(body.keys())}")
        return JSONResponse({"status": "completed"}, status_code=200)

    files = body.get("files", [])
    credentials = body.get("tripletex_credentials", {})

    # Save raw request
    req_filepath = save_request(body)

    # Set up per-session log file
    # Detect production (competition proxy) vs sandbox (direct API)
    base_url = credentials.get("base_url", "")
    is_production = "tx-proxy" in base_url
    env_tag = "PROD" if is_production else "DEV"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    session_id = ts  # unique per request
    session_file = os.path.join(SESSIONS_DIR, f"{env_tag}_{ts}.log")

    # Write request JSON alongside the log
    request_json_path = session_file.replace(".log", "_request.json")
    with open(request_json_path, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=2)

    start_time = time.time()

    # Log to session file directly (bypass root logger to avoid cross-contamination)
    def slog(msg):
        elapsed = time.time() - start_time
        line = f"[{elapsed:7.1f}s] {msg}\n"
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(line)

    slog(f"=== New task received ===")
    slog(f"Prompt: {prompt}")
    slog(f"Base URL: {base_url}")
    slog(f"Files: {len(files)} attachment(s)")
    slog(f"Request saved to: {req_filepath}")

    # Add session-tagged file handler — logs from concurrent runs will bleed
    # but each line carries the session_id from its formatter so we can filter
    file_handler = logging.FileHandler(session_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(f"%(asctime)s [{session_id}] %(levelname)s %(name)s: %(message)s"))
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    try:
        await run_agent(prompt, files, credentials)
    except Exception as e:
        slog(f"Agent error: {e}\n{traceback.format_exc()}")

    elapsed = time.time() - start_time
    slog(f"=== Task completed in {elapsed:.1f}s ===")

    root_logger.removeHandler(file_handler)
    file_handler.close()

    # Always return completed — partial work still gets partial credit
    return JSONResponse({"status": "completed"})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
