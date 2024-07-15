from discord.ext import commands
import math

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_graph(self, data, width=24, height=8):
        if not data:
            return "No data available"

        values = [float(value) for _, value in data]
        min_val, max_val = min(values), max(values)
        range_val = max_val - min_val

        graph = []
        for i in range(height):
            row = []
            for j in range(width):
                if j < len(values):
                    normalized_val = (values[j] - min_val) / range_val if range_val else 0
                    if normalized_val >= 1 - (i / height):
                        row.append('█')
                    else:
                        row.append(' ')
                else:
                    row.append(' ')
            graph.append(''.join(row))

        return '\n'.join(reversed(graph))

    def get_price_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('price', hours=12)
        if not data:
            return "No price data available"

        graph = self.generate_graph(data)
        
        # Calculate 24h trend
        if len(data) >= 2:
            start_price = data[0][1]
            end_price = data[-1][1]
            trend_percent = ((end_price - start_price) / start_price) * 100
            trend_arrow = "▲" if trend_percent >= 0 else "▼"
        else:
            trend_percent = 0
            trend_arrow = "-"

        min_price = min(price for _, price in data)
        max_price = max(price for _, price in data)

        return f"Price (USD) Last 12 Hours\n```\n{max_price:.2f} |\n{graph}\n{min_price:.2f} |\n```\n24h Trend: {trend_arrow} {abs(trend_percent):.2f}%"

    def get_netspace_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('netspace', hours=24*30)  # Last 30 days
        if not data:
            return "No netspace data available"

        graph = self.generate_graph(data)

        min_netspace = min(netspace for _, netspace in data)
        max_netspace = max(netspace for _, netspace in data)

        return f"Netspace (PiB) Last 30 Days\n```\n{max_netspace:.2f} |\n{graph}\n{min_netspace:.2f} |\n```"

async def setup(bot):
    await bot.add_cog(GraphCog(bot))