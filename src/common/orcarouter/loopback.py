"""Flow A support: a loopback listener that receives the browser redirect.

DashGo serves the consent screen from the same host as the user's browser when
``DASH_SERVE_LOCALLY`` is true, so a loopback redirect is possible. This module is
only used for Flow A; Flow B needs no listener.

The listener binds ``127.0.0.1`` on an ephemeral port, answers the browser with a page
that tells the user they can close the tab, and compares ``state`` in constant time
before the code is allowed anywhere near the exchange.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlsplit

_CLOSE_PAGE = (
    b'<!doctype html><html><head><meta charset="utf-8"><title>OrcaRouter</title></head>'
    b'<body style="font-family:sans-serif;padding:2rem">'
    b'<h3>DashGo is connected to OrcaRouter.</h3>'
    b'<p>You can close this tab and return to DashGo.</p>'
    b'</body></html>'
)


class LoopbackReceiver:
    """A one-shot loopback HTTP listener for the Flow A callback."""

    def __init__(self):
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._done = threading.Event()
        self.result: dict = {}

    def start(self) -> int:
        """Bind and start serving. Returns the port the browser must call back on."""
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = parse_qs(urlsplit(self.path).query)
                receiver.result = {key: values[0] for key, values in query.items() if values}
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(_CLOSE_PAGE)))
                self.end_headers()
                self.wfile.write(_CLOSE_PAGE)

            def log_message(self, *args):  # keep the request line out of the project log
                return

        self._server = HTTPServer(('127.0.0.1', 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self._server.server_address[1]

    def callback_url(self) -> str:
        if self._server is None:
            raise RuntimeError('LoopbackReceiver.start() must be called first')
        return f'http://127.0.0.1:{self._server.server_address[1]}/cb'

    def wait(self, timeout: float = 300.0) -> Optional[dict]:
        """Block until the browser calls back, or ``None`` on timeout."""
        deadline = timeout
        step = 0.2
        waited = 0.0
        while waited < deadline:
            if self.result:
                return self.result
            self._done.wait(timeout=step)
            waited += step
        return None

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        self._done.set()

    def __enter__(self) -> LoopbackReceiver:
        self.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self.stop()
