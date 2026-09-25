from todoist_automation import config
from todoist_automation.utils.dates import due_to_date


def process_shopping_subtasks(tf, all_tasks):
    """Move overdue Compra subtasks to the Compra date while preserving each recurrence rule.

    Also makes sure every subtask carries the required labels.

    Returns:
        Tuple[list[str], list[str]]: (shopping_subtasks_msgs, shopping_labels_msgs)
    """
    shopping_subtasks_msgs = []
    shopping_labels_msgs = []

    shopping_task = next((task for task in all_tasks if task.id == config.SHOPPING_TASK_ID), None)
    if shopping_task is None:
        shopping_subtasks_msgs.append('- Compra task not found')
        return shopping_subtasks_msgs, shopping_labels_msgs

    shopping_subtasks = list(filter(lambda task: task.parent_id == config.SHOPPING_TASK_ID, all_tasks))
    for subtask in shopping_subtasks:
        missing_labels = [label for label in config.SHOPPING_REQUIRED_LABELS if label not in subtask.labels]
        if missing_labels:
            tf.update_task(task_id=subtask.id, labels=subtask.labels + missing_labels)
            shopping_labels_msgs.append(
                f'- "{subtask.content}": added {", ".join(missing_labels)}'
            )

    if shopping_task.due is None:
        shopping_subtasks_msgs.append('- Compra has no due date; subtasks were not evaluated')
        return shopping_subtasks_msgs, shopping_labels_msgs

    shopping_due_date = due_to_date(shopping_task.due.date)
    if shopping_due_date is None:
        shopping_subtasks_msgs.append('- Compra due date could not be parsed; subtasks were not evaluated')
        return shopping_subtasks_msgs, shopping_labels_msgs

    shopping_due_str = shopping_due_date.strftime('%Y-%m-%d')
    moved_or_reviewed = 0
    for subtask in filter(lambda task: task.due is not None, shopping_subtasks):
        subtask_due_date = due_to_date(subtask.due.date)
        if subtask_due_date is not None and subtask_due_date < shopping_due_date:
            moved_or_reviewed += 1
            old_due = subtask_due_date.strftime('%Y-%m-%d')
            original_due_string = subtask.due.string
            original_is_recurring = getattr(subtask.due, 'is_recurring', False)
            try:
                if original_is_recurring and original_due_string:
                    # Keep the original recurrence text and shift only the current occurrence date.
                    tf.update_task(
                        task_id=subtask.id,
                        due_string=original_due_string,
                        due_date=shopping_due_str,
                        due_lang='es'
                    )
                else:
                    tf.update_task(task_id=subtask.id, due_date=shopping_due_str)

                updated_subtask = tf.get_task(subtask.id)
                updated_is_recurring = getattr(updated_subtask.due, 'is_recurring', False) if updated_subtask.due is not None else False
                updated_due_string = updated_subtask.due.string if updated_subtask.due is not None else None
                updated_due_date = due_to_date(updated_subtask.due.date) if updated_subtask.due is not None else None

                if original_is_recurring and not updated_is_recurring:
                    shopping_subtasks_msgs.append(
                        f'- "{subtask.content}" moved to {shopping_due_str}, but recurrence was lost. Review needed (original: {original_due_string})'
                    )
                elif updated_due_date is None or updated_due_date != shopping_due_date:
                    shopping_subtasks_msgs.append(
                        f'- "{subtask.content}" kept recurrence but could not be aligned to Compra date. Current due: {updated_subtask.due.date}, target: {shopping_due_str}'
                    )
                else:
                    shopping_subtasks_msgs.append(
                        f'- "{subtask.content}" moved from {old_due} to {shopping_due_str} ({updated_due_string})'
                    )
            except Exception as e:
                shopping_subtasks_msgs.append(
                    f'- "{subtask.content}" could not be moved: {e}'
                )

    if moved_or_reviewed == 0:
        shopping_subtasks_msgs.append('- No overdue Compra subtasks to move')

    return shopping_subtasks_msgs, shopping_labels_msgs
