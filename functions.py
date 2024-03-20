import json
import credentials
import requests
from todoist_api_python.api import TodoistAPI

api_token = credentials.api_token
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

def uncompleteTask(id):
    return api.reopen_task(id)

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
    if n<60:
        return 'Med'
    return 'Long'

def priorityInversal(n):
    return 5 - n
