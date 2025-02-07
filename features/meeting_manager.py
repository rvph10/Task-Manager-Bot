# === File: features/meeting_manager.py ===
from datetime import datetime, timedelta
import pytz
from discord.ext import tasks, commands
import discord
from core.persistence import MeetingStore
from core.models import Meeting
from ui.meeting_views import RSVPView

class MeetingManager:
    def __init__(self, bot: commands.Bot, storage: MeetingStore):
        self.bot = bot
        self.storage = storage
        self.belgian_tz = pytz.timezone('Europe/Brussels')
        self.check_meetings.start()
        
    def get_belgian_time(self) -> datetime:
        """Get current time in Belgian timezone"""
        return datetime.now(self.belgian_tz)
        
    @tasks.loop(minutes=1)
    async def check_meetings(self):
        """Check for upcoming meetings and send notifications"""
        current_time = self.get_belgian_time()
        
        for meeting in self.storage.meetings.values():
            # Check for 30-minute reminder
            time_until_start = meeting.start_time - current_time
            if not meeting.reminder_sent and timedelta(minutes=30) >= time_until_start > timedelta(minutes=29):
                await self.send_meeting_reminder(meeting)
                meeting.reminder_sent = True
                self.storage._save()
            elif time_until_start <= timedelta(minutes=-10):
                await self.check_attendance(meeting)
                
    async def send_meeting_reminder(self, meeting: Meeting):
        """Send reminder to meeting participants"""
        channel = self.bot.get_channel(meeting.channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="📅 Upcoming Meeting Reminder",
            description=f"Meeting '{meeting.title}' starts in 30 minutes!",
            color=discord.Color.blue()
        )
        
        participants = [f"<@{user_id}>" for user_id in meeting.participants]
        embed.add_field(
            name="Participants",
            value=", ".join(participants) if participants else "@everyone",
            inline=False
        )
        
        await channel.send(
            " ".join(participants) if participants else "@everyone",
            embed=embed
        )

    async def setup_meeting_channel(self, guild: discord.Guild) -> discord.TextChannel:
        """Set up the meeting dashboard channel"""
        # Delete existing channel if it exists
        if self.storage.meeting_channel_id:
            old_channel = guild.get_channel(self.storage.meeting_channel_id)
            if old_channel:
                try:
                    await old_channel.delete()
                except discord.errors.Forbidden:
                    raise discord.errors.Forbidden("Missing permissions to delete the old meeting channel")
        
        # Create new channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                add_reactions=False,
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False
            ),
            guild.me: discord.PermissionOverwrite(
                send_messages=True,
                manage_messages=True,
                manage_channels=True,
                add_reactions=True
            )
        }
        
        channel = await guild.create_text_channel('meeting-dashboard', overwrites=overwrites)
        self.storage.set_channel_id(channel.id)
        
        return channel
        
    async def check_attendance(self, meeting: Meeting):
        """Check if all participants are present in the voice channel"""
        # Skip if reminder was already sent
        if meeting.reminder_sent:
            return

        channel = self.bot.get_channel(meeting.channel_id)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            return
            
        # Get members currently in the voice channel
        present_members = {member.id for member in channel.members}
        
        # Get members who were supposed to attend
        attend_members = [uid for uid, response in meeting.rsvp_status.items() if response == 'yes']
        
        # Check who's missing
        missing_members = set(attend_members) - present_members
        
        if missing_members:
            try:
                # Create invite link
                ttl = (meeting.duration - 10) * 60
                meeting_channel = self.bot.get_channel(meeting.channel_id)
                if meeting_channel:
                    channel_invite = await meeting_channel.create_invite(max_age=ttl)
                    
                    # Send notifications to missing members
                    for user_id in missing_members:
                        user = self.bot.get_user(user_id)
                        if user:
                            try:
                                await user.send(
                                    f"🚨 You're late to the meeting {meeting.title} • {meeting.description[:20]}! "
                                    "\nPlease join as soon as possible. 🚨"
                                    "\nIf you're unable to attend, please let the organizer know."
                                    f"\nOr join [HERE]({channel_invite}) to confirm your attendance."
                                    "\nThank you!"
                                )
                            except discord.Forbidden:
                                # Can't DM user, continue with next user
                                continue
                    
                    # Update reminder flag and save
                    meeting.reminder_sent = True
                    self.storage._save()
                    
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"Error sending attendance notifications: {e}")


    async def update_board(self, guild: discord.Guild) -> None:
        """Update the meetings board display"""
        if not self.storage.meeting_channel_id:
            return
            
        channel = guild.get_channel(self.storage.meeting_channel_id)
        if not channel:
            return
            
        # Clear existing messages
        try:
            await channel.purge(limit=100)
        except discord.errors.Forbidden:
            print("Missing permissions to purge messages")
            return
            
        # Create header
        header_embed = discord.Embed(
            title="📅 Meetings Dashboard",
            description="Upcoming meetings and schedules",
            color=discord.Color.blue()
        )
        await channel.send(embed=header_embed)
        
        # Group meetings by date
        current_time = self.get_belgian_time()
        upcoming_meetings = {
            k: v for k, v in self.storage.meetings.items()
            if v.start_time >= current_time
        }
        
        if not upcoming_meetings:
            empty_embed = discord.Embed(
                description="*No upcoming meetings scheduled*",
                color=discord.Color.light_grey()
            )
            await channel.send(embed=empty_embed)
            return
            
        # Sort meetings by start time
        sorted_meetings = sorted(
            upcoming_meetings.values(),
            key=lambda m: m.start_time
        )
        
        # Create meeting embeds
        for meeting in sorted_meetings:
            # Calculate time until meeting
            time_until = meeting.start_time - current_time
            hours_until = time_until.total_seconds() / 3600
            
            # Determine embed color based on time until meeting
            if hours_until <= 1:  # Less than 1 hour
                color = discord.Color.red()
            elif hours_until <= 24:  # Less than 24 hours
                color = discord.Color.orange()
            else:
                color = discord.Color.blue()
                
            embed = discord.Embed(
                title=f"📅 {meeting.title}",
                description=meeting.description,
                color=color
            )

            # Add meeting details
            embed.add_field(
                name="🕒 Date & Time",
                value=meeting.start_time.strftime("%Y-%m-%d %H:%M"),
                inline=True
            )
            embed.add_field(
                name="⏱️ Duration",
                value=f"{meeting.duration} minutes",
                inline=True
            )
            
            # Add voice channel information if available
            if meeting.channel_id:
                voice_channel = guild.get_channel(meeting.channel_id)
                if voice_channel:
                    embed.add_field(
                        name="🔊 Voice Channel",
                        value=voice_channel.mention,
                        inline=True
                    )
                    
                    # Add current participants if meeting is ongoing
                    if -30 < time_until.total_seconds() / 60 < meeting.duration:
                        current_participants = len([member for member in voice_channel.members if not member.bot])
                        embed.add_field(
                            name="👥 Current Participants",
                            value=f"{current_participants} member(s) in channel",
                            inline=True
                        )
            
            # Add separator for readability
            embed.add_field(name="​", value="​", inline=False)
            
            # Add RSVP summary
            yes_count, no_count, maybe_count, pending_count = self.get_rsvp_summary(meeting)
            
            rsvp_summary = (
                f"✅ Going: {yes_count}\n"
                f"❔ Maybe: {maybe_count}\n"
                f"❌ Not Going: {no_count}\n"
                f"⏳ Awaiting Response: {pending_count}"
            )
            
            embed.add_field(
                name="📊 RSVP Status",
                value=rsvp_summary,
                inline=False
            )
            
            # Add detailed RSVP lists
            if meeting.rsvp_status:
                # Going
                going_users = [uid for uid, resp in meeting.rsvp_status.items() if resp == 'yes']
                if going_users:
                    embed.add_field(
                        name="✅ Confirmed Attendees",
                        value=", ".join(f"<@{uid}>" for uid in going_users),
                        inline=False
                    )
                
                # Maybe
                maybe_users = [uid for uid, resp in meeting.rsvp_status.items() if resp == 'maybe']
                if maybe_users:
                    embed.add_field(
                        name="❔ Tentative Attendees",
                        value=", ".join(f"<@{uid}>" for uid in maybe_users),
                        inline=False
                    )
                
                # Not Going
                not_going_users = [uid for uid, resp in meeting.rsvp_status.items() if resp == 'no']
                if not_going_users:
                    embed.add_field(
                        name="❌ Not Attending",
                        value=", ".join(f"<@{uid}>" for uid in not_going_users),
                        inline=False
                    )
            
            # Add pending responses
            pending_users = [uid for uid in meeting.participants if uid not in meeting.rsvp_status]
            if pending_users:
                embed.add_field(
                    name="⏳ Awaiting Response From",
                    value=", ".join(f"<@{uid}>" for uid in pending_users),
                    inline=False
                )
            
            # Add countdown
            if hours_until < 1:
                countdown = f"⏰ Starting in {int(time_until.total_seconds() / 60)} minutes"
            elif hours_until < 24:
                countdown = f"⏰ Starting in {int(hours_until)} hours"
            else:
                days = int(hours_until / 24)
                countdown = f"⏰ Starting in {days} day{'s' if days > 1 else ''}"
                
            embed.add_field(
                name="Status",
                value=countdown,
                inline=True
            )
            
            # Add meeting creator
            creator = guild.get_member(meeting.created_by)
            if creator:
                embed.set_footer(
                    text=f"Created by {creator.display_name}",
                    icon_url=creator.display_avatar.url
                )
            
            # Send embed with RSVP buttons
            message = await channel.send(embed=embed)
            
            # Only add RSVP buttons if the meeting hasn't started yet
            if time_until.total_seconds() > 0:
                view = RSVPView(self, meeting.id)
                self.bot.add_view(view)
                await message.edit(view=view)

    async def update_rsvp(self, meeting_id: int, user_id: int, response: str) -> None:
        """Update a user's RSVP status for a meeting"""
        meeting = self.storage.meetings.get(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
            
        if user_id not in meeting.participants:
            raise ValueError("You are not invited to this meeting")
            
        if response not in ['yes', 'no', 'maybe']:
            raise ValueError("Invalid RSVP response")
            
        meeting.rsvp_status[user_id] = response
        self.storage._save()

    def get_rsvp_summary(self, meeting) -> tuple:
        """Get RSVP counts for a meeting"""
        yes_count = sum(1 for status in meeting.rsvp_status.values() if status == 'yes')
        no_count = sum(1 for status in meeting.rsvp_status.values() if status == 'no')
        maybe_count = sum(1 for status in meeting.rsvp_status.values() if status == 'maybe')
        pending_count = len(meeting.participants) - len(meeting.rsvp_status)
        
        return yes_count, no_count, maybe_count, pending_count
    
    @check_meetings.before_loop
    async def before_check_meetings(self):
        """Wait until the bot is ready before starting the meeting check loop"""
        await self.bot.wait_until_ready()