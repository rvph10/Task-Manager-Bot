class TaskError(Exception):
    """Base exception for task-related errors"""
    pass

class TaskNotFoundError(TaskError):
    """Raised when a task cannot be found"""
    pass

class InvalidTaskDataError(TaskError):
    """Raised when task data is invalid"""
    pass

class StorageError(Exception):
    """Base exception for storage-related errors"""
    pass

