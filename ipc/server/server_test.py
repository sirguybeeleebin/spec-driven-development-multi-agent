import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest

from ipc.server import IPCServer


def test_start_creates_socket_and_submits_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    socket_path = tmp_path / ".sddma" / "ipc.sock"
    socket_path.parent.mkdir(parents=True)
    socket_path.touch()

    connection = Mock()
    executor = Mock()
    server_socket = Mock()

    class StopServerError(Exception):
        pass

    server_socket.accept.side_effect = [
        (connection, None),
        StopServerError,
    ]

    server_socket.__enter__ = Mock(return_value=server_socket)
    server_socket.__exit__ = Mock(return_value=False)

    socket_factory = Mock(return_value=server_socket)
    monkeypatch.setattr(socket, "socket", socket_factory)

    server = IPCServer(
        socket_path=socket_path,
        handler=Mock(),
        executor=executor,
    )

    with pytest.raises(StopServerError):
        server.start()

    socket_factory.assert_called_once_with(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )
    server_socket.bind.assert_called_once_with(str(socket_path))
    server_socket.listen.assert_called_once_with()
    executor.submit.assert_called_once_with(server.handle, connection)
    assert not socket_path.exists()


def test_handle_processes_command_and_sends_response() -> None:
    command = {"type": "task", "task": "Implement feature"}
    response = {"status": "success"}

    handler = Mock(return_value=response)

    server = IPCServer(
        socket_path=Path("/tmp/ipc.sock"),
        handler=handler,
        executor=ThreadPoolExecutor(max_workers=1),
    )

    client, connection = socket.socketpair()

    try:
        client.sendall(json.dumps(command).encode("utf-8"))

        server.handle(connection)

        received = client.recv(65536)

        handler.assert_called_once_with(command)
        assert json.loads(received) == response
    finally:
        client.close()


def test_handle_ignores_empty_message() -> None:
    handler = Mock()

    server = IPCServer(
        socket_path=Path("/tmp/ipc.sock"),
        handler=handler,
        executor=ThreadPoolExecutor(max_workers=1),
    )

    client, connection = socket.socketpair()

    try:
        client.shutdown(socket.SHUT_WR)

        server.handle(connection)

        handler.assert_not_called()
    finally:
        client.close()
