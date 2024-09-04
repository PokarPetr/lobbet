from datetime import datetime, timezone

def convert_timestamp_to_format() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
