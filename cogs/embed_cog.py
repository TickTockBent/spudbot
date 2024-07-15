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

    async def cog_load(self):
        await self.wait_for_api_data()
        self.update_embed.start()

    def cog_unload(self):
        self.update_embed.cancel()
        self.save_embed_id()

    async def wait_for_api_data(self):
        api_cog = self.bot.get_cog('APICog')
        if api_cog:
            await api_cog.initial_data_fetched.wait()
        else:
            logging.error("APICog not found")

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
        
        api_cog = self.bot.get_cog('APICog')
        graph_cog = self.bot.get_cog('GraphCog')
        
        if api_cog and api_cog.current_data:
            embed.add_field(name="Price", value=f"${api_cog.current_data['price']:.2f}", inline=True)
            embed.add_field(name="Layer", value=str(api_cog.current_data['layer']), inline=True)
            embed.add_field(name="Epoch", value=str(api_cog.current_data['epoch']), inline=True)
            
            if graph_cog:
                embed.add_field(name="Price Graph", value=graph_cog.get_price_graph(), inline=False)
                embed.add_field(name="Netspace Graph", value=graph_cog.get_netspace_graph(), inline=False)
        else:
            embed.add_field(name="Error", value="Unable to fetch current data", inline=False)
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return embed

    async def find_existing_embed(self, channel):
        async for message in channel.history(limit=100):
            if message.author == self.bot.user and message.embeds:
                return message
        return None

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
                except discord.errors.NotFound:
                    message = await self.find_existing_embed(channel)
            else:
                message = await self.find_existing_embed(channel)

            if message:
                await message.edit(embed=embed)
                self.embed_message_id = message.id
            else:
                message = await channel.send(embed=embed)
                self.embed_message_id = message.id

            self.save_embed_id()

        except discord.errors.Forbidden:
            logging.error(f"Bot doesn't have permission to send/edit messages in channel {self.embed_channel_id}")
        except discord.errors.HTTPException as e:
            logging.error(f"Failed to send/edit message: {e}")

    @tasks.loop(minutes=5)
    async def update_embed(self):
        await self.create_or_update_embed()

    @update_embed.before_loop
    async def before_update_embed(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))