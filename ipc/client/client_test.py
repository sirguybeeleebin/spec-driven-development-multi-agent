import json
import socket
from pathlib import Path
from unittest.mock import Mock

import pytest

import ipc.client.client as ipc_client_module
from ipc.client import IPCClient


def test_connect_creates_and_connects_socket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    socket_path = tmp_path / ".sddma" / "ipc.sock"
    connection = Mock()
    socket_factory = Mock(return_value=connection)

    monkeypatch.setattr(
        ipc_client_module.socket,
        "socket",
        socket_factory,
    )

    client = IPCClient(socket_path=socket_path)
    client.connect()

    socket_factory.assert_called_once_with(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )
    connection.connect.assert_called_once_with(str(socket_path))
    assert client.connection is connection


def test_send_sends_command_and_returns_response() -> None:
    command = {"type": "task", "task": "Implement feature"}
    response = {"status": "success"}

    connection = Mock()
    connection.recv.return_value = json.dumps(response).encode("utf-8")

    client = IPCClient(socket_path=Path("/tmp/ipc.sock"))
    client.connection = connection

    result = client.send(command)

    connection.sendall.assert_called_once_with(
        json.dumps(command).encode("utf-8"),
    )
    connection.recv.assert_called_once_with(65536)
    assert result == response


def test_send_raises_error_when_not_connected() -> None:
    client = IPCClient(socket_path=Path("/tmp/ipc.sock"))

    with pytest.raises(RuntimeError, match="IPC Client is not connected"):
        client.send({"type": "task"})


def test_close_closes_connection() -> None:
    connection = Mock()

    client = IPCClient(socket_path=Path("/tmp/ipc.sock"))
    client.connection = connection

    client.close()

    connection.close.assert_called_once_with()
    assert client.connection is None


def test_close_does_nothing_when_not_connected() -> None:
    client = IPCClient(socket_path=Path("/tmp/ipc.sock"))

    client.close()

    assert client.connection is None
