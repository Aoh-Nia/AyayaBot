import discord
from discord.ext import commands
from discord import app_commands
import requests
import sqlite3
import os

class Link(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "links.db"  # Name of the database file
        self._setup_database()

    def _setup_database(self):
        """Creates the database and table if they don't exist."""
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_links (
                    discord_id TEXT PRIMARY KEY,
                    discord_name TEXT,
                    speedrun_username TEXT,
                    speedrun_id TEXT,
                    image_url TEXT
                )
            """)
            conn.commit()
            conn.close()

    def _save_link(self, discord_id, discord_name, speedrun_username, speedrun_id, image_url):
        """Saves the link and image URL in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_links (discord_id, discord_name, speedrun_username, speedrun_id, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (discord_id, discord_name, speedrun_username, speedrun_id, image_url))
        conn.commit()
        conn.close()

    def _get_link_by_discord_id(self, discord_id):
        """Queries the database to get the link by Discord ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_links WHERE discord_id = ?", (discord_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def _delete_link(self, discord_id):
        """Deletes the link from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_links WHERE discord_id = ?", (discord_id,))
        conn.commit()
        conn.close()

    @app_commands.command(name="link", description="Link your Discord account to your Speedrun.com account.")
    @app_commands.describe(user="The Speedrun.com username you want to link with your Discord account.")
    async def link(self, interaction: discord.Interaction, user: str = None):
        if user is None:
            # If no username is provided, act as /viewlink
            existing_link = self._get_link_by_discord_id(interaction.user.id)
            if existing_link:
                speedrun_username = existing_link[2]
                image_url = existing_link[4]  # Retrieve image URL from DB
                embed = discord.Embed(
                    title="Linked Account",
                    description=f"Your Discord account is linked with [**{speedrun_username}**](<https://speedrun.com/users/{speedrun_username}>) on Speedrun.com.",
                    color=discord.Color.green()
                )
                if image_url:
                    embed.set_thumbnail(url=image_url)  # Set the image as the embed thumbnail
                # Add a button to unlink and make it ephemeral
                await interaction.response.send_message(
                    embed=embed,
                    view=UnlinkButton(self, interaction.user.id),
                    ephemeral=True  # This ensures only the user who executed the command can see the embed
                )
            else:
                await interaction.response.send_message(
                    "You have no linked account right now.",
                    ephemeral=True
                )
        else:
            try:
                # Check if the user is already linked
                existing_link = self._get_link_by_discord_id(interaction.user.id)
                if existing_link:
                    await interaction.response.send_message(
                        f"You're already linked to the Speedrun.com account '{existing_link[2]}'.",
                        ephemeral=True
                    )
                    return

                # Step 1: Get Speedrun.com user ID
                url = f"https://www.speedrun.com/api/v1/users/{user}"
                print(f"Requesting {url}")
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        user_id = data['data']['id']
                        speedrun_username = data['data']['names']['international']
                        image_url = data['data']['assets']['image']['uri']  # Fetch image URL
                    else:
                        await interaction.response.send_message(f"Couldn't find user '{user}' on Speedrun.com.", ephemeral=True)
                        return
                elif response.status_code == 404:
                    await interaction.response.send_message(f"Couldn't find user '{user}' on Speedrun.com. *[404]*", ephemeral=True)
                    return
                else:
                    await interaction.response.send_message(f"Error trying to search for user '{user}'. Please report this to the bot admin <@780441054704042004>: {response.status_code}", ephemeral=True)
                    return

                # Step 2: Get social connections
                url = f"https://www.speedrun.com/api/v2/GetUserPopoverData?userId={user_id}"
                print(f"Requesting {url}")
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    discord_username = next(
                        (item['value'] for item in data['userSocialConnectionList'] if item['networkId'] == 5),
                        None
                    )
                    # Check if Discord is verified
                    verified = next(
                        (item['verified'] for item in data['userSocialConnectionList'] if item['networkId'] == 5),
                        None
                    )

                    if discord_username:
                        if verified:
                            if discord_username.lower() == interaction.user.name.lower():
                                # Save to database along with image URL
                                self._save_link(interaction.user.id, interaction.user.name, speedrun_username, user_id, image_url)
                                await interaction.response.send_message(
                                    f"Your Discord account '{discord_username}' has been successfully linked to your Speedrun.com account '{speedrun_username}'.",
                                    ephemeral=True
                                )
                            else:
                                await interaction.response.send_message(
                                    f"The Speedrun.com account '{speedrun_username}' is already linked to the Discord account: '{discord_username}'.",
                                    ephemeral=True
                                )
                        else:
                            await interaction.response.send_message(
                                f"The Discord account linked to '{speedrun_username}' is not verified.",
                                ephemeral=True
                            )
                    else:
                        await interaction.response.send_message(f"Couldn't find a Discord account linked to your Speedrun.com account.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"An error occurred while searching for social connections, please report this to the bot admin <@780441054704042004>: {response.status_code}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"An error occurred, please report this to the bot admin <@780441054704042004>: {str(e)}", ephemeral=True)
                print(f"Unexpected error: {e}")


class UnlinkButton(discord.ui.View):
    def __init__(self, cog, discord_id):
        super().__init__()
        self.cog = cog
        self.discord_id = discord_id

    @discord.ui.button(label="Unlink Account", style=discord.ButtonStyle.red)
    async def unlink(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog._delete_link(self.discord_id)
        await interaction.response.send_message("Your account has been successfully unlinked.", ephemeral=True)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Link(bot))
