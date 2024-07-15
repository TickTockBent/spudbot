import sqlite3
from discord.ext import commands, tasks
import asyncio
import logging

class DataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'spacemesh_data.db'
        self.conn = None
        self.setup_database()
        self.price_collection_task.start()
        self.netspace_collection_task.start()

    def setup_database(self):
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_points (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,
                value REAL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp_metric ON data_points(timestamp, metric_type)')
        self.conn.commit()

    def cog_unload(self):
        if self.conn:
            self.conn.close()
        self.price_collection_task.cancel()
        self.netspace_collection_task.cancel()

    @tasks.loop(minutes=10)
    async def price_collection_task(self):
        await self.collect_data('price')

    @tasks.loop(hours=24)
    async def netspace_collection_task(self):
        await self.collect_data('netspace')

    async def collect_data(self, metric_type):
        api_cog = self.bot.get_cog('APICog')
        if api_cog and api_cog.current_data:
            if metric_type == 'price':
                value = api_cog.current_data['price']
            elif metric_type == 'netspace':
                # Convert smeshing units to PiB
                value = api_cog.current_data['effectiveUnitsCommited'] * 64 / (1024 * 1024)  # 64 GiB per unit, convert to PiB
            else:
                logging.error(f"Unknown metric type: {metric_type}")
                return

            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO data_points (metric_type, value) VALUES (?, ?)', (metric_type, value))
            self.conn.commit()
            logging.info(f"Collected {metric_type} data: {value}")
        else:
            logging.error(f"Failed to collect {metric_type} data: API data not available")

    def get_data(self, metric_type, hours=12):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT timestamp, value FROM data_points
            WHERE metric_type = ? AND timestamp >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp
        ''', (metric_type, hours))
        return cursor.fetchall()

    @price_collection_task.before_loop
    @netspace_collection_task.before_loop
    async def before_collection_tasks(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DataCog(bot))