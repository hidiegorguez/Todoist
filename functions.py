import os
import smtplib
import traceback
import sys
import random
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import requests
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

load_dotenv()


class TodoistException(Exception):
    """Excepción personalizada para errores de Todoist con contexto detallado."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        self.traceback_str = traceback.format_exc()


class TodoistFunctions:
    """Clase para interactuar con la API de Todoist."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.api = TodoistAPI(api_token)

    def _is_retryable_exception(self, e: Exception) -> bool:
        """Returns True when the exception likely represents a transient failure."""
        if isinstance(e, requests.exceptions.Timeout):
            return True
        if isinstance(e, requests.exceptions.ConnectionError):
            return True
        if isinstance(e, requests.exceptions.HTTPError):
            status_code = e.response.status_code if hasattr(e, "response") and e.response is not None else None
            return status_code in (429, 500, 502, 503, 504)
        return False

    def _execute_with_retry(self, operation_name: str, operation_fn, max_attempts: int = 5):
        """Executes a Todoist operation with exponential backoff and jitter."""
        last_exception = None
        for attempt in range(1, max_attempts + 1):
            try:
                return operation_fn()
            except Exception as e:
                last_exception = e
                if not self._is_retryable_exception(e) or attempt == max_attempts:
                    break

                # 1.5s, 3s, 6s, 12s + jitter to avoid thundering herd.
                base_delay = 1.5 * (2 ** (attempt - 1))
                sleep_seconds = base_delay + random.uniform(0, 0.6)
                print(
                    f"[{operation_name}] transient error on attempt {attempt}/{max_attempts}: {type(e).__name__}. "
                    f"Retrying in {sleep_seconds:.2f}s"
                )
                time.sleep(sleep_seconds)

        if isinstance(last_exception, requests.exceptions.HTTPError):
            status_code = (
                last_exception.response.status_code
                if hasattr(last_exception, "response") and last_exception.response is not None
                else "N/A"
            )
            response_text = (
                last_exception.response.text
                if hasattr(last_exception, "response") and last_exception.response is not None
                else "N/A"
            )
            raise TodoistException(
                f"{operation_name} failed after {max_attempts} attempts. "
                f"Last HTTP status: {status_code}. Response: {response_text}",
                context={
                    "service": "Todoist API",
                    "operation": operation_name,
                    "attempts": max_attempts,
                    "last_status_code": status_code,
                    "timestamp": datetime.now().isoformat(),
                },
            ) from last_exception

        raise TodoistException(
            f"{operation_name} failed after {max_attempts} attempts. Last error: {last_exception}",
            context={
                "service": "Todoist API",
                "operation": operation_name,
                "attempts": max_attempts,
                "last_exception_type": type(last_exception).__name__ if last_exception is not None else "Unknown",
                "timestamp": datetime.now().isoformat(),
            },
        ) from last_exception

    def _handle_exception(self, e: Exception) -> None:
        """Maneja las excepciones de forma consistente lanzando TodoistException."""
        if isinstance(e, TodoistException):
            raise e

        context = {
            'service': 'Todoist API',
            'original_exception_type': type(e).__name__,
            'timestamp': datetime.now().isoformat(),
        }
        
        if isinstance(e, requests.exceptions.HTTPError):
            context['status_code'] = e.response.status_code if hasattr(e, 'response') else 'N/A'
            context['response_text'] = e.response.text if hasattr(e, 'response') else 'N/A'
            message = f"Todoist API HTTP Error {context['status_code']}: {context['response_text']}"
            raise TodoistException(message, context=context) from e
        elif isinstance(e, requests.exceptions.ConnectionError):
            message = f"Todoist connection error: {e}"
            context['error_details'] = str(e)
            raise TodoistException(message, context=context) from e
        elif isinstance(e, requests.exceptions.Timeout):
            message = f"Todoist timeout error: {e}"
            context['error_details'] = str(e)
            raise TodoistException(message, context=context) from e
        elif isinstance(e, requests.exceptions.RequestException):
            message = f"Todoist request error: {e}"
            context['error_details'] = str(e)
            raise TodoistException(message, context=context) from e
        elif isinstance(e, ValueError):
            message = "Todoist response is not valid JSON."
            context['error_details'] = str(e)
            raise TodoistException(message, context=context) from e
        else:
            message = f"Todoist unexpected error: {e}"
            context['error_details'] = str(e)
            raise TodoistException(message, context=context) from e

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
            def _fetch_projects():
                projects = []
                for project_batch in self.api.get_projects():
                    projects.extend(project_batch)
                return projects

            all_projects = self._execute_with_retry("get_projects", _fetch_projects)
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
            def _fetch_sections():
                sections = []
                for section_batch in self.api.get_sections():
                    sections.extend(section_batch)
                return sections

            all_sections = self._execute_with_retry("get_sections", _fetch_sections)
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

            def _fetch_tasks():
                tasks = []
                for task_batch in self.api.get_tasks():
                    tasks.extend(task_batch)
                return tasks

            all_tasks = self._execute_with_retry("get_tasks", _fetch_tasks)
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
            return self._execute_with_retry(
                operation_name=f"get_task({task_id})",
                operation_fn=lambda: self.api.get_task(task_id=task_id),
            )
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
        payload = {
            "task_id": task_id,
            "content": content,
            "description": description,
            "labels": labels,
            "priority": priority,
            "due_string": due_string,
            "due_lang": due_lang,
            "due_date": due_date,
            "due_datetime": due_datetime,
            "assignee_id": assignee_id,
            "day_order": day_order,
            "duration": duration,
            "collapsed": collapsed,
            "duration_unit": duration_unit,
            "deadline_date": deadline_date,
            "deadline_lang": deadline_lang,
        }

        try:
            self.api.update_task(**payload)
            return True
        except Exception as e:
            error_message = str(e)

            # Compatibility fallback across SDK versions:
            # some versions expect due_date as datetime.date, others as YYYY-MM-DD string.
            if due_date is not None:
                # Newer SDK path: passed string but client tries due_date.isoformat().
                if isinstance(due_date, str) and "isoformat" in error_message:
                    try:
                        payload["due_date"] = datetime.strptime(due_date[:10], "%Y-%m-%d").date()
                        self.api.update_task(**payload)
                        return True
                    except Exception:
                        pass

                # Older SDK path: passed date-like object but JSON serializer expects string.
                if not isinstance(due_date, str) and "JSON serializable" in error_message:
                    try:
                        payload["due_date"] = due_date.isoformat() if hasattr(due_date, "isoformat") else str(due_date)
                        self.api.update_task(**payload)
                        return True
                    except Exception:
                        pass

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
            def _fetch_completed_tasks():
                tasks = []
                for task_batch in self.api.get_completed_tasks_by_completion_date(
                    limit=limit, since=since, until=until
                ):
                    tasks.extend(task_batch)
                return tasks

            return self._execute_with_retry(
                operation_name="get_completed_tasks_by_completion_date",
                operation_fn=_fetch_completed_tasks,
            )
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

