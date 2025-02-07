import json
import discord
from typing import Optional

class TutorialManager:
    def __init__(self, bot):
        self.bot = bot
        self.tutorial_file = "server_data.json"
        self.tutorial_sent = self._load_data()

    def _load_data(self) -> list:
        try:
            with open(self.tutorial_file, 'r') as f:
                data = json.load(f)
                return data.get('tutorial_sent', [])
        except FileNotFoundError:
            return []

    def _save_data(self) -> None:
        with open(self.tutorial_file, 'w') as f:
            json.dump({'tutorial_sent': self.tutorial_sent}, f, indent=4)

    def has_received_tutorial(self, guild_id: int) -> bool:
        return str(guild_id) in self.tutorial_sent

    def mark_tutorial_sent(self, guild_id: int) -> None:
        if str(guild_id) not in self.tutorial_sent:
            self.tutorial_sent.append(str(guild_id))
            self._save_data()

    async def create_tutorial_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        # Check if channel already exists
        existing_channel = discord.utils.get(guild.text_channels, name='bot-tutorial')
        if existing_channel:
            return existing_channel

        # Create channel with proper permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=False
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True
            )
        }

        try:
            return await guild.create_text_channel('bot-tutorial', overwrites=overwrites)
        except discord.Forbidden:
            return None

    async def send_tutorial_messages(self, channel: discord.TextChannel) -> None:
        # Welcome Message
        welcome_embed = discord.Embed(
            title="👋 Welcome to Task & Meeting Manager!",
            description="I'm here to help you manage tasks and meetings in your server. Let me show you how to get started!",
            color=discord.Color.blue()
        )
        welcome_embed.set_footer(text="Read through this tutorial to learn about the bot's features")
        await channel.send(embed=welcome_embed)

        # Setup Instructions
        setup_embed = discord.Embed(
            title="🛠️ Setting Up the Bot",
            description="First, you'll need to set up the necessary channels:",
            color=discord.Color.green()
        )
        setup_embed.add_field(
            name="1️⃣ Run the Setup Command",
            value="Use `/setup` to create the task board and meeting dashboard channels (Admin only)",
            inline=False
        )
        setup_embed.add_field(
            name="2️⃣ Channels Created",
            value="Two channels will be created:\n• 📋 `task-board`\n• 📅 `meeting-dashboard`",
            inline=False
        )
        await channel.send(embed=setup_embed)

        # Task Management
        tasks_embed = discord.Embed(
            title="📋 Task Management",
            description="Here's how to manage tasks:",
            color=discord.Color.blue()
        )
        tasks_embed.add_field(
            name="Creating Tasks",
            value="• `/create` - Create a new task\n• Add title, description, and due date\n• Assign team members with `/assign`",
            inline=False
        )
        tasks_embed.add_field(
            name="Managing Tasks",
            value="• `/update` - Change task status\n• `/thread` - Create discussion threads\n• `/info` - View task details\n• `/list` - See your assigned tasks",
            inline=False
        )
        await channel.send(embed=tasks_embed)

        # Meeting Management
        meetings_embed = discord.Embed(
            title="📅 Meeting Management",
            description="Schedule and manage meetings easily:",
            color=discord.Color.purple()
        )
        meetings_embed.add_field(
            name="Scheduling Meetings",
            value="• `/create_meeting` - Schedule a new meeting\n• Set title, time, duration, and participants\n• Choose a voice channel for the meeting",
            inline=False
        )
        meetings_embed.add_field(
            name="Meeting Features",
            value="• RSVP system (Yes/Maybe/No)\n• Automatic reminders\n• Attendance tracking\n• Meeting dashboard updates",
            inline=False
        )
        await channel.send(embed=meetings_embed)

        # Additional Features
        tips_embed = discord.Embed(
            title="💡 Pro Tips",
            description="Make the most of the bot with these features:",
            color=discord.Color.gold()
        )
        tips_embed.add_field(
            name="Task Organization",
            value="• Tasks are automatically organized by status\n• Due dates are highlighted when approaching\n• Discussion threads keep conversations organized",
            inline=False
        )
        tips_embed.add_field(
            name="Meeting Organization",
            value="• Meetings show RSVP status in real-time\n• Automated reminders 30 minutes before meetings\n• Easy-to-use reaction buttons for RSVP",
            inline=False
        )
        tips_embed.add_field(
            name="Need Help?",
            value="Use `/help` anytime to see all available commands!",
            inline=False
        )
        await channel.send(embed=tips_embed)