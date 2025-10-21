## Supported Databases

| Database Type | Status | Driver Required |
|--------------|--------|-----------------|
| PostgreSQL | ✅ Ready | `psycopg2-binary` |
| MySQL | ✅ Ready | `mysql-connector-python` |
| SQLite | ✅ Ready | Built-in |
| SQL Server | ✅ Ready | `pyodbc` + ODBC Driver |
| MongoDB (Local) | ✅ Ready | `pymongo` |
| MongoDB (Atlas) | ✅ Ready | `pymongo` |

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Setup Steps

1. **Clone the repository**

```bash
git clone https://github.com/TalkToDB/nlq.git
cd nlq
```

2. **Create a virtual environment**

```bash
uv venv .venv
```

3. **Activate the virtual environment**

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

4. **Install dependencies using uv**

```bash
# Sync all dependencies from pyproject.toml
uv sync
```

5. **Install database drivers**

```bash
uv sync --extra all-databases
```

### SQL Server Additional Setup

For SQL Server, you need to install the ODBC Driver:

- **Windows**: Download from [Microsoft ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- **Linux**: Follow the [installation guide](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

## Running the Application

```bash
# Run with uv
uv run python main.py
```

The application will start and open in your default browser at `http://localhost:8080`

## Project Structure

```
nlq/
├── main.py                      # Application entry point
├── pyproject.toml              # Project dependencies and metadata
├── db_connections.json         # Saved database connections
├── src/
│   ├── database/
│   │   ├── schemas.py          # Database-specific field definitions
│   │   ├── manager.py          # Connection CRUD operations
│   │   └── executor.py         # Query execution for all DB types
│   ├── models/
│   │   ├── config.py           # LLM provider configurations
│   │   └── query_engine.py    # Natural language query engine (WIP)
│   └── ui/
│       ├── app.py              # Main Gradio app
│       ├── theme.py            # Custom UI theme
│       ├── query_tab.py        # Natural language query interface
│       ├── sql_query_tab.py    # Direct SQL/NoSQL query interface
│       └── connections_tab.py  # Database connection management
├── db_arena/                   # Docker Compose for test databases
└── debug_mongodb.py           # MongoDB connection debugging tool
```

## Usage

## Configuration Files

### `db_connections.json`

Stores your saved database connections. Example:

```json
[
  {
    "name": "my_postgres",
    "type": "PostgreSQL",
    "host": "localhost",
    "port": "5432",
    "database": "mydb",
    "username": "postgres",
    "password": "password"
  }
]
```

### `pyproject.toml`

Project configuration with dependencies. To add new dependencies:

```bash
uv add package-name
```

## Testing with Docker

The `db_arena` directory contains Docker Compose configurations for testing:

```bash
cd db_arena

# Start all test databases
docker compose up -d

# Stop all databases
docker compose down

# Stop and remove all data
docker compose down -v
```