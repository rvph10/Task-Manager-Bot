import discord
from discord.ext import commands
from typing import Optional
from config import TASKS_FILE, TaskCommands
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

    async def on_interaction(self, interaction: discord.Interaction):
        """Handle Discord interactions (buttons, modals, etc.)"""
        if interaction.type == discord.InteractionType.component:
            try:
                # For button interactions, simply wait for them to process normally
                pass
            except Exception as e:
                print(f"Error handling interaction: {e}")
                if (interaction.channel and 
                    interaction.channel.id == self.task_store.task_channel_id):
                    await self.task_manager.update_board(interaction.guild)