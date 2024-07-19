import discord
from discord.ext import commands, tasks
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
        self.update_events.start()

    def cog_unload(self):
        self.update_events.cancel()

    @tasks.loop(minutes=5)
    async def update_events(self):
        if config.DEBUG_MODE:
            print("Starting events update process")

        try:
            data_cog = self.bot.get_cog('DataCog')
            if not data_cog:
                if config.DEBUG_MODE:
                    print("DataCog not found. Unable to update events.")
                return

            # Wait for processed data to be available
            for _ in range(12):  # Try for up to 1 minute (5 seconds * 12)
                processed_data = data_cog.get_processed_data()
                if processed_data:
                    break
                if config.DEBUG_MODE:
                    print("Waiting for processed data...")
                await asyncio.sleep(5)
            
            if not processed_data:
                if config.DEBUG_MODE:
                    print("No processed data available after waiting. Skipping events update.")
                return

            if config.DEBUG_MODE:
                print("Processed data received for events update:")
                for key, value in processed_data.items():
                    print(f"  {key}: {value}")

            current_epoch = int(processed_data['epoch'])
            await self.update_epoch_event(current_epoch)
            await self.update_poet_cycle_event(current_epoch)
            await self.update_cycle_gap_event(current_epoch)

        except Exception as e:
            if config.DEBUG_MODE:
                print(f"An error occurred in the update_events method: {str(e)}")

    async def update_epoch_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating epoch event for current epoch {current_epoch}")

        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_epoch_start(next_epoch)
        next_epoch_end = next_epoch_start + EPOCH_DURATION
        
        if config.DEBUG_MODE:
            print(f"Calculated next epoch start: {next_epoch_start}")
            print(f"Calculated next epoch end: {next_epoch_end}")
            print(f"Next epoch number: {next_epoch}")

        event_data = self.get_event_data('epoch')
        if event_data and event_data['associated_number'] == next_epoch:
            if config.DEBUG_MODE:
                print(f"Existing epoch event found for epoch {next_epoch}")
            await self.update_discord_event(event_data['event_id'], f"Epoch {next_epoch} Start", f"Epoch {next_epoch} will start at this time.", next_epoch_start, next_epoch_end)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new epoch event for epoch {next_epoch}")
            event_id = await self.create_discord_event(f"Epoch {next_epoch} Start", f"Epoch {next_epoch} will start at this time.", next_epoch_start, next_epoch_end)
            if event_id:
                self.store_event_data('epoch', event_id, next_epoch)

    async def update_poet_cycle_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating poet cycle event for current epoch {current_epoch}")

        next_poet_cycle_start = self.calculate_next_poet_cycle_start(current_epoch)
        next_poet_cycle = current_epoch + 1
        next_poet_cycle_end = next_poet_cycle_start + POET_CYCLE_DURATION
        
        if config.DEBUG_MODE:
            print(f"Calculated next poet cycle start: {next_poet_cycle_start}")
            print(f"Calculated next poet cycle end: {next_poet_cycle_end}")
            print(f"Next poet cycle number: {next_poet_cycle}")

        event_data = self.get_event_data('poet_cycle')
        if event_data and event_data['associated_number'] == next_poet_cycle:
            if config.DEBUG_MODE:
                print(f"Existing poet cycle event found for cycle {next_poet_cycle}")
            await self.update_discord_event(event_data['event_id'], f"Poet Round {next_poet_cycle} Start", f"Poet Round {next_poet_cycle} will start at this time.", next_poet_cycle_start, next_poet_cycle_end)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new poet cycle event for cycle {next_poet_cycle}")
            event_id = await self.create_discord_event(f"Poet Round {next_poet_cycle} Start", f"Poet Round {next_poet_cycle} will start at this time.", next_poet_cycle_start, next_poet_cycle_end)
            if event_id:
                self.store_event_data('poet_cycle', event_id, next_poet_cycle)

    async def update_cycle_gap_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating cycle gap event for current epoch {current_epoch}")

        next_cycle_gap_start = self.calculate_next_cycle_gap_start(current_epoch)
        next_cycle_gap_end = next_cycle_gap_start + CYCLE_GAP_DURATION
        next_poet_cycle = current_epoch + 1
        
        if config.DEBUG_MODE:
            print(f"Calculated next cycle gap start: {next_cycle_gap_start}")
            print(f"Calculated next cycle gap end: {next_cycle_gap_end}")
            print(f"Next poet cycle number: {next_poet_cycle}")

        event_data = self.get_event_data('cycle_gap')
        if event_data and event_data['associated_number'] == next_poet_cycle:
            if config.DEBUG_MODE:
                print(f"Existing cycle gap event found for cycle {next_poet_cycle}")
            await self.update_discord_event(event_data['event_id'], f"Cycle Gap before Epoch {next_poet_cycle}", "The cycle gap will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new cycle gap event for cycle {next_poet_cycle}")
            event_id = await self.create_discord_event(f"Cycle Gap before Epoch {next_poet_cycle}", "The cycle gap will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
            if event_id:
                self.store_event_data('cycle_gap', event_id, next_poet_cycle)

    def calculate_epoch_start(self, epoch_number):
        return GENESIS_TIMESTAMP + (epoch_number - 1) * EPOCH_DURATION

    def calculate_next_poet_cycle_start(self, current_epoch):
        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_epoch_start(next_epoch)
        return next_epoch_start - timedelta(days=4)

    def calculate_next_cycle_gap_start(self, current_epoch):
        next_poet_cycle_start = self.calculate_next_poet_cycle_start(current_epoch)
        return next_poet_cycle_start - CYCLE_GAP_DURATION

    async def create_discord_event(self, name, description, start_time, end_time):
        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            if config.DEBUG_MODE:
                print(f"Guild with ID {config.GUILD_ID} not found")
            return None
        try:
            if config.DEBUG_MODE:
                print(f"Creating event: {name}")
                print(f"Start time: {start_time}")
                print(f"End time: {end_time}")
            
            event = await guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                entity_type=discord.EntityType.external,
                privacy_level=discord.PrivacyLevel.guild_only,
                location="Spacemesh Network"
            )
            if config.DEBUG_MODE:
                print(f"Created Discord event: {name}")
            return event.id
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error creating Discord event: {str(e)}")
            return None

    async def update_discord_event(self, event_id, name, description, start_time, end_time):
        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            if config.DEBUG_MODE:
                print(f"Guild with ID {config.GUILD_ID} not found")
            return

        try:
            # Check if event_id is a valid integer
            if not isinstance(event_id, int):
                raise ValueError("Invalid event ID")

            event = await guild.fetch_scheduled_event(event_id)
            await event.edit(
                name=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                entity_type=discord.EntityType.external,
                location="Spacemesh Network"
            )
            if config.DEBUG_MODE:
                print(f"Updated Discord event: {name}")
        except (discord.NotFound, ValueError) as e:
            if config.DEBUG_MODE:
                print(f"Event with ID {event_id} not found or invalid. Creating a new one.")
            new_event_id = await self.create_discord_event(name, description, start_time, end_time)
            if new_event_id:
                self.store_event_data(name.split()[0].lower(), new_event_id, int(name.split()[1]) if name.split()[1].isdigit() else 0)
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
            if result and result[0] is not None:
                return {'event_id': int(result[0]), 'associated_number': result[1]}
            return None
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error getting event data: {str(e)}")
            return None

    def store_event_data(self, event_type, event_id, associated_number):
        if event_id is None:
            if config.DEBUG_MODE:
                print(f"Attempted to store invalid event data: {event_type}, {event_id}, {associated_number}")
            return
        
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

    @update_events.before_loop
    async def before_update_events(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("EventsCog is ready and will start updating events.")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    if config.DEBUG_MODE:
        print("EventsCog has been loaded.")