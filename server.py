#!/usr/bin/env python3
"""Self-contained interactive Enigma encrypt/decrypt web app."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from machine import Enigma

HOST = "0.0.0.0"
PORT = 8790


def build_machine(key, swaps, rotor_order):
    swaps_list = None
    if swaps:
        swaps_list = [s.strip().upper() for s in swaps if s.strip()]
    return Enigma(key=key.upper(), swaps=swaps_list, rotor_order=rotor_order)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
            return
        self._send(404, '{"error":"not found"}')

    def do_POST(self):
        if self.path != "/api/process":
            self._send(404, '{"error":"not found"}')
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send(400, '{"error":"invalid json"}')
            return
        message = payload.get("message", "")
        key = payload.get("key", "AAA")
        swaps = payload.get("swaps", [])
        rotor_order = payload.get("rotor_order", ["I", "II", "III"])
        if len(key) != 3 or not key.isalpha():
            self._send(400, '{"error":"key must be 3 letters"}')
            return
        try:
            enigma = build_machine(key, swaps, rotor_order)
            result = enigma.encipher(message)
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}))
            return
        self._send(200, json.dumps({"result": result}))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Enigma app running at http://127.0.0.1:{PORT}/")
    httpd.serve_forever()
