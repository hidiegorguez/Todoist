from todoist_automation.utils.labels import get_duration_label


def add_duration_labels(tf, all_tasks):
    """Add a Short/Med/Long label to tasks that have a duration but no such label yet."""
    duration_msgs = []
    for task in list(filter(
        lambda task: task.duration is not None and all(label not in task.labels for label in ['Long', 'Med', 'Short']),
        all_tasks,
    )):
        new_label = get_duration_label(task.duration.amount)
        tf.update_task(task_id=task.id, labels=task.labels + [new_label])
        duration_msgs.append("- " + task.content)
    return duration_msgs
