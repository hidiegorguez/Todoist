import os
from datetime import datetime, timedelta

import requests

from todoist_automation import config
from todoist_automation.api import mailer


def run_weather(tf):
    try:
        all_tasks = tf.get_tasks()

        api_key = os.getenv('OPEN_WEATHER_API_KEY')
        base_url = 'http://api.openweathermap.org/data/2.5/weather'
        full_url = f"{base_url}?q={config.WEATHER_CITY_NAME}&appid={api_key}&units=metric&lang=com"
        response = requests.get(full_url)

        if response.status_code != 200:
            return f'Error getting data: {response.status_code}'

        data = response.json()
        if data['weather'][0]['description'] not in ['clear sky', 'few clouds', 'scattered clouds']:
            return f'Task not created beacuse of weather: {data["weather"][0]["description"]}'

        today = datetime.today()
        if today.month >= 6:
            return 'Not in date'

        today_str = today.strftime('%Y-%m-%d')
        sun_start = today.replace(hour=15, minute=30)
        sun_end = today.replace(hour=16, minute=0)
        for task in all_tasks:
            try:
                if 'Outside' in task.labels and today_str in task.due.date and task.priority in [3, 4]:
                    if '15:30' in task.due.date:
                        return 'Task not created beacuse of time'
                    elif task.duration.amount > 0:
                        task_init = datetime.strptime(task.due.date, '%Y-%m-%dT%H:%M:%S')
                        task_end = task_init + timedelta(minutes=task.duration.amount)
                        if task_init < sun_end and task_end > sun_start:
                            return 'Task not created beacuse of time'
            except Exception:
                pass

        task = tf.get_task(config.WEATHER_TASK_ID)
        if task.is_completed:
            tf.uncomplete_task(config.WEATHER_TASK_ID)
        tf.update_task(task_id=config.WEATHER_TASK_ID, due_string='today at 15:30', duration=30, duration_unit='minute')
        tf.add_reminder(task_id=config.WEATHER_TASK_ID, minute_offset=30)

        return 'Task created'

    except Exception as e:
        return mailer.format_error_for_email(
            operation="Weather Task Creation",
            e=e,
            additional_info={
                "city": config.WEATHER_CITY_NAME,
                "timestamp": datetime.now().isoformat(),
                "total_tasks_to_check": len(all_tasks) if 'all_tasks' in locals() else 'No tasks loaded',
            },
        )
