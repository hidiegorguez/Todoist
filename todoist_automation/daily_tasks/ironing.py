from datetime import datetime, timezone

from todoist_automation import config
from todoist_automation.utils.dates import due_to_date

try:
    from zoneinfo import ZoneInfo

    LOCAL_TZ = ZoneInfo(config.LOCAL_TIMEZONE)
except Exception:
    LOCAL_TZ = None


def _parse_utc(value):
    """Parse a Todoist UTC timestamp (datetime or ISO string) into an aware ``datetime``."""
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def schedule_ironing_after_laundry(tf, today):
    """Schedule the ironing task for today if laundry was done after the last ironing.

    Conditions:
    - Laundry was completed more recently than ironing (completions are read
      from the activity log, since the recurring laundry task never exposes
      ``completed_at``). If a nightly run is missed, the next one catches up.
    - Laundry was completed before today, so ironing is always at least the
      day after.
    - Ironing is not already scheduled for today or a later date (respects
      manual postponements). Overdue or undated ironing is moved to today.
    - If ironing was closed (one-off task), it is reopened first.
    """
    if not config.LAUNDRY_TASK_ID or not config.IRONING_TASK_ID:
        return []

    laundry_last = _parse_utc(tf.get_last_completion(config.LAUNDRY_TASK_ID))
    if laundry_last is None or laundry_last.astimezone(LOCAL_TZ).date() >= today.date():
        return []

    ironing_last = _parse_utc(tf.get_last_completion(config.IRONING_TASK_ID))
    if ironing_last is not None and ironing_last >= laundry_last:
        return []

    ironing_task = tf.get_task(config.IRONING_TASK_ID)
    if ironing_task.is_completed:
        tf.uncomplete_task(config.IRONING_TASK_ID)
    elif ironing_task.due is not None and due_to_date(ironing_task.due.date) >= today.date():
        return []

    tf.update_task(task_id=config.IRONING_TASK_ID, due_string="today")
    return [f'- Task "{ironing_task.content}" scheduled for today (laundry completed after last ironing)']
