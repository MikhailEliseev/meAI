"""
external_api — Hermes tool: call any external API.

Part of toolset "hermes-debug". Unlike api_debug (hardcoded to app:8000),
this tool works with ANY URL — external APIs, webhooks, third-party services.
"""

import json
import logging

import httpx
from tools.registry import registry

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


async def handle_call_api(url=None, method=None, headers=None, body=None, **kwargs) -> str:
    """Make an HTTP request to any external API.

    Args:
        url: Full URL (https://...)
        method: HTTP method (GET, POST, PUT, DELETE, PATCH). Default: GET
        headers: JSON object with request headers (optional)
        body: JSON body for POST/PUT/PATCH (optional)

    Returns:
        JSON with status_code, headers, body (truncated to 8000 chars).
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        method = d.get("method", method or "GET")
        headers = d.get("headers", headers)
        body = d.get("body", body)

    if not url:
        return json.dumps({"error": "url is required"})
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must start with http:// or https://"})

    method = (method or "GET").upper()
    allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if method not in allowed_methods:
        return json.dumps({"error": f"Unsupported method: {method}. Allowed: {', '.join(sorted(allowed_methods))}"})

    req_headers = {"User-Agent": USER_AGENT}
    if headers and isinstance(headers, dict):
        req_headers.update(headers)

    # Parse body: can be a dict (JSON) or string
    req_body = None
    req_json = None
    if body is not None:
        if isinstance(body, dict):
            req_json = body
        elif isinstance(body, str):
            try:
                req_json = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                req_body = body
        else:
            req_body = str(body)

    logger.info("call_api: %s %s", method, url[:120])

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=req_headers) as client:
            if method == "GET":
                resp = await client.get(url)
            elif method == "DELETE":
                resp = await client.delete(url)
            elif method == "PATCH":
                resp = await client.patch(url, json=req_json, content=req_body)
            elif method == "PUT":
                resp = await client.put(url, json=req_json, content=req_body)
            else:  # POST
                resp = await client.post(url, json=req_json, content=req_body)

            return json.dumps({
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp.text[:8000],
                "url": str(resp.url),
            }, ensure_ascii=False)

    except httpx.TimeoutException:
        return json.dumps({"error": f"Timeout calling {url[:120]}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Register ────────────────────────────────────────────────────────

registry.register(
    name="call_api",
    toolset="hermes-debug",
    schema={
        "type": "function",
        "function": {
            "name": "call_api",
            "description": (
                "Make an HTTP request to ANY external API or web service. "
                "Unlike api_debug (limited to app:8000), this works with any URL. "
                "Supports GET, POST, PUT, DELETE, PATCH with custom headers and JSON body. "
                "Use for: external APIs, webhooks, third-party integrations, Apify, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to call (https://...)",
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (default: GET)",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional request headers as JSON object",
                    },
                    "body": {
                        "type": "object",
                        "description": "Optional JSON body for POST/PUT/PATCH requests",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_call_api,
    check_fn=lambda: True,
    is_async=True,
    description="HTTP request to any external API",
    emoji="🔌",
)
