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
    def create_status_section(status: TaskStatus, tasks: List[Task], guild: discord.Guild) -> discord.Embed:
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
            if task.assigned_users:
                # Check if task is assigned to everyone
                all_members = set(member.id for member in guild.members if not member.bot)
                task_users = set(task.assigned_users)
                
                if task_users.issuperset(all_members):
                    assigned_users = "@everyone"
                else:
                    assigned_users = ", ".join([f"<@{user_id}>" for user_id in task.assigned_users])
            else:
                assigned_users = "*Unassigned*"
            
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

            embed.add_field(
                name=f"**__#{task.id} • {task.title}__**",
                value=f"**Task description** :\u200b{task.description}",
                inline=False
            )
            embed.add_field(
                name="**Assigned To**",
                value=assigned_users,
                inline=True
            )
            embed.add_field(
                name="**Due Date**",
                value=due_date_str,
                inline=True
            )
            embed.add_field(
                name="**Status**",
                value=task.status,
                inline=True
            )
            if (task.id != tasks[-1].id):
                embed.add_field(name="\u200b", value="\u200b", inline=False)
            else:
                embed.add_field(name="", value="\u200b", inline=False)

            embed.set_footer(
                text="Use !task_update [task_id] to change the status of a task • Use !task_help for more commands",
                icon_url="https://cdn.discordapp.com/app-icons/1336810436984836226/ce2f15ca0258cffeecfe1fc6276ee28d.png?size=512",
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