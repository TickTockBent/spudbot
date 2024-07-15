import discord
import logging
from discord.ext import commands
import time

class DisplayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_update_time = 0

    @commands.Cog.listener()
    async def on_price_update(self, price_data):
        logging.info(f"Received price update: {price_data}")
        await self.update_price_channel(price_data)

    @commands.Cog.listener()
    async def on_layer_update(self, layer_data):
        logging.info(f"Received layer update: {layer_data}")
        await self.update_channel('layer', layer_data)

    @commands.Cog.listener()
    async def on_epoch_update(self, epoch_data):
        logging.info(f"Received epoch update: {epoch_data}")
        await self.update_channel('epoch', epoch_data)

    @commands.Cog.listener()
    async def on_circulating_supply_update(self, circulating_supply_data):
        logging.info(f"Received circulating supply update: {circulating_supply_data}")
        await self.update_channel('circulatingsupply', f"Circ. Supply: {circulating_supply_data}")

    @commands.Cog.listener()
    async def on_netspace_update(self, netspace_data):
        logging.info(f"Received netspace update: {netspace_data}")
        await self.update_channel('networksize', netspace_data)

    @commands.Cog.listener()
    async def on_market_cap_update(self, market_cap_data):
        logging.info(f"Received market cap update: {market_cap_data}")
        await self.update_channel('marketcap', market_cap_data)

    @commands.Cog.listener()
    async def on_percent_total_supply_update(self, percent_total_supply_data):
        logging.info(f"Received percent of total supply update: {percent_total_supply_data}")
        await self.update_channel('percenttotalsupply', percent_total_supply_data)

    @commands.Cog.listener()
    async def on_active_smeshers_update(self, active_smeshers_data):
        logging.info(f"Received active smeshers update: {active_smeshers_data}")
        await self.update_channel('activesmeshers', active_smeshers_data)

async def update_channel(self, channel_type, new_name):
    current_time = time.time()
    if current_time - self.last_update_time < 600:  # 10 minutes cooldown
        logging.info("Skipping update due to cooldown")
        return

    channel_id = self.bot.config['CHANNEL_IDS'][channel_type]
    channel = self.bot.get_channel(channel_id)
    
    if channel:
        try:
            # Check if the current name is different from the new name
            if channel.name != new_name:
                await channel.edit(name=new_name)
                self.last_update_time = current_time
                logging.info(f"Successfully updated {channel_type} channel name to: {new_name}")
            else:
                logging.info(f"Skipping update for {channel_type}, no change detected")
        except discord.errors.Forbidden:
            logging.error(f"Bot doesn't have permission to edit channel {channel.id}")
        except discord.errors.HTTPException as e:
            logging.error(f"Failed to update channel name: {e}")
    else:
        logging.error(f"Couldn't find channel with ID {channel_id}")

    async def update_price_channel(self, price_data):
        new_name = f"Price: {price_data['formatted_price']} {price_data['trend']}"
        await self.update_channel('price', new_name)

async def setup(bot):
    await bot.add_cog(DisplayCog(bot))