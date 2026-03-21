"""MCP stdio server that provides a tripletex_api tool for making Tripletex API calls."""

import json
import logging
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

# Log to stderr so it doesn't interfere with MCP stdio protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("tripletex")

BASE_URL = os.environ.get("TX_BASE_URL", "")
TOKEN = os.environ.get("TX_TOKEN", "")


@mcp.tool()
def api_call(method: str, endpoint: str, params: dict | None = None, body: dict | list | None = None) -> str:
    """Make an HTTP request to the Tripletex accounting API.

    Args:
        method: HTTP method — GET, POST, PUT, or DELETE
        endpoint: API path, e.g. /customer, /invoice, /employee. Include IDs and actions like /invoice/123/:invoice
        params: Query parameters for filtering or field selection, e.g. {"fields": "id,name"}
        body: JSON request body for POST/PUT requests
    """
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    url = f"{BASE_URL}{endpoint}"
    auth = ("0", TOKEN)

    body_str = json.dumps(body, ensure_ascii=False) if body else None
    logger.info(f">>> {method} {endpoint} params={params} body={body_str}")

    response = httpx.request(
        method=method,
        url=url,
        auth=auth,
        params=params,
        json=body if body else None,
        timeout=30.0,
    )

    try:
        resp_body = response.json()
    except Exception:
        resp_body = response.text

    # Truncate large list responses to prevent Claude context overflow
    if isinstance(resp_body, dict) and "values" in resp_body and isinstance(resp_body["values"], list):
        values = resp_body["values"]
        if len(values) > 40:
            resp_body = {**resp_body, "values": values[:40], "_truncated": f"Showing 40 of {len(values)} results"}

    resp_str = json.dumps(resp_body, ensure_ascii=False) if isinstance(resp_body, (dict, list)) else str(resp_body)
    logger.info(f"<<< {response.status_code} {resp_str}")

    result = json.dumps({"status_code": response.status_code, "body": resp_body}, ensure_ascii=False)

    # Hard cap at 15000 chars to prevent "result too large" errors
    if len(result) > 15000:
        result = result[:15000] + '..."}'

    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