def build_exception_msg(e: Exception) -> str:
    """
    Construye un mensaje detallado de excepción con traceback completo.
    
    Args:
        e: La excepción a procesar.
    
    Returns:
        str: Mensaje detallado formateado para correo.
    """
    msg_parts = []
    msg_parts.append("=" * 80)
    msg_parts.append("ERROR DETALLADO")
    msg_parts.append("=" * 80)
    
    # Información básica
    msg_parts.append(f"\nTipo de error: {type(e).__name__}")
    msg_parts.append(f"Hora: {datetime.now().isoformat()}")
    msg_parts.append(f"Mensaje: {str(e)}")
    
    # Información adicional si es TodoistException
    if isinstance(e, TodoistException):
        msg_parts.append(f"\n" + "=" * 80)
        msg_parts.append("INFORMACIÓN DEL SERVICIO")
        msg_parts.append("=" * 80)
        for key, value in e.context.items():
            if key == 'service':
                msg_parts.append(f"\n🔴 SERVICIO QUE FALLÓ: {value.upper()}")
            else:
                msg_parts.append(f"  - {key}: {value}")
    
    # Traceback completo
    msg_parts.append("\n" + "=" * 80)
    msg_parts.append("TRACEBACK COMPLETO")
    msg_parts.append("=" * 80)
    
    tb_str = traceback.format_exc()
    if tb_str == "NoneType: None\n":
        # Si no hay traceback, construir uno desde la excepción
        tb_str = f"  Exception: {e}\n"
    msg_parts.append(tb_str)
    
    # Información de la causa raíz
    if e.__cause__:
        msg_parts.append("\n" + "=" * 80)
        msg_parts.append("CAUSA RAÍZ")
        msg_parts.append("=" * 80)
        msg_parts.append(f"Tipo: {type(e.__cause__).__name__}")
        msg_parts.append(f"Mensaje: {str(e.__cause__)}")
    
    return "\n".join(msg_parts)

def format_error_for_email(operation: str, e: Exception, additional_info: dict = None) -> str:
    """
    Formatea un error completo para enviar por correo con contexto de operación.
    
    Args:
        operation: Nombre de la operación que falló (ej: "Daily Task Execution").
        e: La excepción capturada.
        additional_info: Diccionario con información adicional (ej: task_id, project_name).
    
    Returns:
        str: Mensaje formateado listo para enviar por correo.
    """
    msg_parts = []
    
    # Encabezado con identificación del servicio
    service = "DESCONOCIDO"
    if isinstance(e, TodoistException) and 'service' in e.context:
        service = e.context['service']
    
    msg_parts.append("\n" + "🚨 " * 20)
    msg_parts.append(f"SERVICIO AFECTADO: {service}")
    msg_parts.append("🚨 " * 20)
    
    msg_parts.append("\n" + "=" * 80)
    msg_parts.append(f"OPERACIÓN FALLIDA: {operation}")
    msg_parts.append("=" * 80)
    msg_parts.append(f"\nFecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Información adicional si está disponible
    if additional_info:
        msg_parts.append("\nDetalles de la operación:")
        for key, value in additional_info.items():
            msg_parts.append(f"  - {key}: {value}")
    
    # Detalles del error
    msg_parts.append("\n" + build_exception_msg(e))
    
    # Recomendaciones según el servicio
    msg_parts.append("\n" + "=" * 80)
    msg_parts.append("RECOMENDACIONES")
    msg_parts.append("=" * 80)
    if service == "Todoist API":
        msg_parts.append("• El error proviene de la API de Todoist")
        msg_parts.append("• Verificar status: https://todoist.com/")
        msg_parts.append("• Revisar limites de rate limit de API")
        msg_parts.append("• El codigo reintentara automaticamente en proximas ejecuciones")
    else:
        msg_parts.append("• Revisar logs de ejecucion")
        msg_parts.append("• Verificar conexion a internet")
    
    return "\n".join(msg_parts)