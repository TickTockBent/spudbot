import discord
import requests
from api_handler import APIHandler
from config_handler import ConfigHandler
import json
import asyncio
import signal
from datetime import datetime
from discord import Intents

# Read Confighandler vals
config_handler = ConfigHandler()
price_channel_id = config_handler.get_channel_id('PriceChannelID')
circulating_supply_channel_id = config_handler.get_channel_id('CirculatingSupplyChannelID')
market_cap_channel_id = config_handler.get_channel_id('MarketCapChannelID')
epoch_channel_id = config_handler.get_channel_id('EpochChannelID')
layer_channel_id = config_handler.get_channel_id('LayerChannelID')
network_size_channel_id = config_handler.get_channel_id('NetworkSizeChannelID')
active_smeshers_channel_id = config_handler.get_channel_id('ActiveSmeshersChannelID')
status_category_id = config_handler.get_channel_id('StatusCategoryID')
percent_total_supply_channel_id = config_handler.get_channel_id('PercentTotalSupplyChannelID')
token = config_handler.get_token()
api_endpoint = config_handler.get_api_endpoint()
wait_time = config_handler.get_wait_time()
api_key = config_handler.get_api_key()

#API Setup
api_handler = APIHandler(api_endpoint, api_key)

# setup vars
last_good_price = None
last_price = None
TOTAL_SUPPLY = 150000000 #Vaulted coins. Needs to change next july or once we make a live API

# Define intents
intents = Intents.default()
intents.messages = True
intents.guilds = True

# Discord client with intents
client = discord.Client(intents=intents)

