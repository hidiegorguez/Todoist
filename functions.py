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

    def getProjects(self, to_dict = True):
        data = {
            "sync_token": "*",
            "resource_types": json.dumps(['projects'])
        }
        response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
        all_projects = response.json().get('projects', [])
        if to_dict:
            projects_dict_id={}
            projects_dict_name={}
            for project in all_projects:
                projects_dict_id[project['id']]=project['name']
                projects_dict_name[project['name']]=project['id']
            return projects_dict_id, projects_dict_name
        return all_projects

    def getTasks(self, to_dict = True):
        active_projects_ids, _ = self.getProjects()
        data = {
            "sync_token": "*",
            "resource_types": json.dumps(['items'])
        }
        response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
        all_tasks = response.json()["items"]
        active_tasks = [task for task in all_tasks if task['project_id'] in active_projects_ids]
        if to_dict:
            projects_dict_id, _ = self.getProjects()
            task_dict_id={}
            task_dict_name={}
            for task in all_tasks:
                task_dict_name[task['content']]=[task['id'],projects_dict_id[task['project_id']]]
                task_dict_id[task['id']]=[task['content'],projects_dict_id[task['project_id']]]
            return task_dict_id, task_dict_name
        return active_tasks

    def getSections(self, to_dict = True, project_id = None):
        data = {
            "sync_token": "*",
            "resource_types": json.dumps(['sections'])
        }
        response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
        all_sections = response.json()["sections"]
        if project_id != None:
            all_sections = [section for section in all_sections if section.get('project_id') == project_id]
        if to_dict:
            sections_dict_id={}
            sections_dict_name={}
            for section in all_sections:
                sections_dict_id[section['id']]=section['name']
                sections_dict_name[section['name']]=section['id']
            return sections_dict_id, sections_dict_name
        return all_sections

    def getTask(self, id):
        task = self.api.get_task(task_id=id)
        return task

    def createSection(self, name, project_id):
        try:
            section = self.api.add_section(name=name, project_id=project_id)
            return section
        except Exception as error:
            return error

    def setReminder(self, task_id, minute_offset): 
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        commands = [
            {
                "type": "reminder_add",
                "temp_id": str(uuid.uuid4()),
                "uuid": str(uuid.uuid4()),
                "args": {
                    "item_id": task_id,
                    "minute_offset": minute_offset,
                    "type": "relative"
                }
            }
        ]
        data = {"commands": commands}
        response = requests.post(self.sync_url, headers=headers, json=data)
        
        return response.json()

    def completeTask(self, id):
        try:
            self.api.close_task(id)
            print(f'La tarea {id} se completó')
        except:
            print(f'No ha sido posible completar la tarea {id}')
            
    def uncompleteTask(self, id):
        try:
            self.api.reopen_task(id)
            print(f'La tarea {id} está activa')
        except:
            print(f'No ha sido posible descompletar la tarea {id}')

    def moveTask(self, task_id, project_id, section_id = None, parent_id = None):
        # Falta contemplar la seccion y el padre
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }
            data = {
                "commands": [{
                    "type": "item_move",
                    "uuid": str(uuid.uuid4()),
                    "args": {
                        "id": task_id,
                        "project_id": project_id
                    }
                }]
            }
            response = requests.post(self.sync_url, json=data, headers=headers)
            return response.json()
        except Exception as error:
            print('errrors')
            return error

    def getLabelsWithoutDuration(self, task_id):
        task = self.getTask(task_id)
        list = task.labels
        if 'Short' in list:
            list.remove('Short')
        if 'Med' in list:
            list.remove('Med')
        if 'Long' in list:
            list.remove('Long')
        return list

    def getDurationLabel(self, n):
        if n<5:
            return 'Short'
        if n<61:
            return 'Med'
        return 'Long'

    def priorityInversal(self, n):
        return 5 - n

    def getCompletedTasks(self, last_days=10):
        active_projects_ids, _ = self.getProjects()
        end_date = datetime.now() - timedelta(days=last_days)
        end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {
            "sync_token": "*",
            "resource_types": json.dumps(['items']),
            "filters": json.dumps({"completed": "true", "until": end_date_str})
        }
        response = requests.post("https://api.todoist.com/sync/v9/completed/get_all", headers=self.headers, data=json.dumps(data))
        all_completed_tasks = response.json()["items"]
        completed_tasks = [task for task in all_completed_tasks if task['project_id'] in active_projects_ids]
        return completed_tasks

class AzureBlobFunctions:

    def __init__(self, api_connection_string):
        self.connect_str = api_connection_string
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)
        self.container_client = self.blob_service_client.get_container_client('todoistcontainer')

    def readCsvFromBlob(self, blob_name):
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_data = blob_client.download_blob().readall()
        data = StringIO(blob_data.decode('utf-8'))
        df = pd.read_csv(data)
        return df

    def uploadCsvToBlob(self, df:pd.DataFrame, blob_name):
        blob_client = self.container_client.get_blob_client(blob_name)
        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        blob_client.upload_blob(output.getvalue(), overwrite=True)

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