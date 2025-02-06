import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tasks.commands import setup_task_commands
from tasks.storage import load_tasks

# Load environment variables
load_dotenv()

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load tasks when the bot starts
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    load_tasks()

# Setup task-related commands
setup_task_commands(bot)

# Run the bot
bot.run(os.getenv("DISCORD_TOKEN"))