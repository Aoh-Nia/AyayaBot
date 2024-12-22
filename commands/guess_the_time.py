import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import random
import re
import datetime

class GuessTheTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://www.speedrun.com/api/v1/runs"
        self.chapter_game_ids = {
            "chapter_1": "w6j7vpx6",
            "chapter_2": "4d7nqx36",
            "chapter_3": "w6jge376"
        }
        self.db_connection = sqlite3.connect("guess_time.db")
        self.create_scores_table()

    def create_scores_table(self):
        """Create a table to store scores if it doesn't already exist."""
        with self.db_connection:
            self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    user_id INTEGER,
                    username TEXT,
                    score INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id)
                )
            """)

    def update_score(self, user_id, username, points):
        """Update the user's score in the database."""
        with self.db_connection:
            cursor = self.db_connection.execute("""
                INSERT INTO scores (user_id, username, score)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET score = score + ?;
            """, (user_id, username, points, points))
        return cursor.rowcount > 0

    async def fetch_all_runs_for_chapter(self, chapter_key):
        """Fetches all verified runs for a specific chapter."""
        game_id = self.chapter_game_ids.get(chapter_key)
        if not game_id:
            return None

        # List to store all runs
        all_runs = []
        offset = 0
        while True:
            # Include the 'status' filter to only get verified runs
            params = {
                "game": game_id,
                "status": "verified",  # Only fetch verified runs
                "max": 200,  # Fetch up to 200 runs per request (you can adjust this as needed)
                "offset": offset,  # Offset for pagination
            }

            try:
                response = requests.get(self.api_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    if data:
                        all_runs.extend(data)  # Add the runs to the list
                        if len(data) < 200:  # No more runs available
                            break
                        offset += 200  # Increase offset for the next page of results
                    else:
                        print(f"No more runs found for {chapter_key}.")
                        break
                else:
                    print(f"Failed to fetch runs for {chapter_key}. Status code: {response.status_code}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"Error fetching runs for {chapter_key}: {e}")
                break

        return all_runs

    def replace_time_with_censored(self, description):
        """Replaces any time in the description with 'CENSORED'."""
        if not description:
            return description
        
        # Regular expression to detect time format and replace with "CENSORED"
        time_patterns = [
            r"\b(\d{1,2}):(\d{2})\b",  # Matches mm:ss (e.g., 01:30)
            r"\b(\d{1,2}):(\d{2})\.(\d{1,3})\b",  # Matches mm:ss.m or mm:ss.123 (e.g., 01:30.123)
            r"\b(\d{1,2})\.(\d{2})\b",  # Matches mm.ss (e.g., 01.30)
            r"\b(\d{1,2}):(\d{2}):(\d{2})\b",  # Matches hh:mm:ss (e.g., 01:30:45)
            r"\b(\d{1,2}):(\d{2}):(\d{2})\.(\d{1,3})\b",  # Matches hh:mm:ss.m or hh:mm:ss.123 (e.g., 01:30:45.123)
            r"\bCENSORED[:.0-9]+\b"  # Prevent replacing already censored times (e.g., CENSORED:10.000)
        ]
        
        for pattern in time_patterns:
            description = re.sub(pattern, "~~__**CENSORED**__~~", description)

        return description  # Return the modified description

    async def select_random_chapter(self):
        """Selects a random chapter and fetches a random run."""
        chapter_key = random.choice(list(self.chapter_game_ids.keys()))  # Randomly select a chapter
        runs = await self.fetch_all_runs_for_chapter(chapter_key)
        if not runs:
            return chapter_key, None

        # Filter out runs without descriptions
        runs_with_description = [run for run in runs if run.get("comment")]

        if not runs_with_description:
            return chapter_key, None

        # Randomly select a run from the list of runs with descriptions
        random_run = random.choice(runs_with_description)
        return chapter_key, random_run

    def clean_description(self, description):
        """Cleans the run description by removing irrelevant content like mod notes."""
        if not description:
            return "No description available."
        
        # Regular expression to match variations of "Mod Note:", "Mod message:", etc.
        # The regex will match any case variations of these phrases and remove everything after them.
        cleaned_description = re.sub(r"(mod\s*(note|message):.*)", "", description, flags=re.IGNORECASE)
        
        # Clean up any extra spaces or newlines
        return cleaned_description.strip()
    
    def time_to_seconds(self, time_str):
        """Convert time strings to seconds."""
        parts = list(map(int, time_str.split(":")))
        return sum(x * 60 ** i for i, x in enumerate(reversed(parts)))
    
    @app_commands.command(name="guess_time", description="Guess the time of a randomly selected run from a random chapter!")
    async def guess_time(self, interaction: discord.Interaction):
        await interaction.response.defer()

        chapter_key, run = await self.select_random_chapter()
        if not run:
            await interaction.followup.send(f"No verified runs found for {chapter_key}. Try again later!")
            return

        description = self.clean_description(run.get("comment"))
        description = self.replace_time_with_censored(description)

        time_in_seconds = run.get("times", {}).get("primary_t")
        run_id = run.get("id")
        run_date = run.get("date")  # Get the run's date
        if time_in_seconds is None:
            await interaction.followup.send("The selected run doesn't have a recorded time. Try again!")
            return

        formatted_time = f"{int(time_in_seconds // 60)}:{int(time_in_seconds % 60):02d}"
        run_url = f"https://www.speedrun.com/run/{run_id}"

        due_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1, seconds=30)
        due_timestamp = int(due_time.timestamp())

        await interaction.followup.send(
            f"## **Guess the Time!**\n"
            f"- **Chapter:** {chapter_key.replace('_', ' ').title()}\n"
            f"- **Description:** {description}\n"
            f"- **Run Date:** {run_date if run_date else 'Unknown'}\n"
            f"⏰ **Time's up <t:{due_timestamp}:R>**"
        )

        def check(msg):
            pattern = r"^\d{1,2}(:\d{2}){1,2}$"
            return msg.author == interaction.user and msg.channel == interaction.channel and re.match(pattern, msg.content.strip())
        
        def calculate_score(difference):
            """Calculate points based on how close the guess is to the actual time."""
            if difference == 0:
                return 100  # Perfect match
            elif difference <= 5:
                return 60  # Close within 5 seconds
            elif difference <= 10:
                return 40  # Close within 10 seconds
            elif difference <= 30:
                return 20  # Close within 30 seconds
            return 0  # Too far off

        try:
            user_message = await self.bot.wait_for("message", timeout=30.0, check=check)
            user_guess = user_message.content.strip()

            actual_seconds = self.time_to_seconds(formatted_time)
            guessed_seconds = self.time_to_seconds(user_guess)
            difference = abs(actual_seconds - guessed_seconds)
            points = calculate_score(difference)

            if difference == 0:
                # Perfect match
                self.update_score(user_message.author.id, user_message.author.name, points)
                await interaction.followup.send(
                    f"🎉 Perfect! The time is {formatted_time}."
                    f"\nYou earned **{points} points**!"
                    f"\n[Link to the run](<{run_url}>)"
                )
            elif points > 0:
                # Close but not exact
                self.update_score(user_message.author.id, user_message.author.name, points)
                await interaction.followup.send(
                    f"👍 You were close! The difference was **{difference}** seconds."
                    f"\nYou earned **{points} points**!"
                    f"\nThe correct time was {formatted_time}."
                    f"\n[Link to the run](<{run_url}>)"
                )
            else:
                # Too far off
                await interaction.followup.send(
                    f"😢 Incorrect. The difference was **{difference}** seconds."
                    f"\nThe correct time was {formatted_time}."
                    f"\n[Link to the run](<{run_url}>)"
                )

        except Exception:
            await interaction.followup.send(f"⏰ Time's up! The correct time was {formatted_time}.\n[Link to the run](<{run_url}>)")

async def setup(bot):
    await bot.add_cog(GuessTheTime(bot))