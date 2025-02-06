import discord
from discord.ext import commands
from tasks.storage import tasks, task_counter, save_tasks, load_tasks, task_channel_id
from tasks.views import StatusButton, CreateTaskButton
from tasks.model import Task
from config import STATUS_COLORS
from discord.ui import View

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
        status = task.status
        if status in status_categories:
            status_categories[status].append((task_id, task))
    
    # Create header
    header_embed = discord.Embed(
        title="📋 Task Management Board",
        description="Real-time task tracking and updates",
        color=discord.Color.blue()
    )
    
    # Add the "Create Task" button
    view = View(timeout=None)
    view.add_item(CreateTaskButton())
    
    await channel.send(embed=header_embed, view=view)
    
    # Create embeds for each status category
    for status, task_list in status_categories.items():
        if task_list:
            embed = discord.Embed(
                title=f"{status} Tasks",
                color=STATUS_COLORS.get(status, discord.Color.default())
            )
            
            for task_id, task in task_list:
                assigned_users = ", ".join([str(user_id) for user_id in task.assigned_users]) if task.assigned_users else "None"
                due_date = f"Due: {task.date}" if task.date else "No due date"
                
                field_value = f"Description: {task.description}\n"
                field_value += f"Assigned to: {assigned_users}\n"
                field_value += f"{due_date}"
                
                embed.add_field(
                    name=f"#{task_id}: {task.title}",
                    value=field_value,
                    inline=False
                )
            
            await channel.send(embed=embed)

def setup_task_commands(bot):
    @bot.command(name="task_setup")
    @commands.has_permissions(administrator=True)
    async def setup_tasks(ctx):
        """Set up the task management channel"""
        global task_channel_id
        
        # If a task channel already exists, delete it
        if task_channel_id:
            old_channel = ctx.guild.get_channel(task_channel_id)
            if old_channel:
                await old_channel.delete()
        
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
        
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete()
        await update_task_board(ctx.guild)

    @bot.command(name="task_assign")
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
                    assigned_users.append(user_id)  # Store user ID instead of Member object
                else:
                    error_mentions.append(mention)
            except (ValueError, AttributeError):
                error_mentions.append(mention)

        if not assigned_users:
            await ctx.send("❌ No valid users mentioned. Please mention users with @username.", delete_after=10)
            return

        if error_mentions:
            await ctx.send(f"⚠️ Warning: Could not assign to these mentions: {', '.join(error_mentions)}", delete_after=10)

        tasks[task_id].assigned_users = assigned_users
        save_tasks()

        embed = discord.Embed(
            title="👥 Task Assigned",
            description=f"Task #{task_id} has been assigned to users",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Assigned Users", 
            value=", ".join(f"<@{user_id}>" for user_id in assigned_users)
        )

        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete()
        await update_task_board(ctx.guild)

    @bot.command(name="task_update")
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
            description=f"Select the new status for Task #{task_id}:\n**{tasks[task_id].title}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Status", value=tasks[task_id].status)

        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()

    @bot.command(name="task_delete")
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
        embed.add_field(name="Title", value=deleted_task.title)
        
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete()
        await update_task_board(ctx.guild)

    @bot.command(name="task_help")
    async def task_help(ctx):
        embed = discord.Embed(
            title="📚 Task Manager Bot Commands",
            description="Here are all the available commands:",
            color=discord.Color.blue()
        )
        
        commands_info = {
            "!task_setup": "Create a dedicated channel for task tracking (Admin only)",
            "!task_create <title> <description> [due_date]": "Create a new task",
            "!task_assign <task_id> @user1 [@user2 ...]": "Assign users to a task",
            "!task_update <task_id>": "Update task status using buttons",
            "!task_delete <task_id>": "Delete a task",
            "!task_help": "Show this help message"
        }
        
        for command, description in commands_info.items():
            embed.add_field(name=command, value=description, inline=False)
        
        embed.add_field(
            name="Task Statuses",
            value="• Not Started\n• In Progress\n• Under Review\n• Blocked\n• Completed",
            inline=False
        )
        
        await ctx.send(embed=embed)

    return update_task_board