"""DeepSeek non-streaming proxy — bypasses CloudFront stream drops."""
import json, logging, os, sys, time
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("ds-proxy")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
LISTEN_PORT = int(os.getenv("PROXY_PORT", "11888"))

# Load API key from .env files (not runtime env)
API_KEY = ""
for p in ["/opt/data/.env", "/opt/hermes/.env"]:
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                if line.startswith("DEEPSEEK_API_KEY="):
                    API_KEY = line.strip().split("=", 1)[1].strip('"').strip("'")
                    break
    if API_KEY:
        break

if not API_KEY:
    logger.error("DEEPSEEK_API_KEY not found in .env files")
    sys.exit(1)

logger.info(f"Key loaded: {API_KEY[:8]}... ({len(API_KEY)} chars)")

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        req = json.loads(body)
        model = req.get("model", "deepseek-chat")
        messages = req.get("messages", [])
        max_tokens = req.get("max_tokens", 4096)
        t0 = time.time()
        logger.info(f"→ {len(messages)} msgs, model={model}")
        try:
            r = httpx.post(DEEPSEEK_URL, json={
                "model": model, "messages": messages,
                "max_tokens": max_tokens, "stream": False
            }, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, timeout=120.0)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            self.send_error(502, str(e)); return
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        finish = data["choices"][0].get("finish_reason", "stop")
        logger.info(f"← {len(content)} chars in {time.time()-t0:.1f}s")
        sse_id = data.get("id", f"proxy-{int(t0)}")
        sse = (f'data: {json.dumps({"id":sse_id,"object":"chat.completion.chunk","created":int(t0),"model":model,"choices":[{"index":0,"delta":{"content":content},"finish_reason":None}]})}\n\n'
               f'data: {json.dumps({"id":sse_id,"object":"chat.completion.chunk","created":int(t0),"model":model,"choices":[{"index":0,"delta":{},"finish_reason":finish}]})}\n\n'
               f'data: [DONE]\n\n')
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(sse.encode())

def main():
    HTTPServer(("127.0.0.1", LISTEN_PORT), ProxyHandler).serve_forever()

if __name__ == "__main__":
    main()
