from discord.ext import commands
import math
from datetime import datetime, timedelta

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    from discord.ext import commands
import math
from datetime import datetime, timedelta

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_graph(self, data, width=24, height=8, is_price=True):
        if not data or len(data) < 2:
            return "Insufficient data for graph"

        values = [float(value) for _, value in data]
        timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts, _ in data]

        min_val, max_val = min(values), max(values)
        val_range = max_val - min_val

        if val_range == 0:
            val_range = 1  # Prevent division by zero

        graph = [[' ' for _ in range(width)] for _ in range(height)]

        # Generate the line
        for i in range(1, len(values)):
            x1 = int((i-1) / (len(values)-1) * (width-1))
            x2 = int(i / (len(values)-1) * (width-1))
            y1 = int((values[i-1] - min_val) / val_range * (height-1))
            y2 = int((values[i] - min_val) / val_range * (height-1))

            if x1 == x2:
                # Handle case where timestamps are the same
                graph[height-1-y2][x2] = '|'
            elif y1 == y2:
                graph[height-1-y1][x1:x2+1] = ['─'] * (x2-x1+1)
            else:
                for x in range(x1, x2+1):
                    y = int(y1 + (y2-y1) * (x-x1) / (x2-x1))
                    char = '/' if y2 > y1 else '\\'  # '/' for rising, '\' for falling
                    graph[height-1-y][x] = char

        # Add Y-axis labels
        y_labels = [f"{'$' if is_price else ''}{min_val + i * val_range / (height-1):.2f}" for i in range(height)]
        max_label_length = max(len(label) for label in y_labels)
        graph_with_labels = [f"{y_labels[i]:>{max_label_length}} │{''.join(row)}" for i, row in enumerate(reversed(graph))]

        # Add X-axis
        x_axis = f"{' ' * max_label_length} └{'─' * width}"
        graph_with_labels.append(x_axis)

        # Add X-axis labels
        x_labels = [ts.strftime("%H:%M" if is_price else "%m-%d") for ts in [timestamps[0], timestamps[-1]]]
        x_label_line = f"{' ' * max_label_length}  {x_labels[0]}{' ' * (width-12)}{x_labels[-1]}"
        graph_with_labels.append(x_label_line)

        return '\n'.join(graph_with_labels)

    def get_price_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('price', hours=6)  # Last 6 hours
        if not data:
            return "Price (USD) Last 6 Hours\n```\nNo price data available yet\n```"

        graph = self.generate_graph(data, width=40, is_price=True)  # Width set to 40
        
        # Calculate 6h trend
        start_price = data[0][1]
        end_price = data[-1][1]
        trend_percent = ((end_price - start_price) / start_price) * 100
        trend_arrow = "▲" if trend_percent >= 0 else "▼"

        return f"Price (USD) Last 6 Hours\n```\n{graph}\n```\n6h Trend: {trend_arrow} {abs(trend_percent):.2f}%"

    def get_netspace_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('netspace', hours=24*30)  # Last 30 days
        if not data:
            return "Netspace (PiB) Last 30 Days\n```\nNo netspace data available yet\n```"

        graph = self.generate_graph(data, is_price=False)

        # Calculate netspace change
        start_netspace = data[0][1]
        end_netspace = data[-1][1]
        change_percent = ((end_netspace - start_netspace) / start_netspace) * 100
        change_arrow = "▲" if change_percent >= 0 else "▼"

        return f"Netspace (PiB) Last 30 Days\n```\n{graph}\n```\n30d Change: {change_arrow} {abs(change_percent):.2f}%"

async def setup(bot):
    await bot.add_cog(GraphCog(bot))