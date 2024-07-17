import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot initialization
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_cogs():
    """Load all cogs from the cogs directory."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    """Event listener for when the bot is ready and connected."""
    print(f'{bot.user} has connected to Discord!')
    await load_cogs()

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for bot commands."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use !help to see available commands.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

async def update_channels():
    """Update Discord channel names with current data."""
    # TODO: Implement channel update logic

async def update_embed():
    """Update the embedded message with current statistics."""
    # TODO: Implement embed update logic

async def schedule_events():
    """Schedule Discord events for Poet cycles and cycle gaps."""
    # TODO: Implement event scheduling logic

def main():
    """Main function to run the bot."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("No token found. Make sure DISCORD_TOKEN is set in your .env file.")
    bot.run(token)

if __name__ == "__main__":
    main()