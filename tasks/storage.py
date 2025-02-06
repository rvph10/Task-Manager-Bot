import json
import os
from config import TASKS_FILE
from tasks.model import Task

tasks = {}
task_counter = 0
task_channel_id = None

def load_tasks():
    global tasks, task_counter, task_channel_id
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                tasks = {int(k): Task.from_dict(v) for k, v in data.get('tasks', {}).items()}
                task_counter = data.get('task_counter', 0)
                task_channel_id = data.get('task_channel_id')
        else:
            print(f"File {TASKS_FILE} does not exist.")
    except Exception as e:
        print(f"Error loading tasks: {e}")
        tasks = {}
        task_counter = 0
        task_channel_id = None

def save_tasks():
    try:
        data = {
            'tasks': {str(k): v.to_dict() for k, v in tasks.items()},
            'task_counter': task_counter,
            'task_channel_id': task_channel_id
        }
        with open(TASKS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving tasks: {e}")