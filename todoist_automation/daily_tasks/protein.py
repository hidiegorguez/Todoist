from datetime import datetime, timedelta

from todoist_automation import config
from todoist_automation.utils.dates import due_to_date


def schedule_protein_task(tf, all_tasks, today, weekday):
    """Schedule the daily protein task based on today's gym session.

    - If exactly one gym task is due today with a time and a minute duration,
      the protein task is scheduled 15 minutes after the gym task ends.
    - Otherwise (no gym task today, several gym tasks, or a gym task without
      time/duration), it falls back to 10 am, or 7 pm on Wednesdays.
    - If the protein task was already completed, it is reactivated first.
    """
    gym_today = [
        task
        for task in all_tasks
        if task.id in config.GYM_TASK_IDS and task.due is not None and due_to_date(task.due.date) == today.date()
    ]

    due_string = None
    reason = None
    if len(gym_today) == 1:
        gym_task = gym_today[0]
        gym_start = gym_task.due.date
        if isinstance(gym_start, datetime) and gym_task.duration is not None and gym_task.duration.unit == 'minute':
            protein_time = gym_start + timedelta(minutes=gym_task.duration.amount + config.PROTEIN_MINUTES_AFTER_GYM)
            due_string = f'today at {protein_time.strftime("%H:%M")}'
            reason = f'{config.PROTEIN_MINUTES_AFTER_GYM} minutes after "{gym_task.content}" ends'

    if due_string is None:
        due_string = config.PROTEIN_WEDNESDAY_DUE_STRING if weekday == 2 else config.PROTEIN_DEFAULT_DUE_STRING
        reason = 'default hour'

    protein_task = tf.get_task(config.PROTEIN_TASK_ID)
    if protein_task.is_completed:
        tf.uncomplete_task(config.PROTEIN_TASK_ID)
    tf.update_task(task_id=config.PROTEIN_TASK_ID, due_string=due_string)
    return [f'- Task "{protein_task.content}" scheduled {due_string} ({reason})']
