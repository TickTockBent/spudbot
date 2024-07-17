import aiohttp
import asyncio
from discord.ext import commands, tasks
import config
import json

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_data = {}
        self.last_fetch_time = None
        self.data_available = asyncio.Event()
        self.fetch_data.start()

    def cog_unload(self):
        self.fetch_data.cancel()

    @tasks.loop(minutes=5)
    async def fetch_data(self):
        if config.DEBUG_MODE:
            print(f"Attempting to fetch data from {config.API_ENDPOINT}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.API_ENDPOINT) as response:
                    if response.status == 200:
                        self.api_data = await response.json()
                        self.last_fetch_time = asyncio.get_event_loop().time()
                        if config.DEBUG_MODE:
                            print("API data fetched successfully")
                            print("Sample of fetched data:")
                            print(json.dumps(dict(list(self.api_data.items())[:5]), indent=2))
                        self.data_available.set()  # Signal that new data is available
                    else:
                        if config.DEBUG_MODE:
                            print(f"Failed to fetch API data. Status code: {response.status}")
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error fetching API data: {str(e)}")

    @fetch_data.before_loop
    async def before_fetch_data(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("APICog is ready and will start fetching data.")

    def get_data(self):
        return self.api_data

    def get_last_fetch_time(self):
        return self.last_fetch_time

    def has_valid_data(self):
        return bool(self.api_data) and self.api_data.get('epoch') != '0'

    async def wait_for_data(self):
        await self.data_available.wait()
        self.data_available.clear()  # Reset the event for the next cycle

async def setup(bot):
    await bot.add_cog(APICog(bot))
    if config.DEBUG_MODE:
        print("APICog has been loaded.")