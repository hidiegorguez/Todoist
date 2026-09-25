from datetime import datetime

from todoist_automation import config
from todoist_automation.api import mailer


def run_superbet(tf, hour=0):
    try:
        today = datetime.today()
        weekday = today.weekday()
        edited = False
        task = tf.get_task(config.SUPERBET_TASK_ID)
        if task.is_completed:
            if weekday in [0, 4] and hour in [16, 17]:
                tf.uncomplete_task(config.SUPERBET_TASK_ID)
                tf.update_task(task_id=config.SUPERBET_TASK_ID, due_string='today at 7 pm')
                edited = True
            elif weekday in [1, 2, 3] and hour in [14, 15]:
                tf.uncomplete_task(config.SUPERBET_TASK_ID)
                tf.update_task(task_id=config.SUPERBET_TASK_ID, due_string='today at 5 pm')
                edited = True
            elif weekday in [5, 6] and hour in [10, 11]:
                tf.uncomplete_task(config.SUPERBET_TASK_ID)
                tf.update_task(task_id=config.SUPERBET_TASK_ID, due_string='today at 1 pm')
                edited = True
            if edited:
                tf.add_reminder(task_id=config.SUPERBET_TASK_ID, minute_offset=0)
        return f'Execution completed, day {weekday}, hour {hour}'

    except Exception as e:
        return mailer.format_error_for_email(
            operation="SuperBet Task Update",
            e=e,
            additional_info={
                "task_id": config.SUPERBET_TASK_ID,
                "day_of_week": weekday,
                "hour": hour,
                "timestamp": datetime.now().isoformat(),
            },
        )
