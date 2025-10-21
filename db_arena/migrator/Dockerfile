FROM debian:bookworm-slim

# Install tools for all databases
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    default-mysql-client \
    curl unzip ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY migrator.sh /app/migrator.sh
RUN chmod +x /app/migrator.sh

CMD ["/app/migrator.sh"]
