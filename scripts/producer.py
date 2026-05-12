#!/usr/bin/env python3
"""File watcher that publishes new CSV files to Kafka topic."""

import json
import time
from pathlib import Path
from typing import override

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from watchdog.events import (
  DirCreatedEvent,
  DirMovedEvent,
  FileCreatedEvent,
  FileMovedEvent,
  FileSystemEventHandler,
)
from watchdog.observers import Observer

from pipeline import config


def ensure_topic_exists(bootstrap_servers: str, topic: str):
  try:
    admin_client = KafkaAdminClient(
      bootstrap_servers=bootstrap_servers, client_id="pgcb-producer"
    )
    if topic not in admin_client.list_topics():
      new_topic = NewTopic(name=topic, num_partitions=1, replication_factor=1)
      admin_client.create_topics([new_topic])
      print(f"Created topic: {topic}")
    admin_client.close()
  except Exception as e:
    print(f"Topic check warning: {e}")


class CSVHandler(FileSystemEventHandler):
  """Watch for new CSV files and publish to Kafka."""

  def __init__(self, producer: KafkaProducer, topic: str):
    self.producer: KafkaProducer = producer
    self.topic: str = topic
    self.seen: set[str] = set()

  @override
  def on_created(self, event: DirCreatedEvent | FileCreatedEvent):
    if event.is_directory:
      return
    filepath = Path(str(event.src_path))
    if filepath.suffix != ".csv":
      return
    if filepath.name in self.seen:
      return

    self.seen.add(filepath.name)
    message = {"filepath": str(filepath), "filename": filepath.name}
    self.producer.send(self.topic, message)
    print(f"Published: {filepath.name}")

  @override
  def on_moved(self, event: DirMovedEvent | FileMovedEvent):
    """Handle files moved into the directory."""
    if event.is_directory:
      return
    dest = Path(str(event.dest_path))
    if dest.suffix != ".csv":
      return
    if dest.name in self.seen:
      return

    self.seen.add(dest.name)
    message = {"filepath": str(dest), "filename": dest.name}
    self.producer.send(self.topic, message)
    print(f"Published: {dest.name}")


def run_producer(watch_dir: Path):
  ensure_topic_exists(config.KAFKA_BOOTSTRAP, config.KAFKA_TOPIC)

  producer = KafkaProducer(
    bootstrap_servers=config.KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
  )

  handler = CSVHandler(producer, config.KAFKA_TOPIC)
  for csv_file in sorted(watch_dir.glob("*.csv")):
    handler.seen.add(csv_file.name)
    message = {"filepath": str(csv_file), "filename": csv_file.name}
    producer.send(config.KAFKA_TOPIC, message)
    print(f"Published existing: {csv_file.name}")

  observer = Observer()
  observer.schedule(handler, str(watch_dir), recursive=False)
  observer.start()

  print(f"Watching {watch_dir} for new CSV files...")
  print(f"Publishing to Kafka topic: {config.KAFKA_TOPIC}")

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()
  finally:
    observer.join()
    producer.close()


if __name__ == "__main__":
  run_producer(Path("data/incoming"))
