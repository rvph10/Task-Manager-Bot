from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

@dataclass
class Task:
    id: int
    title: str
    description: str
    status: str
    created_at: datetime
    due_date: Optional[datetime] = None
    assigned_users: List[int] = None
    thread_id: Optional[int] = None
    thread_creator_id: Optional[int] = None
    
    def __post_init__(self):
        if self.assigned_users is None:
            self.assigned_users = []

    def to_dict(self) -> dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.due_date:
            data['due_date'] = self.due_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        # Convert ISO format strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('due_date'):
            data['due_date'] = datetime.fromisoformat(data['due_date'])
        return cls(**data)