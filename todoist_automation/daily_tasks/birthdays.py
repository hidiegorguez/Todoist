from todoist_automation import config


def _has_schedule_set(task) -> bool:
    """Check whether a birthday task already has the yearly 23:00 due and Phone/Short labels."""
    if task.due is None:
        return False
    hour = getattr(task.due.date, 'hour', None)
    return bool(task.due.is_recurring) and hour == 23 and set(task.labels) == {'Phone', 'Short'}


def apply_birthday_labels(tf, all_tasks):
    """Set the yearly reminder string and Phone/Short labels on birthday tasks."""
    birthday_msgs = []
    birthday_tasks = [task for task in all_tasks if task.project_id == config.BIRTHDAYS_PROJECT_ID]

    for task in filter(lambda task: not _has_schedule_set(task), birthday_tasks):
        try:
            month = task.due.date.month
            day = task.due.date.day
            tf.update_task(
                task_id=task.id,
                due_string=f'cada {day} {month} 23:00',
                labels=['Phone', 'Short'],
            )
            birthday_msgs.append("- " + task.content)
        except Exception:
            birthday_msgs.append(f"Task '{task.content}' probably does not have a proper due_string")

    tasks_with_reminder = {reminder['item_id'] for reminder in tf.get_reminders()}
    for task in filter(lambda task: task.id not in tasks_with_reminder, birthday_tasks):
        try:
            tf.add_reminder(task_id=task.id, minute_offset=1380)
        except Exception:
            birthday_msgs.append(f"Task '{task.content}' reminder could not be added")

    return birthday_msgs
