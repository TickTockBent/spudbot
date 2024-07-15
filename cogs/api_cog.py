import aiohttp
from collections import deque
from discord.ext import commands, tasks
import statistics
import logging
import asyncio

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.price_history = deque(maxlen=10)
        self.current_data = None
        self.session = None
        self.update_interval = self.bot.config['INTERVAL']

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

    def process_price(self, price):
        self.price_history.append(price)
        return {
            'formatted_price': f"${price:.2f}",
            'trend': self.calculate_trend(price)
        }
    
    def process_layer(self, layer):
        return f"Layer: {layer}"

    def process_epoch(self, epoch):
        return f"Epoch: {epoch}"

    def calculate_trend(self, current_price):
        if not self.price_history:
            return "↑"
        avg_price = statistics.mean(self.price_history)
        return "↑" if current_price >= avg_price else "↓"

    def process_circulating_supply(self, supply):
        # Convert smidge to millions of SMH
        smh = supply / 1_000_000  # Convert smidge to SMH
        millions_smh = smh / 1_000_000  # Convert SMH to millions of SMH
        # Round up to two decimal places
        rounded_millions_smh = round(millions_smh, 2)
        return f"{rounded_millions_smh:.2f}M SMH"

    @tasks.loop()
    async def update_data(self):
        try:
            logging.info("Fetching API data...")
            data = await self.fetch_api_data()
            if data:
                self.current_data = data
                price_data = self.process_price(data['price'])
                layer_data = self.process_layer(data['layer'])
                epoch_data = self.process_epoch(data['epoch'])
                circulating_supply_data = self.process_circulating_supply(data['circulatingSupply'])
                
                logging.info(f"Dispatching updates: price={price_data}, layer={layer_data}, epoch={epoch_data}, circulating_supply={circulating_supply_data}")
                self.bot.dispatch('price_update', price_data)
                self.bot.dispatch('layer_update', layer_data)
                self.bot.dispatch('epoch_update', epoch_data)
                self.bot.dispatch('circulating_supply_update', circulating_supply_data)
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