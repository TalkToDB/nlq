#!/bin/bash
set -e

echo "🕐 Waiting for databases to be ready..."

# Wait for Postgres
until pg_isready -h postgres -p 5432 -U admin > /dev/null 2>&1; do
  echo "  ⏳ Waiting for Postgres..."
  sleep 3
done

# Wait for MySQL
until mysqladmin ping -h mysql -u admin -padmin --silent; do
  echo "  ⏳ Waiting for MySQL..."
  sleep 3
done

echo "✅ All databases are up! Starting imports..."

# --------------------------
# PostgreSQL: DVD Rental
# --------------------------
echo "📦 Importing DVD Rental sample into PostgreSQL..."
curl -L -o /tmp/dvdrental.zip https://www.postgresqltutorial.com/wp-content/uploads/2019/05/dvdrental.zip
unzip -o /tmp/dvdrental.zip -d /tmp
export PGPASSWORD=admin
psql -h postgres -U admin -d mydb -c "CREATE ROLE postgres LOGIN;"
pg_restore -h postgres -U admin -d mydb /tmp/dvdrental.tar

# --------------------------
# MySQL: Sakila sample
# --------------------------
echo "📦 Importing Sakila sample into MySQL..."
curl -L -o /tmp/sakila-db.zip https://downloads.mysql.com/docs/sakila-db.zip
unzip -o /tmp/sakila-db.zip -d /tmp/sakila
mysql -h mysql -u root -padmin -e "CREATE DATABASE sakila;"
mysql -h mysql -u root -padmin -e "GRANT ALL PRIVILEGES ON sakila.* TO 'admin'@'%'; FLUSH PRIVILEGES;"
mysql -h mysql -u root -padmin sakila < /tmp/sakila/sakila-db/sakila-schema.sql
mysql -h mysql -u root -padmin sakila < /tmp/sakila/sakila-db/sakila-data.sql