import os
import json
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# File path for persistent storage
TASKS_FILE = "tasks_data.json"

# Task storage
tasks = {}
task_counter = 0
task_channel_id = None

# Colors for different status
STATUS_COLORS = {
    "Not Started": discord.Color.light_grey(),
    "In Progress": discord.Color.blue(),
    "Completed": discord.Color.green(),
    "Blocked": discord.Color.red(),
    "Under Review": discord.Color.purple()
}

def load_tasks():
    """Load tasks from JSON file"""
    global tasks, task_counter, task_channel_id
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                tasks = data.get('tasks', {})
                task_counter = data.get('task_counter', 0)
                task_channel_id = data.get('task_channel_id')
                
                # Convert string keys back to integers
                tasks = {int(k): v for k, v in tasks.items()}
                
                # Reconstruct Member objects for assigned_users
                for task in tasks.values():
                    # Store only user IDs in the file
                    task['assigned_users'] = task.get('assigned_user_ids', [])
    except Exception as e:
        print(f"Error loading tasks: {e}")
        tasks = {}
        task_counter = 0
        task_channel_id = None

def save_tasks():
    """Save tasks to JSON file"""
    try:
        data = {
            'tasks': {str(k): v for k, v in tasks.items()},  # Convert keys to strings for JSON
            'task_counter': task_counter,
            'task_channel_id': task_channel_id
        }
        
        # Before saving, convert Member objects to IDs
        for task in data['tasks'].values():
            # Store user IDs instead of Member objects
            task['assigned_user_ids'] = task['assigned_users']
            task.pop('assigned_users', None)
            
        with open(TASKS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving tasks: {e}")

async def update_task_board(guild):
    """Update the task board in the dedicated channel"""
    if not task_channel_id:
        return
    
    channel = guild.get_channel(task_channel_id)
    if not channel:
        return
        
    # Clear existing messages
    await channel.purge()
    
    # Create status boards
    status_categories = {
        "Not Started": [],
        "In Progress": [],
        "Under Review": [],
        "Blocked": [],
        "Completed": []
    }
    
    # Sort tasks by status
    for task_id, task in tasks.items():
        status = task["status"]
        if status in status_categories:
            # Convert user IDs to Member objects for display
            assigned_users = []
            for user_id in task['assigned_users']:
                member = guild.get_member(user_id)
                if member:
                    assigned_users.append(member)
            task_display = task.copy()
            task_display['assigned_users'] = assigned_users
            status_categories[status].append((task_id, task_display))
    
    # Create header
    header_embed = discord.Embed(
        title="📋 Task Management Board",
        description="Real-time task tracking and updates",
        color=discord.Color.blue()
    )
    await channel.send(embed=header_embed)
    
    # Create embeds for each status category
    for status, task_list in status_categories.items():
        if task_list:
            embed = discord.Embed(
                title=f"{status} Tasks",
                color=STATUS_COLORS.get(status, discord.Color.default())
            )
            
            for task_id, task in task_list:
                assigned_users = ", ".join([user.name for user in task["assigned_users"]]) if task["assigned_users"] else "None"
                due_date = f"Due: {task['date']}" if task['date'] else "No due date"
                
                field_value = f"Description: {task['description']}\n"
                field_value += f"Assigned to: {assigned_users}\n"
                field_value += f"{due_date}"
                
                embed.add_field(
                    name=f"#{task_id}: {task['title']}",
                    value=field_value,
                    inline=False
                )
            
            await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    load_tasks()  # Load tasks when bot starts

@bot.command(name="setup_tasks")
@commands.has_permissions(administrator=True)
async def setup_tasks(ctx):
    """Set up the task management channel"""
    global task_channel_id
    
    # Create a new channel for tasks
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(send_messages=True)
    }
    
    channel = await ctx.guild.create_text_channel('task-board', overwrites=overwrites)
    task_channel_id = channel.id
    save_tasks()  # Save the new channel ID
    
    await ctx.send(f"Task board channel created: {channel.mention}")
    await update_task_board(ctx.guild)

@bot.command(name="create_task")
async def create_task(ctx, title: str, description: str, date: str = None):
    global task_counter
    task_counter += 1
    task_id = task_counter
    
    tasks[task_id] = {
        "title": title,
        "description": description,
        "date": date,
        "assigned_users": [],
        "status": "Not Started"
    }
    
    save_tasks()  # Save after creating task
    
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

