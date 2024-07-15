import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import logging
import config  # Import the entire config module

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Attach config to bot
bot.config = {
    'API_ENDPOINT': config.API_ENDPOINT,
    'INTERVAL': config.INTERVAL,
    'CHANNEL_IDS': config.CHANNEL_IDS
}

# Remove the default help command
bot.remove_command('help')

@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user}')
    await load_cogs()
    await bot.tree.sync()  # Sync slash commands

# Load cogs
initial_cogs = [
    'cogs.api_cog',
    'cogs.display_cog',
    'cogs.general_cog',
    'cogs.embed_cog',
    'cogs.graph_cog',
    'cogs.data_cog'
]

async def load_cogs():
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            logging.info(f'Loaded cog: {cog}')
        except Exception as e:
            logging.error(f'Failed to load cog {cog}: {str(e)}')

# Run the bot
if __name__ == "__main__":
    asyncio.run(bot.start(config.BOT_TOKEN))