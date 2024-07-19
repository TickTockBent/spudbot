import discord
from discord.ext import commands, tasks
import config
import asyncio

class ChannelUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_channels.start()

    def cog_unload(self):
        self.update_channels.cancel()

    @tasks.loop(minutes=5)
    async def update_channels(self):
        if config.DEBUG_MODE:
            print("Starting channel update process")

        data_cog = self.bot.get_cog('DataCog')
        if not data_cog:
            if config.DEBUG_MODE:
                print("DataCog not found. Unable to update channels.")
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
                print("No processed data available after waiting. Skipping channel update.")
            return

        if config.DEBUG_MODE:
            print("Processed data received:")
            for key, value in processed_data.items():
                print(f"  {key}: {value}")

        for channel_name, channel_id in config.CHANNEL_IDS.items():
            # Skip the embed channel
            if channel_name == 'embed':
                if config.DEBUG_MODE:
                    print(f"Skipping update for embed channel (ID: {channel_id})")
                continue

            channel = self.bot.get_channel(channel_id)
            if not channel:
                if config.DEBUG_MODE:
                    print(f"Channel with ID {channel_id} not found.")
                continue

            new_name = self.format_channel_name(channel_name, processed_data)
            if config.DEBUG_MODE:
                print(f"Checking channel {channel_name}:")
                print(f"  Current name: {channel.name}")
                print(f"  New name: {new_name}")

            if new_name != channel.name:
                if config.DEBUG_MODE:
                    print(f"  Updating channel name...")
                try:
                    await channel.edit(name=new_name)
                    if config.DEBUG_MODE:
                        print(f"  Successfully updated channel {channel_name} to: {new_name}")
                except discord.errors.Forbidden:
                    if config.DEBUG_MODE:
                        print(f"  No permission to update channel {channel_name}")
                except discord.errors.HTTPException as e:
                    if config.DEBUG_MODE:
                        print(f"  Failed to update channel {channel_name}: {str(e)}")
            else:
                if config.DEBUG_MODE:
                    print(f"  Channel name is already up to date. Skipping update.")

    def format_channel_name(self, channel_name, data):
        if channel_name == 'price':
            return f"Price: ${data['price']}"
        elif channel_name == 'circulatingsupply':
            return f"Circ. Supply: {data['circulatingSupply']}M SMH"
        elif channel_name == 'marketcap':
            return f"Marketcap: ${data['marketCap']}M"
        elif channel_name == 'epoch':
            return f"Epoch: {data['epoch']}"
        elif channel_name == 'layer':
            return f"Layer: {data['layer']}"
        elif channel_name == 'networksize':
            return f"Netspace: {data['effectiveUnitsCommited']}EiB"
        elif channel_name == 'percenttotalsupply':
            return f"% Total Supply: {data['percentTotalSupply']}%"
        else:
            return channel_name

    @update_channels.before_loop
    async def before_update_channels(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("ChannelUpdateCog is ready and will start updating channels.")

async def setup(bot):
    await bot.add_cog(ChannelUpdateCog(bot))
    if config.DEBUG_MODE:
        print("ChannelUpdateCog has been loaded.")