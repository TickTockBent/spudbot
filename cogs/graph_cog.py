from discord.ext import commands
import math
from datetime import datetime, timedelta

class GraphCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_price_graph(self, data, width=24, height=8):
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

            if y1 == y2:
                graph[height-1-y1][x1:x2+1] = ['_'] * (x2-x1+1)
            else:
                for x in range(x1, x2+1):
                    y = int(y1 + (y2-y1) * (x-x1) / (x2-x1))
                    if x == x1:
                        graph[height-1-y][x] = '/' if y2 > y1 else '\\'
                    elif x == x2:
                        graph[height-1-y][x] = '/' if y2 > y1 else '\\'
                    else:
                        graph[height-1-y][x] = '/' if y2 > y1 else '\\'

        # Add Y-axis labels
        y_labels = [f"${min_val + i * val_range / (height-1):.2f}" for i in range(height)]
        max_label_length = max(len(label) for label in y_labels)
        graph_with_labels = [f"{y_labels[i]:>{max_label_length}} |{''.join(row)}" for i, row in enumerate(reversed(graph))]

        # Add X-axis
        x_axis = f"{' ' * max_label_length} +{'-' * width}"
        graph_with_labels.append(x_axis)

        # Add X-axis labels
        x_labels = [ts.strftime("%H:%M") for ts in [timestamps[0], timestamps[-1]]]
        x_label_line = f"{' ' * max_label_length}  {x_labels[0]}{' ' * (width-12)}{x_labels[-1]}"
        graph_with_labels.append(x_label_line)

        return '\n'.join(graph_with_labels)

    def get_price_graph(self):
        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            return "DataCog not available"

        data = data_cog.get_data('price', hours=12)
        if not data:
            return "Price (USD) Last 12 Hours\n```\nNo price data available yet\n```"

        graph = self.generate_price_graph(data)
        
        # Calculate 24h trend
        start_price = data[0][1]
        end_price = data[-1][1]
        trend_percent = ((end_price - start_price) / start_price) * 100
        trend_arrow = "▲" if trend_percent >= 0 else "▼"

        return f"Price (USD) Last 12 Hours\n```\n{graph}\n```\n24h Trend: {trend_arrow} {abs(trend_percent):.2f}%"

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