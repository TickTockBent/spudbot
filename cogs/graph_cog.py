import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import matplotlib.dates as mdates

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_line_graph(self, data, title, ylabel):
        timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts, _ in data]
        values = [float(value) for _, value in data]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, values, marker='o')
        plt.title(title)
        plt.xlabel('Time')
        plt.ylabel(ylabel)
        plt.grid(True)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gcf().autofmt_xdate()  # Rotation

        # Save the plot to a bytes buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        return buffer

    async def get_price_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('price', hours=6)  # Last 6 hours
        if not data:
            return "No price data available for the last 6 hours"

        graph_buffer = self.generate_line_graph(data, 'Price (USD) Last 6 Hours', 'Price (USD)')
        
        # Calculate 6h trend
        start_price = data[0][1]
        end_price = data[-1][1]
        trend_percent = ((end_price - start_price) / start_price) * 100
        trend_arrow = "▲" if trend_percent >= 0 else "▼"

        file = discord.File(graph_buffer, filename="price_graph.png")
        return file, f"6h Trend: {trend_arrow} {abs(trend_percent):.2f}%"

    async def get_netspace_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('netspace', hours=24*30)  # Last 30 days
        if not data:
            return "No netspace data available for the last 30 days"

        graph_buffer = self.generate_line_graph(data, 'Netspace (PiB) Last 30 Days', 'Netspace (PiB)')

        # Calculate 30d change
        start_netspace = data[0][1]
        end_netspace = data[-1][1]
        change_percent = ((end_netspace - start_netspace) / start_netspace) * 100
        change_arrow = "▲" if change_percent >= 0 else "▼"

        file = discord.File(graph_buffer, filename="netspace_graph.png")
        return file, f"30d Change: {change_arrow} {abs(change_percent):.2f}%"

async def setup(bot):
    await bot.add_cog(GraphCog(bot))