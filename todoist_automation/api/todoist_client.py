import random
import time
import traceback
from datetime import datetime

import requests
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

load_dotenv()


class TodoistException(Exception):
    """Custom exception for Todoist errors with detailed context."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        self.traceback_str = traceback.format_exc()


class TodoistFunctions:
    """Class for interacting with the Todoist API."""

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
        """Handle exceptions consistently by raising TodoistException."""
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
        Get all projects.
        
        Args:
            to_dict: If True, return {id: name} and {name: id} dictionaries.
                     If False, return a list of Project objects.
        
        Returns:
            Tuple[dict, dict] or List[Project], depending on to_dict.
        
        Raises:
            TodoistException: If the request fails.
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
        Get all sections, optionally filtered by project.
        
        Args:
            to_dict: If True, return {id: name} and {name: id} dictionaries.
                     If False, return a list of Section objects.
            project_id: Optional project ID used to filter sections.
        
        Returns:
            Tuple[dict, dict] or List[Section], depending on to_dict.
        
        Raises:
            TodoistException: If the request fails.
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
        Get all active tasks from active projects.
        
        Returns:
            List[Task]: A list of active tasks.
        
        Raises:
            TodoistException: If the request fails.
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
        Get a specific task by ID.
        
        Args:
            task_id: Task ID.
        
        Returns:
            Task: The task object.
        
        Raises:
            TodoistException: If the request fails.
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
        Create a new task.
        
        Args:
            content: Task content/title.
            description: Task description.
            project_id: Destination project ID.
            section_id: Destination section ID.
            parent_id: Parent task ID for subtasks.
            labels: List of labels.
            priority: Priority (1-4, where 4 is the highest).
            due_string: Natural-language due date.
            due_lang: Language for due_string.
            due_date: Due date (YYYY-MM-DD).
            due_datetime: Due date and time (RFC3339).
            assignee_id: Assigned user ID.
            order: Task order.
            auto_reminder: Add an automatic reminder.
            auto_parse_labels: Parse labels automatically.
            duration: Estimated duration.
            duration_unit: Duration unit ('minute' or 'day').
            deadline_date: Deadline date.
            deadline_lang: Language for deadline.
        
        Returns:
            Task: La tarea creada.
        
        Raises:
            TodoistException: If the request fails.
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
        Update an existing task.
        
        Args:
            task_id: ID de la tarea a actualizar.
            content: New content/title.
            description: New description.
            labels: New labels.
            priority: New priority.
            due_string: New natural-language due date.
            due_lang: Language for due_string.
            due_date: New due date.
            due_datetime: New due date and time.
            assignee_id: New assigned user ID.
            day_order: New day order.
            duration: New duration.
            collapsed: Collapsed state.
            duration_unit: New duration unit.
            deadline_date: New deadline date.
            deadline_lang: Language for deadline.
        
        Returns:
            bool: True if the update succeeds.
        
        Raises:
            TodoistException: If the request fails.
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
        Move a task to another project, section, or parent task.
        
        Args:
            task_id: ID of the task to move.
            parent_id: Parent task ID, converting the task into a subtask.
            project_id: Destination project ID.
            section_id: Destination section ID.
        
        Returns:
            bool: True if the move succeeds.
        
        Raises:
            TodoistException: If the operation fails or no destination is provided.
        """
        if not any([parent_id, project_id, section_id]):
            raise TodoistException("Provide project_id, parent_id, or section_id.")

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
        Mark a task as incomplete.
        
        Args:
            task_id: Task ID.
        
        Returns:
            bool: True if the operation succeeds.
        
        Raises:
            TodoistException: If the request fails.
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
        Get completed tasks within a date range.
        
        Args:
            since: Start date (RFC3339).
            until: End date (RFC3339).
            limit: Maximum number of tasks to retrieve.
        
        Returns:
            List[Task]: A list of completed tasks.
        
        Raises:
            TodoistException: If the request fails.
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

    def get_comments(self, task_id: str = None, project_id: str = None):
        """
        Get comments from a task or project.

        Args:
            task_id: ID of the task whose comments should be retrieved.
            project_id: ID of the project whose comments should be retrieved.

        Returns:
            List[Comment]: A list of comments.

        Raises:
            TodoistException: If the request fails.
        """
        try:
            def _fetch_comments():
                kwargs = {}
                if task_id is not None:
                    kwargs["task_id"] = task_id
                if project_id is not None:
                    kwargs["project_id"] = project_id

                comments = []
                # Some SDK versions paginate results (iterator of batches), others return a flat list.
                for item in self.api.get_comments(**kwargs):
                    if isinstance(item, list):
                        comments.extend(item)
                    else:
                        comments.append(item)
                return comments

            return self._execute_with_retry("get_comments", _fetch_comments)
        except Exception as e:
            self._handle_exception(e)

    def add_comment(self, content: str, task_id: str = None, project_id: str = None):
        """
        Add a comment to a task or project.

        Args:
            content: Comment content.
            task_id: ID of the task to comment on.
            project_id: ID of the project to comment on.

        Returns:
            Comment: El comentario creado.

        Raises:
            TodoistException: If the request fails.
        """
        try:
            return self._execute_with_retry(
                "add_comment",
                lambda: self.api.add_comment(content=content, task_id=task_id, project_id=project_id),
            )
        except Exception as e:
            self._handle_exception(e)

    def add_reminder(self, task_id: str, minute_offset: int) -> bool:
        """
        Add a relative reminder to a task.

        The Todoist Python SDK does not expose a reminders method, so this calls
        the REST endpoint (POST /api/v1/reminders) directly.

        Args:
            task_id: Task ID.
            minute_offset: Minutes before the due date for the reminder.
        
        Returns:
            bool: True if the reminder was added.
        
        Raises:
            TodoistException: If the request fails.
        """
        try:
            def _create_reminder():
                response = requests.post(
                    "https://api.todoist.com/api/v1/reminders",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json={
                        "task_id": task_id,
                        "reminder_type": "relative",
                        "minute_offset": minute_offset,
                    },
                    timeout=15,
                )
                response.raise_for_status()
                return response.json()

            self._execute_with_retry("add_reminder", _create_reminder)
            return True
        except Exception as e:
            self._handle_exception(e)

    def get_reminders(self, task_id: str = None) -> list:
        """
        Get active reminders, optionally filtered by task.

        Uses the REST endpoint (GET /api/v1/reminders) directly since the SDK
        does not expose reminders.

        Args:
            task_id: Optional task ID to filter reminders for a single task.

        Returns:
            list: Reminder objects (as dicts).

        Raises:
            TodoistException: If the request fails.
        """
        try:
            def _fetch_reminders():
                reminders = []
                cursor = None
                while True:
                    params = {"limit": 200}
                    if task_id is not None:
                        params["task_id"] = task_id
                    if cursor:
                        params["cursor"] = cursor

                    response = requests.get(
                        "https://api.todoist.com/api/v1/reminders",
                        headers={"Authorization": f"Bearer {self.api_token}"},
                        params=params,
                        timeout=15,
                    )
                    response.raise_for_status()
                    data = response.json()
                    reminders.extend(data.get("results", []))

                    cursor = data.get("next_cursor")
                    if not cursor:
                        break
                return reminders

            return self._execute_with_retry("get_reminders", _fetch_reminders)
        except Exception as e:
            self._handle_exception(e)
