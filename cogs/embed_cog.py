import discord
from discord.ext import commands, tasks
import config
import sqlite3
from datetime import datetime, timedelta
import asyncio

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_embed.start()

    def cog_unload(self):
        self.update_embed.cancel()

    @tasks.loop(minutes=5)
    async def update_embed(self):
        if config.DEBUG_MODE:
            print("Starting embed update process")

        try:
            data_cog = self.bot.get_cog('DataCog')
            if not data_cog:
                if config.DEBUG_MODE:
                    print("DataCog not found. Unable to update embed.")
                return

            # Wait for processed data to be available
            for _ in range(12):  # Try for up to 1 minute (5 seconds * 12)
                processed_data = data_cog.get_processed_data()
                if processed_data:
                    break
                if config.DEBUG_MODE:
                    print("Waiting for processed data...")
                await asyncio.sleep(5)
            
            if not processed_data:
                if config.DEBUG_MODE:
                    print("No processed data available after waiting. Skipping embed update.")
                return

            if config.DEBUG_MODE:
                print("Processed data received for embed update:")
                for key, value in processed_data.items():
                    print(f"  {key}: {value}")

            price_data = self.get_price_data()
            graph = self.generate_graph(price_data)
            trend = self.calculate_trend(price_data)

            embed = discord.Embed(title="Spacemesh Network Statistics", color=0x00ff00)
            embed.add_field(name="Price Graph (Last 12 Hours)", value=f"```{graph}```", inline=False)
            embed.add_field(name="24h Price Trend", value=f"{trend} | Current Price: ${processed_data['price']:.2f}", inline=False)
            embed.add_field(name="Epoch Statistics", value=self.format_epoch_stats(processed_data), inline=False)
            embed.add_field(name="Network Statistics", value=self.format_network_stats(processed_data), inline=False)
            embed.add_field(name="Vesting Statistics", value=self.format_vesting_stats(processed_data), inline=False)
            embed.add_field(name="Next Epoch", value=self.format_next_epoch(processed_data), inline=False)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            embed.set_footer(text=f"Last updated: {current_time}")

            embed_channel_id = config.CHANNEL_IDS['embed']
            channel = self.bot.get_channel(embed_channel_id)
            if channel:
                embed_message_id = self.get_embed_message_id()
                if embed_message_id:
                    try:
                        message = await channel.fetch_message(embed_message_id)
                        await message.edit(embed=embed)
                        if config.DEBUG_MODE:
                            print("Embed updated successfully")
                    except discord.errors.NotFound:
                        if config.DEBUG_MODE:
                            print("Embed message not found. Creating a new one.")
                        new_message = await channel.send(embed=embed)
                        self.store_embed_message_id(new_message.id)
                        if config.DEBUG_MODE:
                            print(f"New embed message created with ID: {new_message.id}")
                else:
                    new_message = await channel.send(embed=embed)
                    self.store_embed_message_id(new_message.id)
                    if config.DEBUG_MODE:
                        print(f"New embed message created with ID: {new_message.id}")
            else:
                if config.DEBUG_MODE:
                    print(f"Embed channel with ID {embed_channel_id} not found")
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"An error occurred in the update_embed method: {str(e)}")

    def get_embed_message_id(self):
        try:
            conn = sqlite3.connect('spacemesh_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_data WHERE key = 'embed_message_id'")
            result = cursor.fetchone()
            conn.close()
            return int(result[0]) if result else None
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error fetching embed message ID: {str(e)}")
            return None

    def store_embed_message_id(self, message_id):
        try:
            conn = sqlite3.connect('spacemesh_data.db')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS bot_data (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT OR REPLACE INTO bot_data (key, value) VALUES (?, ?)", ('embed_message_id', str(message_id)))
            conn.commit()
            conn.close()
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error storing embed message ID: {str(e)}")

    def get_price_data(self):
        try:
            conn = sqlite3.connect('spacemesh_data.db')
            cursor = conn.cursor()
            twelve_hours_ago = (datetime.now() - timedelta(hours=12)).isoformat()
            cursor.execute("SELECT timestamp, value FROM spacemesh_data WHERE data_type = 'price' AND timestamp > ? ORDER BY timestamp", (twelve_hours_ago,))
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error fetching price data: {str(e)}")
            return []

    def generate_graph(self, price_data):
        if not price_data:
            return "No price data available"

        try:
            prices = [price for _, price in price_data]
            min_price, max_price = min(prices), max(prices)
            if min_price == max_price:
                normalized_prices = [0] * len(prices)
            else:
                normalized_prices = [int((price - min_price) / (max_price - min_price) * 5) for price in prices]

            graph = [" " * 40 for _ in range(6)]
            for i, height in enumerate(normalized_prices):
                for j in range(height + 1):
                    graph[5 - j] = graph[5 - j][:i] + "│" + graph[5 - j][i+1:]

            graph = [f"${price:.2f} │" + line for price, line in zip(reversed(prices[:6]), graph)]

            time_labels = ["Now", "3h", "6h", "9h", "12h"]
            graph.append("      " + "─" * 40)
            graph.append("      " + "   ".join(time_labels).center(40))

            return "\n".join(graph)
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error generating graph: {str(e)}")
            return "Error generating graph"

    def calculate_trend(self, price_data):
        if len(price_data) < 2:
            return "N/A"

        try:
            start_price = price_data[0][1]
            end_price = price_data[-1][1]
            if start_price == 0:
                if end_price > 0:
                    return "↑ 100.00%"
                else:
                    return "→ 0.00%"
            else:
                percent_change = ((end_price - start_price) / start_price) * 100

                if percent_change > 0:
                    return f"↑ {abs(percent_change):.2f}%"
                elif percent_change < 0:
                    return f"↓ {abs(percent_change):.2f}%"
                else:
                    return "→ 0.00%"
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error calculating trend: {str(e)}")
            return "Error"

    def format_epoch_stats(self, data):
        return (f"• Epoch: {data['epoch']}\n"
                f"• Layer: {data['layer']}\n"
                f"• Netspace: {data['effectiveUnitsCommited']:.2f} EiB\n"
                f"• Epoch Rewards: {data['epochSubsidy']:.2f}M SMH")

    def format_network_stats(self, data):
        return (f"• Total Rewards: {data['rewards']}\n"
                f"• Circulating Supply: {data['circulatingSupply']:.2f}M SMH\n"
                f"• Market Cap: ${data['marketCap']:.2f}M\n"
                f"• Total Active Wallets: {data['totalAccounts']}\n"
                f"• Activations: {data['totalActiveSmeshers']:.2f}M")

    def format_vesting_stats(self, data):
        vested_value = data['vested'] * data['price']
        remaining_vaulted = data['remainingVaulted'] / 1e6  # Convert to millions
        remaining_value = remaining_vaulted * data['price']
        return (f"• Total VC Coins Vested: {data['vested']:.2f}M SMH\n"
                f"• Value of Vested Coins: ${vested_value:.2f}M\n"
                f"• VC Coins to be Vested: {remaining_vaulted:.2f}M SMH\n"
                f"• Value of Remaining VC Coins: ${remaining_value:.2f}M")

    def format_next_epoch(self, data):
        next_epoch = data['nextEpoch']
        return (f"• Next Epoch: {next_epoch['epoch']}\n"
                f"• Confirmed Space: {next_epoch['effectiveUnitsCommited']:.2f} EiB\n"
                f"• Confirmed Activations: {next_epoch['totalActiveSmeshers']:.3f}M")

    @update_embed.before_loop
    async def before_update_embed(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("EmbedCog is ready and will start updating the embed.")

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
    if config.DEBUG_MODE:
        print("EmbedCog has been loaded.")