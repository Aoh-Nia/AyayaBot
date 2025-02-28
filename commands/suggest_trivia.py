import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="suggest_trivia_question", description="Suggest a trivia question!")
    async def suggest_trivia_question(self, interaction: discord.Interaction):
        # Let the user know to check their DMs (only visible to them)
        await interaction.response.send_message("Check your DMs! 📨", ephemeral=True)

        # Send a DM to the user with the trivia question and cancel button
        user = interaction.user

        # Create a Cancel button
        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.danger)

        # Define the cancel interaction
        async def cancel_button_callback(interaction: discord.Interaction):
            # Delete all messages when the cancel button is pressed
            await interaction.response.send_message("Submission canceled.", ephemeral=True)
            await user.send("Your trivia question suggestion has been canceled.")

            # Delete all related messages
            await question_msg.delete()
            await options_msg.delete()
            await answer_msg.delete()

        cancel_button.callback = cancel_button_callback

        # Create the view with the cancel button
        view = View()
        view.add_item(cancel_button)

        # Send the message asking for the trivia question
        question_msg = await user.send("What's the trivia question?", view=view)

        # Wait for the user's response or cancellation
        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        try:
            # Wait for the question input
            question_input = await self.bot.wait_for('message', check=check, timeout=300)  # 5 minutes timeout
            question = question_input.content

            # Ask for the options
            options_msg = await user.send(f"Thank you! Now, what's the options for the question: ``{question}``")
            options_input = await self.bot.wait_for('message', check=check)
            options = options_input.content

            # Ask for the correct answer
            answer_msg = await user.send("Finally, what's the correct answer from the options?")
            answer_input = await self.bot.wait_for('message', check=check)
            correct_answer = answer_input.content

            # Send the suggestion to the private server #suggestions channel
            guild = self.bot.get_guild(1181645951451009115)  # Replace with your guild's ID
            suggestions_channel = discord.utils.get(guild.text_channels, name="suggestions")
            if suggestions_channel:
                await suggestions_channel.send(
                    f"**New Trivia Question Suggestion**\n"
                    f"Question: ``{question}``\n"
                    f"Options: ``{options}``\n"
                    f"Correct Answer: ``{correct_answer}``\n"
                    f"Suggested by: ``{user.name}`` ``{user.id}``"
                )

            # Wait 5 seconds and delete all the messages
            await asyncio.sleep(5)

            # After 5 seconds, delete all related messages
            await question_msg.delete()
            await options_msg.delete()
            await answer_msg.delete()

            # Acknowledge to the user
            await user.send("Your trivia question has been submitted successfully!")

        except discord.errors.TimeoutError:
            await user.send("You took too long to respond, submission has been canceled.")

            # Delete all the messages after timeout
            await question_msg.delete()
            await options_msg.delete()
            await answer_msg.delete()

            return

# Async setup function to add the cog
async def setup(bot):
    await bot.add_cog(Suggest(bot))
