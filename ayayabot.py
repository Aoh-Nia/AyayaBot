import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Define your bot's intents and command prefix
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Set the bot's status to Idle
    await bot.change_presence(
        status=discord.Status.idle,  # Idle status
        activity=discord.Game("Poppy Playtime")  # Playing "Poppy Playtime"
    )
    print(f"We have logged in as {bot.user}")

@bot.event
async def on_message(message):
    # Check if the bot is mentioned in the message
    if bot.user.mentioned_in(message):
        await message.channel.send("meow! :3")
    
    # Process commands (important to include this line for commands to work)
    await bot.process_commands(message)

load_dotenv()  # This loads the .env file
token = os.getenv("DISCORD_TOKEN")
