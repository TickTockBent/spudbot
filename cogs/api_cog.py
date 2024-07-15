import aiohttp
from discord.ext import commands, tasks
import logging
import asyncio

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_data = None
        self.session = None
        self.update_interval = self.bot.config['INTERVAL']
        self.initial_data_fetched = asyncio.Event()

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        self.update_data.start()
        logging.info("APICog loaded and update loop started")

    async def cog_unload(self):
        self.update_data.cancel()
        if self.session:
            await self.session.close()
        logging.info("APICog unloaded and update loop cancelled")

    async def fetch_api_data(self):
        try:
            async with self.session.get(self.bot.config['API_ENDPOINT']) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logging.error(f"API request failed with status {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logging.error(f"Error fetching API data: {str(e)}")
            return None

    @tasks.loop()
    async def update_data(self):
        try:
            logging.info("Fetching API data...")
            data = await self.fetch_api_data()
            if data:
                self.current_data = data
                if not self.initial_data_fetched.is_set():
                    self.initial_data_fetched.set()
                logging.info("API data updated successfully")
            else:
                logging.warning("Failed to fetch API data")
        except Exception as e:
            logging.error(f"Error updating data: {str(e)}")

    @update_data.before_loop
    async def before_update_data(self):
        await self.bot.wait_until_ready()
        self.update_data.change_interval(seconds=self.update_interval)
        logging.info(f"Starting update_data loop with interval: {self.update_interval} seconds")

async def setup(bot):
    await bot.add_cog(APICog(bot))