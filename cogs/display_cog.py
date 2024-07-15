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

    async def update_price_channel(self, price_data):
        current_time = time.time()
        if current_time - self.last_update_time < 600:  # 10 minutes cooldown
            logging.info("Skipping update due to cooldown")
            return

        new_name = f"Price: {price_data['formatted_price']} {price_data['trend']}"
        logging.info(f"Attempting to update channel name to: {new_name}")

        price_channel_id = self.bot.config['CHANNEL_IDS']['price']
        channel = self.bot.get_channel(price_channel_id)
        
        if channel:
            try:
                await channel.edit(name=new_name)
                self.last_update_time = current_time
                logging.info(f"Successfully updated channel name to: {new_name}")
            except discord.errors.Forbidden:
                logging.error(f"Bot doesn't have permission to edit channel {channel.id}")
            except discord.errors.HTTPException as e:
                logging.error(f"Failed to update channel name: {e}")
        else:
            logging.error(f"Couldn't find channel with ID {price_channel_id}")

async def setup(bot):
    await bot.add_cog(DisplayCog(bot))