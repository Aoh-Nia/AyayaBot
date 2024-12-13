import discord
from discord.ext import commands
from discord import app_commands
import requests

class PB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pb", description="Get a user's PB for a specific category.")
    @app_commands.describe(user="The user to check PB for.", category="The category to look up.")
    async def pb(self, interaction: discord.Interaction, user: discord.Member, category: str):
        # Define the speedrun.com URL for the leaderboard query
        speedrun_api_url = "https://www.speedrun.com/api/v1/"
        
        # Get user data from Speedrun.com API (replace with actual user ID or username)
        username = user.name
        response = requests.get(f"{speedrun_api_url}users?lookup={username}")
        
        if response.status_code != 200:
            await interaction.response.send_message("User not found on Speedrun.com.", ephemeral=True)
            return
        
        user_data = response.json()
        if len(user_data['data']) == 0:
            await interaction.response.send_message(f"No data found for user {user.mention}.", ephemeral=True)
            return
        
        user_id = user_data['data'][0]['id']
        
        # Get leaderboard data for the user based on category
        category_parts = category.split(" | ")
        if len(category_parts) != 4:
            await interaction.response.send_message(
                "Category format is invalid. Expected: `Chapter | Version | Type | Subcategory`.", ephemeral=True
            )
            return

        chapter, version, run_type, subcategory = category_parts
        run_category_id = f"{chapter}_{version}_{run_type}_{subcategory}"

        # Fetch the category's leaderboard
        leaderboard_url = f"{speedrun_api_url}runs?user={user_id}&max=5&orderby=placement&embed=category,game"
        leaderboard_response = requests.get(leaderboard_url)

        if leaderboard_response.status_code != 200:
            await interaction.response.send_message("Error fetching leaderboard data.", ephemeral=True)
            return
        
        leaderboard_data = leaderboard_response.json()

        # Find the PB for the given category
        for run in leaderboard_data['data']:
            if run['category']['name'] == run_category_id:
                time = run['times']['primary_t']
                link = run['weblink']
                time_formatted = self.format_time(time)
                await interaction.response.send_message(
                    f"{user.mention} has the following PB:\n"
                    f"**{chapter} | {version} | {run_type} | {subcategory}:** {time_formatted} [SEE HERE!]({link})"
                )
                return

        # If no run was found
        await interaction.response.send_message(
            f"{user.mention} has the following PB:\n"
            f"**{chapter} | {version} | {run_type} | {subcategory}:** No run was submitted."
        )

    def format_time(self, time_in_seconds):
        """Convert time from seconds (Speedrun.com format) to HH:MM:SS.sss"""
        if time_in_seconds is None:
            return "No time"
        minutes, seconds = divmod(time_in_seconds, 60)
        seconds, milliseconds = divmod(seconds, 1)
        return f"{int(minutes):02}:{int(seconds):02}.{int(milliseconds*1000):03}"

async def setup(bot):
    await bot.add_cog(PB(bot))
