import discord
from discord.ext import commands
import sqlite3
import traceback

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Use separate database connections for each game
        self.guess_time_db_connection = sqlite3.connect("guess_time.db")  
        self.trivia_db_connection = sqlite3.connect("trivia.db")  

    @discord.app_commands.command(name="leaderboard", description="Display the leaderboard for a specific game.")
    @discord.app_commands.describe(game="Specify the game: 'trivia' or 'guess_time'")
    async def leaderboard(self, interaction: discord.Interaction, game: str):
        try:
            # Determine which leaderboard to query based on the 'game' argument
            if game not in ["trivia", "guess_time"]:
                await interaction.response.send_message("Invalid game type! Use 'trivia' or 'guess_time'.")
                return

            # Choose the appropriate database connection and table based on the game type
            if game == "trivia":
                db_connection = self.trivia_db_connection
                table_name = "scores"
                game_name = "Trivia"
            else:
                db_connection = self.guess_time_db_connection
                table_name = "scores"
                game_name = "Guess Time"

            # Query the leaderboard from the respective table
            with db_connection:
                cursor = db_connection.execute(f"""
                    SELECT username, score FROM {table_name} ORDER BY score DESC LIMIT 10
                """)
                rows = cursor.fetchall()

            if not rows:
                await interaction.response.send_message(f"No scores yet for {game_name}! Be the first to play!")
                return

            # Prepare the leaderboard message
            leaderboard = f"**🏆 {game_name} Leaderboard 🏆**\n"
            for rank, (username, score) in enumerate(rows, start=1):
                leaderboard += f"{rank}. **{username}** - {score} points\n"

            # Send the leaderboard to the user
            await interaction.response.send_message(leaderboard)

        except Exception as e:
            # Log the error and send a message to the user
            error_message = f"An error occurred while fetching the leaderboard: {str(e)}"
            await interaction.response.send_message(error_message)
            print(f"Error occurred: {traceback.format_exc()}")

# Async setup function to add the cog
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))