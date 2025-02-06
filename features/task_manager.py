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
    
    async def verify_thread_exists(self, guild: discord.Guild, task: Task) -> bool:
        """
        Verify if a task's thread still exists and clean up if it doesn't
        Returns True if thread exists, False if it was cleaned up
        """
        if not task.thread_id:
            return False
            
        try:
            thread = await guild.fetch_channel(task.thread_id)
            return bool(thread)
        except (discord.NotFound, discord.Forbidden):
            # Thread doesn't exist or can't be accessed, clean up the task data
            self.storage.update_task(
                task.id,
                thread_id=None,
                thread_creator_id=None
            )
            return False
        except Exception as e:
            print(f"Error verifying thread {task.thread_id}: {e}")
            return False
    
    async def update_task_thread(
        self, 
        task_id: int, 
        thread_id: Optional[int], 
        thread_creator_id: Optional[int]
    ) -> Task:
        """Update task thread information"""
        return self.storage.update_task(
            task_id,
            thread_id=thread_id,
            thread_creator_id=thread_creator_id
        )
    
    async def get_task_guild(self) -> Optional[discord.Guild]:
        """Helper method to find the guild where the task board exists"""
        for guild in self.bot.guilds:
            channel = guild.get_channel(self.storage.task_channel_id)
            if channel:
                return guild
        return None

    async def update_task_status(self, task_id: int, status: TaskStatus) -> Task:
        """Update task status and delete thread if task is completed"""
        task = self.storage.get_task(task_id)
        guild = await self.get_task_guild()
        
        if guild:
            # Verify thread still exists
            thread_exists = await self.verify_thread_exists(guild, task)
            
            # If task is being marked as completed and has a valid thread, delete it
            if status == TaskStatus.COMPLETED and thread_exists:
                await self.delete_task_thread(guild, task.thread_id)
                task = self.storage.update_task(
                    task_id,
                    status=status.value,
                    thread_id=None,
                    thread_creator_id=None
                )
            else:
                # Just update the status
                task = self.storage.update_task(task_id, status=status.value)
        else:
            # No guild found, just update the status
            task = self.storage.update_task(task_id, status=status.value)
            
        return task

    async def assign_users(self, task_id: int, user_ids: List[int]) -> Task:
        """Assign users to a task"""
        return self.storage.update_task(task_id, assigned_users=user_ids)

    async def delete_task(self, task_id: int) -> Task:
        """Delete a task and its associated thread"""
        task = self.storage.get_task(task_id)
        guild = await self.get_task_guild()
        
        if guild and task.thread_id:
            # Verify and delete thread if it exists
            thread_exists = await self.verify_thread_exists(guild, task)
            if thread_exists:
                await self.delete_task_thread(guild, task.thread_id)
            
        # Delete the task from storage
        return self.storage.delete_task(task_id)

    async def get_task(self, task_id: int) -> Task:
        """Get a task by ID"""
        return self.storage.get_task(task_id)
    
    async def delete_task_thread(self, guild: discord.Guild, thread_id: int) -> None:
        """Helper method to delete a task's thread"""
        if thread_id:
            try:
                thread = await guild.fetch_channel(thread_id)
                if thread:
                    await thread.delete()
            except discord.NotFound:
                # Thread already deleted or not found
                pass
            except discord.Forbidden:
                print(f"Missing permissions to delete thread {thread_id}")
            except Exception as e:
                print(f"Error deleting thread {thread_id}: {e}")

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
        """Update the task board display and verify all threads"""
        if not self.storage.task_channel_id:
            return
            
        channel = guild.get_channel(self.storage.task_channel_id)
        if not channel:
            return
        
        # Verify all task threads before updating the board
        tasks = self.storage.get_all_tasks()
        for task_id, task in tasks.items():
            if task.thread_id:
                await self.verify_thread_exists(guild, task)
        
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
        tasks_by_status = {
            status: [] for status in TaskStatus
        }
        
        for task in self.storage.get_all_tasks().values():
            status = TaskStatus(task.status)
            tasks_by_status[status].append(task)
        
        # Create status sections
        for status, tasks in tasks_by_status.items():
            if tasks:
                embeds = TaskBoardEmbeds.create_status_section(status, tasks, guild)
                for embed in embeds:
                    await channel.send(embed=embed)