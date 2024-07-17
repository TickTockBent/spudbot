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

        if config.DEBUG_MODE:
            print("Fetching price data for graph")
        price_data = self.get_price_data()
        
        if config.DEBUG_MODE:
            print("Generating graph")
        graph = self.generate_graph(price_data)
        
        if config.DEBUG_MODE:
            print("Calculating price trend")
        trend = self.calculate_trend(price_data)

        if config.DEBUG_MODE:
            print("Creating embed")
        embed = discord.Embed(title="Spacemesh Network Statistics", color=0x00ff00)
        embed.add_field(name="Price Graph (Last 12 Hours)", value=f"```{graph}```", inline=False)
        embed.add_field(name="24h Price Trend", value=f"{trend} | Current Price: ${processed_data['price']:.2f}", inline=False)

        # Add other statistics fields
        embed.add_field(name="Epoch Statistics", value=self.format_epoch_stats(processed_data), inline=False)
        embed.add_field(name="Network Statistics", value=self.format_network_stats(processed_data), inline=False)
        embed.add_field(name="Vesting Statistics", value=self.format_vesting_stats(processed_data), inline=False)
        embed.add_field(name="Next Epoch", value=self.format_next_epoch(processed_data), inline=False)

        # Update the embed message
        embed_channel_id = config.CHANNEL_IDS['embed']
        channel = self.bot.get_channel(embed_channel_id)
        if channel:
            if config.DEBUG_MODE:
                print(f"Found embed channel with ID: {embed_channel_id}")
            try:
                messages = await channel.history(limit=1).flatten()
                if messages:
                    message = messages[0]
                    if config.DEBUG_MODE:
                        print("Updating existing embed message")
                    await message.edit(embed=embed)
                    if config.DEBUG_MODE:
                        print("Embed updated successfully")
                else:
                    if config.DEBUG_MODE:
                        print("No existing message found. Sending new embed message")
                    await channel.send(embed=embed)
                    if config.DEBUG_MODE:
                        print("New embed message sent")
            except discord.errors.NotFound:
                if config.DEBUG_MODE:
                    print("Message not found. Sending new embed message")
                await channel.send(embed=embed)
                if config.DEBUG_MODE:
                    print("New embed message sent")
            except discord.errors.Forbidden:
                if config.DEBUG_MODE:
                    print("Bot doesn't have permission to send/edit messages in the embed channel")
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"An error occurred while updating the embed: {str(e)}")
        else:
            if config.DEBUG_MODE:
                print(f"Embed channel with ID {embed_channel_id} not found")

    def get_price_data(self):
        conn = sqlite3.connect('spacemesh_data.db')
        cursor = conn.cursor()
        twelve_hours_ago = (datetime.now() - timedelta(hours=12)).isoformat()
        cursor.execute("SELECT timestamp, value FROM spacemesh_data WHERE data_type = 'price' AND timestamp > ? ORDER BY timestamp", (twelve_hours_ago,))
        data = cursor.fetchall()
        conn.close()
        return data

    def generate_graph(self, price_data):
        if not price_data:
            return "No price data available"

        # Normalize the data to fit in the graph
        prices = [price for _, price in price_data]
        min_price, max_price = min(prices), max(prices)
        normalized_prices = [int((price - min_price) / (max_price - min_price) * 5) for price in prices]

        # Generate the graph
        graph = [" " * 40 for _ in range(6)]
        for i, height in enumerate(normalized_prices):
            for j in range(height + 1):
                graph[5 - j] = graph[5 - j][:i] + "│" + graph[5 - j][i+1:]

        # Add price labels
        graph = [f"${price:.2f} │" + line for price, line in zip(reversed(prices[:6]), graph)]

        # Add time labels
        time_labels = ["Now", "3h", "6h", "9h", "12h"]
        graph.append("      " + "─" * 40)
        graph.append("      " + "   ".join(time_labels).center(40))

        return "\n".join(graph)

    def calculate_trend(self, price_data):
        if len(price_data) < 2:
            return "N/A"

        start_price = price_data[0][1]
        end_price = price_data[-1][1]
        percent_change = ((end_price - start_price) / start_price) * 100

        if percent_change > 0:
            return f"↑ {abs(percent_change):.2f}%"
        elif percent_change < 0:
            return f"↓ {abs(percent_change):.2f}%"
        else:
            return "→ 0.00%"

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
        remaining_value = data['remainingVaulted'] * data['price']
        return (f"• Total VC Coins Vested: {data['vested']:.2f}M SMH\n"
                f"• Value of Vested Coins: ${vested_value:.2f}M\n"
                f"• VC Coins to be Vested: {data['remainingVaulted']:.2f}M SMH\n"
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