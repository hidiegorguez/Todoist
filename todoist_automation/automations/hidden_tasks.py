from datetime import datetime

from todoist_automation import config
from todoist_automation.api import mailer


def run_hidden_night_tasks(tf):
    try:
        today = datetime.today()
        weekday = today.weekday()
        task_time = 'today at 9 pm'
        wh_task = tf.get_task(config.NIGHT_TASK_WH_ID)
        health_task = tf.get_task(config.NIGHT_TASK_HEALTH_ID)
        apps_task = tf.get_task(config.NIGHT_TASK_APPS_ID)
        activate_wh_task = False
        activate_healt_task = False
        if weekday == 6:
            if apps_task.is_completed:
                tf.uncomplete_task(config.NIGHT_TASK_APPS_ID)
                tf.update_task(task_id=config.NIGHT_TASK_APPS_ID, due_string=task_time)
                tf.add_reminder(task_id=config.NIGHT_TASK_APPS_ID, minute_offset=0)
            else:
                tf.update_task(task_id=config.NIGHT_TASK_APPS_ID, due_string=task_time)
            activate_wh_task = True
            activate_healt_task = True
        elif weekday in [2, 4] or activate_wh_task:
            if wh_task.is_completed:
                tf.uncomplete_task(config.NIGHT_TASK_WH_ID)
                tf.update_task(task_id=config.NIGHT_TASK_WH_ID, due_string=task_time)
                tf.add_reminder(task_id=config.NIGHT_TASK_WH_ID, minute_offset=0)
            else:
                tf.update_task(task_id=config.NIGHT_TASK_WH_ID, due_string=task_time)
        elif weekday in [0, 3] or activate_healt_task:
            if health_task.is_completed:
                tf.uncomplete_task(config.NIGHT_TASK_HEALTH_ID)
                tf.update_task(task_id=config.NIGHT_TASK_HEALTH_ID, due_string=task_time)
                tf.add_reminder(task_id=config.NIGHT_TASK_HEALTH_ID, minute_offset=0)
            else:
                tf.update_task(task_id=config.NIGHT_TASK_HEALTH_ID, due_string=task_time)
        return f'Execution completed, day {weekday}'

    except Exception as e:
        return mailer.format_error_for_email(
            operation="Hidden Night Tasks Update",
            e=e,
            additional_info={
                "day_of_week": weekday,
                "wh_task_id": config.NIGHT_TASK_WH_ID,
                "health_task_id": config.NIGHT_TASK_HEALTH_ID,
                "apps_task_id": config.NIGHT_TASK_APPS_ID,
                "timestamp": datetime.now().isoformat(),
            },
        )


def run_hidden_afternoon_tasks(tf):
    try:
        today = datetime.today()
        weekday = today.weekday()
        if weekday == 3:
            task = tf.get_task(config.AFTERNOON_TASK_ID)
            if task.is_completed:
                tf.uncomplete_task(config.AFTERNOON_TASK_ID)
                tf.update_task(task_id=config.AFTERNOON_TASK_ID, due_string='today at 9 pm')
                tf.add_reminder(task_id=config.AFTERNOON_TASK_ID, minute_offset=0)
            else:
                tf.update_task(task_id=config.AFTERNOON_TASK_ID, due_string='today at 9 pm')
        return f'Execution completed, day {weekday}'

    except Exception as e:
        return mailer.format_error_for_email(
            operation="Hidden Afternoon Tasks Update",
            e=e,
            additional_info={
                "day_of_week": weekday,
                "task_id": config.AFTERNOON_TASK_ID,
                "timestamp": datetime.now().isoformat(),
            },
        )
