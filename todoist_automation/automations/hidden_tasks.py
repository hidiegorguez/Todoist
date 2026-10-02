from datetime import datetime

from todoist_automation import config
from todoist_automation.api import mailer


def _activate_tasks(tf, weekday, schedule):
    """Set the due date (and duration) of tasks scheduled for today, reactivating completed ones."""
    for task_id, active_weekdays, due_string, duration, duration_unit in schedule:
        if weekday not in active_weekdays:
            continue
        task = tf.get_task(task_id)
        was_completed = task.is_completed
        if was_completed:
            tf.uncomplete_task(task_id)
        kwargs = {"task_id": task_id, "due_string": due_string}
        if duration is not None:
            kwargs["duration"] = duration
            kwargs["duration_unit"] = duration_unit
        tf.update_task(**kwargs)
        if was_completed:
            tf.add_reminder(task_id=task_id, minute_offset=0)


def _run(tf, schedule, operation):
    weekday = datetime.today().weekday()
    try:
        _activate_tasks(tf, weekday, schedule)
        return f'Execution completed, day {weekday}'
    except Exception as e:
        return mailer.format_error_for_email(
            operation=operation,
            e=e,
            additional_info={
                "day_of_week": weekday,
                "task_ids": [entry[0] for entry in schedule],
                "timestamp": datetime.now().isoformat(),
            },
        )


def run_hidden_night_tasks(tf):
    return _run(tf, config.HIDDEN_NIGHT_TASKS, "Hidden Night Tasks Update")


def run_hidden_afternoon_tasks(tf):
    return _run(tf, config.HIDDEN_AFTERNOON_TASKS, "Hidden Afternoon Tasks Update")
