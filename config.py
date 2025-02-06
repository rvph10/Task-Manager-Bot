import os
import discord
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TASKS_FILE = "tasks_data.json"
STATUS_COLORS = {
    "Not Started": discord.Color.light_grey(),
    "In Progress": discord.Color.blue(),
    "Completed": discord.Color.green(),
    "Blocked": discord.Color.red(),
    "Under Review": discord.Color.purple()
}
STATUS_EMOJIS = {
    "Not Started": "🆕",
    "In Progress": "⏳",
    "Under Review": "📝",
    "Blocked": "🚫",
    "Completed": "✅"
}

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")