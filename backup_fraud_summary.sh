#!/usr/bin/env bash

# backup_fraud_summary.sh
# Nightly backup of the fraud_summary table to CSV via Docker exec

# Configuration
DB_NAME="fraud_db"
DB_USER="postgres"
CONTAINER_NAME="fraud-postgres"
OUTPUT_DIR="./backups"
DATE=$(date +%F)
OUTFILE="$OUTPUT_DIR/fraud_summary_$DATE.csv"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Dump the table using docker exec
if docker exec "$CONTAINER_NAME" \
    psql -U "$DB_USER" -d "$DB_NAME" -c "COPY fraud_summary TO STDOUT WITH CSV HEADER" \
    > "$OUTFILE"; then
    echo "[$(date)] Backup succeeded: $OUTFILE"
else
    echo "[$(date)] Backup FAILED" >&2
    exit 1
fi
