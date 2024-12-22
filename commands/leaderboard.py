import discord
from discord.ext import commands
import sqlite3

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_connection = sqlite3.connect("guess_time.db")

    @discord.app_commands.command(name="leaderboard", description="Display the leaderboard for Guess the Time.")
    async def leaderboard(self, interaction: discord.Interaction):
        with self.db_connection:
            cursor = self.db_connection.execute("""
                SELECT username, score FROM scores ORDER BY score DESC LIMIT 10
            """)
            rows = cursor.fetchall()

        if not rows:
            await interaction.response.send_message("No scores yet! Be the first to play!")
            return

        leaderboard = "**🏆 Leaderboard 🏆**\n"
        for rank, (username, score) in enumerate(rows, start=1):
            leaderboard += f"{rank}. **{username}** - {score} points\n"

        await interaction.response.send_message(leaderboard)

# Async setup function to add the cog
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
