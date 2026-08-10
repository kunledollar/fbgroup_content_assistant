from datetime import UTC, datetime, timedelta

RANGE_LABELS = [
    "Today",
    "Last 24 Hours",
    "Last 3 Days",
    "Last 7 Days",
    "Last 14 Days",
    "Last 30 Days",
    "Custom Date Range",
]


def since_for_range(label: str, custom_days: int | None = None) -> datetime | None:
    now = datetime.now(UTC).replace(tzinfo=None)
    mapping = {
        "Today": 1,
        "Last 24 Hours": 1,
        "Last 3 Days": 3,
        "Last 7 Days": 7,
        "Last 14 Days": 14,
        "Last 30 Days": 30,
    }
    if label == "Custom Date Range":
        days = custom_days if custom_days and custom_days > 0 else 7
        return now - timedelta(days=days)
    days = mapping.get(label)
    if days is None:
        return None
    return now - timedelta(days=days)
