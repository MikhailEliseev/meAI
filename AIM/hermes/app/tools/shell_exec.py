"""
shell_exec — Hermes debug tool: execute shell commands in container.

Part of toolset "hermes-debug". Restricted to read-only diagnostic commands.
Hermes uses this to debug his own tools — read logs, inspect API responses,
check file contents, test connectivity.
"""

import asyncio
import json
import logging
import os
import subprocess

from tools.registry import registry

logger = logging.getLogger(__name__)

# Whitelist of allowed command prefixes (read-only, safe operations)
ALLOWED_COMMANDS = [
    "curl",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "ls",
    "wc",
    "python3 -c",
    "python -c",
    "stat",
    "file",
    "du",
    "df",
    "env",
    "echo",
    "pwd",
    "hostname",
    "ping -c",
]

# Blocked patterns — commands that will be rejected even if they start with allowed prefix
BLOCKED_PATTERNS = [
    "rm ",
    "kill",
    "shutdown",
    "reboot",
    "mkfs",
    "dd ",
    "> ",
    ">> ",
    "| sh",
    "| bash",
    "$(",
    "`",
    "chmod",
    "chown",
    "docker",
    "sudo",
    "su ",
    "passwd",
]

COMMAND_TIMEOUT = 30  # seconds


def _is_allowed(command: str) -> tuple[bool, str]:
    """Check if command is in the allowed whitelist and not blocked."""
    cmd_clean = command.strip()
    if not cmd_clean:
        return False, "empty command"

    # Check blocked patterns — tokenize command into words/operators,
    # then check each token against blocked list (exact match).
    # This avoids false positives like "kill" matching "skills".
    import re
    tokens = re.findall(r'[a-zA-Z0-9_-]+|[^a-zA-Z0-9_\s-]+', cmd_clean)
    for token in tokens:
        token_lower = token.lower()
        for pattern in BLOCKED_PATTERNS:
            # Patterns with trailing space: check as substring (e.g. "> " blocks redirect)
            # Patterns without: check exact token match (e.g. "kill" blocks only the word "kill")
            if pattern.endswith(' '):
                if pattern in cmd_clean:
                    return False, f"blocked pattern: '{pattern.strip()}'"
            else:
                if token_lower == pattern.lower():
                    return False, f"blocked pattern: '{pattern}'"

    # Check allowed prefixes
    for prefix in ALLOWED_COMMANDS:
        if cmd_clean.startswith(prefix):
            return True, "ok"

    return False, f"not in allowed commands: {', '.join(ALLOWED_COMMANDS)[:120]}"


