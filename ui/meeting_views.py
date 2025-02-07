import discord
from discord.ui import View, Button, button

class RSVPView(View):
    def __init__(self, meeting_manager, meeting_id: int):
        super().__init__(timeout=None)
        self.meeting_manager = meeting_manager
        self.meeting_id = meeting_id
        
    @button(label="Yes", style=discord.ButtonStyle.green, emoji="✅", custom_id=f"rsvp_yes")
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_rsvp(interaction, "yes")
        
    @button(label="Maybe", style=discord.ButtonStyle.gray, emoji="❔", custom_id=f"rsvp_maybe")
    async def maybe_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_rsvp(interaction, "maybe")
        
    @button(label="No", style=discord.ButtonStyle.red, emoji="❌", custom_id=f"rsvp_no")
    async def no_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_rsvp(interaction, "no")
        
    async def handle_rsvp(self, interaction: discord.Interaction, response: str):
        try:
            await self.meeting_manager.update_rsvp(
                self.meeting_id,
                interaction.user.id,
                response
            )
            
            await interaction.response.send_message(
                f"Your response ({response}) has been recorded!",
                ephemeral=True
            )
            
            # Update the meeting board to reflect the new RSVP
            await self.meeting_manager.update_board(interaction.guild)
            
        except Exception as e:
            await interaction.response.send_message(
                f"Failed to record your response: {str(e)}",
                ephemeral=True
            )