import json
import requests
from datetime import datetime, timedelta
from todoist_api_python.api import TodoistAPI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pickle


from dotenv import load_dotenv

load_dotenv()

api_token = os.getenv("API_TOKEN_DIEGO")
api = TodoistAPI(api_token)

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
    data = {
        "sync_token": "*",
        "resource_types": json.dumps(['items'])
    }
    response = requests.post("https://api.todoist.com/sync/v9/sync", headers=headers, data=json.dumps(data))
    print(response.json())
    all_tasks = response.json()["items"]
    return all_tasks

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


# Si modificas estos SCOPES, elimina el archivo token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_authenticate():
    creds = None
    # El archivo token.pickle almacena los tokens de acceso del usuario,
    # y se crea automáticamente cuando el flujo de autorización se completa por primera vez.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # Si no hay credenciales válidas disponibles, haga que el usuario se autentique.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Guardar las credenciales para la próxima ejecución
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def sendEmail(to, subject, body):
    service = gmail_authenticate()
    message = MIMEMultipart()
    message['To'] = to
    message['Subject'] = subject
    msg = MIMEText(body, 'plain')
    message.attach(msg)

    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}
    
    try:
        message = (service.users().messages().send(userId="me", body=body)
                   .execute())
        print("Email sent correctly")
    except Exception as e:
        print(f"Error: {e}")
