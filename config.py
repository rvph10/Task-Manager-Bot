import os
from dotenv import load_dotenv

from bot.constant import TaskStatus

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TASKS_FILE = "tasks_data.json"

# bot/client.py
import discord
from discord.ext import commands
from typing import Optional
from core.persistence import TaskStore
from features.task_manager import TaskManager
from features.board_manager import BoardManager
from core.exceptions import TaskError, StorageError
from ui.views import TaskStatusView

class TaskBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None  # We'll implement our own help command
        )
        
        # Initialize components
        self.task_store: Optional[TaskStore] = None
        self.task_manager: Optional[TaskManager] = None
        self.board_manager: Optional[BoardManager] = None
        
    async def setup_hook(self) -> None:
        """Initialize bot components after login"""
        self.task_store = TaskStore(TASKS_FILE)
        self.task_manager = TaskManager(self, self.task_store)
        self.board_manager = BoardManager(self.task_manager)
        
        # Register commands
        await self.add_cog(TaskCommands(self))
        
    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        
        # Restore task boards
        if self.task_store.task_channel_id:
            for guild in self.guilds:
                try:
                    await self.task_manager.update_board(guild)
                except Exception as e:
                    print(f"Error restoring task board in {guild.name}: {e}")

    async def on_message(self, message: discord.Message):
        # Handle messages in task board channel
        await self.board_manager.handle_message(message)
        await self.process_commands(message)

class TaskCommands(commands.Cog):
    def __init__(self, bot: TaskBot):
        self.bot = bot
    
    @commands.command(name="task_setup")
    @commands.has_permissions(administrator=True)
    async def setup_tasks(self, ctx: commands.Context):
        """Set up the task management channel"""
        try:
            channel = await self.bot.task_manager.setup_board_channel(ctx.guild)
            await ctx.send(f"Task board channel created: {channel.mention}")
            await self.bot.task_manager.update_board(ctx.guild)
        except discord.errors.Forbidden:
            await ctx.send("❌ Missing permissions to create the channel.", delete_after=10)
        except Exception as e:
            await ctx.send(f"❌ Failed to set up task board: {str(e)}", delete_after=10)

    @commands.command(name="task_create")
    async def create_task(self, ctx: commands.Context, *, args: str):
        """Create a new task"""
        try:
            # Parse arguments
            parts = [part.strip() for part in args.split('|')]
            task_data = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    task_data[key.strip().lower()] = value.strip()
            
            title = task_data.get('title')
            description = task_data.get('description')
            due_date = task_data.get('date')
            
            task = await self.bot.task_manager.create_task(
                title=title,
                description=description,
                due_date=due_date
            )
            
            embed = discord.Embed(
                title="✅ Task Created",
                description=f"Task #{task.id} has been created successfully",
                color=discord.Color.green()
            )
            embed.add_field(name="Title", value=task.title, inline=False)
            embed.add_field(name="Description", value=task.description, inline=False)
            if task.due_date:
                embed.add_field(name="Due Date", value=task.due_date.strftime("%Y-%m-%d"), inline=False)
            
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete()
            await self.bot.task_manager.update_board(ctx.guild)
            
        except (TaskError, ValueError) as e:
            await ctx.send(f"❌ {str(e)}", delete_after=10)
        except Exception as e:
            await ctx.send("❌ An error occurred while creating the task.", delete_after=10)

    @commands.command(name="task_assign")
    async def assign_task(self, ctx: commands.Context, task_id: int, *mentions: str):
        """Assign users to a task"""
        try:
            # Get all mentioned users
            assigned_users = []
            error_mentions = []
            
            for mention in mentions:
                try:
                    user_id = int(mention.strip('<@!&>'))
                    member = ctx.guild.get_member(user_id)
                    
                    if member is not None:
                        assigned_users.append(user_id)
                    else:
                        error_mentions.append(mention)
                except (ValueError, AttributeError):
                    error_mentions.append(mention)

            if not assigned_users:
                await ctx.send("❌ No valid users mentioned. Please mention users with @username.", delete_after=10)
                return

            task = await self.bot.task_manager.assign_users(task_id, assigned_users)
            
            embed = discord.Embed(
                title="👥 Task Assigned",
                description=f"Task #{task_id} has been assigned to users",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Assigned Users",
                value=", ".join(f"<@{user_id}>" for user_id in assigned_users)
            )
            
            if error_mentions:
                embed.add_field(
                    name="⚠️ Warnings",
                    value=f"Could not assign to these mentions: {', '.join(error_mentions)}"
                )

            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete()
            await self.bot.task_manager.update_board(ctx.guild)
            
        except TaskError as e:
            await ctx.send(f"❌ {str(e)}", delete_after=10)
        except Exception as e:
            await ctx.send("❌ An error occurred while assigning users.", delete_after=10)

    @commands.command(name="task_update")
    async def update_task(self, ctx: commands.Context, task_id: int):
        """Update task status using buttons"""
        try:
            task = await self.bot.task_manager.get_task(task_id)
            
            embed = discord.Embed(
                title="🔄 Update Task Status",
                description=f"Select the new status for Task #{task_id}:\n**{task.title}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Current Status", value=task.status)
            
            view = TaskStatusView(task_id, self.bot.task_manager)
            self.bot.add_view(view)
            
            await ctx.send(embed=embed, view=view)
            await ctx.message.delete()
            
        except TaskError as e:
            await ctx.send(f"❌ {str(e)}", delete_after=10)
        except Exception as e:
            await ctx.send("❌ An error occurred while updating the task.", delete_after=10)

    @commands.command(name="task_delete")
    async def delete_task(self, ctx: commands.Context, task_id: int):
        """Delete a task"""
        try:
            task = await self.bot.task_manager.delete_task(task_id)
            
            embed = discord.Embed(
                title="🗑️ Task Deleted",
                description=f"Task #{task_id} has been deleted",
                color=discord.Color.red()
            )
            embed.add_field(name="Title", value=task.title)
            
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete()
            await self.bot.task_manager.update_board(ctx.guild)
            
        except TaskError as e:
            await ctx.send(f"❌ {str(e)}", delete_after=10)
        except Exception as e:
            await ctx.send("❌ An error occurred while deleting the task.", delete_after=10)

    @commands.command(name="task_help")
    async def task_help(self, ctx: commands.Context):
        """Show help message with available commands"""
        embed = discord.Embed(
            title="📚 Task Manager Bot Commands",
            description="Here are all the available commands:",
            color=discord.Color.blue()
        )
        
        commands_info = {
            "!task_setup": "Create a dedicated channel for task tracking (Admin only)",
            "!task_create title: Title | description: Description | date: YYYY-MM-DD": 
                "Create a new task",
            "!task_assign <task_id> @user1 [@user2 ...]": 
                "Assign users to a task",
            "!task_update <task_id>": 
                "Update task status using buttons",
            "!task_delete <task_id>": 
                "Delete a task",
            "!task_help": 
                "Show this help message"
        }
        
        for command, description in commands_info.items():
            embed.add_field(
                name=command,
                value=description,
                inline=False
            )
        
        embed.add_field(
            name="Task Statuses",
            value="\n".join([
                f"{status.value}" for status in TaskStatus
            ]),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                f"❌ Command not found. Use `!task_help` to see available commands.",
                delete_after=10
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ You don't have permission to use this command.",
                delete_after=10
            )
        else:
            print(f"Command error: {error}")
            await ctx.send(
                "❌ An error occurred while processing the command.",
                delete_after=10
            )