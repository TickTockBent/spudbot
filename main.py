import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot initialization
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
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
    
    # Sync slash commands
    print("Syncing slash commands...")
    await bot.tree.sync()
    print("Slash commands synced successfully!")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for application commands."""
    if isinstance(error, app_commands.CommandNotFound):
        await interaction.response.send_message("Command not found. Use /help to see available commands.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)

async def update_channels():
    """Update Discord channel names with current data."""
    # TODO: Implement channel update logic

async def update_embed():
    """Update the embedded message with current statistics."""
    # TODO: Implement embed update logic

async def schedule_events():
    """Schedule Discord events for Poet cycles and cycle gaps."""
    # TODO: Implement event scheduling logic

@bot.tree.command(name="ping", description="Check if the bot is responsive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! The bot is responsive.", ephemeral=True)

def main():
    """Main function to run the bot."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("No token found. Make sure DISCORD_TOKEN is set in your .env file.")
    bot.run(token)

if __name__ == "__main__":
    main()