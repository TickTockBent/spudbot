import aiohttp
from discord.ext import commands, tasks
import logging
import asyncio

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_data = {}
        self.processed_data = {}
        self.session = None
        self.update_intervals = self.bot.config['UPDATE_INTERVALS']
        self.initial_data_fetched = asyncio.Event()
        self.update_loops = {}

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        await self.start_update_loops()
        logging.info("APICog loaded and update loops started")

    async def cog_unload(self):
        await self.stop_update_loops()
        if self.session:
            await self.session.close()
        logging.info("APICog unloaded and update loops cancelled")

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

    def process_data(self, data, data_type):
        if not data:
            return None

        try:
            if data_type == 'price':
                return f"${data['price']:.2f}"
            elif data_type == 'circulatingsupply':
                return f"{data['circulatingSupply'] / 1e15:.2f}M SMH"
            elif data_type == 'marketcap':
                return f"${data['marketCap'] / 1e6:.2f}M"
            elif data_type == 'epoch':
                return str(data['epoch'])
            elif data_type == 'layer':
                return str(data['layer'])
            elif data_type == 'networksize':
                return f"{data['effectiveUnitsCommited'] * 64 / (1024 * 1024):.2f} EiB"
            elif data_type == 'activesmeshers':
                return f"{data['totalActiveSmeshers']:,}"
            elif data_type == 'percenttotalsupply':
                total_supply = 15_000_000_000  # 15 billion SMH
                circulating_supply = data['circulatingSupply'] / 1e9  # Convert smidge to SMH
                return f"{(circulating_supply / total_supply) * 100:.2f}%"
            return None
        except KeyError as e:
            logging.error(f"KeyError processing {data_type}: {str(e)}")
            return None

    async def start_update_loops(self):
        for data_type, interval in self.update_intervals.items():
            if data_type not in ['default', 'embed']:
                self.update_loops[data_type] = self.bot.loop.create_task(self.update_data_loop(data_type, interval))

    async def stop_update_loops(self):
        for task in self.update_loops.values():
            task.cancel()
        await asyncio.gather(*self.update_loops.values(), return_exceptions=True)

    async def update_data_loop(self, data_type, interval):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.update_data(data_type)
            await asyncio.sleep(interval)

    async def update_data(self, data_type):
        try:
            logging.info(f"Fetching API data for {data_type}...")
            data = await self.fetch_api_data()
            if data:
                processed = self.process_data(data, data_type)
                if processed:
                    self.processed_data[data_type] = processed
                    if not self.initial_data_fetched.is_set():
                        self.initial_data_fetched.set()
                    logging.info(f"API data for {data_type} updated and processed successfully")
                    self.bot.dispatch('data_update', data_type, processed)
                else:
                    logging.warning(f"Failed to process data for {data_type}")
            else:
                logging.warning(f"Failed to fetch API data for {data_type}")
        except Exception as e:
            logging.error(f"Error updating data for {data_type}: {str(e)}")

async def setup(bot):
    await bot.add_cog(APICog(bot))