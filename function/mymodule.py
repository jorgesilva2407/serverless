from typing import Any


def handler(input: dict, context: object) -> dict[str, Any]:
    # Retrieve environment state
    env = context.env
    if "cpu_moving_avg" not in env:
        env["cpu_moving_avg"] = {}

    # Extract CPUs
    cpu_keys = [key for key in input.keys() if key.startswith("cpu_percent-")]

    # Initialize moving averages if not present
    for cpu_key in cpu_keys:
        if cpu_key not in env["cpu_moving_avg"]:
            env["cpu_moving_avg"][cpu_key] = []

    # Update moving averages
    for cpu_key in cpu_keys:
        env["cpu_moving_avg"][cpu_key].append(input[cpu_key])
        if len(env["cpu_moving_avg"][cpu_key]) > 60:
            env["cpu_moving_avg"][cpu_key].pop(0)

    # Calculate moving averages
    moving_averages = {
        f"avg-util-{cpu_key}-60sec": sum(env["cpu_moving_avg"][cpu_key])
        / len(env["cpu_moving_avg"][cpu_key])
        for cpu_key in cpu_keys
    }

    # Calculate memory caching percentage
    memory_cached = input.get("virtual_memory-cached", 0)
    memory_buffers = input.get("virtual_memory-buffers", 0)
    memory_total = input.get("virtual_memory-total", 1)  # Avoid division by zero
    percent_memory_cache = (memory_cached + memory_buffers) / memory_total * 100

    # Calculate outgoing traffic percentage
    bytes_sent = input.get("net_io_counters_eth0-bytes_sent1", 0)
    bytes_recv = input.get("net_io_counters_eth0-bytes_recv1", 0)
    total_bytes = bytes_sent + bytes_recv
    percent_network_egress = (bytes_sent / total_bytes * 100) if total_bytes > 0 else 0

    # Prepare output
    output = {
        "percent-memory-caching": percent_memory_cache,
        "percent-network-egress": percent_network_egress,
    }
    output.update(moving_averages)

    return output
