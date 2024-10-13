import json
import requests
from datetime import datetime, timedelta
import uuid
from todoist_api_python.api import TodoistAPI
import smtplib
from azure.storage.blob import BlobServiceClient
from io import StringIO
import pandas as pd
import os
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

import spacy

# def load_spacy_model():
#     try:
#         nlp = spacy.load("es_core_news_sm")
#     except OSError:
#         from spacy.cli import download
#         download("es_core_news_sm")
#         nlp = spacy.load("es_core_news_sm")
#     return nlp

# nlp = load_spacy_model()

api_token = os.getenv("TODOIST_API_TOKEN")
api = TodoistAPI(api_token)

connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client('todoistcontainer')

headers = {
    "Content-Type": "application/json",
    "X-Request-Id": "un_valor_único_por_cada_solicitud",
    "Authorization": f"Bearer {api_token}"
}

def getProjects():
    data = {
        "sync_token": "*",
        "resource_types": json.dumps(['projects'])
    }
    response = requests.post("https://api.todoist.com/sync/v9/sync", headers=headers, data=json.dumps(data))
    all_projects = response.json().get('projects', [])
    return all_projects

def getProjectsDicts(all_projects):
    projects_dict_id={}
    projects_dict_name={}
    for project in all_projects:
        projects_dict_id[project['id']]=project['name']
        projects_dict_name[project['name']]=project['id']
    return projects_dict_id, projects_dict_name

def getTasks():
    active_projects = getProjects()
    active_projects_ids, _ = getProjectsDicts(active_projects)
    data = {
        "sync_token": "*",
        "resource_types": json.dumps(['items'])
    }
    response = requests.post("https://api.todoist.com/sync/v9/sync", headers=headers, data=json.dumps(data))
    # print(response.json())
    all_tasks = response.json()["items"]
    active_tasks = [task for task in all_tasks if task['project_id'] in active_projects_ids]
    return active_tasks

def getTasksDicts(all_tasks, projects_dict_id, projects_dict_name):
    task_dict_id={}
    task_dict_name={}
    for task in all_tasks:
        task_dict_name[task['content']]=[task['id'],projects_dict_id[task['project_id']]]
        task_dict_id[task['id']]=[task['content'],projects_dict_id[task['project_id']]]
    return task_dict_id, task_dict_name

def getSections(project_id = None):
    data = {
        "sync_token": "*",
        "resource_types": json.dumps(['sections'])
    }
    response = requests.post("https://api.todoist.com/sync/v9/sync", headers=headers, data=json.dumps(data))
    all_sections = response.json()["sections"]
    if project_id != None:
        # print("he entrado")
        return [section for section in all_sections if section.get('project_id') == project_id]
    return all_sections

def getSectionsDicts(all_sections):
    sections_dict_id={}
    sections_dict_name={}
    for section in all_sections:
        sections_dict_id[section['id']]=section['name']
        sections_dict_name[section['name']]=section['id']
    return sections_dict_id, sections_dict_name

def getTask(id):
    task = api.get_task(task_id = id)
    return task

def completeTask(id):
    try:
        api.close_task(id)
        print(f'La tarea {id} se completó')
    except:
        print(f'No ha sido posible completar la tarea {id}')
        
def uncompleteTask(id):
    try:
        api.reopen_task(id)
        print(f'La tarea {id} está activa')
    except:
        print(f'No ha sido posible descompletar la tarea {id}')

def moveTask(task_id, project_id, section_id = None, parent_id = None):
    try:
        headers = {
            "Authorization": f"Bearer {api_token}"
        }
        data = {
            "commands": [{
                "type": "item_move",
                "uuid": str(uuid.uuid4()),  # Genera un identificador único
                "args": {
                    "id": task_id,
                    "project_id": project_id
                }
            }]
        }
        response = requests.post("https://api.todoist.com/sync/v9/sync", json=data, headers=headers)
        return response.json()
    except Exception as error:
        print('errrors')
        return error

def getLabelsWithoutDuration(task_id):
    task = getTask(task_id)
    list = task.labels
    if 'Short' in list:
        list.remove('Short')
    if 'Med' in list:
        list.remove('Med')
    if 'Long' in list:
        list.remove('Long')
    return list

def getDurationLabel(n):
    if n<5:
        return 'Short'
    if n<61:
        return 'Med'
    return 'Long'

def priorityInversal(n):
    return 5 - n

def getNextMonday():
    _today = datetime.now()
    days_to_monday = (0 - _today.weekday()) % 7 
    closer_monday = _today + timedelta(days=days_to_monday)
    return closer_monday

def sendEmail(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv('MAIL')
    msg['To'] = to

    server = 'smtp-mail.outlook.com'
    port = 587

    username = os.getenv('MAIL')
    password = os.getenv('PASSWORD')

    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)
        
def jaccardCoef(cadena1, cadena2):
    set_cadena1 = set(cadena1.split())
    set_cadena2 = set(cadena2.split())

    interseccion = len(set_cadena1.intersection(set_cadena2))
    union = len(set_cadena1.union(set_cadena2))

    coeficiente = interseccion / union
    return coeficiente

def areSimilar(cadena1, cadena2, umbral=0.5):
    coeficiente = jaccardCoef(cadena1, cadena2)
    if coeficiente >= umbral:
        return f'{cadena1} & {cadena2}'

def readCsvFromBlob(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    blob_data = blob_client.download_blob().readall()
    data = StringIO(blob_data.decode('utf-8'))
    df = pd.read_csv(data)
    return df

def uploadCsvToBlob(df, blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    blob_client.upload_blob(output.getvalue(), overwrite=True)

def getCompletedTasks(last_days=10):
    active_projects = getProjects()
    active_projects_ids, _ = getProjectsDicts(active_projects)
    end_date = datetime.now() - timedelta(days=last_days)
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {
        "sync_token": "*",
        "resource_types": json.dumps(['items']),
        "filters": json.dumps({"completed": "true", "until": end_date_str})
    }
    response = requests.post("https://api.todoist.com/sync/v9/completed/get_all", headers=headers, data=json.dumps(data))
    all_completed_tasks = response.json()["items"]
    completed_tasks = [task for task in all_completed_tasks if task['project_id'] in active_projects_ids]
    return completed_tasks

# def capitalizeProperNounsSpacy(text):
#     doc = nlp(text)
#     result = []
#     capitalize_next = True
#     for token in doc:
#         if token.text.isupper():
#             result.append(token.text)
#         elif capitalize_next and token.is_alpha:
#             result.append(token.text.capitalize())
#             capitalize_next = False
#         elif token.ent_type_ in ['PER', 'LOC', 'ORG', 'MISC', 'PROD', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']:
#             result.append(token.text.capitalize())
#         elif token.text.lower() == "españa":
#             result.append("España")
#         else:
#             result.append(token.text)
#         if token.text in '.!?':
#             capitalize_next = True
#     final_text = ''.join([tok if tok in '.,;:!?()[]{}' else ' ' + tok for tok in result]).strip()
#     return final_text

