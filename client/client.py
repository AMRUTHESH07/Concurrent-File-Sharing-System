import socket
import json
import os
import getpass

HOST = "127.0.0.1"
PORT = 5001
BUFFER_SIZE = 4096


class FileSharingClient:
    def __init__(self, host, port):
        self.socket = socket.create_connection((host, port))
        self.stream = self.socket.makefile("rb")
        self.username = None

    def send_request(self, request):
        self.socket.sendall(
            (json.dumps(request) + "\n").encode("utf-8")
        )
        line = self.stream.readline()

        if not line:
            raise ConnectionError("Server disconnected")

        return json.loads(line.decode("utf-8"))

    def register(self):
        username = input("Choose username: ")
        password = getpass.getpass("Choose password: ")

        response = self.send_request({
            "command": "REGISTER",
            "username": username,
            "password": password
        })

        print(response)

    def login(self):
        username = input("Username: ")
        password = getpass.getpass("Password: ")

        response = self.send_request({
            "command": "LOGIN",
            "username": username,
            "password": password
        })

        print(response)

        if response["status"] == "success":
            self.username = username
            return True

        return False

    def upload(self):
        path = input("Enter file path: ").strip()

        if not os.path.isfile(path):
            print("File does not exist.")
            return

        filename = os.path.basename(path)
        filesize = os.path.getsize(path)

        response = self.send_request({
            "command": "UPLOAD",
            "filename": filename,
            "filesize": filesize
        })

        if response["status"] != "ready":
            print(response)
            return

        with open(path, "rb") as source:
            while True:
                chunk = source.read(BUFFER_SIZE)

                if not chunk:
                    break

                self.socket.sendall(chunk)

        result = self.stream.readline()
        if not result:
            raise ConnectionError("Server disconnected during upload")

        print(json.loads(result.decode("utf-8")))

    def download(self):
        try:
            file_id = int(input("Enter file ID: "))
        except ValueError:
            print("Invalid file ID.")
            return

        response = self.send_request({
            "command": "DOWNLOAD",
            "file_id": file_id
        })

        if response["status"] != "ready":
            print(response)
            return

        filename = os.path.basename(response["filename"])
        filesize = response["filesize"]

        destination = input(
            f"Save as [{filename}]: "
        ).strip() or filename

        destination = os.path.abspath(destination)
        temp_path = destination + ".part"

        remaining = filesize

        try:
            with open(temp_path, "wb") as output:
                while remaining > 0:
                    chunk = self.stream.read(
                        min(BUFFER_SIZE, remaining)
                    )

                    if not chunk:
                        raise ConnectionError("Download interrupted")

                    output.write(chunk)
                    remaining -= len(chunk)

            os.replace(temp_path, destination)

            print(f"Download successful: {destination}")
            print(f"Downloaded {filesize} bytes.")

        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def list_files(self):
        response = self.send_request({
            "command": "LIST"
        })

        if response["status"] != "success":
            print(response)
            return

        files = response["files"]

        if not files:
            print("No files available.")
            return

        print("\nAvailable files:")
        print("-" * 85)
        print(f"{'ID':<8}{'Filename':<30}{'Size':<15}{'Uploader'}")
        print("-" * 85)

        for file in files:
            print(
                f"{file['id']:<8}"
                f"{file['filename']:<30}"
                f"{file['filesize']:<15}"
                f"{file['uploaded_by']}"
            )

        print("-" * 85)

    def close(self):
        try:
            self.socket.sendall(
                (json.dumps({"command": "EXIT"}) + "\n").encode()
            )
        except OSError:
            pass

        self.stream.close()
        self.socket.close()


def main():
    client = None

    try:
        client = FileSharingClient(HOST, PORT)
        print("Connected to Concurrent File Sharing Server.")

        while True:
            print("\n1. Register")
            print("2. Login")
            choice = input("Select option: ").strip()

            if choice == "1":
                client.register()
            elif choice == "2":
                if client.login():
                    break
            else:
                print("Invalid option.")

        while True:
            print("\n===== FILE SHARING MENU =====")
            print("1. Upload file")
            print("2. Download file")
            print("3. List files")
            print("4. Exit")

            choice = input("Select option: ").strip()

            if choice == "1":
                client.upload()
            elif choice == "2":
                client.download()
            elif choice == "3":
                client.list_files()
            elif choice == "4":
                print("Exiting client.")
                break
            else:
                print("Invalid option.")

    except (ConnectionError, OSError, json.JSONDecodeError) as error:
        print(f"Client error: {error}")

    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
