import discord
import random
import json
import sqlite3
from discord.ext import commands
from discord import app_commands
import datetime

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_connection = sqlite3.connect("trivia.db")
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

    async def load_questions(self):
        """Load trivia questions from a JSON file."""
        with open('trivia_questions.json', 'r') as f:
            return json.load(f)

    async def select_random_question(self):
        """Select a random trivia question."""
        questions = await self.load_questions()
        return random.choice(questions['questions'])

    @app_commands.command(name="trivia", description="Guess the answer to a random trivia question!")
    async def trivia(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Select a random trivia question
        question = await self.select_random_question()
        question_text = question['question']
        options = question['options']
        answer = question['answer']

        # Calculate the time limit (30 seconds from now)
        due_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1, seconds=30)  # 30 seconds limit
        due_timestamp = int(due_time.timestamp())

        # Send the question to the user with the time limit
        message = f"**Question:** {question_text}\n"
        for idx, option in enumerate(options, 1):
            message += f"{idx}. {option}\n"
        message += f"⏰ **Time's up <t:{due_timestamp}:R>**"
        
        await interaction.followup.send(message)

        # Wait for the user's answer
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel and msg.content.strip().lower() in [option.lower() for option in options]

        try:
            user_message = await self.bot.wait_for("message", timeout=30.0, check=check)
            user_answer = user_message.content.strip().lower()

            if user_answer == answer.lower():
                points = 50  # Perfect answer gives 50 points
                self.update_score(user_message.author.id, user_message.author.name, points)
                await interaction.followup.send(
                    f"🎉 Correct! The answer is {answer}.\nYou earned **{points} points**!"
                )
            else:
                await interaction.followup.send(
                    f"😢 Incorrect. The correct answer was: {answer}."
                )

        except Exception:
            await interaction.followup.send(f"⏰ Time's up! The correct answer was {answer}.")

# Async setup function to add the cog
async def setup(bot):
    await bot.add_cog(Trivia(bot))