async def handle_shell_exec(command=None, **kwargs) -> str:
    """Execute a read-only shell command in the Hermes container.

    Args:
        command: Shell command to execute. Must start with an allowed prefix
                 (curl, cat, grep, ls, find, etc.) and contain no destructive patterns.

    Returns:
        JSON string with stdout, stderr, exit_code.
    """
    if isinstance(command, dict):
        command = command.get("command", "")

    if not command or not isinstance(command, str):
        return json.dumps({"error": "command is required (string)"})

    allowed, reason = _is_allowed(command)
    if not allowed:
        logger.warning("shell_exec rejected: %s — %s", command[:80], reason)
        return json.dumps({
            "error": f"Command rejected: {reason}",
            "command": command[:200],
        })

    # Hermes v7: file_guard — проверка shell-команд на запись в защищённые пути
    try:
        from app.file_guard import validate_shell_command
        shell_ok, shell_reason = validate_shell_command(command)
        if not shell_ok:
            logger.warning("shell_exec blocked by file_guard: %s — %s", command[:80], shell_reason)
            return json.dumps({
                "error": f"Command blocked by file_guard: {shell_reason}",
                "command": command[:200],
            })
    except ImportError:
        pass  # file_guard not available — fall through to existing checks

    logger.info("shell_exec: %s", command[:120])

    try:
        proc = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=COMMAND_TIMEOUT,
                    cwd="/opt/hermes",
                ),
            ),
            timeout=COMMAND_TIMEOUT + 5,
        )

        return json.dumps({
            "stdout": proc.stdout[-5000:] if proc.stdout else "",
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "exit_code": proc.returncode,
        }, ensure_ascii=False)

    except asyncio.TimeoutError:
        return json.dumps({"error": f"Command timed out after {COMMAND_TIMEOUT}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_file_read(file_path=None, **kwargs) -> str:
    """Read a file from the Hermes container filesystem.

    Args:
        file_path: Absolute path to the file to read.

    Returns:
        JSON string with file content (max 8000 chars), size, line count.
    """
    if isinstance(file_path, dict):
        file_path = file_path.get("file_path", "")

    if not file_path or not isinstance(file_path, str):
        return json.dumps({"error": "file_path is required (string)"})

    # Restrict to safe paths
    allowed_prefixes = [
        "/opt/hermes",
        "/opt/data",
        "/tmp",
        "/proc/1",
        "/etc/hostname",
        "/etc/hosts",
        "/etc/resolv.conf",
    ]
    allowed = any(file_path.startswith(p) for p in allowed_prefixes)
    if not allowed:
        return json.dumps({
            "error": f"Path not allowed. Must start with: {', '.join(allowed_prefixes)}",
            "requested": file_path,
        })

    logger.info("file_read: %s", file_path)

    try:
        with open(file_path, "r") as f:
            content = f.read(10000)

        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        size = len(content)

        return json.dumps({
            "content": content[:8000],
            "size_bytes": size,
            "lines": lines,
            "truncated": size > 8000,
        }, ensure_ascii=False)

    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {file_path}"})
    except PermissionError:
        return json.dumps({"error": f"Permission denied: {file_path}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_api_debug(url_path=None, method=None, **kwargs) -> str:
    """Debug: make a raw HTTP request to the AIM API and return the raw response.

    Args:
        url_path: API path (e.g., "/api/seo/audit/seo-audit-123")
        method: HTTP method ("GET" or "POST"), default "GET"

    Returns:
        JSON string with status_code, headers, body.
    """
    import httpx

    if isinstance(url_path, dict):
        d = url_path
        url_path = d.get("url_path", d.get("path", ""))
        method = d.get("method", method or "GET")

    if not url_path:
        return json.dumps({"error": "url_path is required"})

    method = (method or "GET").upper()
    if method not in ("GET", "POST"):
        return json.dumps({"error": f"Unsupported method: {method}"})

    full_url = f"http://aim-app:8000{url_path}" if not url_path.startswith("http") else url_path

    logger.info("api_debug: %s %s", method, full_url)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            if method == "GET":
                resp = await client.get(full_url)
            else:
                resp = await client.post(full_url, json={})

            return json.dumps({
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp.text[:5000],
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_file_write(file_path=None, content=None, append=None, **kwargs) -> str:
    """Write content to a file in the Hermes container.

    Hermes v7: проверяет file_guard.is_write_allowed() первой проверкой.
    В ONBOARDING режиме запись всегда запрещена.
    В ADMIN режиме — только whitelist-пути.

    Args:
        file_path: Absolute path to the file to write.
        content: String content to write to the file.
        append: If true, open in append mode ("a") instead of write ("w").
            Useful for multi-turn file assembly (e.g. writing long narrative
            reports in chunks when LLM response size is bounded).

    Returns:
        JSON string with path, size_bytes, lines_written.
    """
    if isinstance(file_path, dict):
        d = file_path
        file_path = d.get("file_path", "")
        if not content:
            content = d.get("content", "")
        if append is None:
            append = d.get("append")

    if not file_path or not isinstance(file_path, str):
        return json.dumps({"error": "file_path is required (string)"})
    if not content or not isinstance(content, str):
        return json.dumps({"error": "content is required (string)"})

    # Hermes v7: file_guard — проверка режима и whitelist путей
    try:
        from app.file_guard import is_write_allowed, get_current_mode
        current_mode = get_current_mode()
        if not is_write_allowed(file_path, current_mode):
            return json.dumps({
                "error": f"File write blocked by file_guard: {file_path}",
                "mode": current_mode,
            })
    except ImportError:
        logger.warning("file_guard not available — skipping mode check")

    # Restrict to safe paths — same as file_read
    allowed_prefixes = [
        "/opt/hermes",
        "/opt/data",
        "/tmp",
    ]
    allowed = any(file_path.startswith(p) for p in allowed_prefixes)
    if not allowed:
        return json.dumps({
            "error": f"Path not allowed. Must start with: {', '.join(allowed_prefixes)}",
            "requested": file_path,
        })

    mode = "a" if append else "w"
    logger.info("file_write: %s mode=%s (%d chars)", file_path, mode, len(content))

    try:
        with open(file_path, mode) as f:
            f.write(content)

        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        size_after = os.path.getsize(file_path)

        return json.dumps({
            "path": file_path,
            "mode": mode,
            "bytes_appended": len(content),
            "size_bytes": size_after,
            "lines_written": lines,
        }, ensure_ascii=False)

    except PermissionError:
        return json.dumps({"error": f"Permission denied: {file_path}"})
    except IsADirectoryError:
        return json.dumps({"error": f"Is a directory: {file_path}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_pip_install(package=None, **kwargs) -> str:
    """Install a Python package into /opt/data/pip-packages/ (persistent volume).

    Packages installed here survive container restarts.
    The target path is added to sys.path so imports work immediately.

    Args:
        package: Package name to install (e.g., "instagrapi", "beautifulsoup4")

    Returns:
        JSON string with package, version, install_path.
    """
    if isinstance(package, dict):
        package = package.get("package", "")

    if not package or not isinstance(package, str):
        return json.dumps({"error": "package is required (string)"})

    # Sanitize package name — only allow alphanumeric, hyphens, underscores, dots
    import re
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', package):
        return json.dumps({"error": f"Invalid package name: {package}"})

    target = "/opt/data/pip-packages"
    os.makedirs(target, exist_ok=True)

    logger.info("pip_install: %s -> %s", package, target)

    try:
        proc = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["pip", "install", "--target", target, package],
                    capture_output=True,
                    text=True,
                    timeout=120,
                ),
            ),
            timeout=130,
        )

        # Add to sys.path so imports work
        sys.path.insert(0, target)

        if proc.returncode == 0:
            # Try to get installed version
            version = "unknown"
            try:
                vproc = subprocess.run(
                    ["pip", "show", package],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                for line in vproc.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
            except Exception:
                pass

            return json.dumps({
                "status": "installed",
                "package": package,
                "version": version,
                "install_path": target,
                "stdout": proc.stdout[-3000:] if proc.stdout else "",
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "status": "failed",
                "package": package,
                "exit_code": proc.returncode,
                "stderr": proc.stderr[-3000:] if proc.stderr else "",
            }, ensure_ascii=False)

    except asyncio.TimeoutError:
        return json.dumps({"error": f"pip install {package} timed out after 120s"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def handle_restart_myself(_=None, **kwargs) -> str:
    """Gracefully restart the Hermes uvicorn server.

    Sends SIGHUP to PID 1 (the main uvicorn process).
    Uvicorn handles this by restarting workers gracefully.

    Use after: installing packages via pip_install, fixing tool code via file_write,
    or when Hermes is in a bad state and needs a fresh start.
    """
    logger.info("restart_myself: initiating graceful restart via SIGHUP")

    try:
        # Schedule restart after response is sent (500ms delay)
        import threading
        def _restart():
            import time as _time
            _time.sleep(0.5)
            import os as _os
            _os.kill(1, 1)  # SIGHUP to PID 1

        threading.Thread(target=_restart, daemon=True).start()

        return json.dumps({
            "status": "restarting",
            "message": "SIGHUP sent to uvicorn. Server will restart in ~1 second.",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Register tools ──────────────────────────────────────────────────

registry.register(
    name="shell_exec",
    toolset="hermes-debug",
    schema={
            "name": "shell_exec",
            "description": (
                "Execute a read-only shell command in the Hermes container. "
                "Allowed: curl, cat, grep, ls, find, head, tail, wc, env, ping. "
                "Blocked: rm, kill, docker, sudo, chmod, redirects (>), command substitution ($()). "
                "Use for debugging tools — reading logs, testing API connectivity, inspecting files."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute (must start with allowed prefix)",
                    },
                },
                "required": ["command"],
            },
        },
    handler=handle_shell_exec,
    check_fn=lambda: True,
    is_async=True,
    description="Execute a read-only shell command for debugging",
    emoji="🖥️",
)

registry.register(
    name="file_read",
    toolset="hermes-debug",
    schema={
            "name": "file_read",
            "description": (
                "Read a file from the Hermes container. "
                "Allowed paths: /opt/hermes/, /opt/data/, /tmp/. "
                "Use for inspecting tool code, SOUL.md, configuration, logs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to read",
                    },
                },
                "required": ["file_path"],
            },
        },
    handler=handle_file_read,
    check_fn=lambda: True,
    is_async=True,
    description="Read a file from the container filesystem",
    emoji="📄",
)

registry.register(
    name="api_debug",
    toolset="hermes-debug",
    schema={
            "name": "api_debug",
            "description": (
                "Make a raw HTTP request to the AIM API (app:8000) and return the full response. "
                "Use for debugging API endpoints — checking why a tool returned errors."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url_path": {
                        "type": "string",
                        "description": "API path, e.g. '/api/seo/audit/seo-audit-123'",
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method: GET or POST (default: GET)",
                        "enum": ["GET", "POST"],
                    },
                },
                "required": ["url_path"],
            },
        },
    handler=handle_api_debug,
    check_fn=lambda: True,
    is_async=True,
    description="Raw HTTP request to AIM API for debugging",
    emoji="🔧",
)

registry.register(
    name="file_write",
    toolset="hermes-debug",
    schema={
            "name": "file_write",
            "description": (
                "Write content to a file in the Hermes container. "
                "Allowed paths: /opt/hermes/, /opt/data/, /tmp/. "
                "Use for fixing tool code, updating SOUL.md, writing configuration. "
                "Set append=true to add to an existing file instead of overwriting "
                "(useful for multi-turn narrative assembly when LLM response size is bounded)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                    "append": {
                        "type": "boolean",
                        "description": (
                            "If true, append to the file instead of overwriting. "
                            "Default: false (overwrite)."
                        ),
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    handler=handle_file_write,
    check_fn=lambda: True,
    is_async=True,
    description="Write content to a file in the container",
    emoji="✏️",
)

registry.register(
    name="pip_install",
    toolset="hermes-debug",
    schema={
            "name": "pip_install",
            "description": (
                "Install a Python package into /opt/data/pip-packages/ (persistent volume). "
                "Packages survive container restarts. Use when you need a library that is not "
                "already installed — e.g., 'instagrapi' for Instagram, 'beautifulsoup4' for HTML parsing. "
                "After install, import the package directly in python3 -c commands."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "package": {
                        "type": "string",
                        "description": "Package name to install (e.g., 'instagrapi', 'beautifulsoup4')",
                    },
                },
                "required": ["package"],
            },
        },
    handler=handle_pip_install,
    check_fn=lambda: True,
    is_async=True,
    description="Install Python packages persistently",
    emoji="📦",
)

registry.register(
    name="restart_myself",
    toolset="hermes-debug",
    schema={
            "name": "restart_myself",
            "description": (
                "Gracefully restart the Hermes uvicorn server via SIGHUP. "
                "Use after: installing packages via pip_install, fixing tool code via file_write, "
                "or when Hermes is in a bad state and needs a fresh start."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    handler=handle_restart_myself,
    check_fn=lambda: True,
    is_async=True,
    description="Gracefully restart the Hermes uvicorn server",
    emoji="🔄",
)
