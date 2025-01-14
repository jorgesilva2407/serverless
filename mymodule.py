import json
import redis
from typing import Any
from dataclasses import dataclass


@dataclass
class SystemInfo:
    timestamp: str
    cpu_freq_current: float
    cpu_percent: list[float]
    cpu_stats_ctx_switches: int
    cpu_stats_interrupts: int
    cpu_stats_soft_interrupts: int
    cpu_stats_syscalls: int
    n_pids: int
    virtual_memory_total: int
    virtual_memory_available: int
    virtual_memory_percent: float
    virtual_memory_used: int
    virtual_memory_free: int
    virtual_memory_active: int
    virtual_memory_inactive: int
    virtual_memory_buffers: int
    virtual_memory_cached: int
    virtual_memory_shared: int
    virtual_memory_slab: int
    net_io_counters_eth0_bytes_sent: int
    net_io_counters_eth0_bytes_recv: int
    net_io_counters_eth0_packets_sent: int
    net_io_counters_eth0_packets_recv: int
    net_io_counters_eth0_errin: int
    net_io_counters_eth0_errout: int
    net_io_counters_eth0_dropin: int
    net_io_counters_eth0_dropout: int


def handler(event: dict, context: object) -> dict[str, Any]:
    # Extract system info from the event
    try:
        system_info = SystemInfo(**event["metrics"])
    except KeyError:
        raise ValueError("Invalid input: 'metrics' key is missing from event.")

    # Compute percentage of outgoing traffic bytes
    total_bytes = (
        system_info.net_io_counters_eth0_bytes_sent
        + system_info.net_io_counters_eth0_bytes_recv
    )
    percent_network_egress = (
        (system_info.net_io_counters_eth0_bytes_sent / total_bytes) * 100
        if total_bytes > 0
        else 0
    )

    # Compute percentage of memory caching content
    total_memory = (
        system_info.virtual_memory_cached + system_info.virtual_memory_buffers
    )
    percent_memory_caching = (
        (total_memory / system_info.virtual_memory_total) * 100
        if system_info.virtual_memory_total > 0
        else 0
    )

    # Compute moving average utilization of each CPU over the last minute
    cpu_count = len(system_info.cpu_percent)
    cpu_avg_utilization = []

    if not hasattr(context, "env"):
        context.env = {}

    for i in range(cpu_count):
        key = f"avg_util_cpu{i}_60sec"
        prev_avg = context.env.get(key, 0)
        new_avg = (prev_avg * 59 + system_info.cpu_percent[i]) / 60
        context.env[key] = new_avg
        cpu_avg_utilization.append(new_avg)

    # Prepare the result dictionary
    result = {
        "percent_network_egress": percent_network_egress,
        "percent_memory_caching": percent_memory_caching,
    }
    for i in range(cpu_count):
        result[f"avg_util_cpu{i}_60sec"] = cpu_avg_utilization[i]

    # Store the result in Redis
    redis_host = context.host
    redis_port = context.port
    output_key = context.output_key

    try:
        redis_client = redis.StrictRedis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        redis_client.set(output_key, json.dumps(result))
    except redis.ConnectionError as e:
        raise RuntimeError(f"Failed to connect to Redis: {e}")

    return result
