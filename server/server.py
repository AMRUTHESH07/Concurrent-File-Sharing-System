import socket
import threading
import os
import json
import uuid

from database.db import (
    initialize_database,
    add_file,
    get_file_by_id,
    list_files
)

from database.auth import (
    initialize_auth_database,
    register_user,
    login_user
)

HOST = "0.0.0.0"
PORT = 5001
STORAGE_DIR = "storage/uploaded_files"

MAX_FILE_SIZE = 1024 ** 3

os.makedirs(STORAGE_DIR, exist_ok=True)


def send_json(conn, response):
    conn.sendall((json.dumps(response) + "\n").encode())


def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")

    client_file = conn.makefile("rb")
    authenticated_user = None

    try:
        while True:
            line = client_file.readline()

            if not line:
                break

            request = json.loads(line.decode("utf-8"))
            command = request.get("command")

            # REGISTRATION
            if command == "REGISTER":
                success, message = register_user(
                    request.get("username", ""),
                    request.get("password", "")
                )

                send_json(conn, {
                    "status": "success" if success else "error",
                    "message": message
                })

            # LOGIN
            elif command == "LOGIN":
                username = request.get("username", "")
                password = request.get("password", "")

                if login_user(username, password):
                    authenticated_user = username

                    print(f"[LOGIN SUCCESS] {username}")

                    send_json(conn, {
                        "status": "success",
                        "message": "Login successful"
                    })
                else:
                    send_json(conn, {
                        "status": "error",
                        "message": "Invalid username or password"
                    })

            # FILE OPERATIONS
            elif command in ("UPLOAD", "DOWNLOAD", "LIST"):

                if authenticated_user is None:
                    send_json(conn, {
                        "status": "error",
                        "message": "Please login first"
                    })
                    continue

                # UPLOAD
                if command == "UPLOAD":
                    filename = os.path.basename(
                        request.get("filename", "")
                    )

                    try:
                        filesize = int(request.get("filesize", -1))
                    except (TypeError, ValueError):
                        filesize = -1

                    if (
                        not filename
                        or filename in (".", "..")
                        or filesize < 0
                        or filesize > MAX_FILE_SIZE
                    ):
                        send_json(conn, {
                            "status": "error",
                            "message": "Invalid file details"
                        })
                        continue

                    # Generate a unique physical filename.
                    unique_name = f"{uuid.uuid4().hex}_{filename}"

                    filepath = os.path.join(
                        STORAGE_DIR,
                        unique_name
                    )

                    temp_path = filepath + ".part"

                    send_json(conn, {"status": "ready"})

                    remaining = filesize

                    try:
                        with open(temp_path, "wb") as output:
                            while remaining > 0:
                                chunk = client_file.read(
                                    min(4096, remaining)
                                )

                                if not chunk:
                                    raise ConnectionError(
                                        "Upload interrupted"
                                    )

                                output.write(chunk)
                                remaining -= len(chunk)

                        os.replace(temp_path, filepath)

                        file_id = add_file(
                            filename,
                            filesize,
                            filepath,
                            authenticated_user
                        )

                    except Exception:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        raise

                    print(
                        f"[UPLOAD COMPLETE] ID={file_id} "
                        f"FILE={filename} USER={authenticated_user}"
                    )

                    send_json(conn, {
                        "status": "success",
                        "message": "Upload complete",
                        "file_id": file_id,
                        "filename": filename
                    })

                # DOWNLOAD USING FILE ID
                elif command == "DOWNLOAD":
                    try:
                        file_id = int(request.get("file_id", -1))
                    except (TypeError, ValueError):
                        file_id = -1

                    file = get_file_by_id(file_id)

                    if file is None or not os.path.isfile(file[3]):
                        send_json(conn, {
                            "status": "error",
                            "message": "File not found"
                        })
                        continue

                    _, filename, filesize, filepath, uploaded_by, _ = file

                    send_json(conn, {
                        "status": "ready",
                        "file_id": file_id,
                        "filename": filename,
                        "filesize": filesize
                    })

                    with open(filepath, "rb") as source:
                        while True:
                            chunk = source.read(4096)

                            if not chunk:
                                break

                            conn.sendall(chunk)

                    print(
                        f"[DOWNLOAD COMPLETE] ID={file_id} "
                        f"FILE={filename} USER={authenticated_user}"
                    )

                # LIST FILES
                elif command == "LIST":
                    files = list_files()

                    send_json(conn, {
                        "status": "success",
                        "files": [
                            {
                                "id": row[0],
                                "filename": row[1],
                                "filesize": row[2],
                                "uploaded_by": row[3],
                                "upload_time": row[4]
                            }
                            for row in files
                        ]
                    })

            elif command == "EXIT":
                break

            else:
                send_json(conn, {
                    "status": "error",
                    "message": "Unknown command"
                })

    except Exception as error:
        print(f"[ERROR] {addr}: {error}")

    finally:
        client_file.close()
        conn.close()
        print(f"[DISCONNECTED] {addr}")


def start_server():
    initialize_database()
    initialize_auth_database()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            )

            thread.start()

    except KeyboardInterrupt:
        print("\n[SERVER SHUTTING DOWN]")

    finally:
        server.close()


if __name__ == "__main__":
    start_server()
