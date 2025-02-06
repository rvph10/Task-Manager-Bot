from typing import List, Dict
import discord
from bot.constant import STATUS_EMOJIS, STATUS_COLORS
from core.models import Task
from bot.constant import TaskStatus
from datetime import datetime

class TaskBoardEmbeds:
    @staticmethod
    def create_header() -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Task Management Dashboard",
            description=(
                "**Welcome to the Task Board!**\n\n"
                "📋 Track and manage your team's tasks in real-time\n"
                "📊 Tasks are organized by their current status\n\n"
                "*Use `!task_help` for a list of available commands*"
            ),
            color=discord.Color.blue()
        )
        
        return embed
    
    @staticmethod
    def create_status_section(status: TaskStatus, tasks: List[Task]) -> discord.Embed:
        emoji = STATUS_EMOJIS[status]
        embed = discord.Embed(
            title=f"{emoji} {status.value} ({len(tasks)})",
            color=STATUS_COLORS[status]
        )
        
        if not tasks:
            embed.description = f"*No tasks are currently {status.value.lower()}*"
            return embed
        
        for task in tasks:
            # Format assigned users
            assigned_users = (
                ", ".join([f"<@{user_id}>" for user_id in task.assigned_users])
                if task.assigned_users
                else "*Unassigned*"
            )
            
            # Format due date with warning emoji if close/overdue
            due_date_str = ""
            if task.due_date:
                days_until_due = (task.due_date - datetime.now()).days
                if days_until_due < 0:
                    due_date_str = f"⚠️ **OVERDUE** ({abs(days_until_due)} days)"
                elif days_until_due == 0:
                    due_date_str = "⚠️ **DUE TODAY**"
                elif days_until_due <= 2:
                    due_date_str = f"⚠️ Due in {days_until_due} days"
                else:
                    due_date_str = f"📅 Due {task.due_date.strftime('%Y-%m-%d')}"
            else:
                due_date_str = "📅 No due date"
            
            # Create a compact but informative field
            field_value = (
                f"```{task.description[:100]}{'...' if len(task.description) > 100 else ''}```\n"
                f"👥 **Assigned to:** {assigned_users}\n"
                f"{due_date_str}"
            )
            
            embed.add_field(
                name=f"#{task.id} • {task.title}",
                value=field_value,
                inline=False
            )
        
        return embed

    @staticmethod
    def create_task_info(task: Task) -> discord.Embed:
        """Create an embed for displaying detailed task information"""
        status = TaskStatus(task.status)
        embed = discord.Embed(
            title=f"Task Details: {task.title}",
            color=STATUS_COLORS[status]
        )
        
        # Task ID and Status
        embed.add_field(
            name="🔍 Task ID",
            value=f"#{task.id}",
            inline=True
        )
        embed.add_field(
            name="📊 Status",
            value=f"{STATUS_EMOJIS[status]} {status.value}",
            inline=True
        )
        
        # Task Description
        embed.add_field(
            name="📝 Description",
            value=f"```{task.description}```",
            inline=False
        )
        
        # Assigned Users
        assigned_users = (
            ", ".join([f"<@{user_id}>" for user_id in task.assigned_users])
            if task.assigned_users
            else "*No users assigned*"
        )
        embed.add_field(
            name="👥 Assigned To",
            value=assigned_users,
            inline=False
        )
        
        # Dates
        dates_info = f"🕒 Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        if task.due_date:
            days_until_due = (task.due_date - datetime.now()).days
            if days_until_due < 0:
                dates_info += f"⚠️ **OVERDUE** by {abs(days_until_due)} days"
            elif days_until_due == 0:
                dates_info += "⚠️ **DUE TODAY**"
            else:
                dates_info += f"📅 Due: {task.due_date.strftime('%Y-%m-%-d')}"
        else:
            dates_info += "📅 No due date set"
            
        embed.add_field(
            name="📅 Dates",
            value=dates_info,
            inline=False
        )
        
        # Footer
        embed.set_footer(text="Use !task_update to change the status of this task")
        
        return embed

    @staticmethod
    def create_error_embed(error_message: str) -> discord.Embed:
        """Create an error message embed"""
        return discord.Embed(
            title="❌ Error",
            description=error_message,
            color=discord.Color.red()
        )

    @staticmethod
    def create_success_embed(title: str, description: str) -> discord.Embed:
        """Create a success message embed"""
        return discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green()
        )