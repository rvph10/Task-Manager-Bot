from typing import Optional
from core.models import Meeting
import discord
from discord import app_commands
from discord.ext import commands
from bot.constant import TaskStatus, STATUS_EMOJIS
from datetime import datetime
from core.exceptions import TaskError, InvalidTaskDataError, TaskNotFoundError
from ui.embeds import TaskBoardEmbeds
from ui.views import TaskStatusView

class TaskCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(
        name="setup",
        description="Set up the task and meeting management channels (Admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tasks(self, interaction: discord.Interaction):
        try:
            # Create task board channel
            task_channel = await self.bot.task_manager.setup_board_channel(interaction.guild)
            
            # Create meeting dashboard channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    send_messages=False,
                    add_reactions=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True,
                    add_reactions=True
                )
            }
            
            meeting_channel = await interaction.guild.create_text_channel(
                'meeting-dashboard',
                overwrites=overwrites
            )
            self.bot.meeting_store.set_channel_id(meeting_channel.id)
            
            # Send success message
            embed = discord.Embed(
                title="✅ Setup Complete",
                description="Task and meeting management channels have been created.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📋 Task Board",
                value=task_channel.mention,
                inline=True
            )
            embed.add_field(
                name="📅 Meeting Dashboard",
                value=meeting_channel.mention,
                inline=True
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Update both boards
            await self.bot.task_manager.update_board(interaction.guild)
            await self.bot.meeting_manager.update_board(interaction.guild)
            
        except discord.errors.Forbidden:
            await interaction.response.send_message(
                "❌ Missing permissions to create the channels.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to set up channels: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="reset_data",
        description="Reset all tasks and meetings data and channels (Admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_data(self, interaction: discord.Interaction):
        try:
            deleted_channels = []
            
            # Delete task board channel if it exists
            if self.bot.task_store.task_channel_id:
                task_channel = interaction.guild.get_channel(self.bot.task_store.task_channel_id)
                if task_channel:
                    await task_channel.delete()
                    deleted_channels.append("Task Board")
                self.bot.task_store.task_channel_id = None
            
            # Delete meeting dashboard channel if it exists
            if self.bot.meeting_store.meeting_channel_id:
                meeting_channel = interaction.guild.get_channel(self.bot.meeting_store.meeting_channel_id)
                if meeting_channel:
                    await meeting_channel.delete()
                    deleted_channels.append("Meeting Dashboard")
                self.bot.meeting_store.meeting_channel_id = None
            
            # Delete all task threads
            for task in self.bot.task_store.tasks.values():
                if task.thread_id:
                    try:
                        thread = await interaction.guild.fetch_channel(task.thread_id)
                        if thread:
                            await thread.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
            
            # Clear tasks data
            self.bot.task_store.tasks = {}
            self.bot.task_store.task_counter = 0
            self.bot.task_store._save()
            
            # Clear meetings data
            self.bot.meeting_store.meetings = {}
            self.bot.meeting_store.meeting_counter = 0
            self.bot.meeting_store._save()
            
            # Create response embed
            embed = discord.Embed(
                title="🗑️ Data Reset Complete",
                description="All data has been cleared and reset.",
                color=discord.Color.red()
            )
            
            # Add field for deleted channels
            if deleted_channels:
                embed.add_field(
                    name="Deleted Channels",
                    value="\n".join(f"✅ {channel}" for channel in deleted_channels),
                    inline=False
                )
            
            # Add field for deleted data
            embed.add_field(
                name="Deleted Data",
                value="✅ All tasks\n✅ All meetings\n✅ Task threads",
                inline=False
            )
            
            embed.set_footer(text="Use /setup to create new channels")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An error occurred while resetting data: {str(e)}",
                ephemeral=True
            )

    @reset_data.error
    async def reset_data_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ An error occurred: {str(error)}",
                ephemeral=True
            )


    @app_commands.command(
        name="create",
        description="Create a new task"
    )
    @app_commands.describe(
        title="The title of the task",
        description="Detailed description of the task",
        due_date="Due date in DD-MM-YYYY format (optional)"
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        due_date: Optional[str] = None
    ):
        try:
            task = await self.bot.task_manager.create_task(
                title=title,
                description=description,
                due_date=due_date
            )
            
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
            await self.bot.task_manager.update_board(interaction.guild)
            
        except (TaskError, ValueError) as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while creating the task.",
                ephemeral=True
            )

    @app_commands.command(
        name="assign",
        description="Assign users to a task"
    )
    @app_commands.describe(
        task_id="The ID of the task to assign",
        users="The users to assign (mention them)"
    )
    async def assign_task(
        self,
        interaction: discord.Interaction,
        task_id: int,
        users: str
    ):
        try:
            # Parse user mentions
            assigned_users = []
            mentions = users.split()
            
            for mention in mentions:
                stripped_mention = mention.strip('<@!>')
                
                if mention in ['@everyone', '@here']:
                    assigned_users = [member.id for member in interaction.guild.members if not member.bot]
                    break
                    
                if stripped_mention.isdigit():
                    user_id = int(stripped_mention)
                    member = interaction.guild.get_member(user_id)
                    if member and not member.bot:
                        assigned_users.append(user_id)

            if not assigned_users:
                await interaction.response.send_message(
                    "❌ No valid users mentioned. Please mention users with @username or use @everyone.",
                    ephemeral=True
                )
                return

            task = await self.bot.task_manager.assign_users(task_id, assigned_users)
            
            embed = discord.Embed(
                title="👥 Task Assigned",
                description=f"Task #{task_id} has been assigned to users",
                color=discord.Color.blue()
            )
            
            if '@everyone' in mentions or '@here' in mentions:
                embed.add_field(name="Assigned Users", value="@everyone")
            else:
                embed.add_field(
                    name="Assigned Users",
                    value=", ".join(f"<@{user_id}>" for user_id in assigned_users)
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.task_manager.update_board(interaction.guild)
            
        except TaskError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while assigning users.",
                ephemeral=True
            )

    @app_commands.command(
        name="thread",
        description="Create a discussion thread for a task"
    )
    @app_commands.describe(task_id="The ID of the task to create a thread for")
    async def create_thread(self, interaction: discord.Interaction, task_id: int):
        try:
            task = await self.bot.task_manager.get_task(task_id)
            
            if task.thread_id:
                thread = await interaction.guild.fetch_channel(task.thread_id)
                if thread:
                    await interaction.response.send_message(
                        f"❌ This task already has a thread: {thread.mention}",
                        ephemeral=True
                    )
                    return
            
            task_channel = interaction.guild.get_channel(self.bot.task_store.task_channel_id)
            if not task_channel:
                await interaction.response.send_message(
                    "❌ Task board channel not found.",
                    ephemeral=True
                )
                return
            
            if not task.assigned_users:
                await interaction.response.send_message(
                    "❌ Task must have at least one assigned user to create a thread",
                    ephemeral=True
                )
                return
                
            thread = await task_channel.create_thread(
                name=f"Task #{task_id} - {task.title}",
                type=discord.ChannelType.public_thread
            )
            
            await self.bot.task_manager.update_task_thread(
                task_id=task_id,
                thread_id=thread.id,
                thread_creator_id=interaction.user.id
            )
            
            embed = discord.Embed(
                title=f"📝 Task #{task_id} Discussion",
                description=task.description,
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Assigned Users",
                value=", ".join([f"<@{user_id}>" for user_id in task.assigned_users]),
                inline=False
            )
            await thread.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅ Thread created successfully: {thread.mention}",
                ephemeral=True
            )
            await self.bot.task_manager.update_board(interaction.guild)
            
        except TaskError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while creating the thread.",
                ephemeral=True
            )

    @app_commands.command(
        name="delete_thread",
        description="Delete the discussion thread for a task"
    )
    @app_commands.describe(task_id="The ID of the task whose thread to delete")
    async def delete_thread(self, interaction: discord.Interaction, task_id: int):
        try:
            task = await self.bot.task_manager.get_task(task_id)
            
            if not task.thread_id:
                await interaction.response.send_message(
                    "❌ This task doesn't have a thread",
                    ephemeral=True
                )
                return
                
            if task.thread_creator_id != interaction.user.id:
                await interaction.response.send_message(
                    "❌ Only the thread creator can delete the thread",
                    ephemeral=True
                )
                return
                
            thread = await interaction.guild.fetch_channel(task.thread_id)
            if thread:
                await thread.delete()
            
            await self.bot.task_manager.update_task_thread(
                task_id=task_id,
                thread_id=None,
                thread_creator_id=None
            )
            
            await interaction.response.send_message(
                "✅ Thread deleted successfully",
                ephemeral=True
            )
            await self.bot.task_manager.update_board(interaction.guild)
            
        except TaskError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while deleting the thread.",
                ephemeral=True
            )

    @app_commands.command(
        name="info",
        description="Get detailed information about a specific task"
    )
    @app_commands.describe(task_id="The ID of the task to get info about")
    async def get_task_info(self, interaction: discord.Interaction, task_id: int):
        try:
            task = await self.bot.task_manager.get_task(task_id)
            embed = TaskBoardEmbeds.create_task_info(task)
            
            if task.thread_id:
                thread = interaction.guild.get_thread(task.thread_id)
                if thread:
                    embed.add_field(
                        name="💬 Discussion Thread",
                        value=f"[Go to thread]({thread.jump_url})",
                        inline=False
                    )
                    thread_creator = interaction.guild.get_member(task.thread_creator_id)
                    if thread_creator:
                        embed.add_field(
                            name="Thread Created By",
                            value=thread_creator.mention,
                            inline=True
                        )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An error occurred while fetching task information: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="list",
        description="List all tasks assigned to you"
    )
    async def task_list(self, interaction: discord.Interaction):
        try:
            tasks = self.bot.task_store.get_all_tasks().values()
            user_tasks = [task for task in tasks if interaction.user.id in task.assigned_users]
            
            if not user_tasks:
                await interaction.response.send_message(
                    "📝 You have no tasks assigned to you.",
                    ephemeral=True
                )
                return
                
            tasks_by_status = {status: [] for status in TaskStatus}
            for task in user_tasks:
                status = TaskStatus(task.status)
                tasks_by_status[status].append(task)
                
            header_embed = discord.Embed(
                title="📋 Your Task List",
                description="Tasks assigned to you",
                color=discord.Color.blue()
            )
            
            all_embeds = [header_embed]
            
            for status, tasks in tasks_by_status.items():
                if tasks:
                    status_embeds = TaskBoardEmbeds.create_status_section(
                        status,
                        tasks,
                        interaction.guild
                    )
                    for embed in status_embeds:
                        embed.title = f"{STATUS_EMOJIS[status]} Your {status.value} Tasks ({len(tasks)})"
                        all_embeds.append(embed)
            
            await interaction.response.send_message(
                embed=all_embeds[0],
                ephemeral=True
            )
            
            for embed in all_embeds[1:]:
                await interaction.followup.send(
                    embed=embed,
                    ephemeral=True
                )
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="update",
        description="Update task status"
    )
    @app_commands.describe(task_id="The ID of the task to update")
    async def update_task(self, interaction: discord.Interaction, task_id: int):
        try:
            task = await self.bot.task_manager.get_task(task_id)
            
            embed = discord.Embed(
                title="🔄 Update Task Status",
                description=f"Select the new status for Task #{task_id}:\n**{task.title}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Current Status", value=task.status)
            
            view = TaskStatusView(task_id, self.bot.task_manager)
            self.bot.add_view(view)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except TaskError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while updating the task.",
                ephemeral=True
            )

    @app_commands.command(
        name="delete",
        description="Delete a task"
    )
    @app_commands.describe(task_id="The ID of the task to delete")
    async def delete_task(self, interaction: discord.Interaction, task_id: int):
        try:
            task = await self.bot.task_manager.delete_task(task_id)
            
            embed = discord.Embed(
                title="🗑️ Task Deleted",
                description=f"Task #{task_id} has been deleted",
                color=discord.Color.red()
            )
            embed.add_field(name="Title", value=task.title)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.task_manager.update_board(interaction.guild)
            
        except TaskError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while deleting the task.",
                ephemeral=True
            )

    @app_commands.command(
        name="help",
        description="Show help message with available commands"
    )
    async def task_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 Task Manager Bot Commands",
            description="Here are all the available slash commands:",
            color=discord.Color.blue()
        )
        
        commands_info = {
            "/setup": "Create a dedicated channel for task tracking (Admin only)",
            "/create": "Create a new task with title, description, and optional due date",
            "/assign": "Assign users to a task using their @mentions",
            "/update": "Update task status using buttons",
            "/thread": "Create a discussion thread for a task",
            "/delete_thread": "Delete a task's discussion thread (thread creator only)",
            "/delete": "Delete a task",
            "/info": "Get detailed information about a task",
            "/list": "List all tasks assigned to you",
            "/help": "Show this help message"
        }
        
        for command, description in commands_info.items():
            embed.add_field(
                name=command,
                value=description,
                inline=False
            )
        
        embed.add_field(
            name="Task Statuses",
            value="\n".join([
                f"{STATUS_EMOJIS[status]} {status.value}" for status in TaskStatus
            ]),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Error Handlers
    @setup_tasks.error
    async def setup_tasks_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ An error occurred: {str(error)}",
                ephemeral=True
            )

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for application commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ Please wait {error.retry_after:.2f} seconds before using this command again.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
        else:
            print(f"Command error: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while processing the command.",
                ephemeral=True
            )

    @app_commands.command(
        name="create_meeting",
        description="Schedule a new meeting"
    )
    @app_commands.describe(
        title="Meeting title",
        description="Meeting description",
        start_time="Start time (format: DD-MM-YYYY HH:MM)",
        duration="Duration in minutes",
        participants="Meeting participants (mention them)",
        voice_channel="Voice channel for the meeting (optional)"
    )
    async def create_meeting(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        start_time: str,
        duration: int,
        participants: str,
        voice_channel: discord.VoiceChannel = None
    ):
        try:
            # Parse start time
            start_dt = datetime.strptime(start_time, "%d-%m-%Y %H:%M")
            start_dt = self.bot.meeting_manager.belgian_tz.localize(start_dt)
            
            # Parse participants
            participant_ids = []
            mentions = participants.split()
            
            for mention in mentions:
                stripped_mention = mention.strip('<@!>')
                
                if mention in ['@everyone', '@here']:
                    participant_ids = [m.id for m in interaction.guild.members if not m.bot]
                    break
                    
                if stripped_mention.isdigit():
                    user_id = int(stripped_mention)
                    member = interaction.guild.get_member(user_id)
                    if member and not member.bot:
                        participant_ids.append(user_id)
            
            # Create meeting
            meeting = Meeting(
                id=0,  # Will be set by storage
                title=title,
                description=description,
                start_time=start_dt,
                duration=duration,
                created_by=interaction.user.id,
                participants=participant_ids,
                channel_id=voice_channel.id if voice_channel else None,
                rsvp_status={}  # Initialize empty RSVP status
            )
            
            # Save meeting
            self.bot.meeting_store.add_meeting(meeting)
            
            # Create response embed
            embed = discord.Embed(
                title="✅ Meeting Scheduled",
                description=f"Meeting has been scheduled successfully",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Title", value=meeting.title, inline=False)
            embed.add_field(name="Description", value=meeting.description, inline=False)
            embed.add_field(
                name="📅 Date & Time", 
                value=meeting.start_time.strftime("%Y-%m-%d %H:%M"),
                inline=True
            )
            embed.add_field(name="⏱️ Duration", value=f"{meeting.duration} minutes", inline=True)
            
            if voice_channel:
                embed.add_field(
                    name="🔊 Voice Channel",
                    value=voice_channel.mention,
                    inline=False
                )
            
            if participant_ids:
                embed.add_field(
                    name="👥 Participants",
                    value=", ".join([f"<@{uid}>" for uid in participant_ids]),
                    inline=False
                )
            else:
                embed.add_field(
                    name="👥 Participants",
                    value="@everyone",
                    inline=False
                )
            
            # First send the response to the interaction
            await interaction.response.send_message(embed=embed)
            
            # Then update the board
            try:
                await self.bot.meeting_manager.update_board(interaction.guild)
            except Exception as e:
                print(f"Error updating board: {e}")
                # Send a follow-up message about the board update error
                await interaction.followup.send(
                    "Meeting was created, but there was an error updating the board. An admin may need to check the permissions.",
                    ephemeral=True
                )
                
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Invalid date/time format. Please use DD-MM-YYYY HH:MM",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )