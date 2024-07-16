import discord
from discord.ext import commands, tasks
import logging

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_channel_id = self.bot.config['CHANNEL_IDS'].get('embed')
        if not self.embed_channel_id:
            logging.error("Embed channel ID is not set in the config CHANNEL_IDS")
            return
        self.embed_message_id = None
        self.update_embed.start()

    async def generate_embed(self):
        embed = discord.Embed(title="Spacemesh Network Stats", color=0x00ff00)
        
        api_cog = self.bot.get_cog('APICog')
        graph_cog = self.bot.get_cog('GraphCog')
        
        if api_cog and api_cog.current_data:
            embed.add_field(name="Price", value=f"${api_cog.current_data['price']:.2f}", inline=True)
            embed.add_field(name="Layer", value=str(api_cog.current_data['layer']), inline=True)
            embed.add_field(name="Epoch", value=str(api_cog.current_data['epoch']), inline=True)
            
            if graph_cog:
                price_file, price_trend = await graph_cog.get_price_graph()
                netspace_file, netspace_change = await graph_cog.get_netspace_graph()
                
                embed.add_field(name="Price Graph", value=price_trend, inline=False)
                embed.set_image(url="attachment://price_graph.png")
                
                embed.add_field(name="Netspace Graph", value=netspace_change, inline=False)
                # Note: Discord embeds can only have one image, so we'll add the netspace graph as a separate message
        else:
            embed.add_field(name="Error", value="Unable to fetch current data", inline=False)
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return embed, price_file, netspace_file

    async def create_or_update_embed(self):
        channel = self.bot.get_channel(self.embed_channel_id)
        if not channel:
            logging.error(f"Couldn't find channel with ID {self.embed_channel_id}")
            return

        embed, price_file, netspace_file = await self.generate_embed()

        try:
            if self.embed_message_id:
                try:
                    message = await channel.fetch_message(self.embed_message_id)
                    await message.edit(embed=embed)
                    await message.remove_attachments(message.attachments)
                    await message.add_files(price_file)
                    await channel.send(file=netspace_file)
                except discord.errors.NotFound:
                    message = await channel.send(embed=embed, file=price_file)
                    await channel.send(file=netspace_file)
                    self.embed_message_id = message.id
            else:
                message = await channel.send(embed=embed, file=price_file)
                await channel.send(file=netspace_file)
                self.embed_message_id = message.id

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