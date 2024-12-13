import discord
from discord.ext import commands

class Trans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="trans", description="Support transgender people!")
    async def trans(self, interaction: discord.Interaction):
        """Slash command to send a supportive message."""
        await interaction.response.send_message('<:AYAYA:928769603717460018> Ayaya Supports Transgender People! 🌈')

# Async setup function to add the cog
async def setup(bot):
    await bot.add_cog(Trans(bot))
