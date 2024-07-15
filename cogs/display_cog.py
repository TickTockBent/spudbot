from discord.ext import commands
import logging

class DisplayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("DisplayCog is ready")
        # Display update logic will go here

async def setup(bot):
    await bot.add_cog(DisplayCog(bot))