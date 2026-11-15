
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol


class Handler(Protocol):
    def handle(self, command: dict) -> dict: ...


class IPCServer:
    MAX_MESSAGE_SIZE = 65536

    def __init__(
        self,
        *,
        socket_path: Path,
        task_handler: Handler,
        workflow_handler: Handler,
        task_section_handler: Handler,
        executor: ThreadPoolExecutor,
    ) -> None:
        self.socket_path = socket_path
        self.handlers = {
            "task": task_handler,
            "workflow": workflow_handler,
            "task_section": task_section_handler,
        }
        self.executor = executor

    def start(self) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        if self.socket_path.exists():
            self.socket_path.unlink()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(self.socket_path))
            server.listen()

            while True:
                connection, _ = server.accept()
                self.executor.submit(self.handle, connection)

    def handle(self, connection: socket.socket) -> None:
        with connection:
            try:
                chunks = []
                size = 0

                while message := connection.recv(4096):
                    size += len(message)

                    if size > self.MAX_MESSAGE_SIZE:
                        raise ValueError("Command exceeds maximum size")

                    chunks.append(message)

                command = json.loads(b"".join(chunks))

                if not isinstance(command, dict):
                    raise ValueError("Command must be a JSON object")

                handler = self.handlers[command["type"]]
                result = handler.handle(command)

                if not isinstance(result, dict):
                    raise TypeError("Handler must return a dictionary")

            except Exception as error:
                result = {"error": str(error)}

            connection.sendall(json.dumps(result).encode("utf-8"))
