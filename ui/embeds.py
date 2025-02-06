from typing import List, Dict
import discord
from bot.constant import STATUS_EMOJIS
from core.models import Task
from bot.constant import TaskStatus, STATUS_COLORS

class TaskBoardEmbeds:
    @staticmethod
    def create_header() -> discord.Embed:
        return discord.Embed(
            title="📋 Task Management Board",
            description="Real-time task tracking and updates",
            color=discord.Color.blue()
        )
    
    @staticmethod
    def create_status_section(status: TaskStatus, tasks: List[Task]) -> discord.Embed:
        embed = discord.Embed(
            title=f"{status.value} Tasks",
            color=STATUS_COLORS[status]
        )
        
        for task in tasks:
            assigned_users = ", ".join([f"<@{user_id}>" for user_id in task.assigned_users]) or "None"
            due_date = f"Due: {task.due_date.strftime('%Y-%m-%d')}" if task.due_date else "No due date"
            
            field_value = (
                f"Description: {task.description}\n"
                f"Assigned to: {assigned_users}\n"
                f"{due_date}"
            )
            
            embed.add_field(
                name=f"#{task.id}: {task.title}",
                value=field_value,
                inline=False
            )
        
        return embed

    @staticmethod
    def create_task_info(task: Task) -> discord.Embed:
        """Create an embed for displaying detailed task information"""
        embed = discord.Embed(
            title=f"Task #{task.id}: {task.title}",
            color=STATUS_COLORS[TaskStatus(task.status)]
        )
        
        embed.add_field(name="Description", value=task.description, inline=False)
        embed.add_field(
            name="Status", 
            value=f"{STATUS_EMOJIS[TaskStatus(task.status)]} {task.status}",
            inline=True
        )
        
        assigned_users = ", ".join([f"<@{user_id}>" for user_id in task.assigned_users]) or "None"
        embed.add_field(name="Assigned To", value=assigned_users, inline=True)
        
        if task.due_date:
            embed.add_field(
                name="Due Date", 
                value=task.due_date.strftime("%Y-%m-%d"),
                inline=True
            )
        
        embed.add_field(
            name="Created At",
            value=task.created_at.strftime("%Y-%m-%d %H:%M"),
            inline=True
        )
        
        return embed