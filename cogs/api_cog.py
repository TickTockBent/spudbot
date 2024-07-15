from discord.ext import commands, tasks
import logging

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_data.start()

    def cog_unload(self):
        self.update_data.cancel()

    @tasks.loop(minutes=5)
    async def update_data(self):
        logging.info("Updating data from API")
        # API fetch logic will go here

async def setup(bot):
    await bot.add_cog(APICog(bot))