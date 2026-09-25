def capitalize_titles(tf, all_tasks):
    """Capitalize the first letter of every task whose content starts lowercase."""
    capitalization_msgs = []
    for task in list(filter(lambda task: task.content[0].upper() != task.content[0], all_tasks)):
        tf.update_task(task_id=task.id, content=task.content[0].upper() + task.content[1:])
        capitalization_msgs.append("- " + task.content)
    return capitalization_msgs
