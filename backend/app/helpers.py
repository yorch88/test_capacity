from datetime import datetime, timezone

def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        # lo tratamos como UTC almacenado en Mongo
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
