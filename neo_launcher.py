#!/usr/bin/env python3
"""Launch the Neo AI Terminal server and open the local dashboard."""
import os
import threading
import time
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"

def open_when_ready():
    for _ in range(100):
        try:
            with urllib.request.urlopen(URL + "/api/health", timeout=1):
                webbrowser.open(URL)
                return
        except Exception:
            time.sleep(0.25)

def main():
    if os.environ.get("NEO_SKIP_AUTO_OPEN") != "1":
        threading.Thread(target=open_when_ready, daemon=True).start()
    import uvicorn
    from web_app import app
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

if __name__ == "__main__":
    main()
