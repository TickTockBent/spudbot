import discord
from discord.ext import commands
import config
import sqlite3
from datetime import datetime, timedelta
import asyncio
import pytz

GENESIS_TIMESTAMP = datetime(2023, 7, 14, 8, 0, 0, tzinfo=pytz.UTC)
EPOCH_DURATION = timedelta(days=14)
POET_CYCLE_DURATION = timedelta(days=13, hours=12)
CYCLE_GAP_DURATION = timedelta(hours=12)

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_cog = None

    async def cog_load(self):
        self.data_cog = self.bot.get_cog('DataCog')
        if self.data_cog:
            self.data_cog.data_updated.add_listener(self.on_data_updated)
        else:
            print("DataCog not found. EventsCog will not function properly.")

    def cog_unload(self):
        if self.data_cog:
            self.data_cog.data_updated.remove_listener(self.on_data_updated)

    async def on_data_updated(self, processed_data):
        if config.DEBUG_MODE:
            print("Received updated data in EventsCog. Starting events update process.")
        
        try:
            current_epoch = int(processed_data['epoch'])
            await self.update_epoch_event(current_epoch)
            await self.update_poet_cycle_event(current_epoch)
            await self.update_cycle_gap_event(current_epoch)
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"An error occurred in the on_data_updated method: {str(e)}")

    async def update_epoch_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating epoch event for current epoch {current_epoch}")

        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_epoch_start(next_epoch)
        
        event_data = self.get_event_data('epoch')
        if event_data and event_data['associated_number'] == next_epoch:
            if config.DEBUG_MODE:
                print(f"Existing epoch event found for epoch {next_epoch}")
            await self.update_discord_event(event_data['event_id'], f"Epoch {next_epoch} Start", f"Epoch {next_epoch} will start at this time.", next_epoch_start)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new epoch event for epoch {next_epoch}")
            event_id = await self.create_discord_event(f"Epoch {next_epoch} Start", f"Epoch {next_epoch} will start at this time.", next_epoch_start)
            self.store_event_data('epoch', event_id, next_epoch)

    async def update_poet_cycle_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating poet cycle event for current epoch {current_epoch}")

        next_poet_cycle_start = self.calculate_next_poet_cycle_start(current_epoch)
        next_poet_cycle = self.calculate_poet_cycle_number(next_poet_cycle_start)
        
        event_data = self.get_event_data('poet_cycle')
        if event_data and event_data['associated_number'] == next_poet_cycle:
            if config.DEBUG_MODE:
                print(f"Existing poet cycle event found for cycle {next_poet_cycle}")
            await self.update_discord_event(event_data['event_id'], f"Poet Cycle {next_poet_cycle} Start", f"Poet Cycle {next_poet_cycle} will start at this time.", next_poet_cycle_start)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new poet cycle event for cycle {next_poet_cycle}")
            event_id = await self.create_discord_event(f"Poet Cycle {next_poet_cycle} Start", f"Poet Cycle {next_poet_cycle} will start at this time.", next_poet_cycle_start)
            self.store_event_data('poet_cycle', event_id, next_poet_cycle)

    async def update_cycle_gap_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating cycle gap event for current epoch {current_epoch}")

        next_cycle_gap_start = self.calculate_next_cycle_gap_start(current_epoch)
        next_cycle_gap_end = next_cycle_gap_start + CYCLE_GAP_DURATION
        next_poet_cycle = self.calculate_poet_cycle_number(next_cycle_gap_end)
        
        event_data = self.get_event_data('cycle_gap')
        if event_data and event_data['associated_number'] == next_poet_cycle:
            if config.DEBUG_MODE:
                print(f"Existing cycle gap event found for cycle {next_poet_cycle}")
            await self.update_discord_event(event_data['event_id'], "Cycle Gap", "The cycle gap will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new cycle gap event for cycle {next_poet_cycle}")
            event_id = await self.create_discord_event("Cycle Gap", "The cycle gap will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
            self.store_event_data('cycle_gap', event_id, next_poet_cycle)

    def calculate_epoch_start(self, epoch_number):
        return GENESIS_TIMESTAMP + (epoch_number - 1) * EPOCH_DURATION

    def calculate_next_poet_cycle_start(self, current_epoch):
        current_time = datetime.now(pytz.UTC)
        poet_cycles_since_genesis = (current_time - GENESIS_TIMESTAMP) // POET_CYCLE_DURATION
        next_poet_cycle_start = GENESIS_TIMESTAMP + (poet_cycles_since_genesis + 1) * POET_CYCLE_DURATION
        return next_poet_cycle_start

    def calculate_next_cycle_gap_start(self, current_epoch):
        next_poet_cycle_start = self.calculate_next_poet_cycle_start(current_epoch)
        return next_poet_cycle_start - CYCLE_GAP_DURATION

    def calculate_poet_cycle_number(self, date):
        poet_cycles_since_genesis = (date - GENESIS_TIMESTAMP) // POET_CYCLE_DURATION
        return poet_cycles_since_genesis + 1

    async def create_discord_event(self, name, description, start_time, end_time=None):
        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            if config.DEBUG_MODE:
                print(f"Guild with ID {config.GUILD_ID} not found")
            return None
        try:
            event = await guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                entity_type=discord.EntityType.external,
                location="Spacemesh Network"
            )
            if config.DEBUG_MODE:
                print(f"Created Discord event: {name}")
            return event.id
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error creating Discord event: {str(e)}")
            return None

    async def update_discord_event(self, event_id, name, description, start_time, end_time=None):
        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            if config.DEBUG_MODE:
                print(f"Guild with ID {config.GUILD_ID} not found")
            return
        try:
            event = await guild.fetch_scheduled_event(event_id)
            await event.edit(
                name=name,
                description=description,
                start_time=start_time,
                end_time=end_time
            )
            if config.DEBUG_MODE:
                print(f"Updated Discord event: {name}")
        except discord.NotFound:
            if config.DEBUG_MODE:
                print(f"Event with ID {event_id} not found. Creating a new one.")
            new_event_id = await self.create_discord_event(name, description, start_time, end_time)
            if new_event_id:
                self.store_event_data(name.split()[0].lower(), new_event_id, int(name.split()[1]))
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error updating Discord event: {str(e)}")

    def get_event_data(self, event_type):
        try:
            conn = sqlite3.connect('spacemesh_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, associated_number FROM events WHERE event_type = ?", (event_type,))
            result = cursor.fetchone()
            conn.close()
            return {'event_id': result[0], 'associated_number': result[1]} if result else None
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error getting event data: {str(e)}")
            return None

    def store_event_data(self, event_type, event_id, associated_number):
        try:
            conn = sqlite3.connect('spacemesh_data.db')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS events (event_type TEXT PRIMARY KEY, event_id INTEGER, associated_number INTEGER)")
            cursor.execute("INSERT OR REPLACE INTO events (event_type, event_id, associated_number) VALUES (?, ?, ?)",
                           (event_type, event_id, associated_number))
            conn.commit()
            conn.close()
            if config.DEBUG_MODE:
                print(f"Stored event data: {event_type}, {event_id}, {associated_number}")
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error storing event data: {str(e)}")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    if config.DEBUG_MODE:
        print("EventsCog has been loaded.")