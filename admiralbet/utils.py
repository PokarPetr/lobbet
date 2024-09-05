from datetime import datetime, timezone, timedelta

def convert_timestamp_to_format(td: int = 0) -> str:
    """
        Converts the current UTC timestamp to a string in the format 'YYYY-MM-DD HH:MM:SS'.

        :return: A formatted timestamp string.
    """
    dt = datetime.now(timezone.utc) + timedelta(hours=td) if td else datetime.now(timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
