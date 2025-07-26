from typing import Callable

import psutil
from fastapi import FastAPI
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info


def cpu_usage_metric() -> Callable[[Info], None]:
    # Define a Prometheus Gauge metric for CPU usage
    METRIC = Gauge(
        "process_cpu_usage_percent",
        "CPU usage of the process as a percentage."
    )

    def instrumentation(info: Info) -> None:
        # Get the current CPU usage percentage
        cpu_usage = psutil.Process().cpu_percent(interval=None)
        # Update the Gauge with the current CPU usage
        METRIC.set(cpu_usage)

    return instrumentation


def memory_usage_metric() -> Callable[[Info], None]:
    METRIC = Gauge(
        "process_memory_usage_bytes",
        "Memory usage of the process in bytes."
    )

    def instrumentation(info: Info) -> None:
        # Get the current process memory usage (RSS)
        memory_usage = psutil.Process().memory_info().rss
        # Update the Gauge with the current memory usage
        METRIC.set(memory_usage)

    return instrumentation


def register_prometheus(app: FastAPI):
    instrumentator = Instrumentator(
        # should_respect_env_var=True,
        excluded_handlers=["/metrics"],
        # env_var_name="ENABLE_METRICS",
    )

    # instrumentator.add(memory_usage_metric())
    # instrumentator.add(cpu_usage_metric())
    # instrumentator.add(metrics.default())
    instrumentator.instrument(app)
    instrumentator.expose(app)
