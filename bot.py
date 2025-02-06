import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tasks.commands import setup_task_commands
from tasks.views import set_update_task_board
from tasks.storage import load_tasks, task_channel_id

# Load environment variables
load_dotenv()

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load tasks when the bot starts
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    load_tasks()
    
    # Recreate task board on startup if channel exists
    if task_channel_id:
        for guild in bot.guilds:
            channel = guild.get_channel(task_channel_id)
            if channel:
                await update_task_board(guild)
                print(f"Recreated task board in {guild.name}")

@bot.before_invoke
async def before_command(ctx):
    # Reload tasks before each command
    load_tasks()

# Setup task-related commands and get update_task_board function
update_task_board = setup_task_commands(bot)

# Share update_task_board with views
set_update_task_board(update_task_board)

# Handle message deletion in the task-board channel
@bot.event
async def on_message(message):
    if message.channel.id == task_channel_id and message.author != bot.user:
        await message.delete()
        await message.author.send("You cannot send messages in the task-board channel. Use the buttons to interact.", delete_after=10)
    
    await bot.process_commands(message)

# Handle interaction errors
@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        # If the interaction fails, recreate the task board
        try:
            await bot.process_application_commands(interaction)
        except discord.errors.NotFound:
            if interaction.channel.id == task_channel_id:
                await update_task_board(interaction.guild)

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))