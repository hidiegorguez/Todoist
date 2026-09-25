def reset_recurring_task(tf, task_id, weekday, active_weekdays, due_string, duration=None, duration_unit=None):
    """Uncomplete and reschedule a recurring task when it was already completed.

    This factors out the counter/breakfast/raised/water tasks in the daily
    automation, which all follow the same "if completed today, reset it"
    pattern for a fixed set of weekdays.
    """
    if weekday not in active_weekdays:
        return
    task = tf.get_task(task_id)
    if not task.is_completed:
        return
    tf.uncomplete_task(task_id)
    kwargs = {"task_id": task_id, "due_string": due_string}
    if duration is not None:
        kwargs["duration"] = duration
        kwargs["duration_unit"] = duration_unit
    tf.update_task(**kwargs)
