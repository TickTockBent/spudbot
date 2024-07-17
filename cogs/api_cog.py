import aiohttp
import asyncio
from discord.ext import commands, tasks
import config

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_data = {}
        self.last_fetch_time = None
        self.fetch_data.start()

    def cog_unload(self):
        self.fetch_data.cancel()

    @tasks.loop(minutes=5)
    async def fetch_data(self):
        """Fetch data from the API every 5 minutes."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.API_ENDPOINT) as response:
                    if response.status == 200:
                        self.api_data = await response.json()
                        self.last_fetch_time = asyncio.get_event_loop().time()
                        print("API data fetched successfully")
                    else:
                        print(f"Failed to fetch API data. Status code: {response.status}")
        except Exception as e:
            print(f"Error fetching API data: {str(e)}")

    @fetch_data.before_loop
    async def before_fetch_data(self):
        """Wait for the bot to be ready before starting the fetch loop."""
        await self.bot.wait_until_ready()

    def get_data(self):
        """Return the latest fetched API data."""
        return self.api_data

    def get_last_fetch_time(self):
        """Return the timestamp of the last successful API fetch."""
        return self.last_fetch_time

async def setup(bot):
    await bot.add_cog(APICog(bot))