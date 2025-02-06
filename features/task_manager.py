from typing import List, Optional, Dict
from datetime import datetime
import discord
from discord.ext import commands
from bot.constant import TaskStatus
from core.models import Task
from core.persistence import TaskStore
from core.exceptions import TaskNotFoundError, InvalidTaskDataError
from ui.embeds import TaskBoardEmbeds
from ui.views import TaskStatusView, CreateTaskButton
from utils.validator import validate_date, validate_task_data

class TaskManager:
    def __init__(self, bot: commands.Bot, storage: TaskStore):
        self.bot = bot
        self.storage = storage
        
    async def create_task(
        self, 
        title: str, 
        description: str, 
        due_date: Optional[str] = None
    ) -> Task:
        """Create a new task"""
        # Validate inputs
        validate_task_data(title, description, due_date)
        
        # Create task
        task = Task(
            id=0,  # Will be set by storage
            title=title,
            description=description,
            status=TaskStatus.NOT_STARTED.value,
            created_at=datetime.now(),
            due_date=validate_date(due_date) if due_date else None
        )
        
        # Save task
        self.storage.add_task(task)
        return task

    async def update_task_status(self, task_id: int, status: TaskStatus) -> Task:
        """Update task status"""
        return self.storage.update_task(task_id, status=status.value)

    async def assign_users(self, task_id: int, user_ids: List[int]) -> Task:
        """Assign users to a task"""
        return self.storage.update_task(task_id, assigned_users=user_ids)

    async def delete_task(self, task_id: int) -> Task:
        """Delete a task"""
        return self.storage.delete_task(task_id)

    async def get_task(self, task_id: int) -> Task:
        """Get a task by ID"""
        return self.storage.get_task(task_id)

    async def setup_board_channel(self, guild: discord.Guild) -> discord.TextChannel:
        """Set up the task board channel"""
        # Delete existing channel if it exists
        if self.storage.task_channel_id:
            old_channel = guild.get_channel(self.storage.task_channel_id)
            if old_channel:
                await old_channel.delete()
        
        # Create new channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                add_reactions=False,
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False
            ),
            guild.me: discord.PermissionOverwrite(
                send_messages=True,
                manage_messages=True,
                manage_channels=True,
                add_reactions=True
            )
        }
        
        channel = await guild.create_text_channel('task-board', overwrites=overwrites)
        self.storage.set_channel_id(channel.id)
        
        return channel

    async def update_board(self, guild: discord.Guild) -> None:
        """Update the task board display"""
        if not self.storage.task_channel_id:
            return
            
        channel = guild.get_channel(self.storage.task_channel_id)
        if not channel:
            return
        
        # Clear existing messages
        try:
            await channel.purge(limit=100)
        except discord.errors.Forbidden:
            print("Missing permissions to purge messages")
            return
        
        # Create header
        header_embed = TaskBoardEmbeds.create_header()
        view = discord.ui.View(timeout=None)
        view.add_item(CreateTaskButton(self))
        self.bot.add_view(view)
        await channel.send(embed=header_embed, view=view)
        
        # Group tasks by status
        tasks_by_status: Dict[TaskStatus, List[Task]] = {
            status: [] for status in TaskStatus
        }
        
        for task in self.storage.get_all_tasks().values():
            status = TaskStatus(task.status)
            tasks_by_status[status].append(task)
        
        # Create status sections
        for status, tasks in tasks_by_status.items():
            if tasks:
                embed = TaskBoardEmbeds.create_status_section(status, tasks, guild)
                await channel.send(embed=embed)