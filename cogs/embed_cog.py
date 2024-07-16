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
        await self.wait_for_initial_data()
        self.update_embed.start()

    def cog_unload(self):
        self.update_embed.cancel()
        self.save_embed_id()

    async def wait_for_initial_data(self):
        api_cog = self.bot.get_cog('APICog')
        if api_cog:
            logging.info("Waiting for initial API data...")
            await api_cog.initial_data_fetched.wait()
            logging.info("Initial API data received.")
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
        
        files = []
        
        if api_cog and api_cog.current_data:
            logging.info("Generating embed with current data")
            embed.add_field(name="Price", value=f"${api_cog.current_data['price']:.2f}", inline=True)
            embed.add_field(name="Layer", value=str(api_cog.current_data['layer']), inline=True)
            embed.add_field(name="Epoch", value=str(api_cog.current_data['epoch']), inline=True)
            
            # Circulating supply in millions of SMH
            circulating_supply_smh = api_cog.current_data['circulatingSupply'] / 1e9  # Convert smidge to SMH
            circulating_supply_m = circulating_supply_smh / 1e6  # Convert to millions
            embed.add_field(name="Circulating Supply", value=f"{circulating_supply_m:.2f}M SMH", inline=True)
            
            # Market cap in millions of dollars
            price = api_cog.current_data['price']
            market_cap = (price * circulating_supply_smh) / 1e6  # Convert to millions
            embed.add_field(name="Market Cap", value=f"${market_cap:.2f}M", inline=True)
            
            # Network size in EiB
            network_size_gib = api_cog.current_data['effectiveUnitsCommited'] * 64  # Convert units to GiB
            network_size_eib = network_size_gib / (1024 * 1024)  # Convert GiB to EiB
            embed.add_field(name="Network Size", value=f"{network_size_eib:.2f} EiB", inline=True)
            
            embed.add_field(name="Active Smeshers", value=f"{api_cog.current_data['totalActiveSmeshers']:,}", inline=True)
            percent_total_supply = (api_cog.current_data['circulatingSupply'] / 15_000_000_000_000_000) * 100
            embed.add_field(name="% of Total Supply", value=f"{percent_total_supply:.2f}%", inline=True)
            
            if graph_cog:
                price_result = graph_cog.get_price_graph()
                if isinstance(price_result, tuple):
                    price_file, price_trend = price_result
                    embed.add_field(name="Price Graph", value=price_trend, inline=False)
                    files.append(price_file)
                else:
                    embed.add_field(name="Price Graph", value=price_result, inline=False)
        else:
            logging.warning("Unable to fetch current data for embed")
            embed.add_field(name="Error", value="Unable to fetch current data", inline=False)
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return embed, files

    async def create_or_update_embed(self):
        channel = self.bot.get_channel(self.embed_channel_id)
        if not channel:
            logging.error(f"Couldn't find channel with ID {self.embed_channel_id}")
            return

        api_cog = self.bot.get_cog('APICog')
        if not api_cog or not api_cog.current_data:
            logging.warning("API data not available, skipping embed update")
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

            self.save_embed_id()
            logging.info("Embed updated successfully")

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