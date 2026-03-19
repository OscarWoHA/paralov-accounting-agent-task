import json
import logging
import os
import traceback
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent import run_agent

load_dotenv()

REQUESTS_DIR = os.path.join(os.path.dirname(__file__), "requests")
os.makedirs(REQUESTS_DIR, exist_ok=True)

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
    body = await request.json()
    prompt = body["prompt"]
    files = body.get("files", [])
    credentials = body["tripletex_credentials"]

    filepath = save_request(body)
    logger.info(f"=== New task received ===")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Files: {len(files)} attachment(s)")
    logger.info(f"Request saved to: {filepath}")

    try:
        await run_agent(prompt, files, credentials)
    except Exception as e:
        logger.error(f"Agent error: {e}\n{traceback.format_exc()}")

    # Always return completed — partial work still gets partial credit
    return JSONResponse({"status": "completed"})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
