from discord.ext import commands
from tasks.storage import tasks, task_counter, save_tasks, load_tasks
from tasks.views import StatusButton
from tasks.models import Task
from config import STATUS_COLORS

def setup_task_commands(bot):
    @bot.command(name="create_task")
    async def create_task(ctx, title: str, description: str, date: str = None):
        global task_counter
        task_counter += 1
        task_id = task_counter
        
        tasks[task_id] = Task(task_id, title, description, date)
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
        
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete()
        await update_task_board(ctx.guild)

    # Add other task-related commands here...