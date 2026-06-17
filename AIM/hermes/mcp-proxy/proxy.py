#!/usr/bin/env python3
"""MCP STDIO <-> HTTP proxy for WordPress MCP server (Novamira).

Reads JSON-RPC messages from stdin, forwards them to the WordPress MCP HTTP
endpoint, and writes responses to stdout. Manages MCP session state.
"""

import json
import os
import sys
import urllib.request
import urllib.error


def get_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"FATAL: {name} environment variable is required", file=sys.stderr)
        sys.exit(1)
    return val


WP_API_URL = get_env("WP_API_URL")
WP_API_USERNAME = get_env("WP_API_USERNAME")
WP_API_PASSWORD = get_env("WP_API_PASSWORD")

# MCP session state
_session_id: str | None = None


def _basic_auth() -> str:
    import base64
    creds = f"{WP_API_USERNAME}:{WP_API_PASSWORD}"
    return base64.b64encode(creds.encode()).decode()


AUTH_HEADER = f"Basic {_basic_auth()}"


def _send_request(payload: dict) -> dict:
    global _session_id

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH_HEADER,
    }
    if _session_id:
        headers["Mcp-Session-Id"] = _session_id

    req = urllib.request.Request(WP_API_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            # Capture session ID from initialize response
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                _session_id = sid
            body = resp.read().decode("utf-8")
            # Notifications (no "id") get empty response — that's valid MCP
            if not body.strip():
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32603, "message": f"HTTP {e.code}: {body[:500]}"}}
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32603, "message": str(e.reason)}}


def main() -> None:
    print("MCP proxy started", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {line[:200]}", file=sys.stderr)
            continue

        response = _send_request(request)
        # Notifications get no response in MCP — don't write anything
        if response or "id" in request:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
