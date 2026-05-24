"""Distributed tracing context — OpenTelemetry-ready."""

from contextvars import ContextVar

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)


def bind_trace_context(trace_id: str | None, span_id: str | None = None) -> None:
    if trace_id:
        trace_id_var.set(trace_id)
    if span_id:
        span_id_var.set(span_id)


def get_trace_id() -> str | None:
    return trace_id_var.get()
