"""Centralized constants: Todoist project/section/task IDs and file paths.

Keeping these IDs here (instead of scattered as literals across the
automation modules) makes it possible to know what each one refers to and to
update them in a single place.

ID naming convention: <DESCRIPTION>_<TYPE>_ID, where TYPE is TASK, PROJECT or
SECTION (e.g. NIGHT_WH_TASK_ID, INBOX_PROJECT_ID). Lists of IDs use the plural
suffix <TYPE>_IDS.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SIMILAR_TASKS_CSV = os.path.join(DATA_DIR, "similartasksdiego.csv")

# --- Work label cleanup ---
PERSONAL_PROJECT_ID = "6hHqvV2wh2Jf2vpC"  # Work label should not exist here
INBOX_PROJECT_ID = "6Crcvw8HFvwxMCqc"

# --- Inbox cleanup ---
INBOX_CLEANUP_DESTINATION_PROJECT_ID = "6JqmRWG4gxwvmgRg"

# --- Birthdays ---
BIRTHDAYS_PROJECT_ID = "6Crcvw8HRWFQ4cw3"

# --- Vacations (suitcase / expenses) ---
VACATIONS_PROJECT_ID = "6Crcvw8HQm7HhcFv"
SUITCASE_EXPENSES_PROJECT_ID = "6Crcvw8HP8h84jJV"
SUITCASE_REFERENCE_TASK_ID = "69xHX9fhRF5Rq964"

# --- Recurring toggle tasks ---
COUNTER_TASK_ID = "6W4Q22F3fgF7mMf6"
BREAKFAST_TASK_ID = "6fwqMHR8Q59j76Jc"
RAISED_TASK_ID = "6cX627cCPMmWf9c3"
WATER_TASK_ID = "683VjRQ5j9GmCx94"

# --- Weekly deadlines ---
WEEKLY_PRIORITY_EXEMPT_PROJECT_ID = "6VW5PFC4hgwP8RVP"

# --- Similar tasks detection ---
SIMILAR_TASKS_EXCLUDED_PROJECT_IDS = [
    "6Crcvw8HQ7pGFH8v",
    "6Crcvw8HPWrHFWMx",
    "6g2gVxRGGVQJx76J",
    "6FhQxfCg5jxP4XpP",
    "6V72655fCQ3gChqh",
]
SIMILAR_TASKS_IGNORED_PAIRS = {
    "Agua & Agua",
    "Tweet & Tweet",
    "README & README",
    "Trabajo & Trabajo",
}

# --- Fantasy football ---
FANTASY_TASK_ID = "66V2HG92vFgV7Q2x"
FANTASY_MATCHES_SECTION_ID = "65VQ7M3vHH6q3FCw"
FANTASY_MATCHES_PARENT_TASK_ID = "6cFCJHXxwmQR3v9M"

# --- Permanent tasks ---
PERMANENT_TASKS_DESTINATION_PROJECT_ID = "6F63g3w6f352G8P4"

# --- Shopping subtasks ---
SHOPPING_TASK_ID = "66rjJfXC7599vCc4"
SHOPPING_REQUIRED_LABELS = ["Permanent", "Compras"]

# --- SuperBet ---
SUPERBET_TASK_ID = "6WX594CXh843hx76"

# --- Stretching ---
STRETCHING_TASK_ID = "6785M5hFvc2JXRj4"

# --- Mouth ---
MOUTH_TASK_ID = "69xJGWQjVXHmRMJx"

# --- Hidden night tasks ---
WH_TASK_ID = "6X9345CxhcVwWqc7"
HEALTH_TASK_ID = "6fH8GhMx2R9HRq5c"
APPS_TASK_ID = "6fg2gfqGP2gR5Fjc"

# --- Hidden afternoon tasks ---
TRASH_TASK_ID = "6hWpCqC7FrpPVJQx"

# --- Task schedules ---
# Entries: (task_id, active_weekdays (0=Monday), due_string, duration, duration_unit)
RECURRING_TOGGLE_TASKS = [
    (COUNTER_TASK_ID, list(range(7)), 'today at 6 am', None, None),
    (BREAKFAST_TASK_ID, [0, 1, 3, 5, 6], 'today at 9 am', None, None),
    (RAISED_TASK_ID, [2, 4], 'today at 8 am', None, None),
    (WATER_TASK_ID, [0, 1, 3, 5, 6], 'today at 11 am', 540, 'minute'),
    (STRETCHING_TASK_ID, [5, 6], 'today at 11 am', 10, 'minute')
]

HIDDEN_NIGHT_TASKS = [
    (APPS_TASK_ID, [6], 'today at 9 pm', None, None),
    (WH_TASK_ID, [2, 4], 'today at 9 pm', None, None),
    (HEALTH_TASK_ID, [0, 3], 'today at 9 pm', None, None),
]

HIDDEN_AFTERNOON_TASKS = [
    (TRASH_TASK_ID, [3], 'today at 9 pm', 5, 'minute'),
    (MOUTH_TASK_ID, [3], 'today at 5 pm', 5, 'minute'),
    (STRETCHING_TASK_ID, [0, 3, 4, 5, 6], 'today at 8 pm', None, None),
]

# --- Weather ---
WEATHER_TASK_ID = "6XCPqCqfmV4g424G"
WEATHER_CITY_NAME = "Colmenarejo"
