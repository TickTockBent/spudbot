from collections import deque
import discord
from discord.ext import commands, tasks
import statistics

class APICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.price_history = deque(maxlen=10)
        self.last_update_time = 0

    def format_price(self, price):
        """Format price to two decimal places with "$" prefix."""
        return f"${price:.2f}"

    # Other methods will be implemented here...
    def calculate_trend(self, current_price):
        """Calculate trend based on current price vs average of price_history."""
        if not self.price_history:
            return "↑"  # Default to up arrow if no history
    
        avg_price = statistics.mean(self.price_history)
        if current_price > avg_price:
            return "↑"
        elif current_price < avg_price:
            return "↓"
        else:
            return "↑"  # Default to up arrow if equal

async def setup(bot):
    await bot.add_cog(APICog(bot))