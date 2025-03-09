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
            similar_msgs = []
            fantasy_msg = []
            permanenttasks_msg = []
            messages_dict = {f'Tasks to add duration labels:': duration_msgs,
                            f'Tasks to move out from de inbox:': inbox_cleaning_msg,
                            f'Tasks to capitalize its content:': capitalization_msgs,
                            f'Tasks to add birthday labels:': birthday_msgs,
                            f'New suitcase tasks:': suitcase_msgs,
                            f'New expenses tasks': expenses_msgs,
                            f'Next tasks are similar:': similar_msgs}
            
            # Azure Blob
            connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            az = fun.AzureBlobFunctions(connect_str)
            
            # Projects, sections and tasks
            projects_dict_id, _ = self.tf.getProjects()
            def refreshTasks():
                all_tasks = self.tf.getTasks(to_dict=False)
                task_dict_id, task_dict_name = self.tf.getTasks()
                return all_tasks, task_dict_id, task_dict_name
            all_tasks, task_dict_id, task_dict_name = refreshTasks()
            label_names=[]
            for task in all_tasks:
                gross_labels=task['labels']
                for label in gross_labels:
                    if label not in label_names:
                        label_names.append(label)
            label_names

            # Functions
            def updateTaskDurationLabel(task_id, task_duration):
                duration_label = self.tf.getDurationLabel(task_duration)
                task_id = task_id[0]
                task_labels_without_duration = self.tf.getLabelsWithoutDuration(task_id)
                task_labels_without_duration.append(duration_label)
                self.api.update_task(task_id=task_id,
                                labels=task_labels_without_duration)
            def similarTasks(project_ids, umbral=0.5):
                project_tasks = []
                similars = []
                for task in all_tasks:
                    if task['project_id'] not in project_ids:
                        project_tasks.append(task['id'])
                for i in range(len(project_tasks)-1):
                    for j in range(i+1,len(project_tasks)):
                        message = fun.areSimilar(task_dict_id[project_tasks[i]][0],
                                                 task_dict_id[project_tasks[j]][0],
                                                 umbral=umbral) 
                        if message != None and message != 'Agua & Agua' and message != 'Tweet & Tweet' and message != 'README & README' and message != 'Trabajo & Trabajo':
                            similars.append(message)
                return similars
            
            all_tasks, task_dict_id, task_dict_name = refreshTasks()
            
            # Basic orders
            for task in all_tasks:
                
                # Removing Work label from tasks in Work project
                if task['project_id'] == '2316607649' and 'Work' in task['labels']:
                    task['labels'].remove('Work')
                    self.api.update_task(task_id=task['id'], labels=task['labels'])    
                
                # Add duration
                if task['duration'] != None and task['due'] != None:
                    if self.tf.getDurationLabel(task['duration']['amount']) not in task['labels']:
                        updateTaskDurationLabel([task['id']],
                                                        task['duration']['amount'])
                        message = f'{task["content"]}'
                        duration_msgs.append("- "+message.split(' updated correctly to ')[-1])
                
                # Move out from the inbox
                if task['project_id'] == '2258455386':
                    self.api.update_task(task_id=task['id'],
                                    content=task['content'][0].upper()+task['content'][1:],
                                    priority=self.tf.priorityInversal(3),
                                    due_string="today")
                    message = f'Task "{task["content"]}" moved out from the inbox'
                    self.tf.moveTask(task_id=task['id'],
                                project_id='2298494169')
                    inbox_cleaning_msg.append('- '+message.split(' updated correctly to ')[-1])
                    break
                    
                # Capitalize title
                if task["content"][0].upper() != task["content"][0]:
                    message = self.api.update_task(task_id=task['id'],
                                            content=task['content'][0].upper()+task['content'][1:])
                    message = f'{task["content"]}'
                    capitalization_msgs.append('- '+message.split(' updated correctly to ')[-1])
                    
                # Birthday labels
                if task['project_id'] == '2259726698' and task['labels'] != ['Phone','Short']:
                    try:
                        month = task['due']['date'][5:7]
                        day = task['due']['date'][8:10]
                        self.api.update_task(task_id=task['id'],
                                        due_string=f'cada {day} {month} 23:00',
                                        labels=['Phone','Short'])
                        message = f'{task["content"]}'
                        self.tf.setReminder(task_id=task['id'],
                                        minute_offset=1380)
                        birthday_msgs.append("- "+message.split(' updated correctly to ')[-1])
                    except:
                        birthday_msgs.append(f"Task '{task['content']}' probably does not have a proper due_string")
                        
                # Suitcase task
                if 'Vacations' in task['labels'] and task['project_id'] == '2259406345':
                    title = task["content"]
                    try:
                        task_dict_name[f'Preparar maleta {title}']
                    except:
                        vacation_day = datetime.strptime(task['due']['date'][:10], '%Y-%m-%d')
                        if vacation_day > today + timedelta(days=3):
                            self.api.add_task(content=f'Preparar maleta {title}',
                                              due_string=f"3 dias antes de {task['due']['date']}",
                                              priority=self.tf.priorityInversal(2), #orange
                                              labels=['Long', 'Home'],
                                              project_id='2258518194')
                            message = f'Task "Preparar maleta {title}" created succesfully'
                            suitcase_msgs.append("- "+message)
                
                # Expenses task
                if 'Vacations' in task['labels'] and task['project_id'] == '2259406345':
                    title = task["content"]
                    try:
                        task_dict_name[f'Apuntar gastos de {title}']
                    except:
                        if task['due']['string'][-14:-8] == "fin 20":        
                            self.api.add_task(content=f'Apuntar gastos de {title}',
                                              due_string=f"1 dia despues de {task['due']['string'][-10:]}",
                                              priority=self.tf.priorityInversal(3), #blue
                                              labels=['Phone', 'PC', 'Long'],
                                              project_id='2258518194')
                            message = f'Task "Apuntar gastos de {title}" created succesfully'
                            expenses_msgs.append("- "+message)
        
            if duration_msgs != [] or capitalization_msgs != [] or birthday_msgs != [] or suitcase_msgs != []:
                all_tasks, task_dict_id, task_dict_name = refreshTasks()
                    
            # Counter task
            task_id = 8326227450
            task = self.tf.getTask(task_id)
            if task.is_completed:
                self.tf.uncompleteTask(task_id)
                self.api.update_task(task_id=task_id, due_string=f'today at 6 am')
                
            # Investment task
            task_id = 8715203918
            task = self.tf.getTask(task_id)
            if task.is_completed and (weekday == 0 or today.day == 1):
                self.tf.uncompleteTask(task_id)
                self.api.update_task(task_id=task_id, due_string=f'today at 12 pm')
                
            # Similar tasks       
            similars = similarTasks(project_ids=['2259150181',
                                                 '2269361803',
                                                 '2259111397',
                                                 '2332125933',
                                                 '2320233020'],
                                    umbral=0.7)
            if weekday == 0:
                similars_blob = []
            else:
                similars_df = az.readCsvFromBlob(blob_name='similartasks/similartasksdiego.csv')
                similars_blob = list(similars_df['similar'].values)
            if similars != []:
                for similar in similars:
                    if similar not in similars_blob:
                        similar_msgs.append(f'- {similar}')
                        similars_blob.append(similar)
                similars_df = pd.DataFrame(similars, columns=["similar"])
                az.uploadCsvToBlob(df=similars_df, blob_name='similartasks/similartasksdiego.csv')
                

            # Fantasy
            evaluate = True
            if self.tf.getTask('4632052423').is_completed == True:
                self.tf.uncompleteTask('4632052423')
                self.api.update_task(task_id='4632052423', due_string='every friday 20:00')
                message = 'Fantasy task moved back to weekends'
                fantasy_msg.append(message)
                evaluate = False
            if evaluate:
                if weekday in [0,5,6] and self.tf.getTask('4632052423').due.date != today.strftime('%Y-%m-%d'):
                    for task in all_tasks:
                        if task['section_id'] == '51988025' and task['parent_id'] == '8023322112':
                            try:
                                fantasydate = datetime.strptime(self.tf.getTask('4632052423').due.date, '%Y-%m-%d')
                                matchday = datetime.strptime(task['due']['date'][:10], '%Y-%m-%d')
                                if fantasydate > matchday > fun.getNextMonday():
                                    message = 'Fantasy task moved to Tuesday'
                                    fantasy_msg.append(message) 
                                    self.api.update_task(task_id='4632052423', due_string="Tuesday 7 pm")
                                    all_tasks, task_dict_id, task_dict_name = refreshTasks()
                                    break
                            except TypeError:
                                pass
                
            # Permanent tasks
            update_permanenttasksdiego = True
            permanenttasks_route = 'recurringtasks/recurringtasksdiego.csv'
            try:
                df_permanenttasks = az.readCsvFromBlob(permanenttasks_route)
            except Exception as e:
                message = f'Error reading permanent tasks from blob: {e}'
                update_permanenttasksdiego = False
                permanenttasks_msg.append(message)
                
            if update_permanenttasksdiego:
                permanenttasks = df_permanenttasks.set_index('task_id')['project_id'].to_dict()
                permanenttasks = {str(k): str(v) for k, v in permanenttasks.items()}
                
                completed_tasks = self.tf.getCompletedTasks(3)
                uncompleted_tasks = []
                for task in completed_tasks:
                    task_id = task['task_id']
                    project_id = task['project_id']
                    if task_id in permanenttasks.keys() and task_id not in task_dict_id and task_id not in uncompleted_tasks:
                        self.tf.uncompleteTask(task_id)
                        uncompleted_tasks.append(task_id)
                        self.api.update_task(task_id=task_id,
                                             due_string="No date")
                        message = f'Task "{self.tf.getTask(id=task_id).content}" uncompleted'
                        if project_id == '2259406345':
                            self.tf.moveTask(task_id=task_id,
                                            project_id='2263729931')
                            message += f' and moved from {projects_dict_id["2259406345"]} to {projects_dict_id["2263729931"]}'
                        permanenttasks_msg.append("- " + message)
                    
                all_tasks, task_dict_id, task_dict_name = refreshTasks()

                tasks = self.api.get_tasks()
                permanenttasks={}
                for task in tasks:
                    if 'Permanent' in task.labels:
                        permanenttasks[task.id]=task.project_id
                df_permanenttasks = pd.DataFrame.from_dict({'task_id':permanenttasks.keys(),'project_id':permanenttasks.values()})       
                try:
                    az.uploadCsvToBlob(df_permanenttasks, permanenttasks_route)
                except:
                    permanenttasks_msg.append("Error saving permanent tasks")

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
            print(permanenttasks_msg)
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
                fun.sendEmail(subject="Daily Todoist", body=body, to=address)
                return f'{body}\n\nAnd mail sent correctly'
            
            except Exception as e:
                error_msg = fun.buildExceptionMsg(e)
                return f'{body}\n\nAnd error sending mail: {error_msg}'
        
        except Exception as e:
            try:
                error_msg = fun.buildExceptionMsg(e)
                fun.sendEmail("Daily Todoist - Error", error_msg, address)
                return error_msg
            except Exception as e2:
                return f'{error_msg}\n\nAnd error sending error mail: {e2}\n\n{body}'
               
    def TodoistSuperBet(self, hour: int = 0):
        try:
            today = datetime.today()
            weekday = today.weekday()
            edited = False
            task_id = 8554028033
            task = self.tf.getTask(task_id)
            if task.is_completed:
                if weekday in [0, 4] and hour in [16, 17]:
                    self.tf.uncompleteTask(task_id)
                    self.api.update_task(task_id=task_id, due_string=f'today at 7 pm')
                    edited = True
                elif weekday in [1, 2, 3] and hour in [14, 15]:
                    self.tf.uncompleteTask(task_id)
                    self.api.update_task(task_id=task_id, due_string=f'today at 5 pm')
                    edited = True
                elif weekday in [5, 6] and hour in [10, 11]:
                    self.tf.uncompleteTask(task_id)
                    self.api.update_task(task_id=task_id, due_string=f'today at 1 pm')
                    edited = True
                if edited:
                    self.tf.setReminder(task_id=task_id, minute_offset=0)
            return f'Execution completed, day {weekday}, hour {hour}'
        
        except Exception as e:
            error_msg = fun.buildExceptionMsg(e)
            return error_msg
        
    def TodoistWhatsapp(self):
        try:
            today = datetime.today()
            weekday = today.weekday()
            task_id = 8821892607
            task = self.tf.getTask(task_id)
            if weekday in [2, 4, 6]:
                if task.is_completed:
                    self.tf.uncompleteTask(task_id)
                    self.api.update_task(task_id=task_id, due_string=f'today at 9 pm')
                    self.tf.setReminder(task_id=task_id, minute_offset=0)
                else:
                    self.api.update_task(task_id=task_id, due_string=f'today at 9 pm')
                
            return f'Execution completed, day {weekday}'
        
        except Exception as e:
            error_msg = fun.buildExceptionMsg(e)
            return error_msg
    
    def TodoistToDoLP(self, address):
        try:
            connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            az = fun.AzureBlobFunctions(connect_str)
            
            def refreshTasks():
                all_tasks = self.tf.getTasks(to_dict=False)
                task_dict_id, task_dict_name = self.tf.getTasks()
                return all_tasks, task_dict_id, task_dict_name
            
            _, _, task_dict_name = refreshTasks()
            
            todo_df = az.readCsvFromBlob('todoligapistacho.csv')
            
            task_names = todo_df['Name'].values
            created_tasks = []
            edited_tasks = []
            for task_name in task_names:
                task_name_cap = task_name.capitalize().rstrip()
                task_labels = todo_df[todo_df["Name"] == task_name]["Labels"].values[0].split(" / ")
                task_labels = [task.rstrip() for task in task_labels]
                task_description = todo_df[todo_df['Name'] == task_name]['Link'].values[0]
                if task_name_cap in task_dict_name.keys():
                    task_id = task_dict_name[task_name_cap][0]
                    task = self.tf.getTask(id=task_id)
                    if set(task_labels) != set(task.labels):
                        print(f'Task {task_name_cap} has different labels. From {task.labels} to {task_labels}')
                        self.api.update_task(task_id=task_id, labels=task_labels)
                        edited_tasks.append(task_name_cap)
                    # else:
                    #     print(f'Task {task_name_cap} already there')
                else:
                    self.api.add_task(content=task_name_cap,
                                      labels=task_labels,
                                      priority=self.tf.priorityInversal(3),
                                      description=task_description,
                                      project_id='2330796907')
                    created_tasks.append(task_name_cap) 
                    print(f'{task_name_cap} created')
            body = ""
            if created_tasks != []:
                items = ""
                for task in created_tasks:
                    items += f'\n- {task}'
                body += f'New tasks:\n {items}\n\n\n'
            if edited_tasks != []:
                items = ""
                for task in edited_tasks:
                    items += f'\n- {task}'
                body += f'Updated tasks:\n {items}\n\n\n' 
            if body == "":
                body = 'No changes'
            fun.sendEmail("Todoist ToDo LP", body, address)
            return True
            
        except Exception as e:
            try:
                error_msg = fun.buildExceptionMsg(e)
                fun.sendEmail("Todoist ToDo LP - Error", error_msg, address)
                return error_msg
            except Exception as e2:
                return f'{error_msg}\n\nAnd error sending error mail: {e2}'
 
    def TodoistWeather(self):
        try:
            all_tasks = self.tf.getTasks(to_dict=False)
            
            api_key = os.getenv('OPEN_WEATHER_API_KEY')
            city_name = 'Colmenarejo'
            base_url = 'http://api.openweathermap.org/data/2.5/weather'
            full_url = f"{base_url}?q={city_name}&appid={api_key}&units=metric&lang=com"
            response = requests.get(full_url)

            if response.status_code == 200:
                data = response.json()
                if data['weather'][0]['description'] in ['clear sky', 'few clouds', 'scattered clouds']:
                    
                    today = datetime.today()
                    today_str = today.strftime('%Y-%m-%d')
                    sun_start = today.replace(hour=15, minute=30)
                    sun_end = today.replace(hour=16, minute=0)
                    for task in all_tasks:
                        try:
                            if 'Outside' in task['labels'] and today_str in task['due']['date'] and task['priority'] in [3, 4]:
                                if '15:30' in task['due']['date']:
                                    return f'Task not created beacuse of time'
                                elif task['duration']['amount'] > 0:
                                    task_init = datetime.strptime(task['due']['date'], '%Y-%m-%dT%H:%M:%S')
                                    task_end = task_init + timedelta(minutes=task['duration']['amount'])
                                    if task_init < sun_end and task_end > sun_start:
                                        return f'Task not created beacuse of time'
                        except:
                            pass
                    
                    task_id = 8841964065
                    task = self.tf.getTask(task_id)
                    if task.is_completed:
                        self.tf.uncompleteTask(task_id)
                    self.api.update_task(task_id=task_id, due_string=f'today at 15:30',  duration=30, duration_unit='minute')
                    self.tf.setReminder(task_id=task_id, minute_offset=30)
                    
                    return f'Task created'
                
                else:
                    return f'Task not created beacuse of weather: {data["weather"][0]["description"]}'
                    
            else:
                return f'Error getting data: {response.status_code}'
                
        except Exception as e:
            error_msg = fun.buildExceptionMsg(e)
            return error_msg

               
if __name__ == "__main__":
    main = MainDiego(todoist_api_token=os.getenv('TODOIST_API_TOKEN'))
    print(f'Daily execution: {main.TodoistDaily(address=os.getenv("DIEGO_EMAIL"))}')
    # print(f'SuperBet execution: {main.TodoistSuperBet(weekday=datetime.today().weekday(), hour=datetime.today().hour)}')
    # print(f'Whatsapp execution: {main.TodoistWhatsapp()}')
    # print(f'LigaPistachoToDo execution: {main.TodoistToDoLP(address=os.getenv("DIEGO_EMAIL"))}')
    # print(f'Weather execution: {main.TodoistWeather()}')