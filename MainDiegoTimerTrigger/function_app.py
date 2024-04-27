import logging
import azure.functions as func

app = func.FunctionApp()

@app.schedule(schedule="0 0 3 * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def MainDiegoTimerTrigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    mainDiego()
        
    logging.info('Python timer trigger function executed.')

def mainDiego():
        # %% [markdown]
    # <img src="../data/logo.png" width="420px">
    # 
    # # <span style="font-family:Cascadia mono; color:#db5a5a">TODOIST AUTOMATION - DIEGO</span>

    # %% [markdown]
    # ## <span style="font-family:Cascadia mono; color:#db6a6a">Settings</span>

    # %% [markdown]
    # ### Libraries

    # %%
    from todoist_api_python.api import TodoistAPI
    from datetime import datetime, timedelta, timezone
    import functions as fun
    import random
    import json
    import time
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # %% [markdown]
    # ### Message

    # %%
    today = datetime.today()

    # %%
    messages = [f'Todoist Automation for {today.strftime("%Y-%m-%d")}']

    # %% [markdown]
    # ### Runtime

    # %%
    start_time = time.time()

    # %% [markdown]
    # ### API

    # %%
    api_token = os.getenv("TODOIST_API_TOKEN")
    api = TodoistAPI(api_token)

    # %% [markdown]
    # ## <span style="font-family:Cascadia mono; color:#db6a6a">Data</span>

    # %% [markdown]
    # #### Projects

    # %%
    all_projects = fun.getProjects()
    projects_dict_id, projects_dict_name = fun.getProjectsDicts(all_projects)

    # %% [markdown]
    # #### Tasks

    # %%
    def refreshTasks():
        all_tasks = fun.getTasks()
        task_dict_id, task_dict_name = fun.getTasksDicts(all_tasks, projects_dict_id, projects_dict_name)
        return all_tasks, task_dict_id, task_dict_name

    # %%
    all_tasks, task_dict_id, task_dict_name = refreshTasks()

    # %% [markdown]
    # #### Sections

    # %%
    all_sections = fun.getSections()
    sections_dict_id, sections_dict_name = fun.getSectionsDicts(all_sections)

    # %% [markdown]
    # #### Test

    # %%
    index = random.randint(0,len(all_tasks))
    try:
        print(all_tasks[index]['content'], "-", all_tasks[index]['due']['date'], "-", projects_dict_id[all_tasks[index]['project_id']])
    except TypeError:
        print(all_tasks[index]['content'], "-", "No date" , "-",projects_dict_id[all_tasks[index]['project_id']],)

    # %% [markdown]
    # #### Labels

    # %%
    label_names=[]
    for task in all_tasks:
        gross_labels=task['labels']
        for label in gross_labels:
            if label not in label_names:
                label_names.append(label)
    label_names

    # %% [markdown]
    # 
    # ## <span style="font-family:Cascadia mono; color:#db6a6a">Orders</span>

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Create and edit tasks</span>

    # %%
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
            print(message)
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
            print(message)
            return message
        except Exception as error:
            print(error)
            return error

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Create section</span>

    # %%
    def createSection(name, project_id):
        try:
            section = api.add_section(name=name, project_id=project_id)
            return section
        except Exception as error:
            return error

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Add duration labels</span>

    # %%
    def updateTaskDurationLabel(task_id, task_duration):
        duration_label = fun.getDurationLabel(task_duration)
        task_id = task_id[0]
        task_labels_without_duration = fun.getLabelsWithoutDuration(task_id)
        task_labels_without_duration.append(duration_label)
        return editTask(task_id=task_id,
                labels=task_labels_without_duration)

    # %%
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
        print(message)
        messages.append(message)
    else:
        all_tasks, task_dict_id, task_dict_name = refreshTasks()

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Capitalize titles</span>

    # %%
    to_update = False
    messages.append("Tasks to capitalize it's title...")    
    for task in all_tasks:
        if task["content"][0].upper() != task["content"][0]:
            to_update = True
            task_id = task["id"]
            message = editTask(task_id = task_id,
                            content = task["content"][0].upper() + task["content"][1:])
            messages.append("- " + message)

    if not to_update:
        messages = messages[:-1]
        message = "No tasks to capitalize it's title"
        print(message)
        messages.append(message)
    else:
        all_tasks, task_dict_id, task_dict_name = refreshTasks()

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Uncomplete recurring tasks</span>

    # %%
    with open('data/recurringtasksdiego', 'r') as archivo_json:
        recurringtasks = json.load(archivo_json)

    # %%
    to_update = False
    messages.append('Recurring tasks to uncomplete...')
    for task_id in recurringtasks.keys():
        project_id = recurringtasks[task_id]
        if projects_dict_id[project_id] != "Archivados" and projects_dict_id[project_id] != "Tickler" :
            task = fun.getTask(task_id)
            if task.is_completed:
                to_update = True
                print(task.id)
                fun.uncompleteTask(task_id)
                message = editTask(task_id=task_id,
                                due_string="No date")
                print(task.project_id)
                if task.project_id == projects_dict_name["Calendario"]:
                    fun.moveTask(task_id=task_id,
                                project_id='2263729931')
                messages.append("- " + message)
            
    if not to_update:
        messages = messages[:-1]
        message = "No recurring tasks to uncomplete"
        print(message)
        messages.append(message)
    else:
        all_tasks, task_dict_id, task_dict_name = refreshTasks()

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Add labels to birthday tasks</span>

    # %%
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
        print(message)
        messages.append(message)
    else:
        all_tasks, task_dict_id, task_dict_name = refreshTasks()

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Fantasy task due</span>

    # %%
    evaluate = True
    if fun.getTask('4632052423').is_completed == True:
        fun.uncompleteTask('4632052423')
        editTask('4632052423', due_string='every friday 20:00')
        message = 'Fantasy task moved back to fridays'
        print (message)
        messages.append(message)
        evaluate = False

    # %%
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
            print(message)
            messages.append(message)

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Tasks with similar names</span>

    # %%
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
                

    # %%
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
            print(similar)
            messages.append(f'- {similar}')
    else:
        messages.append('No similar tasks')
        

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Reminder to prepare your suitcase</span>

    # %%
    to_update = False
    for task in all_tasks:
        if 'Vacations' in task['labels']:
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

    # %% [markdown]
    # #### <span style="font-family:Cascadia mono; color:silver">Adding F1 calendar for next season</span>

    # %%
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

    # %%
    # grand_prix_dict = {'AUSTRALIAN GRAND PRIX':'16-03-2025',
    #                    'CHINESE GRAND PRIX':'23-03-2025',
    #                    'JAPANESE GRAND PRIX':'06-04-2025',
    #                    'BAHRAIN GRAND PRIX':'13-04-2025',
    #                    'SAUDI ARABIA GRAND PRIX':'20-04-2025',
    #                    'MIAMI GRAND PRIX':'04-05-2025',
    #                    "GRAN PREMIO DEL MADE IN ITALY DELL'EMILIA-ROMAGNA":'18-05-2025',
    #                    'GRAND PRIX DE MONACO':'25-05-2025',
    #                    'GRAN PREMIO DE ESPAÑA':'01-06-2025',
    #                    'GRAND PRIX DU CANADA':'15-06-2025',
    #                    'GROSSER PREIS VON ÖSTERREICH':'29-06-2025',
    #                    'BRITISH GRAND PRIX':'06-07-2025',
    #                    'BELGIAN GRAND PRIX':'27-07-2025',
    #                    'HUNGARIAN GRAND PRIX':'03-08-2025',
    #                    'DUTCH GRAND PRIX':'31-08-2025',f
    #                    "GRAN PREMIO D'ITALIA":'07-09-2025',
    #                    'AZERBAIJAN GRAND PRIX':'21-09-2025',
    #                    'SINGAPORE GRAND PRIX':'05-10-2025',
    #                    'UNITED STATES GRAND PRIX':'19-10-2025',
    #                    'GRAN PREMIO DE LA CIUDAD DE MEXICO':'26-10-2025',
    #                    'GRANDE PRÊMIO DE SÃO PAULO':'09-11-2025',
    #                    'LAS VEGAS GRAND PRIX':'22-11-2025',
    #                    'QATAR GRAND PRIX':'30-11-2025',
    #                    'ABU DHABI GRAND PRIX':'7-12-2025'
    #                    }

    # %%
    # newF1Season('2025',grand_prix_dict=grand_prix_dict)

    # %% [markdown]
    # ## <span style="font-family:Cascadia mono; color:#db6a6a">Results</span>

    # %% [markdown]
    # ### Export all tasks and it's status

    # %%
    tasks = api.get_tasks()
    recurringtasks={}
    for task in tasks:
        if 'Recurring' in task.labels:
            recurringtasks[task.id]=task.project_id
    with open('data/recurringtasksdiego', 'w') as file:
        json.dump(recurringtasks, file)

    # %% [markdown]
    # ### Runtime

    # %%
    end_time = time.time()

    # %%
    runtime = f'Runtime: {round(end_time-start_time,3)} seconds'
    messages.append(runtime)
    print(runtime)

    # %% [markdown]
    # ### <span style="font-family:Cascadia code; color:#7a3aca">Message</span>

    # %%
    body = messages[0] + "\n"
    count = 0
    for i in range(1, len(messages)):
        if messages[i][0] != "-":
            body = body + "\n" + f"{i - count}. " + messages[i] +"\n"
        else:
            body = body + "  " + messages[i] +"\n"
            count = 1
        print(messages[i],"\n")

    # %% [markdown]
    # ### <span style="font-family:Cascadia code; color:#caba3a">Email</span>

    # %%
    fun.sendEmail("Daily Todoist", body, "diegorodgar17@gmail.com")


    
mainDiego()