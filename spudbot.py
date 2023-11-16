import discord
import requests
import configparser
import json
from discord import Intents

# Read configuration file
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['DEFAULT']['Token']
CHANNEL_NAME = config['DEFAULT']['ChannelName']
API_ENDPOINT = config['DEFAULT']['APIEndpoint']
WAIT_TIME = int(config['DEFAULT']['WaitTime'])
TEST_MODE = config.getboolean('DEFAULT', 'TestMode')

# Define intents
intents = Intents.default()
intents.messages = True
intents.guilds = True

# Discord client with intents
client = discord.Client(intents=intents)

async def fetch_api_data():
    try:
        # Make an API request
        response = requests.get(API_ENDPOINT)
        if response.status_code == 200:
            data = response.json()

            # Display all variables
            print(json.dumps(data, indent=4))

            if TEST_MODE:
                # Exit if in test mode
                await client.close()
                return

            # Create a message string (only if not in test mode)
            message = '\n'.join([f"{key}: {value}" for key, value in data.items()])

            # Find a specific channel to send the message to
            for channel in client.get_all_channels():
                if channel.name == CHANNEL_NAME:
                    await channel.send(message)

        else:
            print("Failed to fetch API data.")

    except Exception as e:
        print(f"An error occurred: {e}")

    if not TEST_MODE:
        # Wait for the specified time before making the next API call
        await asyncio.sleep(WAIT_TIME)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(fetch_api_data())

# Run the bot
client.run(TOKEN)
