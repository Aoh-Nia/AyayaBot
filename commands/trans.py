import discord
from discord.ext import commands
from discord import app_commands

class Trans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="trans", description="I wonder what this does...")
    async def trans(self, interaction: discord.Interaction):
        """I wonder what this does..."""
        await interaction.response.send_message('<:AYAYA:928769603717460018> Ayaya Supports Transgender People! 🏳️‍⚧️')

def setup(bot):
    bot.add_cog(Trans(bot))
