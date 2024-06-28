import functions as fun
from todoist_api_python.api import TodoistAPI
from azure.storage.blob import BlobServiceClient

from datetime import datetime
import pandas as pd
import time
import os

from dotenv import load_dotenv

load_dotenv()
 
def mainDiego():
    try:
        
        start_time = time.time()
        today = datetime.today()
        messages = [f'Todoist Automation for {today.strftime("%Y-%m-%d")}']
        duration_msgs = []
        inbox_cleaning_msg = []
        capitalization_msgs = []
        birthday_msgs = []
        suitcase_msgs = []
        expenses_msgs = []
        similar_msgs = []
        fantasy_msg = []
        recurringtasks_msg = []
        messages_dict = {f'Tasks to add duration labels:': duration_msgs,
                         f'Tasks to move out from de inbox:': inbox_cleaning_msg,
                         f'Tasks to capitalize its content:': capitalization_msgs,
                         f'Tasks to add birthday labels:': birthday_msgs,
                         f'New suitcase tasks:': suitcase_msgs,
                         f'New expenses tasks': expenses_msgs,
                         f'Next tasks are similar:': similar_msgs}
        
        # Todoist
        api_token = os.getenv("TODOIST_API_TOKEN")
        api = TodoistAPI(api_token)
        
        # Azure Blob
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        try:
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client("todoist-container")
        except Exception as e:
            return False
        
        # Projects, sections and tasks
        all_projects = fun.getProjects()
        projects_dict_id, projects_dict_name = fun.getProjectsDicts(all_projects)
        def refreshTasks():
            all_tasks = fun.getTasks()
            task_dict_id, task_dict_name = fun.getTasksDicts(all_tasks, projects_dict_id, projects_dict_name)
            return all_tasks, task_dict_id, task_dict_name
        all_tasks, task_dict_id, task_dict_name = refreshTasks()
        all_sections = fun.getSections()
        sections_dict_id, sections_dict_name = fun.getSectionsDicts(all_sections)
        label_names=[]
        for task in all_tasks:
            gross_labels=task['labels']
            for label in gross_labels:
                if label not in label_names:
                    label_names.append(label)
        label_names

        # Functions
        def createTask(
            content = "Tarea creada automáticamente",
            description = None,
            project_id = projects_dict_name['Inbox'],
            section_id = None,
            parent_id = None,
            order = 1,
            labels = [],
            priority = 1,
            comment_count = 0,
            due_string = None,
            due_date = None,
            due_datetime = None,
            due_lang = None,
            assignee_id = None,
            duration = None,
            duration_unit = None
        ):
            for label in labels:
                if label not in label_names:
                    return f'La etiqueta {label} no existe'
            try:
                task = api.add_task(
                    assignee_id = assignee_id,
                    comment_count = comment_count,
                    content = content,
                    description = description,
                    due_string = due_string,
                    due_date = due_date,
                    due_datetime = due_datetime,
                    due_lang = due_lang,
                    duration = duration,
                    labels = labels,
                    order = order,
                    priority = fun.priorityInversal(priority),
                    project_id = project_id,
                    section_id = section_id,
                    parent_id = parent_id,
                    duration_unit = duration_unit
                )
                message = f'Task "{task.content}" ({task.id}) was created correctly'
                return message
            except Exception as error:
                print (error)
                return error
        def editTask(
            task_id,
            content = None,
            assignee_id = None,
            description = None,
            due_date = None,
            due_string = None,
            due_datetime = None,
            labels = None,
            priority = None,
        ):
            task = api.get_task(task_id)
            labels = task.labels if labels == None else labels
            content = task.content if content == None else content
            for label in labels:
                if label not in label_names:
                    return f'La etiqueta {label} no existe'
            if priority != None:
                priority = fun.priorityInversal(priority)
            try:
                api.update_task(
                    task_id = task_id,
                    assignee_id = assignee_id,
                    content = content,
                    description = description,
                    labels = labels,
                    priority = priority,
                    due_date = due_date,
                    due_string = due_string,
                    due_datetime = due_datetime,
                )
                message = f'Task {task.content} updated correctly to {content}'
                return message
            except Exception as error:
                return error
        def createSection(name, project_id):
            try:
                section = api.add_section(name=name, project_id=project_id)
                return section
            except Exception as error:
                return error
        def updateTaskDurationLabel(task_id, task_duration):
            duration_label = fun.getDurationLabel(task_duration)
            task_id = task_id[0]
            task_labels_without_duration = fun.getLabelsWithoutDuration(task_id)
            task_labels_without_duration.append(duration_label)
            return editTask(task_id=task_id,
                    labels=task_labels_without_duration)
        def similarTasks(project_ids, umbral=0.5):
            project_tasks = []
            similars = []
            for task in all_tasks:
                if task['project_id'] in project_ids:
                    project_tasks.append(task['id'])
            for i in range(len(project_tasks)-1):
                for j in range(i+1,len(project_tasks)):
                    message = fun.areSimilar(task_dict_id[project_tasks[i]][0],
                                                task_dict_id[project_tasks[j]][0],
                                                umbral=umbral) 
                    if message != None and message != 'Agua & Agua' and message != 'Tweet & Tweet' and message != 'README & README':
                        similars.append(message)
            return similars
        
        all_tasks, task_dict_id, task_dict_name = refreshTasks()
        
        # Basic orders
        for task in all_tasks:
            
            # Add duration
            if task['duration'] != None and task['due'] != None:
                if fun.getDurationLabel(task['duration']['amount']) not in task['labels']:
                    message = updateTaskDurationLabel([task['id']],
                                                      task['duration']['amount'])
                    duration_msgs.append("- "+message.split(' updated correctly to ')[-1])
            
            # Move out from the inbox
            if task['project_id'] == projects_dict_name['Inbox']:
                message = editTask(task_id=task['id'],
                                   content=task['content'][0].upper()+task['content'][1:],
                                   priority=3,
                                   due_string="today")
                fun.moveTask(task_id=task['id'],
                             project_id=projects_dict_name['Tareas'])
                inbox_cleaning_msg.append('- '+message.split(' updated correctly to ')[-1])
                break
                
            # Capitalize title
            if task["content"][0].upper() != task["content"][0]:
                message = editTask(task_id=task['id'],
                                   content=task['content'][0].upper()+task['content'][1:])
                capitalization_msgs.append('- '+message.split(' updated correctly to ')[-1])
                
            # Capitalize some words 
            if task['project_id'] == projects_dict_name['Inbox']:
                break
                retext = fun.capitalizeProperNounsSpacy(task['content'])
                if retext != task['content']:
                    to_update = True
                    task_id = task["id"]
                    message = editTask(task_id = task_id,
                                    content = retext)
                    capitalization_msgs.append("- " + message)
                
            # Birthday labels
            if task['project_id'] == projects_dict_name['Cumpleaños'] and task['labels'] != ['Phone','Short']:
                to_update = True
                message = editTask(task_id=task['id'],
                        labels=['Phone','Short'])
                birthday_msgs.append("- "+message.split(' updated correctly to ')[-1])

            # Suitcase task
            if 'Vacations' in task['labels'] and task['project_id'] == projects_dict_name['Calendario']:
                title = task["content"]
                try:
                    task_dict_name[f'Preparar maleta {title}']
                except:
                    message = createTask(content=f'Preparar maleta {title}',
                                         due_string=f"3 dias antes de {task['due']['date']}",
                                         priority=2,
                                         project_id=projects_dict_name['Recordatorios'])
                    suitcase_msgs.append("- "+message)
            
            # Expenses task
            if 'Vacations' in task['labels'] and task['project_id'] == projects_dict_name['Calendario']:
                title = task["content"]
                try:
                    task_dict_name[f'Apuntar gastos de {title}']
                except:
                    if task['due']['string'][-14:-8] == "fin 20":        
                        message = createTask(content=f'Apuntar gastos de {title}',
                                                due_string=f"1 dia despues de {task['due']['string'][-10:]}",
                                                priority=3,
                                                project_id=projects_dict_name['Recordatorios'])
                        expenses_msgs.append("- "+message)
    
        if duration_msgs != [] or capitalization_msgs != [] or birthday_msgs != [] or suitcase_msgs != []:
            all_tasks, task_dict_id, task_dict_name = refreshTasks()
                
        # Similar tasks       
        similars = similarTasks(project_ids=[projects_dict_name['Archivados'],
                                             projects_dict_name['Recordatorios'],
                                             projects_dict_name['Tareas'],
                                             projects_dict_name['Calendario'],
                                             projects_dict_name['Cursos'],
                                             projects_dict_name['GitHub'],
                                             projects_dict_name['Diarias'],
                                             projects_dict_name['Semanales'],
                                             projects_dict_name['Mensuales']],
                                umbral=0.7)
        if similars != []:
            for similar in similars:
                similar_msgs.append(f'- {similar}')
        
        # Fantasy
        evaluate = True
        if fun.getTask('4632052423').is_completed == True:
            fun.uncompleteTask('4632052423')
            editTask('4632052423', due_string='every friday 20:00')
            message = 'Fantasy task moved back to fridays'
            fantasy_msg.append(message)
            evaluate = False
        if evaluate:
            if today.weekday() in [0,5,6] and fun.getTask('4632052423').due.date != today.strftime('%Y-%m-%d'):
                for task in all_tasks:
                    if task['section_id'] == '51988025' and task['parent_id'] == '8023322112':
                        try:
                            fantasydate = datetime.strptime(fun.getTask('4632052423').due.date, '%Y-%m-%d')
                            matchday = datetime.strptime(task['due']['date'][:10], '%Y-%m-%d')
                            if fantasydate > matchday > fun.getNextMonday():
                                message = 'Fantasy task moved to Tuesday'
                                fantasy_msg.append(message)
                                editTask('4632052423', due_string="Tuesday")
                                all_tasks, task_dict_id, task_dict_name = refreshTasks()
                                break
                        except TypeError:
                            pass
             
        # Recurring tasks
        update_recurringtasksdiego = True
        try:
            df_recurringtasks = fun.readCsvFromBlob('recurringtasks/recurringtasksdiego.csv')
        except Exception as e:
            message = f'Error al cargar el csv de recurrentes del blob: {e}'
            update_recurringtasksdiego = False
            recurringtasks_msg.append(message)
            
        if update_recurringtasksdiego:
            recurringtasks = df_recurringtasks.set_index('task_id')['project_id'].to_dict()
            recurringtasks = {str(k): str(v) for k, v in recurringtasks.items()}
            exists = True
            to_update = False
            for task_id in recurringtasks.keys():
                project_id = recurringtasks[task_id]
                try:
                    project_name = projects_dict_id[project_id]
                except KeyError:
                    message = f'La tarea {task_id} está un proyecto que no existe: {project_id}'
                    recurringtasks_msg.append("- " + message)
                    exists = False
                if exists:
                    if project_name != "Archivados" and project_name != "Tickler" :
                        task = fun.getTask(task_id)
                        if task.is_completed:
                            to_update = True
                            fun.uncompleteTask(task_id)
                            message = editTask(task_id=task_id,
                                               due_string="No date")
                            if task.project_id == projects_dict_name["Calendario"]:
                                fun.moveTask(task_id=task_id,
                                             project_id='2263729931')
                                message += 'and it was moved from "Calendario" to "Archivados"'
                            recurringtasks_msg.append("- " + message)
                
            if to_update:
                
                all_tasks, task_dict_id, task_dict_name = refreshTasks()

                tasks = api.get_tasks()
                recurringtasks={}
                for task in tasks:
                    if 'Recurring' in task.labels:
                        recurringtasks[task.id]=task.project_id
                df_recurringtasks = pd.DataFrame.from_dict({'task_id':recurringtasks.keys(),'project_id':recurringtasks.values()})       
                try:
                    fun.uploadCsvToBlob(df_recurringtasks, 'recurringtasks/recurringtasksdiego.csv')
                except:
                    recurringtasks_msg.append("Error al guardar las tareas recurrentes")

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
            body += "\n" + f"{count}." + fantasy_msg + "\n"  
        if recurringtasks_msg != []:
            if recurringtasks_msg[0][:2] != "- ":
                body += "\n" + f"{count}. " + recurringtasks_msg[0] + "\n"
            else:
                body += "\n" + f"{count}. Recurring task to uncomplete: \n"
                for msg in recurringtasks_msg:
                    body += "  " + msg +"\n"
        if body == messages[0] + "\n":
            body += '\nNo changes\n'
        runtime = f'Runtime: {round(time.time()-start_time,3)} seconds'
        body += "\n" + runtime
        
        # Mail
        fun.sendEmail("Daily Todoist", body, "diegorodgar17@gmail.com")

        return True
    
    except Exception as e:
        try:
            fun.sendEmail("Daily Todoist - Error", f"{messages[0]}\n\nThere was an error:\n- {e}", "diegorodgar17@gmail.com")
            return False
        except Exception as e2:
            return f'Error {e}\n\nAnd error sending error mail: {e2}'

def mainToni():
    try:
        fun.sendEmail("Daily Todoist", f'...', 'asevillasastre@gmail.com')
        return True
    except Exception as e:
        fun.sendEmail("Daily Todoist - Error", f'...', 'asevillasastre@gmail.com')
        return e
    
def mainRetu():
    try:
        fun.sendEmail("Daily Todoist", f'...', 'marioretu00@gmail.com')
        return True
    except Exception as e:
        fun.sendEmail("Daily Todoist - Error", f'...', 'marioretu00@gmail.com')
        return e
    
if __name__ == "__main__":
    print(f'Diego execution: {mainDiego()}')
    # print(f'Toni execution: {mainToni()}')
    # print(f'Retu execution: {mainRetu()}')