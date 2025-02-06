from typing import List
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
    def create_status_section(status: TaskStatus, tasks: List[Task], guild: discord.Guild) -> List[discord.Embed]:
        """Create status section embeds, splitting into multiple embeds if needed"""
        embeds = []
        # Reduced to 3 tasks per embed since each task uses 7 fields max (4 main + 3 for thread)
        tasks_per_embed = 3  
        
        for i in range(0, len(tasks), tasks_per_embed):
            chunk = tasks[i:i + tasks_per_embed]
            
            emoji = STATUS_EMOJIS[status]
            embed = discord.Embed(
                title=f"{emoji} {status.value} ({len(tasks)})",
                color=STATUS_COLORS[status]
            )
            
            if not chunk:
                embed.description = f"*No tasks are currently {status.value.lower()}*"
                embeds.append(embed)
                continue
            
            for task in chunk:
                # Format due date
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

                # Add task fields
                embed.add_field(
                    name=f"**__#{task.id} • {task.title}__**",
                    value=f"**Task description** :\n```{task.description}```\n",
                    inline=False
                )
                embed.add_field(
                    name="**Assigned To**",
                    value= ", ".join([f"<@{user_id}>" for user_id in task.assigned_users]) if len(task.assigned_users) > 1 else f"<@{task.assigned_users[0]}>" if len(task.assigned_users) > 0 else "Unassigned",
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

                embed.set_thumbnail(url=f"https://placehold.co/400x400/2C2D31/FFFFFF/png?text=%23{len(embeds) + 1}")

                # Add thread information if exists
                if task.thread_id:
                    thread = guild.get_thread(task.thread_id)
                    if thread:  
                        embed.add_field(
                            name="💬 Discussion",
                            value=f"[Go to thread]({thread.jump_url})",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="💬 Discussion",
                            value="*Thread not found*",
                            inline=True
                        )

                # Add separator only between tasks, not after the last one
                if task != chunk[-1]:
                    embed.add_field(name="\u200b", value="\u200b", inline=False)

            # Set footer for each embed
            embed.set_footer(
                text="Use !task_update [task_id] to change status • Use !task_help for more commands",
                icon_url="https://cdn.discordapp.com/app-icons/1336810436984836226/ce2f15ca0258cffeecfe1fc6276ee28d.png?size=512"
            )
            
            embeds.append(embed)
        
        return embeds

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