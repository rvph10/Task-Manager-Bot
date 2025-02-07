import json
import os
from typing import Dict, Optional
from core.models import Meeting, Task
from core.exceptions import StorageError, TaskNotFoundError

class MeetingStore:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.meetings: Dict[int, Meeting] = {}
        self.meeting_counter: int = 0
        self.meeting_channel_id: Optional[int] = None
        self._load()
    
    def _load(self) -> None:
        """Load meetings from storage file"""
        try:
            if not os.path.exists(self.file_path):
                self._save()
                return

            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.meetings = {
                    int(k): Meeting.from_dict(v) 
                    for k, v in data.get('meetings', {}).items()
                }
                self.meeting_counter = data.get('meeting_counter', 0)
                self.meeting_channel_id = data.get('meeting_channel_id')
        except Exception as e:
            raise StorageError(f"Failed to load meetings: {str(e)}")

    def _save(self) -> None:
        """Save meetings to storage file"""
        try:
            data = {
                'meetings': {
                    str(k): v.to_dict() 
                    for k, v in self.meetings.items()
                },
                'meeting_counter': self.meeting_counter,
                'meeting_channel_id': self.meeting_channel_id
            }
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise StorageError(f"Failed to save meetings: {str(e)}")

    def add_meeting(self, meeting: Meeting) -> None:
        """Add a new meeting to storage"""
        self.meeting_counter += 1
        meeting.id = self.meeting_counter
        self.meetings[meeting.id] = meeting
        self._save()

    def update_meeting(self, meeting_id: int, **kwargs) -> Meeting:
        """Update an existing meeting"""
        if meeting_id not in self.meetings:
            raise TaskNotFoundError(f"Meeting {meeting_id} not found")
        
        meeting = self.meetings[meeting_id]
        for key, value in kwargs.items():
            if hasattr(meeting, key):
                setattr(meeting, key, value)
        
        self._save()
        return meeting

    def delete_meeting(self, meeting_id: int) -> Meeting:
        """Delete a meeting"""
        if meeting_id not in self.meetings:
            raise TaskNotFoundError(f"Meeting {meeting_id} not found")
        
        meeting = self.meetings.pop(meeting_id)
        self._save()
        return meeting

    def get_meeting(self, meeting_id: int) -> Meeting:
        """Get a meeting by ID"""
        if meeting_id not in self.meetings:
            raise TaskNotFoundError(f"Meeting {meeting_id} not found")
        return self.meetings[meeting_id]

    def get_all_meetings(self) -> Dict[int, Meeting]:
        """Get all meetings"""
        return self.meetings.copy()

    def set_channel_id(self, channel_id: int) -> None:
        """Set the meetings board channel ID"""
        self.meeting_channel_id = channel_id
        self._save()

class TaskStore:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tasks: Dict[int, Task] = {}
        self.task_counter: int = 0
        self.task_channel_id: Optional[int] = None
        self._load()
    
    def _load(self) -> None:
        """Load tasks from storage file"""
        try:
            if not os.path.exists(self.file_path):
                self._save()
                return

            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.tasks = {
                    int(k): Task.from_dict(v) 
                    for k, v in data.get('tasks', {}).items()
                }
                self.task_counter = data.get('task_counter', 0)
                self.task_channel_id = data.get('task_channel_id')
        except Exception as e:
            raise StorageError(f"Failed to load tasks: {str(e)}")

    def _save(self) -> None:
        """Save tasks to storage file"""
        try:
            data = {
                'tasks': {
                    str(k): v.to_dict() 
                    for k, v in self.tasks.items()
                },
                'task_counter': self.task_counter,
                'task_channel_id': self.task_channel_id
            }
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise StorageError(f"Failed to save tasks: {str(e)}")

    def add_task(self, task: Task) -> None:
        """Add a new task to storage"""
        self.task_counter += 1
        task.id = self.task_counter
        self.tasks[task.id] = task
        self._save()

    def update_task(self, task_id: int, **kwargs) -> Task:
        """Update an existing task"""
        if task_id not in self.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self._save()
        return task

    def delete_task(self, task_id: int) -> Task:
        """Delete a task"""
        if task_id not in self.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        
        task = self.tasks.pop(task_id)
        self._save()
        return task

    def get_task(self, task_id: int) -> Task:
        """Get a task by ID"""
        if task_id not in self.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return self.tasks[task_id]

    def get_all_tasks(self) -> Dict[int, Task]:
        """Get all tasks"""
        return self.tasks.copy()

    def set_channel_id(self, channel_id: int) -> None:
        """Set the task board channel ID"""
        self.task_channel_id = channel_id
        self._save()