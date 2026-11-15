import json
import socket
import threading

import pytest

from database import auth, db
from server import server


@pytest.fixture
def test_environment(tmp_path, monkeypatch):
    test_db_path = str(tmp_path / "test_server.db")
    storage_path = tmp_path / "uploaded_files"
    storage_path.mkdir()

    monkeypatch.setattr(auth, "DB_PATH", test_db_path)
    monkeypatch.setattr(db, "DB_PATH", test_db_path)
    monkeypatch.setattr(server, "STORAGE_DIR", str(storage_path))

    auth.initialize_auth_database()
    db.initialize_database()

    return storage_path


@pytest.fixture
def connected_client():
    server_socket, client_socket = socket.socketpair()

    thread = threading.Thread(
        target=server.handle_client,
        args=(server_socket, ("local-test", 0)),
        daemon=True
    )
    thread.start()

    client_file = client_socket.makefile("rb")

    yield client_socket, client_file

    try:
        client_socket.sendall(b'{"command": "EXIT"}\n')
        client_socket.shutdown(socket.SHUT_WR)
    except OSError:
        pass

    thread.join(timeout=3)
    client_file.close()
    client_socket.close()


def send_request(client_socket, client_file, request):
    client_socket.sendall(
        (json.dumps(request) + "\n").encode()
    )
    response = client_file.readline()
    return json.loads(response.decode())


def test_unauthenticated_client_cannot_list_files(
    test_environment, connected_client
):
    client_socket, client_file = connected_client

    response = send_request(
        client_socket,
        client_file,
        {"command": "LIST"}
    )

    assert response["status"] == "error"
    assert response["message"] == "Please login first"


def test_authenticated_upload_list_download(
    test_environment, connected_client
):
    client_socket, client_file = connected_client

    # Register user
    response = send_request(
        client_socket,
        client_file,
        {
            "command": "REGISTER",
            "username": "alice",
            "password": "Password123"
        }
    )

    assert response["status"] == "success"

    # Login
    response = send_request(
        client_socket,
        client_file,
        {
            "command": "LOGIN",
            "username": "alice",
            "password": "Password123"
        }
    )

    assert response["status"] == "success"

    # Upload file
    content = b"Integration test file content"

    client_socket.sendall(
        (
            json.dumps({
                "command": "UPLOAD",
                "filename": "integration.txt",
                "filesize": len(content)
            }) + "\n"
        ).encode()
    )

    ready_response = json.loads(
        client_file.readline().decode()
    )

    assert ready_response["status"] == "ready"

    client_socket.sendall(content)

    upload_response = json.loads(
        client_file.readline().decode()
    )

    assert upload_response["status"] == "success"

    file_id = upload_response["file_id"]

    # List files
    list_response = send_request(
        client_socket,
        client_file,
        {"command": "LIST"}
    )

    assert list_response["status"] == "success"
    assert any(
        item["id"] == file_id
        for item in list_response["files"]
    )

    # Download file
    client_socket.sendall(
        (
            json.dumps({
                "command": "DOWNLOAD",
                "file_id": file_id
            }) + "\n"
        ).encode()
    )

    download_response = json.loads(
        client_file.readline().decode()
    )

    assert download_response["status"] == "ready"
    assert download_response["filesize"] == len(content)

    downloaded_content = client_file.read(len(content))

    assert downloaded_content == content


def test_invalid_upload_is_rejected(
    test_environment, connected_client
):
    client_socket, client_file = connected_client

    # Register and login
    send_request(
        client_socket,
        client_file,
        {
            "command": "REGISTER",
            "username": "bob",
            "password": "Password123"
        }
    )

    send_request(
        client_socket,
        client_file,
        {
            "command": "LOGIN",
            "username": "bob",
            "password": "Password123"
        }
    )

    # Attempt upload with invalid file size
    response = send_request(
        client_socket,
        client_file,
        {
            "command": "UPLOAD",
            "filename": "invalid.txt",
            "filesize": -1
        }
    )

    assert response["status"] == "error"
    assert response["message"] == "Invalid file details"
