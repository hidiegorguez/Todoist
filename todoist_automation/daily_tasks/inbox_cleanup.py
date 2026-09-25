from todoist_automation import config
from todoist_automation.utils.labels import priority_inversal


def move_tasks_out_of_inbox(tf, all_tasks):
    """Capitalize, prioritize, schedule for today and move non-Work inbox tasks out."""
    inbox_cleaning_msg = []
    for task in list(filter(
        lambda task: task.project_id == config.INBOX_PROJECT_ID and 'Work' not in task.labels,
        all_tasks,
    )):
        tf.update_task(
            task_id=task.id,
            content=task.content[0].upper() + task.content[1:],
            priority=priority_inversal(3),
            due_string="today",
        )
        tf.move_task(task_id=task.id, project_id=config.INBOX_CLEANUP_DESTINATION_PROJECT_ID)
        inbox_cleaning_msg.append(f'- Task "{task.content}" moved out from the inbox')
    return inbox_cleaning_msg
