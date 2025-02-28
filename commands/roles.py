import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# Create database and table if they don't exist
def create_tables():
    conn = sqlite3.connect('buttons.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS message_data (
        message_id TEXT PRIMARY KEY,
        channel_id INTEGER,
        guild_id INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS button_data (
        message_id TEXT,
        button_name TEXT,
        button_id TEXT,
        role_id INTEGER,
        FOREIGN KEY(message_id) REFERENCES message_data(message_id)
    )
    ''')
    conn.commit()
    conn.close()
    print("Database and tables created (if not exist).")

# Save message data (message_id, channel_id, guild_id) into the database
def save_message_data(message_id, channel_id, guild_id, buttons_data):
    try:
        conn = sqlite3.connect('buttons.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO message_data (message_id, channel_id, guild_id) VALUES (?, ?, ?)', 
                       (message_id, channel_id, guild_id))
        for button_name, button_id, role_id in buttons_data:
            cursor.execute('INSERT INTO button_data (message_id, button_name, button_id, role_id) VALUES (?, ?, ?, ?)',
                           (message_id, button_name, button_id, role_id))
        conn.commit()
        conn.close()
        print(f"Successfully saved message data: message_id={message_id}, channel_id={channel_id}, guild_id={guild_id}.")
    except Exception as e:
        print(f"Error saving message data: {e}")

# Remove existing message data from the database
def remove_existing_message_data():
    try:
        conn = sqlite3.connect('buttons.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM message_data')
        cursor.execute('DELETE FROM button_data')
        conn.commit()
        conn.close()
        print("Successfully removed previous message data from the database.")
    except Exception as e:
        print(f"Error removing message data: {e}")

# Get message data (message_id, channel_id, guild_id) and button data from the database
def get_message_data():
    try:
        conn = sqlite3.connect('buttons.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM message_data ORDER BY rowid DESC LIMIT 1')
        message_data = cursor.fetchone()

        if message_data:
            cursor.execute('SELECT button_name, button_id, role_id FROM button_data WHERE message_id = ?', (message_data[0],))
            buttons_data = cursor.fetchall()
            conn.close()
            return message_data, buttons_data
        else:
            conn.close()
            return None, None
    except Exception as e:
        print(f"Error fetching message data: {e}")
        return None, None

# Remove invalid message data (if channel is not found, etc.)
def remove_invalid_message_data():
    try:
        conn = sqlite3.connect('buttons.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM message_data')
        cursor.execute('DELETE FROM button_data')
        conn.commit()
        conn.close()
        print("Removed invalid message data from the database.")
    except Exception as e:
        print(f"Error removing invalid message data: {e}")

# Role Buttons View
class RoleButtons(discord.ui.View):
    def __init__(self, buttons_data=None):
        super().__init__(timeout=None)  # The message stays indefinitely
        if buttons_data:
            self.generate_buttons(buttons_data)

    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        guild = interaction.guild
        if guild is None:
            print("Guild not found.")
            return

        role = guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message("Role not found.", ephemeral=True)
            print(f"Role with ID {role_id} not found in guild {guild.name}.")
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed {role.name} role!", ephemeral=True)
            print(f"Removed {role.name} role for {interaction.user.name}.")
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added {role.name} role!", ephemeral=True)
            print(f"Added {role.name} role for {interaction.user.name}.")

    def generate_buttons(self, buttons_data):
        print("Generating buttons.")
        for button_name, button_id, role_id in buttons_data:
            button = discord.ui.Button(label=button_name, custom_id=button_id, style=discord.ButtonStyle.primary)
            button.callback = lambda interaction, role_id=role_id: self.toggle_role(interaction, role_id)
            self.add_item(button)

# Role Command Cog
class RoleCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        create_tables()  # Make sure the database and table are created when the bot starts
        print("RoleCommand cog initialized.")

    @app_commands.command(name="roles", description="Create a message with buttons to receive roles.")
    @app_commands.default_permissions(administrator=True)
    async def roles(self, interaction: discord.Interaction):
        # Remove any existing data before saving new data
        remove_existing_message_data()

        embed = discord.Embed(
            title="Click to receive the role for the Chapter specified!",
            description="Click the buttons below to toggle the roles:",
            color=discord.Color.blue()
        )
        print(f"Sending role selection message in channel {interaction.channel.name}.")

        # Define buttons and their roles
        buttons_data = [
            ("Chapter 1", "role_ch1", 1345154403216392293),
            ("Chapter 2", "role_ch2", 1345154701423018064),
            ("Chapter 3", "role_ch3", 1345154689729040536),
            ("Chapter 4", "role_ch4", 1345154697329119234)
        ]

        # Send message with role buttons
        message = await interaction.channel.send(embed=embed, view=RoleButtons(buttons_data))

        # Save message, channel, guild, and button data to the database
        save_message_data(message.id, message.channel.id, interaction.guild.id, buttons_data)

        await interaction.response.send_message("Role selection message created!", ephemeral=True)

    # Restore roles (called automatically when the bot starts)
    async def restore_roles(self):
        print("Attempting to restore roles...")
        message_data, buttons_data = get_message_data()
        if message_data is None or buttons_data is None:
            print("No previous message data found to restore.")
            return

        message_id, channel_id, guild_id = message_data
        try:
            # Fetch the saved guild
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                print(f"Guild with ID {guild_id} not found.")
                self.remove_invalid_message_data()
                return

            # Fetch the saved channel
            channel = guild.get_channel(channel_id)
            if channel is None:
                print(f"Channel with ID {channel_id} not found in guild {guild.name}.")
                self.remove_invalid_message_data()
                return

            # Fetch the saved message and re-add the buttons
            message = await channel.fetch_message(message_id)
            view = RoleButtons(buttons_data)
            await message.edit(view=view)
            print(f"Restored the role selection message with buttons in channel {channel.name}!")

        except discord.NotFound:
            print("The saved message could not be found.")
            self.remove_invalid_message_data()

        except discord.Forbidden:
            print("The bot does not have permission to access the channel.")
        
        except discord.HTTPException as e:
            print(f"An HTTP error occurred while restoring the roles: {e}")

    # Ensure roles are restored when the bot starts up
    @commands.Cog.listener()
    async def on_ready(self):
        await self.restore_roles()

# Set up the cog
async def setup(bot):
    await bot.add_cog(RoleCommand(bot))
    print("RoleCommand cog setup complete.")
