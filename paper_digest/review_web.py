"""Serve a local review window using the existing locked decision ledger."""

import json
import logging
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import cast

from paper_digest.storage import locked_storage

logger = logging.getLogger(__name__)
ASSET_DIR = Path(__file__).with_name("web")


class ReviewServer(ThreadingHTTPServer):
    """Bind one review session to loopback and a fixed set of pending paper IDs."""

    def __init__(self, state_file: Path) -> None:
        self.state_file: Path = state_file
        self.token: str = secrets.token_urlsafe(32)
        self.paper_ids: list[str] = []
        if state_file.exists():
            with locked_storage(state_file) as storage:
                self.paper_ids = [
                    item_id for item_id, record in storage.state["papers"].items()
                    if record["decision"] == "pending"
                ]
        super().__init__(("127.0.0.1", 0), ReviewHandler)
        self.origin: str = f"http://127.0.0.1:{self.server_port}"


class ReviewHandler(BaseHTTPRequestHandler):
    """Expose only bundled assets and authenticated local review operations."""

    timeout = 10

    @property
    def review(self) -> ReviewServer:
        """Return the application server with its session state."""
        return cast(ReviewServer, self.server)

    def log_message(self, format: str, *args: object) -> None:
        """Keep routine browser requests out of the review terminal."""
        logger.debug(format, *args)

    def _respond(self, status: int, body: bytes, content_type: str) -> None:
        """Send an uncached response with a local-only content policy."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: object) -> None:
        """Serialize a response without embedding source metadata into HTML."""
        self._respond(status, json.dumps(data).encode(), "application/json")

    def _authorized(self, api: bool = False) -> bool:
        """Reject foreign hosts/origins and require the session token for data."""
        if (self.headers.get("Host") != self.review.origin.removeprefix("http://")
                or self.headers.get("Origin", self.review.origin) != self.review.origin):
            self._json(403, {"error": "This window is available only on its local URL."})
            return False
        if api and not secrets.compare_digest(
            self.headers.get("X-Review-Token", "").encode(), self.review.token.encode()
        ):
            self._json(403, {"error": "Open the full review URL printed in the terminal."})
            return False
        return True

    def do_GET(self) -> None:
        """Read this session's papers or serve a bundled page asset."""
        if not self._authorized(api=self.path == "/api/papers"):
            return
        if self.path == "/favicon.ico":
            self._respond(204, b"", "image/x-icon")
            return
        if self.path == "/api/papers":
            try:
                papers: list[dict[str, object]] = []
                if self.review.state_file.exists():
                    with locked_storage(self.review.state_file) as storage:
                        for number, item_id in enumerate(self.review.paper_ids, 1):
                            record = storage.state["papers"].get(item_id)
                            if record:
                                papers.append({
                                    "id": item_id, "number": number,
                                    "decision": record["decision"], **record["paper"],
                                })
                self._json(200, {"papers": papers})
            except (OSError, ValueError, RuntimeError) as exc:
                logger.exception("Cannot read review papers")
                self._json(409, {"error": str(exc)})
            return
        assets = {
            "/": ("review.html", "text/html; charset=utf-8"),
            "/review.css": ("review.css", "text/css; charset=utf-8"),
            "/review.js": ("review.js", "text/javascript; charset=utf-8"),
        }
        if self.path not in assets:
            self._json(404, {"error": "Not found"})
            return
        name, content_type = assets[self.path]
        try:
            self._respond(200, (ASSET_DIR / name).read_bytes(), content_type)
        except OSError:
            logger.exception("Cannot read review asset: %s", name)
            self._json(500, {"error": "Cannot load the review window files."})

    def do_POST(self) -> None:
        """Validate the complete selection, then save each explicit decision."""
        if not self._authorized(api=True):
            return
        if self.path != "/api/decisions":
            self._json(404, {"error": "Not found"})
            return
        saved: list[dict[str, str]] = []
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1_048_576:
                raise ValueError("Invalid request size")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected JSON decisions")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not isinstance(payload.get("decisions"), list):
                raise ValueError("Expected a list of decisions")
            decisions: dict[str, str] = {}
            for choice in payload["decisions"]:
                if not isinstance(choice, dict):
                    raise ValueError("Invalid decision")
                item_id, decision = choice.get("id"), choice.get("decision")
                if (not isinstance(item_id, str) or item_id not in self.review.paper_ids
                        or item_id in decisions or not isinstance(decision, str)
                        or decision not in {"accepted", "skipped"}):
                    raise ValueError("Invalid, duplicate, or out-of-session paper choice")
                decisions[item_id] = decision
        except (ValueError, UnicodeError) as exc:
            self._json(400, {"error": str(exc), "saved": saved})
            return
        if not decisions:
            self._json(200, {"saved": saved})
            return
        try:
            if not self.review.state_file.exists():
                raise RuntimeError("The paper ledger is missing; no decisions were saved.")
            with locked_storage(self.review.state_file) as storage:
                # Check every choice before writing, so a stale tab cannot overwrite
                # a different decision made in another window or via the CLI.
                for item_id, decision in decisions.items():
                    record = storage.state["papers"].get(item_id)
                    if not record or record["decision"] not in {"pending", decision}:
                        raise RuntimeError(
                            f"{item_id} changed since this review opened. "
                            "Reload before choosing again; this batch was not saved."
                        )
                for item_id, decision in decisions.items():
                    if storage.state["papers"][item_id]["decision"] != decision:
                        storage.decide(item_id, decision)
                    saved.append({"id": item_id, "decision": decision})
            self._json(200, {"saved": saved})
        except (OSError, ValueError, RuntimeError) as exc:
            logger.exception("Cannot save review decisions")
            # Each existing decide() call is atomic. Report the completed prefix
            # if a later write fails, so the page never claims a full batch saved.
            self._json(409, {"error": str(exc), "saved": saved})


def serve_review(state_file: Path, open_browser: bool = True) -> int:
    """Run a loopback review session until Ctrl+C, without fetching any sources."""
    with ReviewServer(state_file) as server:
        if not server.paper_ids:
            print("No pending papers to review.")
            return 0
        url = f"{server.origin}/#{server.token}"
        print(f"Review {len(server.paper_ids)} pending papers: {url}", flush=True)
        print("Keep this process running while reviewing. Press Ctrl+C to stop.", flush=True)
        if open_browser:
            try:
                if not webbrowser.open(url):
                    print("Open the URL above in your browser.", flush=True)
            except webbrowser.Error:
                logger.exception("Cannot open browser; use the printed review URL")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nReview window stopped. Saved decisions are retained.")
    return 0
