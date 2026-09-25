from datetime import timedelta

from todoist_automation import config


def restore_permanent_tasks(tf, today, projects_dict_id):
    """Uncomplete 'Permanent' tasks completed in the last 10 days and reset their due date."""
    permanenttasks_msg = []
    completed_tasks = tf.get_completed_tasks_by_completion_date(
        limit=100, since=(today - timedelta(days=10)), until=today
    )

    for task in list(filter(lambda task: 'Permanent' in task.labels, completed_tasks)):
        task_id = task.id
        project_id = task.project_id
        tf.uncomplete_task(task_id)
        tf.update_task(task_id=task_id, due_string="No date")
        message = f'Task "{task.content}" uncompleted'
        if project_id == config.VACATIONS_PROJECT_ID:
            tf.move_task(task_id=task_id, project_id=config.PERMANENT_TASKS_DESTINATION_PROJECT_ID)
            message += f' and moved from {projects_dict_id[config.VACATIONS_PROJECT_ID]} to {projects_dict_id[config.PERMANENT_TASKS_DESTINATION_PROJECT_ID]}'
        permanenttasks_msg.append("- " + message)

    return permanenttasks_msg
