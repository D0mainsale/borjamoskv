import sys
import socket
import os
import signal
import json
import logging
import time
from typing import Final

SOCKET_PATH: Final[str] = os.environ.get("CORTEX_SOCKET_PATH", "/tmp/cortex_swarm.sock")
MAX_DGRAM_SIZE: Final[int] = int(os.environ.get("CORTEX_MAX_DGRAM_SIZE", "65535"))
SOCKET_MODE: Final[int] = int(os.environ.get("CORTEX_SOCKET_MODE", "660"), 8)

logger = logging.getLogger("cortex_uds_forwarder")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    class JsonlFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            return json.dumps(
                {
                    "timestamp": time.time(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                },
                ensure_ascii=False,
            )

    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(JsonlFormatter())
    logger.addHandler(ch)


class StatelessCortexDaemon:
    """
    Stateless UDS datagram forwarder.
    Receives opaque bytes and forwards them to stdout.buffer.
    """

    def __init__(self) -> None:
        self._running = True
        self.server: socket.socket | None = None

        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.server.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, SOCKET_MODE)

    def start(self) -> int:
        logger.info("Stateless Swarm UDS Forwarder active.")

        try:
            while self._running:
                assert self.server is not None
                try:
                    data = self.server.recv(MAX_DGRAM_SIZE)
                    if not data:
                        continue

                    # Si el contrato downstream es line-delimited, deja el newline.
                    # Si no, cambia a write(data).
                    sys.stdout.buffer.write(data + b"\n")
                    sys.stdout.buffer.flush()

                except BrokenPipeError:
                    logger.error("stdout pipe closed. Stopping forwarder.")
                    self._running = False

                except OSError as e:
                    if self._running:
                        logger.error(f"UDS packet drop: {e}")

                except Exception as e:
                    logger.error(f"Unexpected forwarder error: {e}")

        finally:
            self._cleanup()

        return 0

    def stop(self) -> None:
        logger.info("Stopping UDS forwarder.")
        self._running = False
        if self.server is not None:
            try:
                self.server.close()
            except Exception:
                pass

    def _cleanup(self) -> None:
        if self.server is not None:
            try:
                self.server.close()
            except Exception:
                pass
            self.server = None

        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except OSError:
                pass


daemon: StatelessCortexDaemon | None = None


def _handle_signal(signum: int, frame) -> None:
    global daemon
    if daemon is not None:
        daemon.stop()


if __name__ == "__main__":
    daemon = StatelessCortexDaemon()
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    raise SystemExit(daemon.start())
