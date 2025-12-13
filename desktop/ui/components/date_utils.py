from datetime import datetime


def format_ddmmyyyy(val):
    """Return a date in DD/MM/YYYY format.

    Accepts an ISO datetime string (with optional Z), a datetime object,
    or any value that can be stringified. Returns empty string for falsy input.
    """
    if not val:
        return ''
    try:
        if isinstance(val, str):
            cleaned = val.replace('Z', '+00:00')
            dt = datetime.fromisoformat(cleaned)
        elif isinstance(val, datetime):
            dt = val
        else:
            # fallback: coerce to str and take first 10 chars
            return str(val)[:10]
        return dt.strftime('%d/%m/%Y')
    except Exception:
        try:
            return str(val)[:10]
        except Exception:
            return ''
