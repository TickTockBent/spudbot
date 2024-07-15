import aiohttp
from collections import deque
from discord.ext import commands, tasks
import statistics
import logging

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.price_history = deque(maxlen=10)
        self.current_data = None
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def fetch_api_data(self):
        api_url = "https://spacemesh-api-v2.swarmbit.io/network/info"
        try:
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logging.error(f"API request failed with status {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logging.error(f"Error fetching API data: {str(e)}")
            return None

    def process_price(self, price):
        self.price_history.append(price)
        return {
            'formatted_price': f"${price:.2f}",
            'trend': self.calculate_trend(price)
        }

    def calculate_trend(self, current_price):
        if not self.price_history:
            return "↑"
        avg_price = statistics.mean(self.price_history)
        return "↑" if current_price >= avg_price else "↓"

    @tasks.loop(minutes=5)
    async def update_data(self):
        try:
            data = await self.fetch_api_data()
            if data:
                self.current_data = data
                price_data = self.process_price(data['price'])
                self.bot.dispatch('price_update', price_data)
            else:
                logging.warning("Failed to fetch API data")
        except Exception as e:
            logging.error(f"Error updating data: {str(e)}")

    @update_data.before_loop
    async def before_update_data(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(APICog(bot))