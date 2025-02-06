from datetime import datetime
from typing import Optional
from core.exceptions import InvalidTaskDataError

def validate_date(date_str: str) -> Optional[datetime]:
    """Validate and convert date string to datetime object"""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        raise InvalidTaskDataError("Invalid date format. Please use YYYY-MM-DD")

def validate_task_data(title: str, description: str, due_date: Optional[str] = None) -> None:
    """Validate task data before creation/update"""
    if not title or len(title.strip()) == 0:
        raise InvalidTaskDataError("Task title cannot be empty")
    
    if not description or len(description.strip()) == 0:
        raise InvalidTaskDataError("Task description cannot be empty")
    
    if len(title) > 100:
        raise InvalidTaskDataError("Task title cannot exceed 100 characters")
        
    if len(description) > 500:
        raise InvalidTaskDataError("Task description cannot exceed 500 characters")
    
    if due_date:
        validate_date(due_date)