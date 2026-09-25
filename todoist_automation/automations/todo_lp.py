from datetime import datetime

from todoist_automation.api import mailer


def run_todo_lp(tf, address):
    """Placeholder for the LigaPistacho ToDo sync; the original logic is disabled.

    See git history for the previous CSV-driven implementation.
    """
    try:
        return True
    except Exception as e:
        try:
            error_msg = mailer.format_error_for_email(
                operation="ToDoLP Data Sync",
                e=e,
                additional_info={
                    "timestamp": datetime.now().isoformat(),
                    "recipient": address,
                },
            )
            mailer.send_email("Todoist ToDo LP - Error", error_msg, address)
            return error_msg
        except Exception as e2:
            return f'Critical error in ToDoLP: {e2}'
