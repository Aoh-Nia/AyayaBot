from dotenv import load_dotenv
import os

load_dotenv()  # This loads the .env file
token = os.getenv("DISCORD_TOKEN")
