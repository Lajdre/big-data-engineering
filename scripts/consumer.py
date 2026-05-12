#!/usr/bin/env python3
"""Kafka consumer that triggers pipeline on new file messages."""

import json
from pathlib import Path

from kafka import KafkaConsumer

from pipeline import config
from pipeline.main import run_file


def run_consumer():
  """Consume from Kafka and run pipeline for each file."""
  consumer = KafkaConsumer(
    config.KAFKA_TOPIC,
    bootstrap_servers=config.KAFKA_BOOTSTRAP,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="pgcb-pipeline",
  )

  print(f"Subscribed to topic: {config.KAFKA_TOPIC}")
  print("Waiting for messages...")

  for message in consumer:
    data = message.value
    filepath = Path(data["filepath"])
    filename = data["filename"]

    print(f"\nReceived: {filename}")

    if not filepath.exists():
      print(f"  ERROR: File not found: {filepath}")
      continue

    try:
      run_file(str(filepath))
      processed_path = Path("data/processed") / filename
      filepath.rename(processed_path)
      print(f"  Moved to: {processed_path}")
    except Exception as e:
      print(f"  ERROR processing {filename}: {e}")


if __name__ == "__main__":
  run_consumer()
