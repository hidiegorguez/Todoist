from datetime import datetime, timedelta


def due_to_date(due_value):
    """Normalize a Todoist ``due.date`` value (str or date-like) into a ``date``."""
    if due_value is None:
        return None
    if isinstance(due_value, str):
        try:
            return datetime.strptime(due_value[:10], '%Y-%m-%d').date()
        except Exception:
            return None
    try:
        return datetime.strptime(due_value.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
    except Exception:
        return None


def get_next_monday():
    _today = datetime.now()
    days_to_monday = (0 - _today.weekday()) % 7
    closer_monday = _today + timedelta(days=days_to_monday)
    return closer_monday