@bot.command(name="assign_task")
async def assign_task(ctx, task_id: int, *mentions):
    if task_id not in tasks:
        await ctx.send("❌ Task not found.", delete_after=5)
        return

    # Get all mentioned users
    assigned_users = []
    error_mentions = []
    
    for mention in mentions:
        try:
            # Try to convert mention to user ID
            user_id = int(mention.strip('<@!&>'))
            member = ctx.guild.get_member(user_id)
            
            if member is not None:
                assigned_users.append(member)
            else:
                error_mentions.append(mention)
        except (ValueError, AttributeError):
            error_mentions.append(mention)

    if not assigned_users:
        await ctx.send("❌ No valid users mentioned. Please mention users with @username.", delete_after=10)
        return

    if error_mentions:
        await ctx.send(f"⚠️ Warning: Could not assign to these mentions: {', '.join(error_mentions)}", delete_after=10)

    # Store user IDs
    tasks[task_id]["assigned_users"] = [user.id for user in assigned_users]
    save_tasks()

    embed = discord.Embed(
        title="👥 Task Assigned",
        description=f"Task #{task_id} has been assigned to users",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Assigned Users", 
        value=", ".join(user.mention for user in assigned_users)
    )

    await ctx.send(embed=embed, delete_after=10)
    await ctx.message.delete()
    await update_task_board(ctx.guild)

class StatusButton(Button):
    def __init__(self, status: str, task_id: int):
        emoji_map = {
            "Not Started": "🆕",
            "In Progress": "⏳",
            "Under Review": "📝",
            "Blocked": "🚫",
            "Completed": "✅"
        }
        super().__init__(
            label=status,
            style=discord.ButtonStyle.secondary,
            emoji=emoji_map.get(status, "❔"),
            custom_id=f"status_{task_id}_{status}"
        )
        self.status = status
        self.task_id = task_id

    async def callback(self, interaction: discord.Interaction):
        if self.task_id not in tasks:
            await interaction.response.send_message("❌ Task not found.", ephemeral=True)
            return

        tasks[self.task_id]["status"] = self.status
        save_tasks()

        embed = discord.Embed(
            title="🔄 Task Updated",
            description=f"Task #{self.task_id} status has been updated to {self.status}",
            color=STATUS_COLORS[self.status]
        )

        # Disable all buttons in the view after selection
        for child in self.view.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self.view)
        await update_task_board(interaction.guild)

@bot.command(name="update_task")
async def update_task(ctx, task_id: int):
    """Update task status using buttons"""
    if task_id not in tasks:
        await ctx.send("❌ Task not found.", delete_after=5)
        return

    # Create view with status buttons
    view = View(timeout=60)  # Buttons will be disabled after 60 seconds
    for status in STATUS_COLORS.keys():
        view.add_item(StatusButton(status, task_id))

    embed = discord.Embed(
        title="🔄 Update Task Status",
        description=f"Select the new status for Task #{task_id}:\n**{tasks[task_id]['title']}**",
        color=discord.Color.blue()
    )
    embed.add_field(name="Current Status", value=tasks[task_id]["status"])

    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

@bot.command(name="delete_task")
async def delete_task(ctx, task_id: int):
    if task_id not in tasks:
        await ctx.send("❌ Task not found.", delete_after=5)
        return
    
    deleted_task = tasks.pop(task_id)
    save_tasks()  # Save after deleting task
    
    embed = discord.Embed(
        title="🗑️ Task Deleted",
        description=f"Task #{task_id} has been deleted",
        color=discord.Color.red()
    )
    embed.add_field(name="Title", value=deleted_task["title"])
    
    await ctx.send(embed=embed, delete_after=10)
    await ctx.message.delete()
    await update_task_board(ctx.guild)

@bot.command(name="taskhelp")
async def task_help(ctx):
    embed = discord.Embed(
        title="📚 Task Manager Bot Commands",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )
    
    commands_info = {
        "!setup_tasks": "Create a dedicated channel for task tracking (Admin only)",
        "!create_task <title> <description> [due_date]": "Create a new task",
        "!assign_task <task_id> @user1 [@user2 ...]": "Assign users to a task",
        "!update_task <task_id>": "Update task status using buttons",
        "!delete_task <task_id>": "Delete a task",
        "!taskhelp": "Show this help message"
    }
    
    for command, description in commands_info.items():
        embed.add_field(name=command, value=description, inline=False)
    
    embed.add_field(
        name="Task Statuses",
        value="• Not Started\n• In Progress\n• Under Review\n• Blocked\n• Completed",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Run the bot
bot.run(os.getenv("DISCORD_TOKEN"))