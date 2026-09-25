from datetime import datetime, timedelta

from todoist_automation import config
from todoist_automation.utils.labels import priority_inversal


def sync_weekly_deadlines(tf, all_tasks):
    """Align each 'Weekly' task's deadline to the Sunday following its due date

    and adjust its priority based on the weekday it falls on.
    """
    weekly_deadlines_msgs = []
    for task in list(filter(lambda task: 'Weekly' in task.labels, all_tasks)):
        due = datetime.strptime(task.due.date.strftime('%Y-%m-%d'), "%Y-%m-%d").date()
        priority = task.priority
        evaluate_deadline = True
        if task.deadline is not None:
            deadline = datetime.strptime(task.deadline.date.strftime('%Y-%m-%d'), "%Y-%m-%d").date()
        else:
            evaluate_deadline = False
        days_until_sunday_from_due = (6 - due.weekday()) % 7
        next_sunday_from_due = due + timedelta(days=days_until_sunday_from_due)
        if not evaluate_deadline or next_sunday_from_due != deadline:
            tf.update_task(task_id=task.id, deadline_date=next_sunday_from_due)
            weekly_deadlines_msgs.append(f'- Task "{task.content}" moved to {next_sunday_from_due.strftime("%Y-%m-%d")}')
        if task.project_id != config.WEEKLY_PRIORITY_EXEMPT_PROJECT_ID:
            if due.weekday() in [4, 5] and priority != priority_inversal(2):
                tf.update_task(task_id=task.id, priority=priority_inversal(2))
            elif due.weekday() == 6 and priority != priority_inversal(1):
                tf.update_task(task_id=task.id, priority=priority_inversal(1))
            elif due.weekday() in [0, 1, 2, 3] and priority != priority_inversal(3):
                tf.update_task(task_id=task.id, priority=priority_inversal(3))
    return weekly_deadlines_msgs
