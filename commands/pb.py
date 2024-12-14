"""import discord
from discord.ext import commands
from discord import app_commands
import requests

class PB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define the /pb command
    @app_commands.command(name="pb", description="Obtener el PB de un usuario para un capítulo y categoría de Poppy Playtime.")
    @app_commands.describe(user="El usuario de Speedrun.com para verificar el PB.", chapter="El capítulo de Poppy Playtime.", category="La categoría del speedrun.")
    async def pb(self, interaction: discord.Interaction, user: str, chapter: str, category: str):
        await interaction.response.defer()  # Acknowledge the interaction and delay the response

        # Fetch PB data in a separate thread to prevent blocking
        data = await asyncio.to_thread(self.get_pb_data, user, chapter, category)
        
        if data:
            await interaction.followup.send(data)
        else:
            await interaction.followup.send("Hubo un problema al obtener los datos.")

    def get_pb_data(self, user, chapter_name, category_name):
        # Define the Speedrun API URL
        speedrun_api_url = "https://www.speedrun.com/api/v1/"

        # Dictionary of known Poppy Playtime chapters and their Speedrun.com IDs
        chapter_ids = {
            "chapter_1": "ppt_c1",
            "chapter_2": "ppt_c2",
            "chapter_3": "ppt_c3",
        }

        # Dictionary of categories for each chapter
        chapter_categories = {
            "chapter_1": ["Any%", "All Minigames", "100%", "All Achievements"],
            "chapter_2": ["Any%", "All Minigames", "100%", "No Major Glitches"],
            "chapter_3": ["Any%", "All Minigames", "100%"]
        }

        logging.debug(f"Received request for user {user} in chapter {chapter_name} and category {category_name}.")

        # Check if the chapter exists in the dictionary
        chapter_id = chapter_ids.get(chapter_name.lower())
        if not chapter_id:
            logging.error(f"Chapter `{chapter_name}` not found.")
            return f"Capítulo `{chapter_name}` no encontrado. Los capítulos disponibles son: {', '.join(chapter_ids.keys())}."

        # Get categories for the selected chapter
        available_categories = chapter_categories.get(chapter_name.lower())
        if not available_categories or category_name not in available_categories:
            logging.error(f"Category `{category_name}` not available for chapter `{chapter_name}`.")
            return f"Categoría `{category_name}` no disponible para el capítulo `{chapter_name}`. Las categorías disponibles son: {', '.join(available_categories)}."

        # Get user data from Speedrun.com API
        logging.debug(f"Fetching user data for {user} from Speedrun.com.")
        response = requests.get(f"{speedrun_api_url}users?lookup={user}")
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch user data for {user}. Status code: {response.status_code}")
            return f"Usuario `{user}` no encontrado en Speedrun.com."
        
        user_data = response.json()
        if len(user_data['data']) == 0:
            logging.warning(f"No data found for user {user}.")
            return f"No se encontraron datos para el usuario `{user}`."
        
        user_id = user_data['data'][0]['id']

        # Get the run data for the selected chapter and category
        logging.debug(f"Fetching run data for user {user_id} in chapter {chapter_name} and category {category_name}.")
        runs_response = requests.get(f"{speedrun_api_url}runs", params={
            "user": user_id,
            "game": chapter_id,
            "category": category_name
        })
        
        if runs_response.status_code != 200:
            logging.error(f"Error fetching run data. Status code: {runs_response.status_code}")
            return f"Error al obtener datos del tiempo para el usuario `{user}` en la categoría `{category_name}`."

        runs_data = runs_response.json()
        if not runs_data['data']:
            logging.warning(f"No runs found for user {user} in category {category_name}.")
            return f"No hay tiempo registrado para `{user}` en la categoría `{category_name}`."

        # Get the best time from the user's runs
        best_run = runs_data['data'][0]  # Taking the first run (best time)
        time = best_run['times']['primary_t']
        formatted_time = self.format_time(time)

        # Construct the message
        return (f"**{user}** en `{chapter_name.capitalize()}` - `{category_name}`:\n"
                f"Tiempo: {formatted_time} [Ver aquí!](https://www.speedrun.com/{chapter_id}/run/{best_run['id']})")

    def format_time(self, time):
        # Format time from seconds to the typical minutes:seconds.milliseconds format
        minutes = int(time // 60)
        seconds = int(time % 60)
        milliseconds = int((time * 1000) % 1000)
        return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

async def setup(bot):
    await bot.add_cog(PB(bot))
"""