import requests
from datetime import datetime, timedelta
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

class TodoistFunctions:
    
    def __init__(self, api_token):
        self.api_token = api_token
        self.api = TodoistAPI(api_token)

    def get_projects(
            self,
            to_dict=True
        ):
        
        try:
            all_projects = []
            for project_batch in self.api.get_projects():
                all_projects.extend(project_batch)
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}

        if to_dict:
            projects_dict_id = {project.id: project.name for project in all_projects}
            projects_dict_name = {project.name: project.id for project in all_projects}
            return projects_dict_id, projects_dict_name
        return all_projects
    
    def get_sections(
            self,
            to_dict=True,
            project_id=None
        ):
        try:
            all_sections = []
            for section_batch in self.api.get_sections():
                all_sections.extend(section_batch)
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}
        if project_id is not None:
            all_sections = [section for section in all_sections if section.project_id == project_id]
        if to_dict:
            sections_dict_id = {section.id: section.name for section in all_sections}
            sections_dict_name = {section.name: section.id for section in all_sections}
            return sections_dict_id, sections_dict_name
        return all_sections
    
    def get_tasks(self):
        try:
            active_projects_ids, _ = self.get_projects()
            all_tasks = []
            for task_batch in self.api.get_tasks():
                all_tasks.extend(task_batch)
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}, {}
        except ValueError:
            print("Response is not a valid JSON.")
            return {}, {}
        active_tasks = [task for task in all_tasks if task.project_id in active_projects_ids]
        return active_tasks

    def get_task(self, id):
        try:
            task = self.api.get_task(task_id=id)
            return task
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except ValueError:
            print("Response is not a valid JSON.")
            return None
        except Exception as e:
            print(f"Function error: {e}")
            return None
    
    def add_task(
            self,
            content,
            description=None,
            project_id=None,
            section_id=None,
            parent_id=None,
            labels=None,
            priority=None,
            due_string=None,
            due_lang=None,
            due_date=None,
            due_datetime=None,
            assignee_id=None,
            order=None,
            auto_reminder=None,
            auto_parse_labels=None,
            duration=None,
            duration_unit=None,
            deadline_date=None,
            deadline_lang=None,
        ):
        try:
            task = self.api.add_task(
                content=content,
                description=description,
                project_id=project_id,
                section_id=section_id,
                parent_id=parent_id,
                labels=labels,
                priority=priority,
                due_string=due_string,
                due_lang=due_lang,
                due_date=due_date,
                due_datetime=due_datetime,
                assignee_id=assignee_id,
                order=order,
                auto_reminder=auto_reminder,
                auto_parse_labels=auto_parse_labels,
                duration=duration,
                duration_unit=duration_unit,
                deadline_date=deadline_date,
                deadline_lang=deadline_lang
                
            )
            return task
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {e.status_code}: {e.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
    
    def update_task(
            self,
            task_id,
            content=None,
            description=None,
            labels=None,
            priority=None,
            due_string=None,
            due_lang=None,
            due_date=None,
            due_datetime=None,
            assignee_id=None,
            day_order=None,
            duration=None,
            collapsed=None,
            duration_unit=None,
            deadline_date=None,
            deadline_lang=None,
        ):
        try:
            self.api.update_task(
                task_id=task_id,
                content=content,
                description=description,
                labels=labels,
                priority=priority,
                due_string=due_string,
                due_lang=due_lang,
                due_date=due_date,
                due_datetime=due_datetime,
                assignee_id=assignee_id,
                day_order=day_order,
                duration=duration,
                collapsed=collapsed,
                duration_unit=duration_unit,
                deadline_date=deadline_date,
                deadline_lang=deadline_lang
            )
            
        
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {e.status_code}: {e.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
     
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
            
            self.api.move_task(
                task_id=task_id,
                parent_id=parent_id,
                project_id=project_id,
                section_id=section_id
            )
            
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {e.status_code}: {e.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"
    
    def uncomplete_task(
            self,
            task_id: str
        ):
        
        try:
            self.api.uncomplete_task(task_id=task_id)
            
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {e.status_code}: {e.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"

    def get_completed_tasks_by_completion_date(
            self,
            since,
            until,
            limit = 50,
        ):
        try:
            all_tasks = []
            for task_batch in self.api.get_completed_tasks_by_completion_date(limit=limit, since=since, until=until):
                all_tasks.extend(task_batch)
          
            return all_tasks  
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except ValueError:
            return "Response is not a valid JSON."
        except Exception as e:
            return f"Function error: {e}"

    def add_reminder(
            self,
            task_id,
            minute_offset
        ):
        try:
            self.api.add_reminder(
                item_id=task_id,
                minute_offset=minute_offset,
                type="relative"
            )
            
        except requests.exceptions.HTTPError as e:
            return f"Error HTTP {e.status_code}: {e.text}"
        except requests.exceptions.RequestException as e:
            return f"Request error: {e}"
        except Exception as e:
            return f"Function error: {e}"

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