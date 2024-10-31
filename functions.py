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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class TodoistFunctions:
    
    def __init__(self, api_token):
        self.api_token = api_token
        self.api = TodoistAPI(api_token)
        self.sync_url = "https://api.todoist.com/sync/v9/sync"
        self.headers = {
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid.uuid4()),
            "Authorization": f"Bearer {self.api_token}"
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
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    usuario = "diegorodgar17@gmail.com"
    app_password = "mthu fsxe skvs rppi"  # La contraseña de aplicación de 16 caracteres

    # Configuración del mensaje
    mensaje = MIMEMultipart()
    mensaje["From"] = usuario
    mensaje["To"] = to
    mensaje["Subject"] = subject
    cuerpo = body
    mensaje.attach(MIMEText(cuerpo, "plain"))

    # Enviar el correo
    try:
        servidor = smtplib.SMTP(smtp_server, smtp_port)
        servidor.starttls()
        servidor.login(usuario, app_password)
        servidor.sendmail(usuario, usuario, mensaje.as_string())
        servidor.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")