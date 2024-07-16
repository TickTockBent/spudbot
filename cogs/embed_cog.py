import discord
from discord.ext import commands, tasks
import logging
import json
import os
import asyncio

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_channel_id = self.bot.config['CHANNEL_IDS'].get('embed')
        if not self.embed_channel_id:
            logging.error("Embed channel ID is not set in the config CHANNEL_IDS")
            return
        self.embed_message_id = None
        self.load_embed_id()
        self.current_data = {}
        self.api_cog_ready = asyncio.Event()

    async def cog_load(self):
        self.bot.loop.create_task(self.wait_for_api_cog())
        self.update_embed.start()

    def cog_unload(self):
        self.update_embed.cancel()
        self.save_embed_id()

    async def wait_for_api_cog(self):
        while True:
            api_cog = self.bot.get_cog('APICog')
            if api_cog:
                logging.info("APICog found, waiting for initial data...")
                await api_cog.initial_data_fetched.wait()
                self.api_cog_ready.set()
                logging.info("Initial API data received.")
                break
            await asyncio.sleep(1)

    def load_embed_id(self):
        try:
            with open('embed_data.json', 'r') as f:
                data = json.load(f)
                self.embed_message_id = data.get('message_id')
        except FileNotFoundError:
            self.embed_message_id = None

    def save_embed_id(self):
        with open('embed_data.json', 'w') as f:
            json.dump({'message_id': self.embed_message_id}, f)

    def generate_embed(self):
        embed = discord.Embed(title="Spacemesh Network Stats", color=0x00ff00)
        
        for field, value in self.current_data.items():
            embed.add_field(name=field.capitalize(), value=value, inline=True)
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return embed

    @commands.Cog.listener()
    async def on_data_update(self, data_type, processed_data):
        self.current_data[data_type] = processed_data

    async def create_or_update_embed(self):
        channel = self.bot.get_channel(self.embed_channel_id)
        if not channel:
            logging.error(f"Couldn't find channel with ID {self.embed_channel_id}")
            return

        embed = self.generate_embed()

        try:
            if self.embed_message_id:
                try:
                    message = await channel.fetch_message(self.embed_message_id)
                    await message.edit(embed=embed)
                except discord.errors.NotFound:
                    message = await channel.send(embed=embed)
                    self.embed_message_id = message.id
            else:
                message = await channel.send(embed=embed)
                self.embed_message_id = message.id

            self.save_embed_id()
            logging.info("Embed updated successfully")

        except discord.errors.Forbidden:
            logging.error(f"Bot doesn't have permission to send/edit messages in channel {self.embed_channel_id}")
        except discord.errors.HTTPException as e:
            logging.error(f"Failed to send/edit message: {e}")

    @tasks.loop(seconds=300)  # 5 minutes, adjust as needed
    async def update_embed(self):
        await self.create_or_update_embed()

    @update_embed.before_loop
    async def before_update_embed(self):
        await self.bot.wait_until_ready()
        await self.api_cog_ready.wait()

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))