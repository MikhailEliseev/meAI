"""Bearer token authentication for Hermes FastAPI wrapper.

Per D-25: Next.js passes HERMES_API_KEY in Authorization header.
Per D-27: static key in .env, generated once.
Per D-28: ADMIN mode protection is at Next.js layer (NextAuth role=admin),
         Hermes trusts the X-Client-Mode header from Next.js.
"""

import os
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

security = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
) -> str:
    """Verify Bearer token from Authorization header.

    Returns the validated API key or raises 401.
    Called as a FastAPI dependency.

    Important: security(request) is called explicitly instead of declaring
    HTTPAuthorizationCredentials as a parameter — otherwise FastAPI 0.133+
    wraps it alongside the ChatRequest body, causing 422 "body.body" errors.
    """
    if request.url.path == "/health":
        return "health"

    if not HERMES_API_KEY:
        return "dev-no-key"

    credentials = await security(request)
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = credentials.credentials
    if token != HERMES_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return token
