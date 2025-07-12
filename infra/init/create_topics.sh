#!/bin/sh
# Create Kafka topics required by the Intelligent Data Quality Platform.
set -e

BROKER=${KAFKA_BROKERS:-redpanda:9092}

create_topic() {
  topic="$1"
  partitions="${2:-1}"
  rpk topic create "$topic" -p "$partitions" -r 1 --brokers "$BROKER" || true
}

# Example topics; extend as needed
create_topic incidents 1
create_topic quality_checks 1