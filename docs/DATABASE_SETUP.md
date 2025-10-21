# Database Drivers Installation Guide

The application now supports **real database query execution**! 

To use this feature, you need to install the appropriate database drivers for the databases you want to connect to.

## Installation Options

### Install all database drivers:
```bash
uv sync --extra all-databases
```

### Or install specific database drivers:

**PostgreSQL:**
```bash
uv sync --extra postgres
```

**MySQL:**
```bash
uv sync --extra mysql
```

**SQL Server:**
```bash
uv sync --extra sqlserver
```

**MongoDB:**
```bash
uv sync --extra mongodb
```

### SQLite
SQLite is included with Python by default - no additional installation needed!

## Usage

Once you've installed the drivers for your database:

1. Go to **Manage Connections** tab
2. Add your database connection
3. Go to **Database Query** tab
4. Select your connection
5. Write and execute real queries!

The application will show you actual results from your database, including:
- Execution time
- Number of rows returned
- Complete data in JSON format
- Any errors if queries fail

## Note

If you try to query a database without its driver installed, you'll see a helpful error message telling you which package to install.
