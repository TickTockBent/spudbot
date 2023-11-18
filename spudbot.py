import discord
import requests
import configparser
import json
import asyncio
import signal
from datetime import datetime
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
last_good_price = None
trading_stats_channel_id = int(config['CHANNELS'['TradingStatsCategoryID'])
network_stats_channel_id = int(config['CHANNELS'['NetworkStatsCategoryID'])

# Define intents
intents = Intents.default()
intents.messages = True
intents.guilds = True

# Discord client with intents
client = discord.Client(intents=intents)

async def fetch_api_data():
    global last_good_price
    while not client.is_closed():
        try:
            price_message = "No price data."
            price = "No price data available."
            # Make an API request
            print("Spudbot fetching API data...")
            response = requests.get(API_ENDPOINT)
            if response.status_code == 200:
                print("API fetch successful!")
                data = response.json()
                print("Calculating...")
                price = data.get('price')
                if price != -1:
                    # Update the last good price
                    last_good_price = round(data['price'], 2)
                    price_message = f"Price: ${last_good_price}"
                    print("Price found: $"+str(price_message))
                elif last_good_price is not None:
                    # Use the last good price with an indication of being outdated
                    price_message = f"Price: ${last_good_price} (outdated)"
                    print("Price API offline. Using old price: $"+str(price_message))
                next_epoch_data = data['nextEpoch']
                # Extract circulatingSupply and divide by 1 billion
                circulating_supply = "{:,}".format(round(data['circulatingSupply'] / 1_000_000_000)) #divide by 1 billion and round so we report SMH not smidge
                print("Circulating supply found: "+str(circulating_supply)+" SMH")
                market_cap = "{:,}".format(round(data['marketCap'] / 1_000_000_000)) #divide by 1 billion and round so we report SMH not smidge
                print("Market Cap found: $"+str(market_cap))
                # Extract effectiveUnitsCommited and multiply by 64
                effective_units_commited = "{:,}".format(round(data['effectiveUnitsCommited'] * 64 / 1024))
                print("Network size computed: "+str(effective_units_commited)+" TiB")
                next_epoch_units_commited = "{:,}".format(round(next_epoch_data['effectiveUnitsCommited'] * 64 / 1024))
                print("The next epoch will have: "+str(next_epoch_units_commited)+" TiB")
                curr_epoch = data['epoch']
                print("Epoch: "+str(curr_epoch))
                next_epoch = next_epoch_data['epoch']
                print("Next Epoch: "+str(next_epoch))
                curr_layer = "{:,}".format(data['layer'])
                print("Current layer: "+str(curr_layer))
                active_smeshers = "{:,}".format(data['totalActiveSmeshers'])
                print("Total active smeshers: "+str(active_smeshers))
                next_epoch_active_smeshers = "{:,}".format(round(next_epoch_data['totalActiveSmeshers']))
                print("The next epoch will have "+str(next_epoch_active_smeshers)+" active smeshers.")

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
                    print ("Total Network Size: " + str(effective_units_commited) + "TiB")
                    print ("Active Smeshers: " + str(active_smeshers))
                    # Exit if in test mode
                    await client.close()
                    return

                # Create a message string (only if not in test mode)
                # message = '\n'.join([f"{key}: {value}" for key, value in data.items()])
                current_time = datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                print ("Channel updates starting at: ", formatted_time)
                await client.get_channel(price_channel_id).edit(name=f"{price_message}")
                print ("...Price updated...")
                await client.get_channel(circulating_supply_channel_id).edit(name=f"C.Supply: {circulating_supply} SMH")
                print ("...Circulating Supply updated...")
                await client.get_channel(market_cap_channel_id).edit(name=f"M.Cap: ${market_cap}")
                print ("...Market Cap updated...")
                await client.get_channel(epoch_channel_id).edit(name=f"Epoch: {curr_epoch}")
                print ("...Current epoch updated...")
                await client.get_channel(layer_channel_id).edit(name=f"Layer: {curr_layer}")
                print ("...Current layer updated...")
                await client.get_channel(network_size_channel_id).edit(name=f"Network Size: {effective_units_commited} TiB")
                print ("...Network size updated...")
                await client.get_channel(active_smeshers_channel_id).edit(name=f"Active Smeshers: {active_smeshers}")
                print ("...Active smeshers updated...")
                current_time = datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                print ("...Channel updates completed at: ", formatted_time)

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
    print ("***********************")
    print ("**SPUDBOT 9000 ONLINE**")
    print ("***********************")
    print ("***Prod Mode Enabled***")
    print ("***********************")
    print ("Finding category...")
    # Find the category by ID
    new_category_name = "Trading Stats (Online)"
    category = discord.utils.get(client.get_all_channels(), id=trading_stats_channel_id)
    print ("Checking category...")
    # Check if the category is found and is indeed a category channel
    if category and isinstance(category, discord.CategoryChannel):
        # Rename the category
        await category.edit(name=new_category_name)
        print(f"Category renamed to: {new_category_name}")
    else:
        print("Category not found or not a category channel")
    client.loop.create_task(fetch_api_data())

async def shutdown_signal():
    new_category_name = "Trading Stats (Offline)"
    print(f"Shutting down... :(")
    print(f"Category renamed to: {new_category_name}")
    category = discord.utils.get(client.get_all_channels(), id=trading_stats_channel_id)
    if category:
        await category.edit(name=new_category_name)
    await client.close()

# Signal handler
def handle_shutdown_signal(*args):
    asyncio.create_task(shutdown_signal())

signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

# Run the bot
client.run(TOKEN)
