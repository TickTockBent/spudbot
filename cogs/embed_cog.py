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
        self.load_message_id()

    async def cog_load(self):
        await self.wait_for_initial_data()
        self.update_embed.start()

    def cog_unload(self):
        self.update_embed.cancel()
        self.save_message_id()

    async def wait_for_initial_data(self):
        data_cog = self.bot.get_cog('DataCog')
        if data_cog:
            await data_cog.initial_data_collected.wait()
        else:
            logging.error("DataCog not found")

    def load_message_id(self):
        try:
            with open('embed_data.json', 'r') as f:
                data = json.load(f)
                self.embed_message_id = data.get('message_id')
        except FileNotFoundError:
            self.embed_message_id = None

    def save_message_id(self):
        with open('embed_data.json', 'w') as f:
            json.dump({'message_id': self.embed_message_id}, f)

    def generate_embed(self):
        embed = discord.Embed(title="Spacemesh Network Stats", color=0x00ff00)
        
        api_cog = self.bot.get_cog('APICog')
        graph_cog = self.bot.get_cog('GraphCog')
        
        files = []
        
        if api_cog and api_cog.current_data:
            embed.add_field(name="Price", value=f"${api_cog.current_data['price']:.2f}", inline=True)
            embed.add_field(name="Layer", value=str(api_cog.current_data['layer']), inline=True)
            embed.add_field(name="Epoch", value=str(api_cog.current_data['epoch']), inline=True)
            
            if graph_cog:
                price_result = graph_cog.get_price_graph()
                if isinstance(price_result, tuple):
                    price_file, price_trend = price_result
                    embed.add_field(name="Price Graph", value=price_trend, inline=False)
                    files.append(price_file)
                else:
                    embed.add_field(name="Price Graph", value=price_result, inline=False)

                netspace_result = graph_cog.get_netspace_graph()
                if isinstance(netspace_result, tuple):
                    netspace_file, netspace_change = netspace_result
                    embed.add_field(name="Netspace Graph", value=netspace_change, inline=False)
                    files.append(netspace_file)
                else:
                    embed.add_field(name="Netspace Graph", value=netspace_result, inline=False)
        else:
            embed.add_field(name="Error", value="Unable to fetch current data", inline=False)
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return embed, files

    async def create_or_update_embed(self):
        channel = self.bot.get_channel(self.embed_channel_id)
        if not channel:
            logging.error(f"Couldn't find channel with ID {self.embed_channel_id}")
            return

        embed, files = self.generate_embed()

        try:
            if self.embed_message_id:
                try:
                    message = await channel.fetch_message(self.embed_message_id)
                    await message.edit(embed=embed)
                    await message.remove_attachments(*message.attachments)
                    if files:
                        await message.add_files(*files)
                except discord.errors.NotFound:
                    message = await channel.send(embed=embed, files=files)
                    self.embed_message_id = message.id
            else:
                message = await channel.send(embed=embed, files=files)
                self.embed_message_id = message.id

            self.save_message_id()

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