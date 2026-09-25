from datetime import datetime

from todoist_automation import config
from todoist_automation.utils.dates import get_next_monday


def manage_fantasy_task(tf, all_tasks, today, weekday):
    """Reschedule the Fantasy Football task back to the weekend, or move it to

    Tuesday when a match is scheduled before the weekend.
    """
    fantasy_msg = []
    evaluate = True

    if tf.get_task(config.FANTASY_TASK_ID).is_completed:
        tf.uncomplete_task(config.FANTASY_TASK_ID)
        tf.update_task(task_id=config.FANTASY_TASK_ID, due_string='every friday 20:00')
        fantasy_msg.append('Fantasy task moved back to weekends')
        evaluate = False

    if evaluate and weekday in [0, 5, 6] and tf.get_task(config.FANTASY_TASK_ID).due.date != today.strftime('%Y-%m-%d'):
        for task in filter(
            lambda task: task.section_id == config.FANTASY_MATCHES_SECTION_ID
            and task.parent_id == config.FANTASY_MATCHES_PARENT_TASK_ID,
            all_tasks,
        ):
            try:
                fantasy_task = list(filter(lambda task: task.id == config.FANTASY_TASK_ID, all_tasks))[0]
                fantasydate = datetime.strptime(fantasy_task.due.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                matchday = datetime.strptime(task.due.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                if fantasydate > matchday > get_next_monday():
                    fantasy_msg.append('Fantasy task moved to Tuesday')
                    tf.update_task(task_id=config.FANTASY_TASK_ID, due_string="Tuesday 7 pm")
                    break
            except TypeError:  # Due date is None; match date has not been released yet.
                pass

    return fantasy_msg
