from todoist_automation import config


def apply_birthday_labels(tf, all_tasks):
    """Set the yearly reminder string and Phone/Short labels on birthday tasks."""
    birthday_msgs = []
    for task in list(filter(
        lambda task: task.project_id == config.BIRTHDAYS_PROJECT_ID and task.labels != ['Phone', 'Short'],
        all_tasks,
    )):
        try:
            month = task.due.date[5:7]
            day = task.due.date[8:10]
            tf.update_task(
                task_id=task.id,
                due_string=f'cada {day} {month} 23:00',
                labels=['Phone', 'Short'],
            )
            tf.add_reminder(task_id=task.id, minute_offset=1380)
            birthday_msgs.append("- " + task.content)
        except Exception:
            birthday_msgs.append(f"Task '{task.content}' probably does not have a proper due_string")
    return birthday_msgs
