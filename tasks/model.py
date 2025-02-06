class Task:
    def __init__(self, task_id, title, description, date=None, assigned_users=None, status="Not Started"):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.date = date
        self.assigned_users = assigned_users or []
        self.status = status

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "date": self.date,
            "assigned_users": self.assigned_users,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            date=data.get("date"),
            assigned_users=data.get("assigned_users", []),
            status=data.get("status", "Not Started")
        )