# Concurrent File Sharing System Using Software-Defined Networking

## 1. Project Overview

The Concurrent File Sharing System is a Python-based file-sharing application
that allows multiple authenticated clients to upload, download, and list files
through a TCP server.

The application uses multithreading to handle concurrent client connections
and SQLite to store user credentials and file metadata.

Software-Defined Networking (SDN) is integrated using Mininet, Open vSwitch,
and an OS-Ken controller. The controller manages network forwarding,
implements traffic access policies, and monitors network traffic statistics.

## 2. Objectives

- Develop a TCP-based file-sharing application.
- Support multiple simultaneous client connections.
- Implement user registration and authentication.
- Store file metadata and user credentials in SQLite.
- Support file upload, download, and listing.
- Integrate an SDN controller using OpenFlow 1.3.
- Implement network-level traffic access control.
- Monitor network traffic statistics.
- Evaluate performance under concurrent transfers.

## 3. System Architecture

The project consists of the following components:

### Client
- Python socket-based client application.
- Provides registration and login.
- Supports file upload and download.
- Displays available file metadata.

### File Server
- Uses TCP sockets.
- Handles multiple clients using Python threads.
- Checks authentication before file operations.
- Stores uploaded files on the server.
- Generates unique physical filenames to avoid collisions.

### Database
- SQLite database.
- Stores registered users.
- Stores password salts and password hashes.
- Stores file metadata, uploader information, and upload timestamps.

### SDN Controller
- Implemented using OS-Ken.
- Communicates with Open vSwitch using OpenFlow 1.3.
- Installs table-miss and forwarding rules.
- Implements IP-address and TCP-port-based access control.
- Collects flow statistics.

### SDN Network
- Mininet provides the virtual network.
- Two hosts, h1 and h2, connect through switch s1.
- Open vSwitch connects to the remote controller.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| TCP sockets | Client-server communication |
| Threading | Concurrent client handling |
| SQLite | Database management |
| PBKDF2-HMAC-SHA256 | Password hashing |
| OS-Ken | SDN controller |
| Open vSwitch | Software switch |
| OpenFlow 1.3 | Controller-switch communication |
| Mininet | Virtual network emulation |
| pytest | Automated testing |
| pandas | Performance data analysis |
| matplotlib | Performance visualization |

## 5. Project Structure

```text
Concurrent_File_Sharing_System/
|
|-- client/
|   |-- client.py
|
|-- server/
|   |-- server.py
|
|-- database/
|   |-- auth.py
|   |-- db.py
|   |-- files.db
|
|-- sdn/
|   |-- controller.py
|   |-- run_controller.py
|
|-- storage/
|   |-- uploaded_files/
|
|-- tests/
|   |-- test_database.py
|   |-- test_server.py
|
|-- results/
|   |-- performance_results.csv
|   |-- concurrent_throughput.png
|   |-- generate_graph.py
|
|-- documentation/
|
|-- README.md

