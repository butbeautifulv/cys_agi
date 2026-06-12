from __future__ import annotations

from bootstrap.settings import settings
from cys_core.infrastructure.bus_transport import get_bus_transport
from interfaces.control_plane.bus_consumer import run_bus_consumer
from interfaces.control_plane.critic_service import get_critic_service


def run_critic_daemon(*, idle_timeout: float = 0.0) -> int:
    """Kafka or Redis bus consumer daemon for critic control plane."""
    critic = get_critic_service()
    if not settings.use_kafka:
        transport = get_bus_transport()
        start_loop = getattr(transport, "start_subscriber_loop", None)
        if start_loop is not None:
            start_loop(["critic"])
    return run_bus_consumer("critic", critic.handle_message, idle_timeout=idle_timeout, group_id="critic-consumer")
