
# ─── Build stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System packages needed to compile/install Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # pyodbc (SQL Server support)
    unixodbc-dev \
    # psycopg2 binary wheel / general build
    gcc \
    # unstructured[pdf] – document parsing
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files (IMPORTANT: include lock file)
COPY pyproject.toml uv.lock ./

# Install dependencies into a separate directory
RUN uv sync --frozen --no-dev

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy only the runtime system libs we need (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Bring in the installed Python packages from the builder
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source (changes frequently — kept after the slow layers)
COPY . /app

# Directory for schema cache and any runtime-written JSON files
RUN mkdir -p chroma_db query_results

EXPOSE 7860

# HOST and PORT can be overridden; defaults match HF Spaces / Docker conventions
ENV HOST=0.0.0.0 \
    PORT=7860 \
    DATA_DIR=/data

CMD ["python", "main.py"]

