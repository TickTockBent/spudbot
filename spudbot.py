import discord
import requests
import configparser
import json
import asyncio
from discord import Intents

# Read configuration file
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['DEFAULT']['Token']
API_ENDPOINT = config['DEFAULT']['APIEndpoint']
WAIT_TIME = int(config['DEFAULT']['WaitTime'])
TEST_MODE = config.getboolean('DEFAULT', 'TestMode')
price_channel_id = int(config['CHANNELS']['PriceChannelID'])
circulating_supply_channel_id = int(config['CHANNELS']['CirculatingSupplyChannelID'])
market_cap_channel_id = int(config['CHANNELS']['MarketCapChannelID'])
epoch_channel_id = int(config['CHANNELS']['EpochChannelID'])
layer_channel_id = int(config['CHANNELS']['LayerChannelID'])
network_size_channel_id = int(config['CHANNELS']['NetworkSizeChannelID'])
active_smeshers_channel_id = int(config['CHANNELS']['ActiveSmeshersChannelID'])

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

            # Extract and round the price
            price = round(data['price'], 2)  # Rounds the price to two decimal places
            # Extract circulatingSupply and divide by 1 billion
            circulating_supply = "{:,}".format(round(data['circulatingSupply'] / 1_000_000_000)) #divide by 1 billion and round so we report SMH not smidge
            market_cap = "{:,}".format(round(data['marketCap'] / 1_000_000_000)) #divide by 1 billion and round so we report SMH not smidge
            # Extract effectiveUnitsCommited and multiply by 64
            effective_units_commited = "{:,}".format(round(data['effectiveUnitsCommited'] * 64 / 1000))
            curr_epoch = data['epoch']
            curr_layer = "{:,}".format(data['layer'])
            active_smeshers = "{:,}".format(data['totalActiveSmeshers'])

            if TEST_MODE:
                # Display test mode output variables
                print ("***********************")
                print ("**SPUDBOT 9000 ONLINE**")
                print ("***********************")
                print ("***Test Mode Enabled***")
                print ("***********************")
                print ("Raw API output: ")
                print(json.dumps(data, indent=4))
                print ("Primary Stats: ")
                print ("Price = $" + str(price))
                print ("Circulating Supply = " + str(circulating_supply) + " SMH")
                print ("Market Cap = $" + str(market_cap))
                print ("Nerd Stats:")
                print ("Current Epoch: " + str(curr_epoch))
                print ("Current Layer: " + str(curr_layer))
                print ("Total Network Size: " + str(effective_units_commited) + "GB")
                print ("Active Smeshers: " + str(active_smeshers))
                # Exit if in test mode
                await client.close()
                return

            # Create a message string (only if not in test mode)
            message = '\n'.join([f"{key}: {value}" for key, value in data.items()])
            await client.get_channel(price_channel_id).edit(name=f"Price: ${price}")
            await client.get_channel(circulating_supply_channel_id).edit(name=f"C.Supply: {circulating_supply} SMH")
            await client.get_channel(market_cap_channel_id).edit(name=f"M.Cap: ${market_cap}")
            await client.get_channel(epoch_channel_id).edit(name=f"Epoch: {curr_epoch}")
            await client.get_channel(layer_channel_id).edit(name=f"Layer: {curr_layer}")
            await client.get_channel(network_size_channel_id).edit(name=f"Network Size: {effective_units_commited}PiB")
            await client.get_channel(active_smeshers_channel_id).edit(name=f"Active Smeshers: {active_smeshers}")

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
