from typing import Optional
import discord
from discord.ui import View, Button
from bot.constant import TaskStatus, STATUS_COLORS, STATUS_EMOJIS
from ui.modals import CreateTaskModal

class CreateTaskButton(Button):
    def __init__(self, task_manager):
        super().__init__(
            label="Create Task",
            style=discord.ButtonStyle.primary,
            emoji="➕",
            custom_id="create_task"
        )
        self.task_manager = task_manager

    async def callback(self, interaction: discord.Interaction):
        modal = CreateTaskModal(self.task_manager)
        await interaction.response.send_modal(modal)

class StatusButton(Button):
    def __init__(self, status: TaskStatus, task_id: int, task_manager):
        super().__init__(
            label=status.value,
            style=discord.ButtonStyle.secondary,
            emoji=STATUS_EMOJIS[status],
            custom_id=f"status_{task_id}_{status.value}"
        )
        self.status = status
        self.task_id = task_id
        self.task_manager = task_manager

    async def callback(self, interaction: discord.Interaction):
        try:
            task = await self.task_manager.update_task_status(self.task_id, self.status)
            
            embed = discord.Embed(
                title="🔄 Task Updated",
                description=f"Task #{self.task_id} status has been updated to {self.status.value}",
                color=STATUS_COLORS[self.status]
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            await self.task_manager.update_board(interaction.guild)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to update task status: {str(e)}", 
                ephemeral=True
            )

class TaskStatusView(View):
    def __init__(self, task_id: int, task_manager):
        super().__init__(timeout=None)
        for status in TaskStatus:
            self.add_item(StatusButton(status, task_id, task_manager))