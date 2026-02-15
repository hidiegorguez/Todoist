import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO

import pandas as pd
import requests
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

load_dotenv()


class TodoistException(Exception):
    """Excepción personalizada para errores de Todoist."""
    pass


class TodoistFunctions:
    """Clase para interactuar con la API de Todoist."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.api = TodoistAPI(api_token)

    def _handle_exception(self, e: Exception) -> None:
        """Maneja las excepciones de forma consistente lanzando TodoistException."""
        if isinstance(e, requests.exceptions.HTTPError):
            raise TodoistException(f"HTTP Error {e.response.status_code}: {e.response.text}") from e
        elif isinstance(e, requests.exceptions.RequestException):
            raise TodoistException(f"Request error: {e}") from e
        elif isinstance(e, ValueError):
            raise TodoistException("Response is not valid JSON.") from e
        else:
            raise TodoistException(f"Unexpected error: {e}") from e

    def get_projects(self, to_dict: bool = True):
        """
        Obtiene todos los proyectos.
        
        Args:
            to_dict: Si True, devuelve diccionarios {id: name} y {name: id}.
                     Si False, devuelve lista de objetos Project.
        
        Returns:
            Tuple[dict, dict] o List[Project] según to_dict.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            all_projects = []
            for project_batch in self.api.get_projects():
                all_projects.extend(project_batch)
        except Exception as e:
            self._handle_exception(e)

        if to_dict:
            projects_dict_id = {project.id: project.name for project in all_projects}
            projects_dict_name = {project.name: project.id for project in all_projects}
            return projects_dict_id, projects_dict_name
        
        return all_projects

    def get_sections(self, to_dict: bool = True, project_id: str = None):
        """
        Obtiene todas las secciones, opcionalmente filtradas por proyecto.
        
        Args:
            to_dict: Si True, devuelve diccionarios {id: name} y {name: id}.
                     Si False, devuelve lista de objetos Section.
            project_id: ID del proyecto para filtrar secciones (opcional).
        
        Returns:
            Tuple[dict, dict] o List[Section] según to_dict.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            all_sections = []
            for section_batch in self.api.get_sections():
                all_sections.extend(section_batch)
        except Exception as e:
            self._handle_exception(e)

        if project_id is not None:
            all_sections = [s for s in all_sections if s.project_id == project_id]

        if to_dict:
            sections_dict_id = {section.id: section.name for section in all_sections}
            sections_dict_name = {section.name: section.id for section in all_sections}
            return sections_dict_id, sections_dict_name
        
        return all_sections

    def get_tasks(self):
        """
        Obtiene todas las tareas activas de proyectos activos.
        
        Returns:
            List[Task]: Lista de tareas activas.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            active_projects_ids, _ = self.get_projects()
            all_tasks = []
            for task_batch in self.api.get_tasks():
                all_tasks.extend(task_batch)
        except TodoistException:
            raise
        except Exception as e:
            self._handle_exception(e)

        return [task for task in all_tasks if task.project_id in active_projects_ids]

    def get_task(self, task_id: str):
        """
        Obtiene una tarea específica por ID.
        
        Args:
            task_id: ID de la tarea.
        
        Returns:
            Task: Objeto de la tarea.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            return self.api.get_task(task_id=task_id)
        except Exception as e:
            self._handle_exception(e)

    def add_task(
        self,
        content: str,
        description: str = None,
        project_id: str = None,
        section_id: str = None,
        parent_id: str = None,
        labels: list = None,
        priority: int = None,
        due_string: str = None,
        due_lang: str = None,
        due_date: str = None,
        due_datetime: str = None,
        assignee_id: str = None,
        order: int = None,
        auto_reminder: bool = None,
        auto_parse_labels: bool = None,
        duration: int = None,
        duration_unit: str = None,
        deadline_date: str = None,
        deadline_lang: str = None,
    ):
        """
        Crea una nueva tarea.
        
        Args:
            content: Contenido/título de la tarea.
            description: Descripción de la tarea.
            project_id: ID del proyecto destino.
            section_id: ID de la sección destino.
            parent_id: ID de la tarea padre (para subtareas).
            labels: Lista de etiquetas.
            priority: Prioridad (1-4, donde 4 es la más alta).
            due_string: Fecha de vencimiento en texto natural.
            due_lang: Idioma para due_string.
            due_date: Fecha de vencimiento (YYYY-MM-DD).
            due_datetime: Fecha y hora de vencimiento (RFC3339).
            assignee_id: ID del usuario asignado.
            order: Orden de la tarea.
            auto_reminder: Agregar recordatorio automático.
            auto_parse_labels: Parsear etiquetas automáticamente.
            duration: Duración estimada.
            duration_unit: Unidad de duración ('minute' o 'day').
            deadline_date: Fecha límite.
            deadline_lang: Idioma para deadline.
        
        Returns:
            Task: La tarea creada.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            return self.api.add_task(
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
                deadline_lang=deadline_lang,
            )
        except Exception as e:
            self._handle_exception(e)

    def update_task(
        self,
        task_id: str,
        content: str = None,
        description: str = None,
        labels: list = None,
        priority: int = None,
        due_string: str = None,
        due_lang: str = None,
        due_date: str = None,
        due_datetime: str = None,
        assignee_id: str = None,
        day_order: int = None,
        duration: int = None,
        collapsed: bool = None,
        duration_unit: str = None,
        deadline_date: str = None,
        deadline_lang: str = None,
    ) -> bool:
        """
        Actualiza una tarea existente.
        
        Args:
            task_id: ID de la tarea a actualizar.
            content: Nuevo contenido/título.
            description: Nueva descripción.
            labels: Nuevas etiquetas.
            priority: Nueva prioridad.
            due_string: Nueva fecha de vencimiento en texto.
            due_lang: Idioma para due_string.
            due_date: Nueva fecha de vencimiento.
            due_datetime: Nueva fecha y hora de vencimiento.
            assignee_id: Nuevo usuario asignado.
            day_order: Nuevo orden del día.
            duration: Nueva duración.
            collapsed: Estado de colapso.
            duration_unit: Nueva unidad de duración.
            deadline_date: Nueva fecha límite.
            deadline_lang: Idioma para deadline.
        
        Returns:
            bool: True si la actualización fue exitosa.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
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
                deadline_lang=deadline_lang,
            )
            return True
        except Exception as e:
            self._handle_exception(e)

    def move_task(
        self,
        task_id: str,
        parent_id: str = None,
        project_id: str = None,
        section_id: str = None,
    ) -> bool:
        """
        Mueve una tarea a otro proyecto, sección o como subtarea.
        
        Args:
            task_id: ID de la tarea a mover.
            parent_id: ID de la tarea padre (para convertir en subtarea).
            project_id: ID del proyecto destino.
            section_id: ID de la sección destino.
        
        Returns:
            bool: True si el movimiento fue exitoso.
        
        Raises:
            TodoistException: Si hay error o no se proporciona destino.
        """
        if not any([parent_id, project_id, section_id]):
            raise TodoistException("Debe proporcionar project_id, parent_id o section_id.")

        try:
            self.api.move_task(
                task_id=task_id,
                parent_id=parent_id,
                project_id=project_id,
                section_id=section_id,
            )
            return True
        except Exception as e:
            self._handle_exception(e)

    def uncomplete_task(self, task_id: str) -> bool:
        """
        Marca una tarea como no completada.
        
        Args:
            task_id: ID de la tarea.
        
        Returns:
            bool: True si la operación fue exitosa.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            self.api.uncomplete_task(task_id=task_id)
            return True
        except Exception as e:
            self._handle_exception(e)

    def get_completed_tasks_by_completion_date(
        self,
        since: str,
        until: str,
        limit: int = 50,
    ):
        """
        Obtiene tareas completadas en un rango de fechas.
        
        Args:
            since: Fecha de inicio (RFC3339).
            until: Fecha de fin (RFC3339).
            limit: Número máximo de tareas a obtener.
        
        Returns:
            List[Task]: Lista de tareas completadas.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            all_tasks = []
            for task_batch in self.api.get_completed_tasks_by_completion_date(
                limit=limit, since=since, until=until
            ):
                all_tasks.extend(task_batch)
            return all_tasks
        except Exception as e:
            self._handle_exception(e)

    def add_reminder(self, task_id: str, minute_offset: int) -> bool:
        """
        Agrega un recordatorio relativo a una tarea.
        
        Args:
            task_id: ID de la tarea.
            minute_offset: Minutos antes del vencimiento para el recordatorio.
        
        Returns:
            bool: True si el recordatorio fue agregado.
        
        Raises:
            TodoistException: Si hay error en la petición.
        """
        try:
            self.api.add_reminder(
                item_id=task_id,
                minute_offset=minute_offset,
                type="relative",
            )
            return True
        except Exception as e:
            self._handle_exception(e)

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