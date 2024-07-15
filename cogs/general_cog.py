import discord
from discord import app_commands
from discord.ext import commands

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Check if the bot is online")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message("I'm online and ready to serve!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))