# DS Replicated Log

DS Replicated Log is a distributed system project that showcases the replication of messages from a master service to multiple secondary services using FastAPI and Docker.

## Deployment architecture 

**Master** should expose a simple HTTP server (or alternative service with a similar API) with: 
* POST method - appends a message into the in-memory list
* GET method - returns all messages from the in-memory list

**Secondary** should expose a simple  HTTP server(or alternative service with a similar API)  with:
* GET method - returns all replicated messages from the in-memory list

## Features
**Asynchronous Replication**: Messages sent to the master are asynchronously replicated to secondary services to ensure high availability and fault tolerance.

**Health Check**: Each service provides a health endpoint to verify its operational status.

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