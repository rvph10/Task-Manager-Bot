import discord
from discord.ui import Button, View, Modal, TextInput
from discord import Interaction
from tasks.storage import tasks, task_counter, save_tasks
from tasks.model import Task
from config import STATUS_COLORS, STATUS_EMOJIS
from utils.helpers import validate_date

# This will store the update_task_board function
_update_task_board = None

def set_update_task_board(func):
    global _update_task_board
    _update_task_board = func

class StatusButton(Button):
    def __init__(self, status: str, task_id: int):
        super().__init__(
            label=status,
            style=discord.ButtonStyle.secondary,
            emoji=STATUS_EMOJIS.get(status, "❔"),
            custom_id=f"status_{task_id}_{status}"
        )
        self.status = status
        self.task_id = task_id

    async def callback(self, interaction: Interaction):
        if self.task_id not in tasks:
            await interaction.response.send_message("❌ Task not found.", ephemeral=True)
            return

        tasks[self.task_id].status = self.status
        save_tasks()

        embed = discord.Embed(
            title="🔄 Task Updated",
            description=f"Task #{self.task_id} status has been updated to {self.status}",
            color=STATUS_COLORS[self.status]
        )

        for child in self.view.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self.view)
        
        if _update_task_board:
            await _update_task_board(interaction.guild)

class CreateTaskModal(Modal, title="Create a New Task"):
    def __init__(self):
        super().__init__()
        self.title_input = TextInput(
            label="Task Title",
            placeholder="Enter the task title...",
            max_length=100
        )
        self.description_input = TextInput(
            label="Task Description",
            placeholder="Enter the task description...",
            style=discord.TextStyle.long,
            max_length=500
        )
        self.date_input = TextInput(
            label="Due Date (Optional)",
            placeholder="YYYY-MM-DD",
            required=False,
            max_length=10
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.date_input)

    async def on_submit(self, interaction: Interaction):
        title = self.title_input.value
        description = self.description_input.value
        date = self.date_input.value if self.date_input.value else None

        # Validate the date if provided
        if date and not validate_date(date):
            await interaction.response.send_message("❌ Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
            return

        # Create the task
        global task_counter
        task_counter += 1
        task_id = task_counter
        new_task = Task(task_id, title, description, date)
        tasks[task_id] = new_task
        save_tasks()

        embed = discord.Embed(
            title="✅ Task Created",
            description=f"Task #{task_id} has been created successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Title", value=title, inline=False)
        embed.add_field(name="Description", value=description, inline=False)
        if date:
            embed.add_field(name="Due Date", value=date, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        if _update_task_board:
            await _update_task_board(interaction.guild)

class CreateTaskButton(Button):
    def __init__(self):
        super().__init__(
            label="Create Task",
            style=discord.ButtonStyle.primary,
            emoji="➕",
            custom_id="create_task"
        )

    async def callback(self, interaction: Interaction):
        modal = CreateTaskModal()
        await interaction.response.send_modal(modal)