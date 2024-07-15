from discord.ext import commands
import math
from datetime import datetime, timedelta

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_graph(self, data, width=24, height=8):
        values = [float(value) for _, value in data] if data else [0]
        min_val, max_val = min(values), max(values)
        range_val = max(max_val - min_val, 0.01)  # Prevent division by zero

        graph = []
        for i in range(height):
            row = ['│'] + [' '] * width
            for j, value in enumerate(values):
                if j < width:
                    normalized_val = (value - min_val) / range_val
                    if normalized_val >= 1 - (i / (height - 1)):
                        row[j + 1] = '█'
            graph.append(''.join(row))

        # Add X-axis
        x_axis = '└' + '─' * width
        graph.append(x_axis)

        return '\n'.join(reversed(graph))

    def get_price_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('price', hours=12)
        graph = self.generate_graph(data)
        
        if not data:
            return f"Price (USD) Last 12 Hours\n```\n{graph}\n```\nNo price data available yet"

        # Calculate 24h trend
        start_price = data[0][1]
        end_price = data[-1][1]
        trend_percent = ((end_price - start_price) / start_price) * 100
        trend_arrow = "▲" if trend_percent >= 0 else "▼"

        min_price = min(price for _, price in data)
        max_price = max(price for _, price in data)

        # Format timestamps
        start_time = datetime.strptime(data[0][0], "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(data[-1][0], "%Y-%m-%d %H:%M:%S")

        return (f"Price (USD) Last 12 Hours\n```\n"
                f"${max_price:.2f} │\n"
                f"{graph}\n"
                f"${min_price:.2f} │\n"
                f"     {start_time.strftime('%H:%M')}{'    ' * 9}{end_time.strftime('%H:%M')}\n"
                f"```\n24h Trend: {trend_arrow} {abs(trend_percent):.2f}%")

    def get_netspace_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('netspace', hours=24*30)  # Last 30 days
        graph = self.generate_graph(data)

        if not data:
            return f"Netspace (PiB) Last 30 Days\n```\n{graph}\n```\nNo netspace data available yet"

        min_netspace = min(netspace for _, netspace in data)
        max_netspace = max(netspace for _, netspace in data)

        # Format timestamps
        start_time = datetime.strptime(data[0][0], "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(data[-1][0], "%Y-%m-%d %H:%M:%S")

        return (f"Netspace (PiB) Last 30 Days\n```\n"
                f"{max_netspace:.2f} │\n"
                f"{graph}\n"
                f"{min_netspace:.2f} │\n"
                f"     {start_time.strftime('%m-%d')}{'    ' * 9}{end_time.strftime('%m-%d')}\n"
                f"```")

async def setup(bot):
    await bot.add_cog(GraphCog(bot))