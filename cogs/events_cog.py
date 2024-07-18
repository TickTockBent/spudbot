import discord
from discord.ext import commands, tasks
import config
import sqlite3
from datetime import datetime, timedelta
import asyncio
import pytz  # Make sure to install this: pip install pytz

GENESIS_TIMESTAMP = datetime(2023, 7, 14, 8, 0, 0, tzinfo=pytz.UTC)
EPOCH_DURATION = timedelta(days=14)
POET_CYCLE_DURATION = timedelta(days=13, hours=12)
CYCLE_GAP_DURATION = timedelta(hours=12)

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_events.start()

    def cog_unload(self):
        self.update_events.cancel()

    @tasks.loop(hours=1)  # Run every hour
    async def update_events(self):
        if config.DEBUG_MODE:
            print("Starting events update process")

        try:
            data_cog = self.bot.get_cog('DataCog')
            if not data_cog:
                if config.DEBUG_MODE:
                    print("DataCog not found. Unable to update events.")
                return

            current_epoch_data = data_cog.get_processed_data()
            if not current_epoch_data:
                if config.DEBUG_MODE:
                    print("No processed data available. Skipping events update.")
                return

            current_epoch = int(current_epoch_data['epoch'])
            await self.update_epoch_event(current_epoch)
            await self.update_poet_cycle_event(current_epoch)
            await self.update_cycle_gap_event(current_epoch)

        except Exception as e:
            if config.DEBUG_MODE:
                print(f"An error occurred in the update_events method: {str(e)}")

    async def update_epoch_event(self, current_epoch):
        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_epoch_start(next_epoch)
        
        event_data = self.get_event_data('epoch')
        if event_data and event_data['associated_number'] == next_epoch:
            # Event already exists, update if necessary
            await self.update_discord_event(event_data['event_id'], f"Epoch {next_epoch} Start", f"Epoch {next_epoch} will start at this time.", next_epoch_start)
        else:
            # Create new event
            event_id = await self.create_discord_event(f"Epoch {next_epoch} Start", f"Epoch {next_epoch} will start at this time.", next_epoch_start)
            self.store_event_data('epoch', event_id, next_epoch)

    async def update_poet_cycle_event(self, current_epoch):
        next_poet_cycle_start = self.calculate_next_poet_cycle_start(current_epoch)
        next_poet_cycle = self.calculate_poet_cycle_number(next_poet_cycle_start)
        
        event_data = self.get_event_data('poet_cycle')
        if event_data and event_data['associated_number'] == next_poet_cycle:
            # Event already exists, update if necessary
            await self.update_discord_event(event_data['event_id'], f"Poet Cycle {next_poet_cycle} Start", f"Poet Cycle {next_poet_cycle} will start at this time.", next_poet_cycle_start)
        else:
            # Create new event
            event_id = await self.create_discord_event(f"Poet Cycle {next_poet_cycle} Start", f"Poet Cycle {next_poet_cycle} will start at this time.", next_poet_cycle_start)
            self.store_event_data('poet_cycle', event_id, next_poet_cycle)

    async def update_cycle_gap_event(self, current_epoch):
        next_cycle_gap_start = self.calculate_next_cycle_gap_start(current_epoch)
        next_cycle_gap_end = next_cycle_gap_start + CYCLE_GAP_DURATION
        next_poet_cycle = self.calculate_poet_cycle_number(next_cycle_gap_end)
        
        event_data = self.get_event_data('cycle_gap')
        if event_data and event_data['associated_number'] == next_poet_cycle:
            # Event already exists, update if necessary
            await self.update_discord_event(event_data['event_id'], "Cycle Gap", "The cycle gap will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
        else:
            # Create new event
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
        event = await guild.create_scheduled_event(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            entity_type=discord.EntityType.external,
            location="Spacemesh Network"
        )
        return event.id

    async def update_discord_event(self, event_id, name, description, start_time, end_time=None):
        guild = self.bot.get_guild(config.GUILD_ID)
        event = await guild.fetch_scheduled_event(event_id)
        await event.edit(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time
        )

    def get_event_data(self, event_type):
        conn = sqlite3.connect('spacemesh_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT event_id, associated_number FROM events WHERE event_type = ?", (event_type,))
        result = cursor.fetchone()
        conn.close()
        return {'event_id': result[0], 'associated_number': result[1]} if result else None

    def store_event_data(self, event_type, event_id, associated_number):
        conn = sqlite3.connect('spacemesh_data.db')
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS events (event_type TEXT PRIMARY KEY, event_id INTEGER, associated_number INTEGER)")
        cursor.execute("INSERT OR REPLACE INTO events (event_type, event_id, associated_number) VALUES (?, ?, ?)",
                       (event_type, event_id, associated_number))
        conn.commit()
        conn.close()

    @update_events.before_loop
    async def before_update_events(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("EventsCog is ready and will start updating events.")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    if config.DEBUG_MODE:
        print("EventsCog has been loaded.")