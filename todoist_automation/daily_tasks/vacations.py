from datetime import datetime, timedelta

from todoist_automation import config
from todoist_automation.utils.labels import priority_inversal


def process_vacation_tasks(tf, all_tasks, today):
    """Create the "prepare suitcase" and "log expenses" tasks for upcoming vacations.

    Returns:
        Tuple[list[str], list[str]]: (suitcase_msgs, expenses_msgs)
    """
    suitcase_msgs = []
    expenses_msgs = []

    for task in list(filter(
        lambda task: 'Vacations' in task.labels and task.project_id == config.VACATIONS_PROJECT_ID,
        all_tasks,
    )):
        title = task.content
        if not any(filter(lambda t: t.content == f'Preparar maleta {title}', all_tasks)):
            vacation_day = datetime.strptime(task.due.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
            if vacation_day > today + timedelta(days=3):
                new_suitcase_task = tf.add_task(
                    content=f'Preparar maleta {title}',
                    due_string=f"3 dias antes de {task.due.date.strftime('%Y-%m-%d')}",
                    priority=priority_inversal(2),  # orange
                    labels=['Long', 'Home'],
                    project_id=config.SUITCASE_EXPENSES_PROJECT_ID,
                )
                suitcase_msgs.append(f'- Task "Preparar maleta {title}" created succesfully')

                # Copy the packing checklist from the reference "Maleta" task comments,
                # but only if the new task does not already have one.
                try:
                    existing_comments = tf.get_comments(task_id=new_suitcase_task.id)
                    if existing_comments:
                        suitcase_msgs.append(f'- "Preparar maleta {title}" already has a comment; skipped copy')
                    else:
                        maleta_comments = tf.get_comments(task_id=config.MALETA_REFERENCE_TASK_ID)
                        if maleta_comments:
                            tf.add_comment(content=maleta_comments[0].content, task_id=new_suitcase_task.id)
                            suitcase_msgs.append(f'- Packing checklist copied to "Preparar maleta {title}"')
                        else:
                            suitcase_msgs.append('- Maleta task has no comments to copy')
                except Exception as e:
                    suitcase_msgs.append(f'- Could not copy packing checklist: {e}')

        if not any(filter(lambda t: t.content == f'Apuntar gastos {title}', all_tasks)):
            if 'fin' in task.due.string or 'ending' in task.due.string:
                tf.add_task(
                    content=f'Apuntar gastos {title}',
                    due_string=f"1 dia despues de {task.due.date.strftime('%Y-%m-%d')}",
                    priority=priority_inversal(3),  # blue
                    labels=['Phone', 'PC', 'Long'],
                    project_id=config.SUITCASE_EXPENSES_PROJECT_ID,
                )
                expenses_msgs.append(f'- Task "Apuntar gastos {title}" created succesfully')

    return suitcase_msgs, expenses_msgs
