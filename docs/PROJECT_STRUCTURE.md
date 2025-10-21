# Natural Language Database Querying

Query your databases using natural language powered by LLM agents.

## Project Structure

```
nlq/
├── main.py                          # Application entry point
├── src/
│   ├── database/
│   │   ├── schemas.py              # Database connection schemas for different DB types
│   │   └── manager.py              # Database connection manager
│   ├── models/
│   │   ├── config.py               # Model provider configurations
│   │   └── query_engine.py        # Query processing engine (mock for now)
│   └── ui/
│       ├── app.py                  # Main Gradio application
│       ├── query_tab.py            # Query interface tab
│       └── connections_tab.py      # Connection management tab
├── db_connections.json             # Stored database connections (auto-generated)
└── pyproject.toml                  # Project dependencies
```

## Features

### Database Connection Management

- **Multiple Database Types**: PostgreSQL, MySQL, SQLite, SQL Server, MongoDB
- **Dynamic Forms**: Form fields adapt based on selected database type
- **Persistent Storage**: Connections saved to `db_connections.json`
- **Easy Management**: Add, view, and delete connections

### Query Interface

- **Natural Language Queries**: Ask questions in plain English
- **Model Selection**: Choose between Ollama and OpenAI models
- **Chat Interface**: Interactive conversation-style querying
- **Mock Responses**: Placeholder for future LangChain integration

## Supported Database Types

### PostgreSQL

- Host, Port (default: 5432)
- Database name, Username, Password
- Optional: Schema

### MySQL

- Host, Port (default: 3306)
- Database name, Username, Password

### SQLite

- Database file path

### SQL Server

- Host, Port (default: 1433)
- Database name, Username, Password
- Optional: Driver

### MongoDB

- Host, Port (default: 27017)
- Database name
- Optional: Username, Password, Auth Source

## Installation

This project uses `uv` for package management.

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py
```

## Usage

1. **Start the application**

   ```bash
   uv run python main.py
   ```
2. **Add Database Connections**

   - Navigate to "Manage Connections" tab
   - Select your database type
   - Fill in the connection details (fields adapt to database type)
   - Click "Add Connection"
3. **Query Your Database**

   - Go to "Query Database" tab
   - Select a database connection
   - Choose your preferred model provider and model
   - Type your question in natural language
   - Submit your query

## Development

### Adding New Database Types

1. Create a new schema class in `src/database/schemas.py`:

   ```python
   class NewDBSchema(DatabaseSchema):
       @staticmethod
       def get_fields() -> List[DatabaseField]:
           return [...]

       @staticmethod
       def get_default_port() -> str:
           return "port_number"
   ```
2. Register it in `DATABASE_SCHEMAS` dictionary

### Adding New Model Providers

Update `src/models/config.py` with new provider information:

```python
MODEL_PROVIDERS = {
    "NewProvider": {
        "models": ["model1", "model2"],
        "default": "model1"
    }
}
```

## Roadmap

- [ ] LangChain integration for actual database querying
- [ ] SQL query validation and preview
- [ ] Query history and saved queries
- [ ] Export results to CSV/JSON
- [ ] Connection testing before saving
- [ ] Encrypted password storage
- [ ] Multi-database queries
