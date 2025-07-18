#!/usr/bin/env bash

# etl_cleanup.sh
# -----------------------------------
# Rotate logs and purge old Kafka topics

# Configuration
LOG_DIR="./"
LOG_RETENTION_DAYS=7
KAFKA_BROKER="localhost:9092"
TOPIC_NAME="transactions"

# 1) Rotate & compress old logs
# Compress each log file older than retention days
echo "Rotating logs older than $LOG_RETENTION_DAYS days..."
for pattern in producer.log consumer.log backup.log; do
  find "$LOG_DIR" -maxdepth 1 -type f -name "$pattern" -mtime +$LOG_RETENTION_DAYS -print0 \
    | xargs -0 -r echo "Compressing" | sed 's/^/    /'
  find "$LOG_DIR" -maxdepth 1 -type f -name "$pattern" -mtime +$LOG_RETENTION_DAYS -print0 \
    | xargs -0 -r gzip
done

# 2) Purge Kafka topic by recreating (delete+create) by recreating (delete+create) by recreating (delete+create)
echo "Checking Kafka broker at $KAFKA_BROKER..."
# Try to describe topic; if fails, skip purge
if ! docker run --rm confluentinc/cp-kafka:6.2.1 \
    kafka-topics --bootstrap-server "$KAFKA_BROKER" --describe --topic "$TOPIC_NAME" > /dev/null 2>&1; then
  echo "Warning: Kafka broker unreachable or topic '$TOPIC_NAME' not found. Skipping Kafka purge."
else
  # Get partition count
  PARTS=$(docker run --rm confluentinc/cp-kafka:6.2.1 \
    kafka-topics --bootstrap-server "$KAFKA_BROKER" --describe --topic "$TOPIC_NAME" \
    | grep -oP 'Partition:\s*\K[0-9]+' | wc -l)
  echo "Purging Kafka topic '$TOPIC_NAME' with $PARTS partitions..."
  # Delete topic
docker run --rm confluentinc/cp-kafka:6.2.1 \
    kafka-topics --bootstrap-server "$KAFKA_BROKER" --delete --topic "$TOPIC_NAME"
  sleep 5
  # Recreate topic
docker run --rm confluentinc/cp-kafka:6.2.1 \
    kafka-topics --bootstrap-server "$KAFKA_BROKER" --create --topic "$TOPIC_NAME" \
    --partitions "$PARTS" --replication-factor 1
  echo "Kafka topic '$TOPIC_NAME' purged and recreated."
fi

echo "ETL cleanup complete: logs rotated >${LOG_RETENTION_DAYS}d."
