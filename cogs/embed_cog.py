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

    # ... (rest of the methods remain the same)

    @update_embed.before_loop
    async def before_update_embed(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("EmbedCog is ready and will start updating the embed.")

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
    if config.DEBUG_MODE:
        print("EmbedCog has been loaded.")