from todoist_automation import config


def cleanup_work_label(tf, all_tasks):
    """Remove the 'Work' label from personal tasks, moving inbox ones out to today."""
    for task in list(filter(
        lambda task: 'Work' in task.labels and task.project_id == config.PERSONAL_PROJECT_ID,
        all_tasks,
    )):
        tf.update_task(task_id=task.id, labels=[label for label in task.labels if label != 'Work'])

    for task in list(filter(
        lambda task: 'Work' in task.labels and task.project_id == config.INBOX_PROJECT_ID,
        all_tasks,
    )):
        tf.update_task(
            task_id=task.id,
            labels=[label for label in task.labels if label != 'Work'],
            due_string="today",
        )
        tf.move_task(task_id=task.id, project_id=config.PERSONAL_PROJECT_ID)
