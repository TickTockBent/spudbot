import asyncio
import discord
from discord.ext import commands
import logging
from config import BOT_TOKEN

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs
initial_cogs = [
    'cogs.api_cog',
    'cogs.display_cog'
]

async def load_cogs():
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            logging.info(f'Loaded cog: {cog}')
        except Exception as e:
            logging.error(f'Failed to load cog {cog}: {str(e)}')

@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user}')
    await load_cogs()

# Run the bot
if __name__ == "__main__":
    asyncio.run(bot.start(BOT_TOKEN))