async def fetch_api_data():
    global last_good_price, last_price
    while not client.is_closed():
        try:
            #Reset temp vars
            price_message = "No price data."
            trend_indicator = ""  # Initialize trend_indicator
            market_cap_message = "Pending price data"  # Default market cap message

            # Make an API request
            print("Spudbot fetching API data...")
            raw_data = api_handler.fetch_data()

            if raw_data:
                print("API fetch successful!")
                data = api_handler.parse_data(raw_data)
                next_epoch_data = data.get('nextEpoch', {})  # Get nextEpoch data directly
                print("Got raw data, now calculating the display data...")

                curr_epoch = data['epoch']
                print("Epoch: "+str(curr_epoch))
                
                curr_layer = "{:,}".format(data['layer'])
                print("Current layer: "+str(curr_layer))
                
                # Extract circulatingSupply and divide by 1 billion to get raw number of SMH
                circulating_supply_raw = round(data['circulatingSupply'] / 1_000_000_000)
                # Recalculate TOTAL_SUPPLY with updated circulating_supply_raw
                TOTAL_SUPPLY = 150000000 + circulating_supply_raw  
                # Compute the percentage of total supply and round to two decimal places
                supply_percentage = round((circulating_supply_raw / TOTAL_SUPPLY) * 100, 2)
                print("Percentage of total supply: %"+str(supply_percentage))
                
                effective_capacity_eib = (data['effectiveUnitsCommited'] * 64) / (1024 * 1024 * 1024)
                effective_units_committed = "{:.2f}".format(effective_capacity_eib)
                print("Network size computed: "+str(effective_capacity_eib)+" EiB")
                active_smeshers = data['totalActiveSmeshers']                
                print("Total active smeshers: "+str(active_smeshers))
                formatted_smeshers = f"{active_smeshers / 1_000_000:.1f}M"
                print(f"Formatting active smeshers: {formatted_smeshers}")

                # Next Epoch Data (As far as we know from submitted ATX)
                next_epoch = next_epoch_data['epoch']
                print("Next Epoch: "+str(next_epoch))
                next_epoch_units_commited = "{:,}".format(round(next_epoch_data['effectiveUnitsCommited'] * 64 / 1024 / 1024, 2))
                print("The next epoch will have: "+str(next_epoch_units_commited)+" PiB")
                next_epoch_active_smeshers = "{:,}".format(round(next_epoch_data['totalActiveSmeshers']))
                print("The next epoch will have "+str(next_epoch_active_smeshers)+" active smeshers.")

                # Format data for display
                circulating_supply_formatted = "{:,}".format(circulating_supply_raw)
                print("Circulating supply found: "+str(circulating_supply_formatted)+" SMH")
                
                price = data.get('price')
                if price != -1:
                    # Update the last good price
                    last_good_price = round(data['price'], 2)

                    # Determine the price trend indicator
                    if last_price is not None:
                        if last_good_price > last_price:
                            trend_indicator = " 🔼"
                        elif last_good_price < last_price:
                            trend_indicator = " 🔽"

                    price_message = f"Price: ${last_good_price}{trend_indicator}"
                    print("Price found: $"+str(price_message))

                    # Update last_price for the next comparison
                    last_price = last_good_price

                    # Calculate market cap based on current price
                    market_cap = round(circulating_supply_raw * last_good_price,2)
                    market_cap_message = f"M.Cap: ${'{:,}'.format(market_cap)}"
                    print("Market Cap found: $"+str(market_cap_message))

                elif last_good_price is not None:
                    # If the API returns -1 but a last good price exists
                    price_message = f"Price: ${last_good_price} (outdated)"
                    print("Price API offline. Using old price: $"+str(price_message))
                    # Estimate market cap based on last good price
                    estimated_market_cap = circulating_supply_raw * last_good_price
                    market_cap_message = f"M.Cap: est ~${'{:,}'.format(estimated_market_cap)}"
                    print("Price API offline. Approximate Market Cap: $"+str(estimated_market_cap))
                else:
                    # If there's no last good price and the API returns -1
                    price_message = "Price data unavailable"
                    print(price_message)

                # Create a message string (only if not in test mode)
                # message = '\n'.join([f"{key}: {value}" for key, value in data.items()])
                current_time = datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                print ("Channel updates starting at: ", formatted_time)
                await client.get_channel(price_channel_id).edit(name=f"{price_message}")
                print ("...Price updated...")
                await client.get_channel(circulating_supply_channel_id).edit(name=f"C.Supply: {circulating_supply_formatted} SMH")
                print ("...Circulating Supply updated...")
                await client.get_channel(market_cap_channel_id).edit(name=market_cap_message)
                print ("...Market Cap updated...")
                await client.get_channel(epoch_channel_id).edit(name=f"Epoch: {curr_epoch}")
                print ("...Current epoch updated...")
                await client.get_channel(layer_channel_id).edit(name=f"Layer: {curr_layer}")
                print ("...Current layer updated...")
                await client.get_channel(network_size_channel_id).edit(name=f"Network Size: {effective_units_committed} EiB")
                print ("...Network size updated...")
                await client.get_channel(active_smeshers_channel_id).edit(name=f"Activations: {formatted_smeshers}")
                print ("...Active smeshers updated...")
                await client.get_channel(percent_total_supply_channel_id).edit(name=f"% Total Supply: {supply_percentage}%")
                print ("...Percent total supply updated...")
                current_time = datetime.now()
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                print ("...Channel updates completed at: ", formatted_time)
            
            else:
                print("Failed to fetch API data.")

        except Exception as e:
            print(f"An error occurred: {e}")

        await asyncio.sleep(wait_time)



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
    new_category_name = "🥔 Spudbot 9000 🥔 (Online)"
    category = discord.utils.get(client.get_all_channels(), id=status_category_id)
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
    new_category_name = "🥔 Spudbot 9000 🥔 (Offline)"
    print(f"Shutting down... :(")
    print(f"Category renamed to: {new_category_name}")
    category = discord.utils.get(client.get_all_channels(), id=status_category_id)
    if category:
        await category.edit(name=new_category_name)
    await client.close()

# Signal handler
def handle_shutdown_signal(*args):
    asyncio.create_task(shutdown_signal())

signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

# Run the bot
client.run(token)
