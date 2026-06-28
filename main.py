import json
import os
import sys
import threading
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from bot import run_bot
from config import config_exists, from_env

PORT = int(os.environ.get("PORT", 8080))
CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")

SETUP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bot Setup</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: -apple-system, sans-serif; max-width: 460px; margin: 60px auto; padding: 0 20px; background: #f5f5f5; }
    .card { background: #fff; padding: 32px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
    h1 { font-size: 22px; margin: 0 0 24px; color: #222; }
    label { display: block; font-size: 14px; font-weight: 600; margin: 16px 0 4px; color: #333; }
    input { width: 100%; padding: 10px 12px; font-size: 15px; border: 1px solid #ccc; border-radius: 6px; }
    input:focus { outline: none; border-color: #0088cc; box-shadow: 0 0 0 2px rgba(0,136,204,.15); }
    .hint { font-size: 12px; color: #888; margin: 2px 0 0; }
    button { width: 100%; margin-top: 24px; padding: 12px; font-size: 15px; font-weight: 600;
             background: #0088cc; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:hover { background: #0077b3; }
    .error { color: #d32f2f; font-size: 13px; margin-top: 8px; }
    .success { color: #2e7d32; font-size: 13px; margin-top: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Telegram API Bot Setup</h1>
    <form method="POST" action="/save" id="form">
      <label for="bot_token">Bot Token</label>
      <input type="text" id="bot_token" name="bot_token" placeholder="123456:ABCdef..." required>
      <p class="hint">From @BotFather on Telegram</p>
      <label for="admin_id">Admin User ID</label>
      <input type="text" id="admin_id" name="admin_id" placeholder="123456789" required>
      <p class="hint">Your Telegram user ID (numeric)</p>
      <button type="submit">Save &amp; Start Bot</button>
    </form>
    <div id="msg"></div>
  </div>
  <script>
    document.getElementById("form").onsubmit = async function(e) {
      e.preventDefault();
      const fd = new FormData(this);
      const data = new URLSearchParams(fd);
      const res = await fetch("/save", { method: "POST", body: data });
      const text = await res.text();
      document.getElementById("msg").innerHTML = text;
    };
  </script>
</body>
</html>"""


class SetupHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self._send(200, SETUP_HTML, "text/html")
        else:
            self._send(404, "Not Found", "text/plain")

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(body)
            bot_token = params.get("bot_token", [""])[0].strip()
            admin_id = params.get("admin_id", [""])[0].strip()

            if not bot_token or not admin_id:
                self._send(400, '<p class="error">Both fields are required.</p>', "text/html")
                return

            try:
                int(admin_id)
            except ValueError:
                self._send(400, '<p class="error">Admin ID must be a number.</p>', "text/html")
                return

            with open(CONFIG_FILE, "w") as f:
                json.dump({"bot_token": bot_token, "admin_id": int(admin_id)}, f)

            self._send(200, '<p class="success">Saved! Starting bot...</p>', "text/html")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self._send(404, "Not Found", "text/plain")

    def _send(self, status, content, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.end_headers()
        if isinstance(content, str):
            content = content.encode()
        self.wfile.write(content)

    def log_message(self, fmt, *args):
        pass


def start_setup_server():
    server = HTTPServer(("0.0.0.0", PORT), SetupHandler)
    print(f"\n{'='*50}")
    print(f"SETUP UI: http://0.0.0.0:{PORT}")
    print(f"Open this URL in your browser to configure the bot.")
    print(f"{'='*50}\n")
    sys.stdout.flush()
    server.serve_forever()


def main():
    env_config = from_env()
    if env_config:
        run_bot()
        return

    if config_exists():
        run_bot()
        return

    t = threading.Thread(target=start_setup_server, daemon=True)
    t.start()

    while not config_exists():
        time.sleep(1)

    print("Config saved. Starting bot...")
    time.sleep(0.5)
    run_bot()


if __name__ == "__main__":
    main()
