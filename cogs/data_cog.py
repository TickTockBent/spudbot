import discord
from discord.ext import commands, tasks
import sqlite3
from datetime import datetime, timedelta
import config
import asyncio

class DataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.processed_data = {}
        self.process_data.start()

    def cog_unload(self):
        self.process_data.cancel()

    @tasks.loop()
    async def process_data(self):
        api_cog = self.bot.get_cog('APICog')
        if api_cog:
            await api_cog.wait_for_data()  # Wait for the APICog to signal new data
            
            raw_data = api_cog.get_data()
            if api_cog.has_valid_data():
                self.processed_data = self.convert_data(raw_data)
                self.store_data(self.processed_data)
                if config.DEBUG_MODE:
                    print("Data processed and stored successfully")
            else:
                if config.DEBUG_MODE:
                    print("Received invalid data from APICog")
        else:
            if config.DEBUG_MODE:
                print("APICog not found. Unable to process data.")
            await asyncio.sleep(60)  # Wait a bit before trying again

    def convert_data(self, raw_data):
        processed = {}

        def debug_print(key, value, calculation=""):
            if config.DEBUG_MODE:
                print(f"DEBUG: {key} = {value} {calculation}")

        processed['epoch'] = raw_data.get('epoch', '0')
        debug_print('epoch', processed['epoch'])

        processed['layer'] = raw_data.get('layer', '0')
        debug_print('layer', processed['layer'])
        
        euc = int(raw_data.get('effectiveUnitsCommited', 0))
        processed['effectiveUnitsCommited'] = round(euc * 64 / (1024**6), 2)
        debug_print('effectiveUnitsCommited', processed['effectiveUnitsCommited'], 
                    f"(raw: {euc} SU)")

        epoch_subsidy = int(raw_data.get('epochSubsidy', 0)) / 1e9  # Convert Smidge to SMH
        processed['epochSubsidy'] = round(epoch_subsidy / 1e6, 2)  # Convert to millions of SMH
        debug_print('epochSubsidy', processed['epochSubsidy'], 
                    f"(raw: {raw_data.get('epochSubsidy', 0)} Smidge)")

        circ_supply = int(raw_data.get('circulatingSupply', 0)) / 1e9  # Convert Smidge to SMH
        processed['circulatingSupply'] = round(circ_supply / 1e6, 2)  # Convert to millions of SMH
        debug_print('circulatingSupply', processed['circulatingSupply'], 
                    f"(raw: {raw_data.get('circulatingSupply', 0)} Smidge)")

        rewards = int(raw_data.get('rewards', 0)) / 1e9  # Convert Smidge to SMH
        processed['rewards'] = f"{round(rewards / 1e6, 2)}"  # Convert to millions of SMH
        debug_print('rewards', processed['rewards'], 
                    f"(raw: {raw_data.get('rewards', 0)} Smidge)")

        processed['price'] = round(float(raw_data.get('price', 0)), 2)
        debug_print('price', processed['price'])
        
        market_cap = processed['price'] * circ_supply
        processed['marketCap'] = round(market_cap / 1e6, 2)  # Convert to millions of dollars
        debug_print('marketCap', processed['marketCap'], 
                    f"(price * circulatingSupply)")

        processed['totalAccounts'] = raw_data.get('totalAccounts', '0')
        debug_print('totalAccounts', processed['totalAccounts'])
        
        total_smeshers = int(raw_data.get('totalActiveSmeshers', 0))
        processed['totalActiveSmeshers'] = round(total_smeshers / 1e6, 2)
        debug_print('totalActiveSmeshers', processed['totalActiveSmeshers'], 
                    f"(raw: {total_smeshers})")

        vested = int(raw_data.get('vested', 0)) / 1e9  # Convert Smidge to SMH
        processed['vested'] = round(vested / 1e6, 2)  # Convert to millions of SMH
        debug_print('vested', processed['vested'], 
                    f"(raw: {raw_data.get('vested', 0)} Smidge)")

        total_vaulted = 150e6  # 150 million SMH
        processed['remainingVaulted'] = round(total_vaulted - processed['vested'], 2)
        debug_print('remainingVaulted', processed['remainingVaulted'], 
                    f"(totalVaulted - vested)")

        total_supply = total_vaulted
        processed['percentTotalSupply'] = round((circ_supply / total_supply) * 100, 2)
        debug_print('percentTotalSupply', processed['percentTotalSupply'], 
                    f"(circulatingSupply / totalSupply * 100)")

        next_epoch = raw_data.get('nextEpoch', {})
        processed['nextEpoch'] = {
            'epoch': next_epoch.get('epoch', str(int(processed['epoch']) + 1)),
            'effectiveUnitsCommited': round(int(next_epoch.get('effectiveUnitsCommited', 0)) * 64 / (1024**6), 2),
            'totalActiveSmeshers': round(int(next_epoch.get('totalActiveSmeshers', 0)) / 1e6, 3)
        }
        debug_print('nextEpoch', processed['nextEpoch'])

        return processed

    def store_data(self, processed_data):
        conn = sqlite3.connect('spacemesh_data.db')
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS spacemesh_data
        (timestamp TEXT, data_type TEXT, value REAL)
        ''')

        current_time = datetime.now().isoformat()

        data_to_store = [
            ('effectiveUnitsCommited', processed_data['effectiveUnitsCommited']),
            ('price', processed_data['price'])
        ]

        for data_type, value in data_to_store:
            cursor.execute('INSERT INTO spacemesh_data VALUES (?, ?, ?)',
                           (current_time, data_type, value))

        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute('DELETE FROM spacemesh_data WHERE data_type = "price" AND timestamp < ?',
                       (twenty_four_hours_ago,))

        conn.commit()
        conn.close()

        if config.DEBUG_MODE:
            print(f"DEBUG: Stored data: {data_to_store}")
            print(f"DEBUG: Removed price data older than {twenty_four_hours_ago}")

    def get_processed_data(self):
        return self.processed_data

    @process_data.before_loop
    async def before_process_data(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("DataCog is ready and will start processing data.")

async def setup(bot):
    await bot.add_cog(DataCog(bot))
    if config.DEBUG_MODE:
        print("DataCog has been loaded.")