# Concurrent File Sharing System Using Software-Defined Networking

## 1. Abstract

This project implements a concurrent file-sharing system integrated with Software-Defined Networking (SDN). It allows authenticated users to upload, download, and list files through a TCP-based client-server application.

The server supports concurrent client connections using threading and stores file metadata in an SQLite database. Passwords are securely hashed using PBKDF2-HMAC-SHA256.

The SDN component uses the OS-Ken controller and OpenFlow 1.3 to manage network forwarding and apply traffic policies. The system was tested using Mininet with two hosts connected through an Open vSwitch.

## 2. Introduction

File sharing is an important function in computer networks. Traditional file-sharing systems may face challenges when multiple clients access the server simultaneously.

This project addresses concurrent file access by implementing a threaded server. It also integrates SDN to provide programmable network control.

The application layer handles authentication and file operations, while the SDN controller manages network forwarding and traffic policies.

## 3. Problem Statement

To design and implement a concurrent file-sharing system that allows multiple authenticated clients to upload and download files while providing centralized network management through Software-Defined Networking.

## 4. Objectives

- Implement a TCP-based file-sharing application.
- Support multiple simultaneous client connections.
- Provide user registration and authentication.
- Store file metadata using SQLite.
- Implement file upload, download, and listing operations.
- Integrate an SDN controller using OS-Ken.
- Use OpenFlow 1.3 for network forwarding and traffic control.
- Test the system using Mininet.
- Evaluate concurrent file-transfer performance.

## 5. System Architecture

The system consists of three major components.

### 5.1 Client

The client application connects to the file server through TCP. It supports:

- User registration.
- User login.
- File upload.
- File download.
- Listing available files.

### 5.2 File Server

The server listens on TCP port 5001 and handles multiple client connections using threads.

Its responsibilities include:

- Processing client requests.
- Authenticating users.
- Receiving uploaded files.
- Sending requested files.
- Maintaining file metadata.
- Managing concurrent connections.

### 5.3 Database

SQLite is used to store user information and file metadata.

Password storage uses PBKDF2-HMAC-SHA256 with a random 16-byte salt and 200,000 iterations.

File metadata includes information required to identify and retrieve stored files.

### 5.4 SDN Controller

The SDN controller is implemented using OS-Ken and OpenFlow 1.3.

Its responsibilities include:

- Connecting to the Open vSwitch.
- Installing forwarding rules.
- Learning network addresses.
- Monitoring switch statistics.
- Applying traffic-control policies.

## 6. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application and controller implementation |
| TCP sockets | Client-server communication |
| SQLite | Database management |
| OS-Ken | SDN controller framework |
| OpenFlow 1.3 | Switch communication protocol |
| Open vSwitch | Software-based network switch |
| Mininet | Network emulation |
| Linux | Development and execution environment |
| Pytest | Automated testing |

## 7. Implementation Methodology

### 7.1 Server Implementation

A threaded TCP server was developed to handle multiple client connections. The server listens on port 5001 and processes client requests.

File uploads are initially written to temporary `.part` files. After a successful transfer, the files are moved to their final storage locations using atomic replacement.

A maximum upload size of 3 GB is configured.

### 7.2 Authentication

The system supports user registration and login.

Passwords are not stored as plain text. Instead, PBKDF2-HMAC-SHA256 is used with a random salt and 200,000 iterations. Password verification uses a constant-time comparison.

### 7.3 File Management

The application supports:

- Uploading files.
- Downloading files by file ID.
- Listing available files.

UUID-based physical filenames are used for stored files, while metadata is maintained in SQLite.

### 7.4 Client Implementation

An interactive command-line client was developed to communicate with the server.

Users can log in and perform file operations through the client interface.

## 8. SDN Integration

The SDN environment was created using Mininet with:

- One Open vSwitch.
- Two hosts.
- One remote SDN controller.

Host configuration:

| Host | IP Address |
|---|---|
| h1 | 10.0.0.1 |
| h2 | 10.0.0.2 |

The remote controller runs on `127.0.0.1:6653`.

OpenFlow 1.3 is used for communication between the controller and the switch.

The controller implements forwarding rules and periodically monitors switch statistics.

### 8.1 Traffic-Control Policy

A flow rule was installed to drop TCP traffic from `10.0.0.1` to `10.0.0.2` when the destination port is 5002.

This policy was verified using the Open vSwitch flow table.

The iperf TCP connection to port 5002 timed out, while ICMP connectivity between the hosts remained successful.

The file-sharing application uses port 5001, so this test policy does not block its application traffic.

## 9. Testing and Results

### 9.1 Unit Testing

Automated tests were implemented using Pytest.

| Test File | Tests |
|---|---:|
| test_database.py | 8 |
| test_server.py | 3 |
| Total | 11 |

All 11 tests passed.

The tests cover authentication, database operations, concurrent metadata insertion, file transfers, and access restrictions.

### 9.2 File Transfer Testing

File upload and download operations were tested between clients and the server.

Downloaded files were compared with their original files to verify content integrity.

### 9.3 Concurrent Client Testing

Multiple clients were used to upload files simultaneously.

Three concurrent uploads completed successfully, and the uploaded files were subsequently downloaded and checked.

### 9.4 Network Testing

The Mininet network was tested using:

- `pingall` for host connectivity.
- Open vSwitch flow-table inspection.
- TCP iperf tests.
- File transfers between Mininet hosts.

The hosts successfully communicated using ICMP, and the configured TCP traffic-control policy was verified.

## 10. Performance Analysis

A preliminary benchmark was conducted using 64 MiB files and one, two, and three concurrent clients.

Average measured throughput:

| Concurrent Clients | Average Throughput |
|---|---:|
| 1 | 363.78 MiB/s |
| 2 | 584.31 MiB/s |
| 3 | 775.76 MiB/s |

The results show increased aggregate throughput as the number of concurrent clients increased in the tested Mininet environment.

These measurements are preliminary. The transfers were short, and caching and virtual-network conditions may affect the results. They should not be interpreted as physical network throughput measurements.

The benchmark data and graph are available in the `results/` directory.

## 11. Limitations

- The TCP application connection does not currently use TLS encryption.
- Per-file ownership-based access control is not implemented.
- The demonstrated OpenFlow traffic policy is based on IP addresses and TCP ports rather than application usernames.
- Performance measurements were conducted in a virtual Mininet environment.
- Further testing is required under larger workloads and longer transfer durations.

## 12. Future Enhancements

Possible future improvements include:

- Implementing TLS encryption.
- Adding per-file ownership and access permissions.
- Supporting more advanced SDN traffic-management policies.
- Improving monitoring and performance reporting.
- Conducting longer-duration benchmarks.
- Testing with larger numbers of concurrent clients.
- Developing a graphical user interface.

## 13. Conclusion

The project successfully demonstrates a concurrent TCP-based file-sharing application integrated with an SDN-controlled network.

The application supports authentication, file upload, file download, and file listing. SQLite provides persistent metadata storage, while multithreading enables concurrent client handling.

The SDN component uses OS-Ken, OpenFlow 1.3, Open vSwitch, and Mininet to demonstrate programmable network forwarding, traffic monitoring, and traffic-control policies.

Testing confirmed that all 11 automated tests passed, concurrent file uploads worked, and the SDN policy behaved as expected in the emulated network.

The project provides a foundation for further development of secure and scalable file-sharing systems using Software-Defined Networking.
