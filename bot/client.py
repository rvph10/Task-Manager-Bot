from typing import Optional
import discord
from discord.ext import commands
from .commands import TaskCommands
from .tutorial import TutorialManager
from core.persistence import TaskStore, MeetingStore
from features.task_manager import TaskManager
from features.board_manager import BoardManager
from features.meeting_manager import MeetingManager
from config import TASKS_FILE, MEETINGS_FILE

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
        self.meeting_store: Optional[MeetingStore] = None
        self.task_manager: Optional[TaskManager] = None
        self.meeting_manager: Optional[MeetingManager] = None
        self.board_manager: Optional[BoardManager] = None
        self.tutorial_manager: Optional[TutorialManager] = None
        
    async def setup_hook(self) -> None:
        """Initialize bot components after login"""
        # Initialize stores
        self.task_store = TaskStore(TASKS_FILE)
        self.meeting_store = MeetingStore(MEETINGS_FILE)
        
        # Initialize managers
        self.task_manager = TaskManager(self, self.task_store)
        self.meeting_manager = MeetingManager(self, self.meeting_store)
        self.board_manager = BoardManager(self.task_manager)
        self.tutorial_manager = TutorialManager(self)
        
        # Register commands
        await self.add_cog(TaskCommands(self))
        
        # Sync slash commands
        print("Syncing slash commands...")
        await self.tree.sync()
        print("Slash commands synced!")
        
    async def on_ready(self):
        """Handle bot ready event"""
        print(f"{self.user} has connected to Discord!")
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="/help for commands"
        )
        await self.change_presence(activity=activity)
        
        # Restore boards
        for guild in self.guilds:
            try:
                if self.task_store.task_channel_id:
                    await self.task_manager.update_board(guild)
                if self.meeting_store.meeting_channel_id:
                    print(f"Restoring boards in {guild.name}")
                    await self.meeting_manager.update_board(guild)
            except Exception as e:
                print(f"Error restoring boards in {guild.name}: {e}")

    async def on_guild_join(self, guild: discord.Guild):
        """Handle when bot joins a new server"""
        if not self.tutorial_manager.has_received_tutorial(guild.id):
            try:
                # Create tutorial channel
                tutorial_channel = await self.tutorial_manager.create_tutorial_channel(guild)
                if tutorial_channel:
                    # Send tutorial messages
                    await self.tutorial_manager.send_tutorial_messages(tutorial_channel)
                    # Mark tutorial as sent
                    self.tutorial_manager.mark_tutorial_sent(guild.id)
                    print(f"Tutorial sent in {guild.name}")
            except Exception as e:
                print(f"Error sending tutorial in {guild.name}: {e}")