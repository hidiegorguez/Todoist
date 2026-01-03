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

from dotenv import load_dotenv
load_dotenv()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Task:
    class Due:
        date: str
        is_recurring: bool 
        lang: str
        string: str
        timezone: str
        
    class Deadline:
        date: str
        lang: str
        
    class Duration:
        amount: int
        unit: str # "minute", "hour", "day"
        
    id: str 
    user_id: str
    project_id: str
    content: str
    description: str
    due: Due
    deadline: Deadline
    priority: int
    parent_id: str
    child_order: int # The order of the task. Defines the position of the task among all the tasks with the same parent.
    section_id: str
    day_order: int # The order of the task inside the Today or Next 7 days view (a number, where the smallest value would place the task at the top).
    collapsed: bool # Whether the task's sub-tasks are collapsed (a true or false value).
    labels: list[str]
    added_by_uid: str
    assigned_by_uid: str
    responsible_uid: str
    checked: bool
    is_deleted: bool
    sync_id: str # Identifier to find the match between tasks in shared projects of different collaborators. When you share a task, its copy has a different ID in the projects of your collaborators. To find a task in another account that matches yours, you can use the "sync_id" attribute. For non-shared tasks, the attribute is null.
    completed_at: str
    added_at: str
    duration: Duration
    
class CompletedTask:
    id: str
    user_id: str
    project_id: str
    section_id: str
    content: str
    completed_at: str
    task_id: str
    note_count: int
    meta_data: str
    
    def __init__(self):
        self.user_id = ""
        self.id = ""
        self.project_id = ""
        self.section_id = ""
        self.parent_id = ""
        self.added_by_uid = ""
        self.assigned_to_uid = ""
        self.responsible_uid = ""
        self.labels = []
        self.deadline = None
        self.duration = None
        self.checked = False
        self.is_deleted = False
        self.added_at = ""
        self.completed_at = ""
        self.updated_at = ""
        self.due = None
        self.priority = 1
        self.child_order = 0
        self.content = ""
        self.description = ""
        self.note_count = 0
        self.day_order = 0
        self.is_collapsed = False
         
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
    
    def get_tasks(self):
        try:
            active_projects_ids, _ = self.get_projects()
            data = {
                "sync_token": "*",
                "resource_types": json.dumps(['items'])
            }
            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            all_tasks = response.json().get("items", [])
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}
        active_tasks = [task for task in all_tasks if task['project_id'] in active_projects_ids]
        task_objects = []
        
        for task_data in active_tasks:
            task_obj = Task()
            for key, value in task_data.items():
                if hasattr(task_obj, key):
                    setattr(task_obj, key, value)
            task_objects.append(task_obj)
        return task_objects

    def update_task(
            self,
            task_id,
            content=None,
            description=None,
            due_date=None,
            due_is_recurring=None,
            due_lang=None,
            due_string=None,
            due_timezone=None,
            deadline_date=None,
            deadline_lang=None,
            priority=None,
            collapsed=None,
            labels=None,
            day_order=None,
            duration_amount=None,
            duration_unit=None,
        ):
        
        try:
            data = {
                "commands": [
                    {
                        "type": "item_update",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id,
                            **({"content": content} if content is not None else {}),
                            **({"description": description} if description is not None else {}),
                            **({"due": {
                                **({"date": due_date} if due_date is not None else {}),
                                **({"is_recurring": due_is_recurring} if due_is_recurring is not None else {}),
                                **({"lang": due_lang} if due_lang is not None else {}),
                                **({"string": due_string} if due_string is not None else {}),
                                **({"timezone": due_timezone} if due_timezone is not None else {})
                            }} if any(v is not None for v in [due_date, due_is_recurring, due_lang, due_string, due_timezone]) else {}),
                            **({"deadline": {
                                **({"date": deadline_date} if deadline_date is not None else {}),
                                **({"lang": deadline_lang} if deadline_lang is not None else {})
                            }} if any(v is not None for v in [deadline_date, deadline_lang]) else {}),
                            **({"priority": priority} if priority is not None else {}),
                            **({"collapsed": collapsed} if collapsed is not None else {}),
                            **({"labels": labels} if labels is not None else {}),
                            **({"day_order": day_order} if day_order is not None else {}),
                            **({"duration": {
                                **({"amount": duration_amount} if duration_amount is not None else {}),
                                **({"unit": duration_unit} if duration_unit is not None else {})
                            }} if any(v is not None for v in [duration_amount, duration_unit]) else {})
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()
    
    def move_task(
            self,
            task_id,
            parent_id=None,
            project_id=None,
            section_id=None
        ):
        
        try:
            if not any([parent_id, project_id, section_id]):
                return "Function error: Either project_id, parent_id or section_id must be provided."
            
            data = {
                "commands": [
                    {
                        "type": "item_move",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id,
                            **({"parent_id": parent_id} if parent_id is not None else {}),
                            **({"project_id": project_id} if project_id is not None else {}),
                            **({"section_id": section_id} if section_id is not None else {})
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()
    
    def reorder_tasks(
            self,
            tasks: dict[str, int]
        ):
        
        try:
            items = [{"id": task_id, "child_order": order} for task_id, order in tasks.items()]
            data = {
                "commands": [
                    {
                        "type": "item_reorder",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "items": items
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:   
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()
    
    def delete_task(
            self,
            task_id: str
        ):
        
        try:
            data = {
                "commands": [
                    {
                        "type": "item_delete",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()

    def complete_task(
            self,
            task_id: str
        ):
        
        try:
            data = {
                "commands": [
                    {
                        "type": "item_complete",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()
    
    def uncomplete_task(
            self,
            task_id: str
        ):
        
        try:
            data = {
                "commands": [
                    {
                        "type": "item_uncomplete",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()

    def complete_recurring_task(
            self,
            task_id: str,
            due_date: str = None,
            due_string: str = None,
            due_lang: str = None,
            due_timezone: str = None,
            is_forward: bool = True,
            reset_subtasks: bool = False
        ):
        
        try:
            is_forward = 1 if is_forward else 0
            reset_subtasks = 1 if reset_subtasks else 0
            data = {
                "commands": [
                    {
                        "type": "item_update_date_complete",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id,
                            **({"due": {
                                **({"date": due_date} if due_date is not None else {}),
                                **({"string": due_string} if due_string is not None else {}),
                                **({"lang": due_lang} if due_lang is not None else {}),
                                **({"timezone": due_timezone} if due_timezone is not None else {})
                            }} if any(v is not None for v in [due_date, due_string, due_lang, due_timezone]) else {}),
                            **({"is_forward": is_forward} if is_forward is not None else {}),
                            **({"reset_subtasks": reset_subtasks} if reset_subtasks is not None else {})
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
        
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()

    def close_task(
            self,
            task_id
        ):
        
        try:
            data = {
                "commands": [
                    {
                        "type": "item_close",
                        "uuid": str(uuid.uuid4()),
                        "args": {
                            "id": task_id
                        }
                    }
                ]
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()

    def update_day_orders(
            self,
            ids_to_orders: dict[str, int]
        ):
        
        try:
            commands = []
            for task_id, day_order in ids_to_orders.items():
                commands.append({
                    "type": "item_update_day_orders",
                    "uuid": str(uuid.uuid4()),
                    "args": {
                        "id": task_id,
                        "day_order": day_order
                    }
                })
            data = {
                "commands": commands
            }

            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
    def get_task(
            self,
            task_id: str
        ):
        
        # doesn't work
        try:
            url = f"https://api.todoist.com/api/v1/tasks/{task_id}"
            data = {
                "task_id": task_id
            }
            response = requests.get(url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            task_data = response.json().get("item")

            if not task_data:
                print('Task not found.')
                return None
            
            task_obj = Task()
            for key, value in task_data.items():
                if hasattr(task_obj, key):
                    setattr(task_obj, key, value)
            return task_obj

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except ValueError:
            print("Response is not a valid JSON.")
            return None
        except Exception as e:
            print(f"Function error: {e}")
            return None

    def get_completed_tasks(
            self,
            limit = 30,
            since = None,
            until = None
        ):
        
        try:
            active_projects_ids, _ = self.get_projects()
            data = {
                "sync_token": "*",
                "resource_types": json.dumps(['items']),
                "limit": limit,
                "since": since,
                "until": until
            }
            response = requests.post(f'{self.sync_url[:-5]}/completed/get_all', headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            all_tasks = response.json().get("items", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}
        
        active_tasks = [task for task in all_tasks if task['project_id'] in active_projects_ids]
        task_objects = []
        
        for task_data in active_tasks:
            task_obj = CompletedTask()
            for key, value in task_data.items():
                if hasattr(task_obj, key) or key == 'task_id':
                    setattr(task_obj, key, value)
            task_objects.append(task_obj)
        return task_objects

    def add_reminder(
            self,
            task_id,
            minute_offset
        ):
        
        try:
            data = {
                "commands": [
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
            }
            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
        
        return response.json()
    
    def get_projects(
            self,
            to_dict=True
        ):
        
        try:
            data = {
                "sync_token": "*",
                "resource_types": json.dumps(['projects'])
            }
            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            all_projects = response.json().get('projects', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}

        if to_dict:
            projects_dict_id = {project['id']: project['name'] for project in all_projects}
            projects_dict_name = {project['name']: project['id'] for project in all_projects}
            return projects_dict_id, projects_dict_name
        return all_projects
    
    def get_sections(
            self,
            to_dict=True,
            project_id=None
        ):
        
        try:
            data = {
                "sync_token": "*",
                "resource_types": json.dumps(['sections'])
            }
            response = requests.post(self.sync_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            all_sections = response.json().get("sections", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}

        if project_id is not None:
            all_sections = [section for section in all_sections if section.get('project_id') == project_id]

        if to_dict:
            sections_dict_id = {section['id']: section['name'] for section in all_sections}
            sections_dict_name = {section['name']: section['id'] for section in all_sections}
            return sections_dict_id, sections_dict_name
        return all_sections

    # old methods
    def getTask(self, id):
        task = self.api.get_task(task_id=id)
        return task

    # old methods not used anymore (to remove later)
    def createSection(self, name, project_id):
        try:
            section = self.api.add_section(name=name, project_id=project_id)
            return section
        except Exception as error:
            return error

    def setDeadline(self, task_id, deadline: str):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }
        commands = [
            {
                "type": "item_update",
                "uuid": str(uuid.uuid4()),
                "args": {
                    "id": task_id,
                    "deadline": {
                        "date": deadline
                    }
                }
            }
        ]
        data = {"commands": commands}
        response = requests.post(self.sync_url, headers=headers, json=data)
        return response.json()

    def completeTask(self, id):
        try:
            self.api.close_task(id)
            print(f'Task {id} is now completed')
        except:
            print(f'Task {id} was not possible to complete')
            
    def uncompleteTask(self, id):
        try:
            self.api.reopen_task(id)
            print(f'Task {id} is now uncompleted')
        except:
            print(f'Task {id} was not possible to uncomplete')

    def moveTask(self, task_id, project_id, section_id=None, parent_id=None):
        # Yet to check section and father task
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
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}

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

    
class AzureBlobFunctions:

    def __init__(self, api_connection_string):
        self.connect_str = api_connection_string
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)
        self.container_client = self.blob_service_client.get_container_client('todoistcontainer')

    def read_csv_from_blob(self, blob_name):
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_data = blob_client.download_blob().readall()
        data = StringIO(blob_data.decode('utf-8'))
        df = pd.read_csv(data)
        return df

    def upload_csv_to_blob(self, df:pd.DataFrame, blob_name):
        blob_client = self.container_client.get_blob_client(blob_name)
        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        blob_client.upload_blob(output.getvalue(), overwrite=True)
        
    def list_blobs_in_container(self):
        blob_list = self.container_client.list_blobs()
        blobs = [blob.name for blob in blob_list]
        return blobs
    
    def delete_blob(self, blob_name):
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.delete_blob()

def get_duration_label(n):
    if n<5:
        return 'Short'
    if n<61:
        return 'Med'
    return 'Long'

def priority_inversal(n):
    return 5 - n

def jaccard_coef(cadena1, cadena2):
    set_cadena1 = set(cadena1.split())
    set_cadena2 = set(cadena2.split())

    interseccion = len(set_cadena1.intersection(set_cadena2))
    union = len(set_cadena1.union(set_cadena2))

    coeficiente = interseccion / union
    return coeficiente

def are_similar(cadena1, cadena2, umbral=0.5):
    coeficiente = jaccard_coef(cadena1, cadena2)
    if coeficiente >= umbral:
        return f'{cadena1} & {cadena2}'

def get_next_monday():
    _today = datetime.now()
    days_to_monday = (0 - _today.weekday()) % 7 
    closer_monday = _today + timedelta(days=days_to_monday)
    return closer_monday

def send_email(subject, body, to):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    usuario = os.getenv('ECLIPSE_EMAIL')
    app_password = os.getenv('ECLIPSE_APP_PASSWORD')

    mensaje = MIMEMultipart()
    mensaje["From"] = usuario
    mensaje["To"] = to
    mensaje["Subject"] = subject
    cuerpo = body
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        servidor = smtplib.SMTP(smtp_server, smtp_port)
        servidor.starttls()
        servidor.login(usuario, app_password)
        servidor.sendmail(usuario, to, mensaje.as_string())
        servidor.quit()
        print("Email sent succesfully")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e

def build_exception_msg(e: Exception):
    tb = e.__traceback__
    while tb.tb_next:
        tb = tb.tb_next
    line = tb.tb_lineno
    file = tb.tb_frame.f_code.co_filename
    return f"Error in {file}, line {line}:\n {e}"