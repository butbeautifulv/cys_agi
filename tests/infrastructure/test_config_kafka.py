import pytest
from config import Settings


def test_kafka_defaults():
    s = Settings(
        _env_file=None,  # ignore .env
    )
    assert s.kafka_bootstrap_servers == "localhost:9092"
    assert s.use_kafka is False
    assert s.kafka_consumer_group_prefix == "cys-agi"


def test_kafka_from_env(monkeypatch):
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")
    monkeypatch.setenv("USE_KAFKA", "true")
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP_PREFIX", "myapp")
    s = Settings(_env_file=None)
    assert s.kafka_bootstrap_servers == "redpanda:29092"
    assert s.use_kafka is True
    assert s.kafka_consumer_group_prefix == "myapp"
