import discord
from discord.ext import commands

class Greet(commands.Cog):
    def __init__(self, ayayabot):
        self.ayayabot = ayayabot

    @commands.command()
    async def greet(self, ctx):
        """I wonder what this does..."""
        await ctx.send(f'<:AYAYA:928769603717460018> Ayaya Supports Transgender People! �')

def setup(ayayabot):
    ayayabot.add_cog(Greet(ayayabot))
