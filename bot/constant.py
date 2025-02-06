from enum import Enum
import discord

class TaskStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    UNDER_REVIEW = "Under Review"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"

STATUS_COLORS = {
    TaskStatus.NOT_STARTED: discord.Color.light_grey(),
    TaskStatus.IN_PROGRESS: discord.Color.blue(),
    TaskStatus.UNDER_REVIEW: discord.Color.purple(),
    TaskStatus.BLOCKED: discord.Color.red(),
    TaskStatus.COMPLETED: discord.Color.green()
}

STATUS_EMOJIS = {
    TaskStatus.NOT_STARTED: "🆕",
    TaskStatus.IN_PROGRESS: "⏳",
    TaskStatus.UNDER_REVIEW: "📝",
    TaskStatus.BLOCKED: "🚫",
    TaskStatus.COMPLETED: "✅"
}