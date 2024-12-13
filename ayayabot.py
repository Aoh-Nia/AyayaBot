import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Define intents and bot initialization
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Set the bot's status to Competing
    await bot.change_presence(
        status=discord.Status.idle,  # Idle status
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="Poppy Playtime",
            url="https://www.speedrun.com/poppy_playtime"  # The URL to link when clicked
        ),
    )
    print(f"We have logged in as {bot.user}")
    try:
        # Sync slash commands with Discord
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Load cogs from the "commands" folder
async def load_cogs():
    print("Loading cogs...")
    for filename in os.listdir('./commands'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(f"Loaded cog: {filename}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")

# Main function
async def main():
    async with bot:
        await load_cogs()
        await bot.start(token)

if __name__ == "__main__":
    load_dotenv()  # Load .env file for token
    token = os.getenv("DISCORD_TOKEN")
    import asyncio
    asyncio.run(main())
