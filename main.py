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
        today = datetime.today()

        messages = [f'Todoist Automation for {today.strftime("%Y-%m-%d")}']

        start_time = time.time()

        api_token = os.getenv("TODOIST_API_TOKEN")
        api = TodoistAPI(api_token)
        
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        try:
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client("todoist-container")
        except Exception as e:
            print(f'estamos aqui {e}')
            return False
        
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

        to_update = False
        messages.append('Tasks to add duration label...')
        for task in all_tasks:
            if task['duration'] != None and task['due'] != None:
                if fun.getDurationLabel(task['duration']['amount']) not in task['labels']:
                    to_update = True
                    message = updateTaskDurationLabel([task['id']], task['duration']['amount'])
                    messages.append("- " + message)

        if not to_update:
            messages = messages[:-1]
            message = 'No tasks to add duration label'
            messages.append(message)
        else:
            all_tasks, task_dict_id, task_dict_name = refreshTasks()

        to_update = False
        messages.append("Tasks to capitalize some of it's words...")    
        for task in all_tasks:
            if task['project_id'] == projects_dict_name['Inbox']:
                retext = fun.capitalizeProperNounsSpacy(task['content'])
                if retext != task['content']:
                    to_update = True
                    task_id = task["id"]
                    message = editTask(task_id = task_id,
                                    content = retext)
                    messages.append("- " + message)

        if not to_update:
            messages = messages[:-1]
            message = "No tasks to capitalize some of it's words"
            messages.append(message)
        else:
            all_tasks, task_dict_id, task_dict_name = refreshTasks()
        
        try:
            df_recurringtasks = fun.readCsvFromBlob('recurringtasks/recurringtasksdiego.csv')
        except Exception as e:
            print(f'Error al cargar el csv del blob: {e}')
            return False
    
        recurringtasks = df_recurringtasks.set_index('task_id')['project_id'].to_dict()
        recurringtasks = {str(k): str(v) for k, v in recurringtasks.items()}

        cont = True
        to_update = False
        messages.append('Recurring tasks to uncomplete...')
        for task_id in recurringtasks.keys():
            project_id = recurringtasks[task_id]
            try:
                project_name = projects_dict_id[project_id]
            except KeyError:
                message = f'La tarea {task_id} está un proyecto que no existe: {project_id}'
                messages.append("- " + message)
                cont = False
            if cont:
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
                        messages.append("- " + message)
                
        if not to_update:
            messages = messages[:-1]
            message = "No recurring tasks to uncomplete"
            messages.append(message)
        else:
            all_tasks, task_dict_id, task_dict_name = refreshTasks()

        to_update = False
        messages.append('Birthday tasks to add labels...')
        for task in all_tasks:
            if task['project_id'] == projects_dict_name['Cumpleaños'] and task['labels'] != ['Phone','Short']:
                to_update = True
                message = editTask(task_id=task['id'],
                        labels=['Phone','Short'])
                messages.append("- " + message)
                
        if not to_update:
            messages = messages[:-1]
            message = "No birthday tasks to add labels"
            messages.append(message)
        else:
            all_tasks, task_dict_id, task_dict_name = refreshTasks()

        evaluate = True
        if fun.getTask('4632052423').is_completed == True:
            fun.uncompleteTask('4632052423')
            editTask('4632052423', due_string='every friday 20:00')
            message = 'Fantasy task moved back to fridays'
            print (message)
            messages.append(message)
            evaluate = False

        to_update = False
        if evaluate:
            if today.weekday() in [0,5,6] and fun.getTask('4632052423').due.date != today.strftime('%Y-%m-%d'):
                for task in all_tasks:
                    if task['section_id'] == '51988025' and task['parent_id'] == '6968182312':
                        try:
                            fantasydate = datetime.strptime(fun.getTask('4632052423').due.date, '%Y-%m-%d')
                            matchday = datetime.strptime(task['due']['date'][:10], '%Y-%m-%d')
                            if fantasydate > matchday > fun.getNextMonday():
                                message = 'Fantasy task moved to Tuesday'
                                messages.append(message)
                                editTask('4632052423', due_string="Tuesday")
                                to_update = True
                                all_tasks, task_dict_id, task_dict_name = refreshTasks()
                                break
                        except TypeError:
                            pass
            if not to_update:
                message = 'Fantasy not moved'
                messages.append(message)

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
            messages.append('Next tasks are similar:')
            for similar in similars:
                messages.append(f'- {similar}')
        else:
            messages.append('No similar tasks')

        to_update = False
        for task in all_tasks:
            if 'Vacations' in task['labels'] and task['project_id']==projects_dict_name['Calendario']:
                title = task["content"]
                try:
                    task_dict_name[f'Preparar maleta {title}']
                except:
                    to_update = True
                    message = createTask(content=f'Preparar maleta {title}',
                                        due_string=f"3 dias antes de {task['due']['date']}",
                                        priority=2,
                                        project_id=projects_dict_name['Recordatorios'])
                    messages.append(message)
        if to_update:
            all_tasks, task_dict_id, task_dict_name = refreshTasks()

        def newF1Season(year, grand_prix_dict):
            f1_project_id = projects_dict_name['Fórmula 1']
            section_id = createSection(year, f1_project_id).id
            for gp in grand_prix_dict.keys():
                task_id = createTask(content=f'* {gp.upper()}', project_id=f1_project_id, section_id=section_id)[-33:-23]
                day = grand_prix_dict[gp]
                createTask(content=f"Apuntar hora {gp.capitalize()}", priority = 3, due_string=f'4 weeks before {day}', project_id=projects_dict_name['Recordatorios'], labels=['PC','Short'])
                createTask(content='Practice 1', priority=3, due_string=f'2 days before {day}', parent_id=task_id)
                createTask(content='Practice 2', priority=3, due_string=f'2 days before {day}', parent_id=task_id)
                createTask(content='Practice 3', priority=3, due_string=f'1 day before {day}', parent_id=task_id)
                createTask(content='Qualifying', priority=1, due_string=f'1 day before {day}', parent_id=task_id)
                createTask(content='Race', priority=1, due_string=day, parent_id=task_id)

        grand_prix_dict = {'AUSTRALIAN GRAND PRIX':'16-03-2025',
                           'CHINESE GRAND PRIX':'23-03-2025',
                           'JAPANESE GRAND PRIX':'06-04-2025',
                           'BAHRAIN GRAND PRIX':'13-04-2025',
                           'SAUDI ARABIA GRAND PRIX':'20-04-2025',
                           'MIAMI GRAND PRIX':'04-05-2025',
                           "GRAN PREMIO DEL MADE IN ITALY DELL'EMILIA-ROMAGNA":'18-05-2025',
                           'GRAND PRIX DE MONACO':'25-05-2025',
                           'GRAN PREMIO DE ESPAÑA':'01-06-2025',
                           'GRAND PRIX DU CANADA':'15-06-2025',
                           'GROSSER PREIS VON ÖSTERREICH':'29-06-2025',
                           'BRITISH GRAND PRIX':'06-07-2025',
                           'BELGIAN GRAND PRIX':'27-07-2025',
                           'HUNGARIAN GRAND PRIX':'03-08-2025',
                           'DUTCH GRAND PRIX':'31-08-2025',
                           "GRAN PREMIO D'ITALIA":'07-09-2025',
                           'AZERBAIJAN GRAND PRIX':'21-09-2025',
                           'SINGAPORE GRAND PRIX':'05-10-2025',
                           'UNITED STATES GRAND PRIX':'19-10-2025',
                           'GRAN PREMIO DE LA CIUDAD DE MEXICO':'26-10-2025',
                           'GRANDE PRÊMIO DE SÃO PAULO':'09-11-2025',
                           'LAS VEGAS GRAND PRIX':'22-11-2025',
                           'QATAR GRAND PRIX':'30-11-2025',
                           'ABU DHABI GRAND PRIX':'7-12-2025'
                           }

        # newF1Season('2025',grand_prix_dict=grand_prix_dict)

        tasks = api.get_tasks()
        recurringtasks={}
        for task in tasks:
            if 'Recurring' in task.labels:
                recurringtasks[task.id]=task.project_id
        df_recurringtasks = pd.DataFrame.from_dict({'task_id':recurringtasks.keys(),'project_id':recurringtasks.values()})
        
        try:
            fun.uploadCsvToBlob(df_recurringtasks, 'recurringtasks/recurringtasksdiego.csv')
        except:
            messages.append("Error al guardar las tareas recurrentes")
        
        end_time = time.time()

        runtime = f'Runtime: {round(end_time-start_time,3)} seconds'
        messages.append(runtime)

        body = messages[0] + "\n"
        count = 0
        for i in range(1, len(messages)):
            if messages[i][0] != "-":
                body = body + "\n" + f"{i - count}. " + messages[i] +"\n"
            else:
                body = body + "  " + messages[i] +"\n"
                count += 1

        fun.sendEmail("Daily Todoist", body, "diegorodgar17@gmail.com")

        return True
    
    except Exception as e:
        body = messages[0] + "\n"
        count = 0
        for i in range(1, len(messages)):
            if messages[i][0] != "-":
                body = body + "\n" + f"{i - count}. " + messages[i] +"\n"
            else:
                body = body + "  " + messages[i] +"\n"
                count += 1
        try:
            fun.sendEmail("Daily Todoist - Error", f"{body}\n\n{e}", "diegorodgar17@gmail.com")
        except:
            pass
        
        return e

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