import discord
import logging
from discord.ext import commands
import time

class DisplayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_update_time = {}

    @commands.Cog.listener()
    async def on_data_update(self, data_type, processed_data):
        logging.info(f"Received data update for {data_type}: {processed_data}")
        await self.update_channel(data_type, processed_data)

    async def update_channel(self, channel_type, new_data):
        current_time = time.time()
        if channel_type in self.last_update_time and current_time - self.last_update_time[channel_type] < 600:  # 10 minutes cooldown
            logging.info(f"Skipping update for {channel_type} due to cooldown")
            return

        channel_id = self.bot.config['CHANNEL_IDS'].get(channel_type)
        if not channel_id:
            logging.error(f"No channel ID found for {channel_type}")
            return

        channel = self.bot.get_channel(channel_id)
        
        if channel:
            new_name = f"{channel_type.capitalize()}: {new_data}"
            try:
                if channel.name != new_name:
                    await channel.edit(name=new_name)
                    self.last_update_time[channel_type] = current_time
                    logging.info(f"Successfully updated {channel_type} channel name to: {new_name}")
                else:
                    logging.info(f"Skipping update for {channel_type}, no change detected")
            except discord.errors.Forbidden:
                logging.error(f"Bot doesn't have permission to edit channel {channel.id}")
            except discord.errors.HTTPException as e:
                logging.error(f"Failed to update channel name: {e}")
        else:
            logging.error(f"Couldn't find channel with ID {channel_id}")

async def setup(bot):
    await bot.add_cog(DisplayCog(bot))