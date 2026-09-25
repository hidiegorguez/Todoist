import os

from dotenv import load_dotenv

from todoist_automation.api.todoist_client import TodoistFunctions
from todoist_automation.automations import daily, hidden_tasks, superbet, todo_lp, weather

load_dotenv()

if __name__ == "__main__":
    tf = TodoistFunctions(api_token=os.getenv('TODOIST_API_TOKEN'))
    print(f'Daily execution: {daily.run_daily(tf, address=os.getenv("DIEGO_EMAIL"))}')
    # print(f'SuperBet execution: {superbet.run_superbet(tf, hour=datetime.today().hour)}')
    # print(f'Hidden night tasks execution: {hidden_tasks.run_hidden_night_tasks(tf)}')
    # print(f'Hidden afternoon tasks execution: {hidden_tasks.run_hidden_afternoon_tasks(tf)}')
    # print(f'LigaPistachoToDo execution: {todo_lp.run_todo_lp(tf, address=os.getenv("DIEGO_EMAIL"))}')
    # print(f'Weather execution: {weather.run_weather(tf)}')
