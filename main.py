import functions as fun
from todoist_api_python.api import TodoistAPI

from datetime import datetime, timedelta
import pandas as pd
import time
import os

import requests

from dotenv import load_dotenv

load_dotenv()

class MainDiego:
    
    def __init__(self, todoist_api_token):
        self.api_token = todoist_api_token
        self.tf = fun.TodoistFunctions(self.api_token)
        self.api = TodoistAPI(self.api_token)
 
    def TodoistDaily(self, address: str):
        try:
            
            start_time = time.time()
            today = datetime.today()
            weekday = today.weekday()
            messages = [f'Todoist Automation for {today.strftime("%Y-%m-%d")}']
            duration_msgs = []
            inbox_cleaning_msg = []
            capitalization_msgs = []
            birthday_msgs = []
            suitcase_msgs = []
            expenses_msgs = []
            weekly_deadlines_msgs = []
            similar_msgs = []
            fantasy_msg = []
            permanenttasks_msg = []
            shopping_subtasks_msgs = []
            messages_dict = {f'Tasks to add duration labels:': duration_msgs,
                            f'Tasks to move out from de inbox:': inbox_cleaning_msg,
                            f'Tasks to capitalize its content:': capitalization_msgs,
                            f'Tasks to add birthday labels:': birthday_msgs,
                            f'New suitcase tasks:': suitcase_msgs,
                            f'New expenses tasks': expenses_msgs,
                            f'Weekly deadlines updated:': weekly_deadlines_msgs,
                            f'Next tasks are similar:': similar_msgs,
                            f'Shopping subtasks rescheduled to Compra date:': shopping_subtasks_msgs}
            
            # Projects, sections and tasks
            projects_dict_id, _ = self.tf.get_projects()
            all_tasks = self.tf.get_tasks()

            def due_to_date(due_value):
                if due_value is None:
                    return None
                if isinstance(due_value, str):
                    try:
                        return datetime.strptime(due_value[:10], '%Y-%m-%d').date()
                    except Exception:
                        return None
                try:
                    return datetime.strptime(due_value.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                except Exception:
                    return None

            # Feature: move overdue Compra subtasks to Compra date while keeping each original recurrence rule.
            compra_task_id = '66rjJfXC7599vCc4'
            compra_task = next((task for task in all_tasks if task.id == compra_task_id), None)
            if compra_task is None:
                shopping_subtasks_msgs.append('- Compra task not found')
            elif compra_task.due is None:
                shopping_subtasks_msgs.append('- Compra has no due date; subtasks were not evaluated')
            else:
                compra_due_date = due_to_date(compra_task.due.date)
                if compra_due_date is None:
                    shopping_subtasks_msgs.append('- Compra due date could not be parsed; subtasks were not evaluated')
                else:
                    compra_due_str = compra_due_date.strftime('%Y-%m-%d')
                    moved_or_reviewed = 0
                    compra_subtasks = list(filter(lambda task: task.parent_id == compra_task_id and task.due is not None, all_tasks))
                    for subtask in compra_subtasks:
                        subtask_due_date = due_to_date(subtask.due.date)
                        if subtask_due_date is not None and subtask_due_date < compra_due_date:
                            moved_or_reviewed += 1
                            old_due = subtask_due_date.strftime('%Y-%m-%d')
                            original_due_string = subtask.due.string
                            original_is_recurring = getattr(subtask.due, 'is_recurring', False)
                            try:
                                if original_is_recurring and original_due_string:
                                    # Keep the original recurrence text and only shift the current occurrence date.
                                    self.tf.update_task(
                                        task_id=subtask.id,
                                        due_string=original_due_string,
                                        due_date=compra_due_str,
                                        due_lang='es'
                                    )
                                else:
                                    self.tf.update_task(task_id=subtask.id, due_date=compra_due_str)

                                updated_subtask = self.tf.get_task(subtask.id)
                                updated_is_recurring = getattr(updated_subtask.due, 'is_recurring', False) if updated_subtask.due is not None else False
                                updated_due_string = updated_subtask.due.string if updated_subtask.due is not None else None
                                updated_due_date = due_to_date(updated_subtask.due.date) if updated_subtask.due is not None else None

                                if original_is_recurring and not updated_is_recurring:
                                    shopping_subtasks_msgs.append(
                                        f'- "{subtask.content}" moved to {compra_due_str}, but recurrence was lost. Review needed (original: {original_due_string})'
                                    )
                                elif updated_due_date is None or updated_due_date != compra_due_date:
                                    shopping_subtasks_msgs.append(
                                        f'- "{subtask.content}" kept recurrence but could not be aligned to Compra date. Current due: {updated_subtask.due.date}, target: {compra_due_str}'
                                    )
                                else:
                                    shopping_subtasks_msgs.append(
                                        f'- "{subtask.content}" moved from {old_due} to {compra_due_str} ({updated_due_string})'
                                    )
                            except Exception as e:
                                shopping_subtasks_msgs.append(
                                    f'- "{subtask.content}" could not be moved: {e}'
                                )

                    if moved_or_reviewed == 0:
                        shopping_subtasks_msgs.append('- No overdue Compra subtasks to move')

            def similar_tasks(project_ids, umbral=0.5):
                project_tasks = []
                similars = []
                for task in all_tasks:
                    if task.project_id not in project_ids:
                        project_tasks.append(task.content)
                for i in range(len(project_tasks)-1):
                    for j in range(i+1,len(project_tasks)):
                        message = fun.are_similar(project_tasks[i], project_tasks[j], umbral=umbral) 
                        if message != None and message != 'Agua & Agua' and message != 'Tweet & Tweet' and message != 'README & README' and message != 'Trabajo & Trabajo':
                            similars.append(message)
                return similars 
            
            # Remove Work label
            for task in list(filter(lambda task: 'Work' in task.labels and task.project_id == '6Q7XxhMv85jvw69M', all_tasks)):
                self.tf.update_task(task_id=task.id,
                                    labels=[label for label in task.labels if label != 'Work'])
                
            # Remove Work label and move from the inbox
            for task in list(filter(lambda task: 'Work' in task.labels and task.project_id == '6Crcvw8HFvwxMCqc', all_tasks)):
                self.tf.update_task(task_id=task.id,
                                    labels=[label for label in task.labels if label != 'Work'],
                                    due_string="today")
                self.tf.move_task(task_id=task.id,
                                  project_id='6Q7XxhMv85jvw69M')
            
            # Add duration labels
            for task in list(filter(lambda task: task.duration is not None and all(label not in task.labels for label in ['Long', 'Med', 'Short']), all_tasks)):
                new_label = fun.get_duration_label(task.duration.amount)
                self.tf.update_task(task_id=task.id,
                                    labels=task.labels+[new_label])
                message = f'{task.content}'
                duration_msgs.append("- "+message.split(' updated correctly to ')[-1])
            
            # Move out from the inbox
            for task in list(filter(lambda task: task.project_id == '6Crcvw8HFvwxMCqc' and 'Work' not in task.labels, all_tasks)):
                self.tf.update_task(task_id=task.id,
                                    content=task.content[0].upper()+task.content[1:],
                                    priority=fun.priority_inversal(3),
                                    due_string="today")
                message = f'Task "{task.content}" moved out from the inbox'
                self.tf.move_task(task_id=task.id,
                                  project_id='6JqmRWG4gxwvmgRg')
                inbox_cleaning_msg.append('- '+message.split(' updated correctly to ')[-1])
            
            # Capitalize title
            for task in list(filter(lambda task: task.content[0].upper() != task.content[0], all_tasks)):
                self.tf.update_task(task_id=task.id,
                                    content=task.content[0].upper()+task.content[1:])
                message = f'{task.content}'
                capitalization_msgs.append('- '+message.split(' updated correctly to ')[-1])
            
            # Birthday labels
            for task in list(filter(lambda task: task.project_id == '6Crcvw8HRWFQ4cw3' and task.labels != ['Phone','Short'], all_tasks)):
                try:
                    month = task.due.date[5:7]
                    day = task.due.date[8:10]
                    self.tf.update_task(task_id=task.id,
                                        due_string=f'cada {day} {month} 23:00',
                                        labels=['Phone','Short'])
                    message = f'{task.content}'
                    self.tf.add_reminder(task_id=task.id,
                                         minute_offset=1380)
                    birthday_msgs.append("- "+message.split(' updated correctly to ')[-1])
                except:
                    birthday_msgs.append(f"Task '{task.content}' probably does not have a proper due_string")
            
            # Suitcase and expenses tasks
            for task in list(filter(lambda task: 'Vacations' in task.labels and task.project_id == '6Crcvw8HQm7HhcFv', all_tasks)):
                title = task.content
                if not any(filter(lambda t: t.content == f'Preparar maleta {title}', all_tasks)):
                    vacation_day = datetime.strptime(task.due.date.strftime('%Y-%m-%d'), '%Y-%m-%d') 
                    if vacation_day > today + timedelta(days=3):
                        self.tf.add_task(content=f'Preparar maleta {title}',
                                          due_string=f"3 dias antes de {task.due.date.strftime('%Y-%m-%d')}",
                                          priority=fun.priority_inversal(2), #orange
                                          labels=['Long', 'Home'],
                                          project_id='6Crcvw8HP8h84jJV')
                        message = f'Task "Preparar maleta {title}" created succesfully'
                        suitcase_msgs.append("- "+message)
                        
                if not any(filter(lambda t: t.content == f'Apuntar gastos {title}', all_tasks)):
                    if 'fin' in task.due.string or 'ending' in task.due.string:        
                        self.tf.add_task(content=f'Apuntar gastos {title}',
                                          due_string=f"1 dia despues de {task.due.date.strftime('%Y-%m-%d')}",
                                          priority=fun.priority_inversal(3), #blue
                                          labels=['Phone', 'PC', 'Long'],
                                          project_id='6Crcvw8HP8h84jJV')
                        message = f'Task "Apuntar gastos {title}" created succesfully'
                        expenses_msgs.append("- "+message)
            
            # Counter task
            task_id = '6W4Q22F3fgF7mMf6'
            task = self.tf.get_task(task_id)
            if task.is_completed:
                self.tf.uncomplete_task(task_id)
                self.tf.update_task(task_id=task_id, due_string=f'today at 6 am')
                
            
            # Breakfast task
            task_id = '6fwqMHR8Q59j76Jc'
            task = self.tf.get_task(task_id)
            if weekday in [0, 2, 5, 6]:
                if task.is_completed:
                    self.tf.uncomplete_task(task_id)
                    self.tf.update_task(task_id=task_id, due_string=f'today at 9 am')

            # Weekly tasks
            for task in list(filter(lambda task: 'Weekly' in task.labels, all_tasks)):
                due = datetime.strptime(task.due.date.strftime('%Y-%m-%d'), "%Y-%m-%d").date()
                priority = task.priority
                evaluate_deadline = True
                if task.deadline is not None:
                    deadline = datetime.strptime(task.deadline.date.strftime('%Y-%m-%d'), "%Y-%m-%d").date()
                else:
                    evaluate_deadline = False
                days_until_sunday_from_due = (6 - due.weekday()) % 7
                next_sunday_from_due = due + timedelta(days=days_until_sunday_from_due)
                if not evaluate_deadline or next_sunday_from_due != deadline:
                    self.tf.update_task(task_id=task.id, deadline_date=next_sunday_from_due)
                    weekly_deadlines_msgs.append(f'- Task "{task.content}" moved to {next_sunday_from_due.strftime("%Y-%m-%d")}')
                if task.project_id != '6VW5PFC4hgwP8RVP':
                    if due.weekday() in [4, 5] and priority != fun.priority_inversal(2):
                        self.tf.update_task(task_id=task.id, priority=fun.priority_inversal(2))
                    elif due.weekday() == 6 and priority != fun.priority_inversal(1):
                        self.tf.update_task(task_id=task.id, priority=fun.priority_inversal(1))
                    elif due.weekday() in [0, 1, 2, 3] and priority != fun.priority_inversal(3):
                        self.tf.update_task(task_id=task.id, priority=fun.priority_inversal(3))
                
            # Similar tasks       
            similars = similar_tasks(project_ids=['6Crcvw8HQ7pGFH8v',
                                                 '6Crcvw8HPWrHFWMx',
                                                 '6g2gVxRGGVQJx76J',
                                                 '6FhQxfCg5jxP4XpP',
                                                 '6V72655fCQ3gChqh'],
                                       umbral=0.7)
            similar_tasks_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'similartasksdiego.csv')
            if weekday == 0:
                similars_blob = []
            else:
                if os.path.exists(similar_tasks_csv):
                    similars_df = pd.read_csv(similar_tasks_csv)
                    similars_blob = list(similars_df['similar'].values)
                else:
                    similars_blob = []
            if similars != []:
                for similar in similars:
                    if similar not in similars_blob:
                        similar_msgs.append(f'- {similar}')
                        similars_blob.append(similar)
                similars_df = pd.DataFrame(similars, columns=["similar"])
                os.makedirs(os.path.dirname(similar_tasks_csv), exist_ok=True)
                similars_df.to_csv(similar_tasks_csv, index=False)
                

            # Fantasy
            evaluate = True
            fantasy_task_id = '66V2HG92vFgV7Q2x'
            if self.tf.get_task(fantasy_task_id).is_completed == True:
                self.tf.uncomplete_task(fantasy_task_id)
                self.tf.update_task(task_id=fantasy_task_id, due_string='every friday 20:00')
                message = 'Fantasy task moved back to weekends'
                fantasy_msg.append(message)
                evaluate = False
            if evaluate:
                if weekday in [0,5,6] and self.tf.get_task(fantasy_task_id).due.date != today.strftime('%Y-%m-%d'):
                    for task in filter(lambda task: task.section_id == '65VQ7M3vHH6q3FCw' and task.parent_id == '6cFCJHXxwmQR3v9M', all_tasks):
                        try:
                            fantasy_task = list(filter(lambda task: task.id == fantasy_task_id, all_tasks))[0]
                            fantasydate = datetime.strptime(fantasy_task.due.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                            matchday = datetime.strptime(task.due.date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                            if fantasydate > matchday > fun.get_next_monday():
                                message = 'Fantasy task moved to Tuesday'
                                fantasy_msg.append(message) 
                                self.tf.update_task(task_id=fantasy_task_id, due_string="Tuesday 7 pm")
                                break
                        except TypeError: # due date is None, not matchdate released yet
                            pass
                
            # Permanent tasks
            completed_tasks = self.tf.get_completed_tasks_by_completion_date(limit=100, since=(today - timedelta(days=10)), until=today)
            
            for task in list(filter(lambda task: 'Permanent' in task.labels, completed_tasks)):
                task_id = task.id
                project_id = task.project_id
                self.tf.uncomplete_task(task_id)
                self.tf.update_task(task_id=task_id, due_string="No date")
                message = f'Task "{task.content}" uncompleted'
                if project_id == '6Crcvw8HQm7HhcFv':
                    self.tf.move_task(task_id=task_id, project_id='6F63g3w6f352G8P4')
                    message += f' and moved from {projects_dict_id["6Crcvw8HQm7HhcFv"]} to {projects_dict_id["6F63g3w6f352G8P4"]}'
                permanenttasks_msg.append("- " + message)

            # Results
            body = messages[0] + "\n"
            count = 1
            for title in messages_dict.keys():
                if messages_dict[title] != []:
                    body += "\n" + f"{count}. " + title + "\n"
                    for msg in messages_dict[title]:
                        body += "  " + msg +"\n"
                    count += 1
            if fantasy_msg != []:
                body += "\n" + f"{count}. " + fantasy_msg[0] + "\n"
            if permanenttasks_msg != []:
                if permanenttasks_msg[0][:2] != "- ":
                    body += "\n" + f"{count}. " + permanenttasks_msg[0] + "\n"
                else:
                    body += "\n" + f"{count}. Permanent task to uncomplete: \n"
                    for msg in permanenttasks_msg:
                        body += "  " + msg +"\n"
            if body == messages[0] + "\n":
                body += '\nNo changes\n'
            runtime = f'Runtime: {round(time.time()-start_time,3)} seconds'
            body += "\n" + runtime
            
            # Mail
            try:
                fun.send_email(subject="Daily Todoist", body=body, to=address)
                return f'{body}\n\nAnd mail sent correctly'
            
            except Exception as e:
                error_msg = fun.format_error_for_email(
                    operation="Daily Todoist - Email Send",
                    e=e,
                    additional_info={
                        "fecha": today.strftime('%Y-%m-%d'),
                        "dia_semana": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday],
                        "tareas_procesadas": len(all_tasks),
                        "cambios_realizados": body.count('\n') - 2
                    }
                )
                return f'{body}\n\nError sending mail:\n{error_msg}'
        
        except Exception as e:
            try:
                additional_info = {
                    "fecha": today.strftime('%Y-%m-%d'),
                    "dia_semana": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday],
                    "estado": "Fallo durante procesamiento de tareas"
                }
                if 'all_tasks' in locals():
                    additional_info['tareas_intentadas'] = len(all_tasks)
                if 'body' in locals():
                    additional_info['progress'] = body[:200] + "..." if len(body) > 200 else body
                    
                error_msg = fun.format_error_for_email(
                    operation="Daily Todoist - Main Process",
                    e=e,
                    additional_info=additional_info
                )
                fun.send_email("Daily Todoist - Error", error_msg, address)
                return error_msg
            except Exception as e2:
                return f'Critical error in Daily execution: {e2}'
               
    def TodoistSuperBet(self, hour: int = 0):
        try:
            today = datetime.today()
            weekday = today.weekday()
            edited = False
            task_id = '6WX594CXh843hx76'
            task = self.tf.get_task(task_id)
            if task.is_completed:
                if weekday in [0, 4] and hour in [16, 17]:
                    self.tf.uncomplete_task(task_id)
                    self.tf.update_task(task_id=task_id, due_string=f'today at 7 pm')
                    edited = True
                elif weekday in [1, 2, 3] and hour in [14, 15]:
                    self.tf.uncomplete_task(task_id)
                    self.tf.update_task(task_id=task_id, due_string=f'today at 5 pm')
                    edited = True
                elif weekday in [5, 6] and hour in [10, 11]:
                    self.tf.uncomplete_task(task_id)
                    self.tf.update_task(task_id=task_id, due_string=f'today at 1 pm')
                    edited = True
                if edited:
                    self.tf.add_reminder(task_id=task_id, minute_offset=0)
            return f'Execution completed, day {weekday}, hour {hour}'
        
        except Exception as e:
            return fun.format_error_for_email(
                operation="SuperBet Task Update",
                e=e,
                additional_info={
                    "task_id": task_id,
                    "day_of_week": weekday,
                    "hour": hour,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
    def TodoistHiddenNightTasks(self):
        try:
            today = datetime.today()
            weekday = today.weekday()
            task_time = 'today at 9 pm'
            wh_task_id = '6X9345CxhcVwWqc7'
            health_task_id = '6fH8GhMx2R9HRq5c'
            apps_task_id = '6fg2gfqGP2gR5Fjc'
            wh_task = self.tf.get_task(wh_task_id)
            health_task = self.tf.get_task(health_task_id)
            apps_task = self.tf.get_task(apps_task_id)
            activate_wh_task = False
            activate_healt_task = False
            if weekday == 6:
                if apps_task.is_completed:
                    self.tf.uncomplete_task(apps_task_id)
                    self.tf.update_task(task_id=apps_task_id, due_string=task_time)
                    self.tf.add_reminder(task_id=apps_task_id, minute_offset=0)
                else:
                    self.tf.update_task(task_id=apps_task_id, due_string=task_time)
                activate_wh_task = True
                activate_healt_task = True
            elif weekday in [2, 4] or activate_wh_task:
                if wh_task.is_completed:
                    self.tf.uncomplete_task(wh_task_id)
                    self.tf.update_task(task_id=wh_task_id, due_string=task_time)
                    self.tf.add_reminder(task_id=wh_task_id, minute_offset=0)
                else:
                    self.tf.update_task(task_id=wh_task_id, due_string=task_time)
            elif weekday in [0, 3] or activate_healt_task:
                if health_task.is_completed:
                    self.tf.uncomplete_task(health_task_id)
                    self.tf.update_task(task_id=health_task_id, due_string=task_time)
                    self.tf.add_reminder(task_id=health_task_id, minute_offset=0)
                else:
                    self.tf.update_task(task_id=health_task_id, due_string=task_time)
            return f'Execution completed, day {weekday}'
        
        except Exception as e:
            return fun.format_error_for_email(
                operation="Hidden Night Tasks Update",
                e=e,
                additional_info={
                    "day_of_week": weekday,
                    "wh_task_id": wh_task_id,
                    "health_task_id": health_task_id,
                    "apps_task_id": apps_task_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
    def TodoistToDoLP(self, address):
        try:
    #         def refreshTasks():
    #             all_tasks = self.tf.get_tasks(to_dict=False)
    #             task_dict_id, task_dict_name = self.tf.get_tasks()
    #             return all_tasks, task_dict_id, task_dict_name
            
    #         _, _, task_dict_name = refreshTasks()
            
    #         task_names = todo_df['Name'].values
    #         created_tasks = []
    #         edited_tasks = []
    #         for task_name in task_names:
    #             task_name_cap = task_name.capitalize().rstrip()
    #             task_labels = todo_df[todo_df["Name"] == task_name]["Labels"].values[0].split(" / ")
    #             task_labels = [task.rstrip() for task in task_labels]
    #             task_description = todo_df[todo_df['Name'] == task_name]['Link'].values[0]
    #             if task_name_cap in task_dict_name.keys():
    #                 task_id = task_dict_name[task_name_cap][0]
    #                 task = self.tf.get_task(id=task_id)
    #                 if set(task_labels) != set(task.labels):
    #                     print(f'Task {task_name_cap} has different labels. From {task.labels} to {task_labels}')
    #                     self.tf.update_task(task_id=task_id, labels=task_labels)
    #                     edited_tasks.append(task_name_cap)
    #                 # else:
    #                 #     print(f'Task {task_name_cap} already there')
    #             else:
    #                 self.tf.add_task(content=task_name_cap,
    #                                   labels=task_labels,
    #                                   priority=fun.priority_inversal(3),
    #                                   description=task_description,
    #                                   project_id='2330796907')
    #                 created_tasks.append(task_name_cap) 
    #                 print(f'{task_name_cap} created')
    #         body = ""
    #         if created_tasks != []:
    #             items = ""
    #             for task in created_tasks:
    #                 items += f'\n- {task}'
    #             body += f'New tasks:\n {items}\n\n\n'
    #         if edited_tasks != []:
    #             items = ""
    #             for task in edited_tasks:
    #                 items += f'\n- {task}'
    #             body += f'Updated tasks:\n {items}\n\n\n' 
    #         if body == "":
    #             body = 'No changes'
    #         fun.send_email("Todoist ToDo LP", body, address)
            return True
            
        except Exception as e:
            try:
                error_msg = fun.format_error_for_email(
                    operation="ToDoLP Data Sync",
                    e=e,
                    additional_info={
                        "timestamp": datetime.now().isoformat(),
                        "recipient": address
                    }
                )
                fun.send_email("Todoist ToDo LP - Error", error_msg, address)
                return error_msg
            except Exception as e2:
                return f'Critical error in ToDoLP: {e2}'
 
    def TodoistWeather(self):
        try:
            all_tasks = self.tf.get_tasks()
            
            api_key = os.getenv('OPEN_WEATHER_API_KEY')
            city_name = 'Colmenarejo'
            base_url = 'http://api.openweathermap.org/data/2.5/weather'
            full_url = f"{base_url}?q={city_name}&appid={api_key}&units=metric&lang=com"
            response = requests.get(full_url)

            if response.status_code == 200:
                data = response.json()
                if data['weather'][0]['description'] in ['clear sky', 'few clouds', 'scattered clouds']:
                    
                    today = datetime.today()
                    month = today.month
                    if month >= 6:
                        return f'Not in date'
                    today_str = today.strftime('%Y-%m-%d')
                    sun_start = today.replace(hour=15, minute=30)
                    sun_end = today.replace(hour=16, minute=0)
                    for task in all_tasks:
                        try:
                            if 'Outside' in task.labels and today_str in task.due.date and task.priority in [3, 4]:
                                if '15:30' in task.due.date:
                                    return f'Task not created beacuse of time'
                                elif task.duration.amount > 0:
                                    task_init = datetime.strptime(task.due.date, '%Y-%m-%dT%H:%M:%S')
                                    task_end = task_init + timedelta(minutes=task.duration.amount)
                                    if task_init < sun_end and task_end > sun_start:
                                        return f'Task not created beacuse of time'
                        except:
                            pass
                    
                    task_id = '6XCPqCqfmV4g424G'
                    task = self.tf.get_task(task_id)
                    if task.is_completed:
                        self.tf.uncomplete_task(task_id)
                    self.tf.update_task(task_id=task_id, due_string=f'today at 15:30', duration=30, duration_unit='minute')
                    self.tf.add_reminder(task_id=task_id, minute_offset=30)
                    
                    return f'Task created'
                
                else:
                    return f'Task not created beacuse of weather: {data["weather"][0]["description"]}'
                    
            else:
                return f'Error getting data: {response.status_code}'
                
        except Exception as e:
            return fun.format_error_for_email(
                operation="Weather Task Creation",
                e=e,
                additional_info={
                    "city": 'Colmenarejo',
                    "timestamp": datetime.now().isoformat(),
                    "total_tasks_to_check": len(all_tasks) if 'all_tasks' in locals() else 'No tasks loaded'
                }
            )

               
if __name__ == "__main__":
    main = MainDiego(todoist_api_token=os.getenv('TODOIST_API_TOKEN'))
    print(f'Daily execution: {main.TodoistDaily(address=os.getenv("DIEGO_EMAIL"))}')
    # print(f'SuperBet execution: {main.TodoistSuperBet(weekday=datetime.today().weekday(), hour=datetime.today().hour)}')
    # print(f'Whatsapp execution: {main.TodoistWhatsapp()}')
    # print(f'Whatsapp execution: {main.TodoistHealthcare()}')
    # print(f'LigaPistachoToDo execution: {main.TodoistToDoLP(address=os.getenv("DIEGO_EMAIL"))}')
    # print(f'Weather execution: {main.TodoistWeather()}')