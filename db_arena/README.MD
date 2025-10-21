# Database Arena

This directory contains Docker Compose configurations for running various databases for testing.

## Starting Database Services

To start all database services in the background:

```bash
docker compose up -d
```

This will start all configured databases (PostgreSQL, MySQL, MongoDB, SQL Server, etc.) in detached mode.

## Stopping Database Services

To stop all database services:

```bash
docker compose down
```

To stop and remove all volumes (this will delete all data):

```bash
docker compose down -v
```