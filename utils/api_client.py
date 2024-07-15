from collections import deque
from discord.ext import commands, tasks
import statistics

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.price_history = deque(maxlen=10)
        self.current_data = None

    async def fetch_api_data(self):
        # Implement API data fetching here
        pass

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
            self.current_data = await self.fetch_api_data()
            price_data = self.process_price(self.current_data['price'])
            self.bot.dispatch('price_update', price_data)
        except Exception as e:
            print(f"Error updating data: {e}")

async def setup(bot):
    await bot.add_cog(APICog(bot))