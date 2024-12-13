import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from flask import Flask
from threading import Thread

# Initialize Flask app to keep the bot alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Define your bot's intents and command prefix
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Set the bot's status to Idle with competing activity
    await bot.change_presence(
        status=discord.Status.idle,  # Idle status
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="Poppy Playtime",
            url="https://www.speedrun.com/poppy_playtime"  # The URL to link when clicked
        ),
    )
    print(f"We have logged in as {bot.user}")
    
    # Sync slash commands globally after bot is ready
    await bot.tree.sync()

# Load the .env file and get the token
load_dotenv()  
token = os.getenv("DISCORD_TOKEN")

# Start the keep_alive function to ensure the bot stays active on platforms like Replit
keep_alive()

# Run the bot with the token
bot.run(token)
