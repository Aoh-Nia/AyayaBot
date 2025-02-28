import discord
from discord.ext import commands

class Trans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="lgbt", description="Support LGBTQIA+ people!")
    async def trans(self, interaction: discord.Interaction):
        await interaction.response.send_message('<:AYAYA:928769603717460018> Ayaya Supports LGBTQIA+ People! 🌈')

# Async setup function to add the cog
async def setup(bot):
    await bot.add_cog(Trans(bot))
