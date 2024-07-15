import discord
from discord.ext import commands, tasks
import json
import os

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_channel_id = self.bot.config['EMBED_CHANNEL_ID']
        self.embed_message_id = None
        self.load_message_id()
        self.update_embed.start()

    def cog_unload(self):
        self.update_embed.cancel()

    def load_message_id(self):
        try:
            with open('embed_message_id.json', 'r') as f:
                data = json.load(f)
                self.embed_message_id = data.get('message_id')
        except FileNotFoundError:
            self.embed_message_id = None

    def save_message_id(self):
        with open('embed_message_id.json', 'w') as f:
            json.dump({'message_id': self.embed_message_id}, f)

    def generate_embed(self):
        embed = discord.Embed(title="Spacemesh Network Stats", color=0x00ff00)
        
        # TODO: Add fields for each stat
        embed.add_field(name="Price", value=f"${self.bot.get_cog('APICog').current_data['price']:.2f}", inline=True)
        embed.add_field(name="Layer", value=str(self.bot.get_cog('APICog').current_data['layer']), inline=True)
        embed.add_field(name="Epoch", value=str(self.bot.get_cog('APICog').current_data['epoch']), inline=True)
        
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return embed

    async def create_or_update_embed(self):
        channel = self.bot.get_channel(self.embed_channel_id)
        if not channel:
            print(f"Couldn't find channel with ID {self.embed_channel_id}")
            return

        embed = self.generate_embed()

        try:
            if self.embed_message_id:
                message = await channel.fetch_message(self.embed_message_id)
                await message.edit(embed=embed)
            else:
                message = await channel.send(embed=embed)
                self.embed_message_id = message.id
                self.save_message_id()
        except discord.errors.NotFound:
            message = await channel.send(embed=embed)
            self.embed_message_id = message.id
            self.save_message_id()
        except discord.errors.Forbidden:
            print(f"Bot doesn't have permission to send/edit messages in channel {self.embed_channel_id}")
        except discord.errors.HTTPException as e:
            print(f"Failed to send/edit message: {e}")

    @tasks.loop(minutes=5)
    async def update_embed(self):
        await self.create_or_update_embed()

    @update_embed.before_loop
    async def before_update_embed(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))