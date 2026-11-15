import json
import socket
from pathlib import Path


class IPCClient:
    def __init__(self, *, socket_path: Path) -> None:
        self.socket_path = socket_path
        self.connection: socket.socket | None = None

    def connect(self) -> None:
        self.connection = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        )
        self.connection.connect(str(self.socket_path))

    def send(self, command: dict) -> dict:
        if self.connection is None:
            raise RuntimeError("IPC Client is not connected")

        self.connection.sendall(json.dumps(command).encode("utf-8"))

        response = self.connection.recv(65536)

        return json.loads(response)

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None
