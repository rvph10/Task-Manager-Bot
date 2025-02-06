import discord
from discord import TextStyle
from discord.ui import Modal, TextInput
from core.exceptions import InvalidTaskDataError
from datetime import datetime

from utils.validator import validate_task_data

class CreateTaskModal(Modal):
    def __init__(self, task_manager):
        super().__init__(title="Create a New Task")
        self.task_manager = task_manager
        
        self.title_input = TextInput(
            label="Task Title",
            placeholder="Enter the task title...",
            max_length=100,
            required=True
        )
        
        self.description_input = TextInput(
            label="Task Description",
            placeholder="Enter the task description...",
            style=TextStyle.long,
            max_length=500,
            required=True
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

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate inputs
            title = self.title_input.value
            description = self.description_input.value
            due_date = self.date_input.value if self.date_input.value else None
            
            validate_task_data(title, description, due_date)
            
            # Create task
            task = await self.task_manager.create_task(
                title=title,
                description=description,
                due_date=due_date
            )
            
            # Create response embed
            embed = discord.Embed(
                title="✅ Task Created",
                description=f"Task #{task.id} has been created successfully",
                color=discord.Color.green()
            )
            embed.add_field(name="Title", value=task.title, inline=False)
            embed.add_field(name="Description", value=task.description, inline=False)
            if task.due_date:
                embed.add_field(name="Due Date", value=task.due_date.strftime("%Y-%m-%d"), inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Update task board
            await self.task_manager.update_board(interaction.guild)
            
        except InvalidTaskDataError as e:
            await interaction.response.send_message(
                f"❌ {str(e)}", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while creating the task.", 
                ephemeral=True
            )