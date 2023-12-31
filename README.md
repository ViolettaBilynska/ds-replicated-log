# DS Replicated Log

DS Replicated Log is a distributed system project that showcases the replication of messages from a master service to multiple secondary services using FastAPI and Docker.

## Deployment architecture

**Master** should expose a simple HTTP server (or alternative service with a similar API) with: 
* POST method - appends a message to the in-memory list with a write concern parameter specifying the replication requirement before acknowledgment to the client.
* GET method - returns all messages from the in-memory list, ensuring total order of messages.

**Secondary** should expose a simple  HTTP server(or alternative service with a similar API)  with:
* GET method - returns all replicated messages from its in-memory list, which may temporarily differ from the master's list due to eventual consistency.

## Features
**Asynchronous Replication**: Messages sent to the master are asynchronously replicated to secondary services to ensure high availability and fault tolerance.

**Health Check**: Each service provides a health endpoint to verify its operational status.

**Containerization**: The entire suite of services can be seamlessly deployed, orchestrated, and scaled. 

**Semi-Synchronous Replication**: Replication to secondaries can be configured for semi-synchronicity. The master will respond to the client based on the specified write concern level.

**Eventual Consistency Emulation**: Artificial delays can be introduced in secondary services to emulate eventual consistency.

**Deduplication Logic**: Prevents the same message from being stored twice.

**Total Ordering Guarantee**: Messages are assigned an incremental sequence ID to guarantee the total order, ensuring they are stored and retrieved in the exact order they were received.

## Getting Started

### Prerequisites
* Docker and Docker Compose installed on your machine.
* Python 3.9 (optional, for local development without Docker).

### Run the app

```bash
 docker-compose up --build
 docker-compose down
```
**Containerization**: The entire suite of services can be seamlessly deployed, orchestrated, and scaled. 

## Getting Started

### Prerequisites
* Docker and Docker Compose installed on your machine.
* Python 3.9 (optional, for local development without Docker).

### Run the app

```bash
 docker-compose up --build
 docker-compose down
```