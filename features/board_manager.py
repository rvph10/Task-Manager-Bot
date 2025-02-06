import discord

from features.task_manager import TaskManager


class BoardManager:
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
    
    async def handle_message(self, message: discord.Message) -> None:
        """Handle messages in the task board channel"""
        if message.channel.id != self.task_manager.storage.task_channel_id:
            return
            
        if message.author == self.task_manager.bot.user:
            return
            
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} You cannot send messages in the task-board channel. "
                "Use the buttons to interact.",
                delete_after=5
            )
        except discord.errors.Forbidden:
            print("Missing permissions to delete message")