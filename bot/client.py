from typing import Optional
import discord
from discord.ext import commands
from .commands import TaskCommands
from core.persistence import TaskStore
from features.task_manager import TaskManager
from features.board_manager import BoardManager
from config import TASKS_FILE

class TaskBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",  # Keep a prefix for potential admin commands
            intents=intents,
            help_command=None
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
        
        # Sync slash commands
        print("Syncing slash commands...")
        await self.tree.sync()
        print("Slash commands synced!")
        
    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="/help for commands"
        )
        await self.change_presence(activity=activity)
        
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