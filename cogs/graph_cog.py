import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io
from datetime import datetime
import matplotlib.dates as mdates

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_graph(self, data, title, ylabel):
        timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts, _ in data]
        values = [float(value) for _, value in data]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, values, marker='o')
        plt.title(title)
        plt.xlabel('Time')
        plt.ylabel(ylabel)
        plt.grid(True)

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gcf().autofmt_xdate()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        return discord.File(buffer, filename=f"{title.lower().replace(' ', '_')}.png")

    def get_price_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('price', hours=12)  # Last 12 hours
        if not data:
            return "No price data available for the last 12 hours"

        graph_file = self.generate_graph(data, 'Price (USD) Last 12 Hours', 'Price (USD)')
        
        start_price = data[0][1]
        end_price = data[-1][1]
        trend_percent = ((end_price - start_price) / start_price) * 100
        trend_arrow = "▲" if trend_percent >= 0 else "▼"

        return graph_file, f"12h Trend: {trend_arrow} {abs(trend_percent):.2f}%"

async def setup(bot):
    await bot.add_cog(GraphCog(bot))