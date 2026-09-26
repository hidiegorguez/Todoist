import time
from datetime import datetime

from todoist_automation import config
from todoist_automation.api import mailer
from todoist_automation.daily_tasks import (
    birthdays,
    capitalization,
    duration_labels,
    fantasy,
    inbox_cleanup,
    permanent_tasks,
    recurring_toggles,
    shopping,
    similar_tasks,
    vacations,
    weekly_deadlines,
    work_label,
)
from todoist_automation.utils.report import build_daily_report

WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# (task_id, active_weekdays, due_string, duration, duration_unit)
RECURRING_TOGGLE_TASKS = [
    (config.COUNTER_TASK_ID, list(range(7)), 'today at 6 am', None, None),
    (config.BREAKFAST_TASK_ID, [0, 3, 4, 5, 6], 'today at 9 am', None, None),
    (config.RAISED_TASK_ID, [1, 2], 'today at 8:30 am', None, None),
    (config.WATER_TASK_ID, [0, 3, 4, 5, 6], 'today at 11 am', 540, 'minute'),
    (config.STRETCHING_TASK_ID, [0, 3, 4, 5, 6], 'today at 9 am', 10, 'minute'),
    (config.MOUTH_TASK_ID, [4], 'today at 3 pm', 10, 'minute'),
]


def run_daily(tf, address):
    try:
        start_time = time.time()
        today = datetime.today()
        weekday = today.weekday()

        projects_dict_id, _ = tf.get_projects()
        all_tasks = tf.get_tasks()

        shopping_subtasks_msgs, shopping_labels_msgs = shopping.process_shopping_subtasks(tf, all_tasks)
        work_label.cleanup_work_label(tf, all_tasks)
        duration_msgs = duration_labels.add_duration_labels(tf, all_tasks)
        inbox_cleaning_msg = inbox_cleanup.move_tasks_out_of_inbox(tf, all_tasks)
        capitalization_msgs = capitalization.capitalize_titles(tf, all_tasks)
        birthday_msgs = birthdays.apply_birthday_labels(tf, all_tasks)
        suitcase_msgs, expenses_msgs = vacations.process_vacation_tasks(tf, all_tasks, today)

        for task_id, active_weekdays, due_string, duration, duration_unit in RECURRING_TOGGLE_TASKS:
            recurring_toggles.reset_recurring_task(
                tf, task_id, weekday, active_weekdays, due_string, duration, duration_unit
            )

        weekly_deadlines_msgs = weekly_deadlines.sync_weekly_deadlines(tf, all_tasks)
        similar_msgs = similar_tasks.find_new_similar_tasks(all_tasks, weekday, umbral=0.7)
        fantasy_msg = fantasy.manage_fantasy_task(tf, all_tasks, today, weekday)
        permanenttasks_msg = permanent_tasks.restore_permanent_tasks(tf, today, projects_dict_id)

        messages_dict = {
            'Tasks to add duration labels:': duration_msgs,
            'Tasks to move out from de inbox:': inbox_cleaning_msg,
            'Tasks to capitalize its content:': capitalization_msgs,
            'Tasks to add birthday labels:': birthday_msgs,
            'New suitcase tasks:': suitcase_msgs,
            'New expenses tasks': expenses_msgs,
            'Weekly deadlines updated:': weekly_deadlines_msgs,
            'Next tasks are similar:': similar_msgs,
            'Shopping subtasks rescheduled to Compra date:': shopping_subtasks_msgs,
            'Shopping subtask labels updated:': shopping_labels_msgs,
        }

        body = build_daily_report(
            today, messages_dict, fantasy_msg, permanenttasks_msg, runtime_seconds=time.time() - start_time
        )

        try:
            mailer.send_email(subject="Daily Todoist", body=body, to=address)
            return f'{body}\n\nAnd mail sent correctly'
        except Exception as e:
            error_msg = mailer.format_error_for_email(
                operation="Daily Todoist - Email Send",
                e=e,
                additional_info={
                    "fecha": today.strftime('%Y-%m-%d'),
                    "dia_semana": WEEKDAY_NAMES[weekday],
                    "tareas_procesadas": len(all_tasks),
                    "cambios_realizados": body.count('\n') - 2,
                },
            )
            return f'{body}\n\nError sending mail:\n{error_msg}'

    except Exception as e:
        try:
            additional_info = {
                "fecha": today.strftime('%Y-%m-%d'),
                "dia_semana": WEEKDAY_NAMES[weekday],
                "estado": "Fallo durante procesamiento de tareas",
            }
            if 'all_tasks' in locals():
                additional_info['tareas_intentadas'] = len(all_tasks)
            if 'body' in locals():
                additional_info['progress'] = body[:200] + "..." if len(body) > 200 else body

            error_msg = mailer.format_error_for_email(
                operation="Daily Todoist - Main Process",
                e=e,
                additional_info=additional_info,
            )
            mailer.send_email("Daily Todoist - Error", error_msg, address)
            return error_msg
        except Exception as e2:
            return f'Critical error in Daily execution: {e2}'
