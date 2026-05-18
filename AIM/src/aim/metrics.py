"""Prometheus business metrics for AIM Agency.

Single source of truth — import counters from here.
"""

from prometheus_client import Counter, Gauge

leads_captured_total = Counter(
    "aim_leads_captured_total",
    "Total leads captured",
    ["source", "specialty"],
)

leads_scored_total = Counter(
    "aim_leads_scored_total",
    "Total leads scored",
    ["tier"],
)

rate_limit_hits_total = Counter(
    "aim_rate_limit_hits_total",
    "Rate limit triggers",
    ["endpoint"],
)

leads_by_tier = Gauge(
    "aim_leads_by_tier", "Current lead count by tier", ["tier"],
)

payments_total = Counter(
    "aim_payments_total",
    "Total payment attempts",
    ["status"],
)

payment_failures_total = Counter(
    "aim_payment_failures_total",
    "Total payment failures",
    ["reason"],
)

yookassa_webhooks_total = Counter(
    "aim_yookassa_webhooks_total",
    "Total YooKassa webhooks received",
    ["event"],
)

signings_total = Counter(
    "aim_signings_total",
    "Total contract signing attempts",
    ["status"],
)
