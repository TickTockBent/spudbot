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

            processed_data = await self.wait_for_processed_data(data_cog)
            if not processed_data:
                return

            current_epoch = int(processed_data['epoch'])
            
            # Fetch all upcoming events and clean up the database
            await self.sync_events_with_discord()

            # Now update or create the events as needed
            await self.update_epoch_event(current_epoch)
            await self.update_poet_cycle_event(current_epoch)
            await self.update_cycle_gap_event(current_epoch)

        except Exception as e:
            if config.DEBUG_MODE:
                print(f"An error occurred in the update_events method: {str(e)}")

    async def wait_for_processed_data(self, data_cog):
        for _ in range(12):  # Try for up to 1 minute (5 seconds * 12)
            processed_data = data_cog.get_processed_data()
            if processed_data:
                if config.DEBUG_MODE:
                    print("Processed data received for events update:")
                    for key, value in processed_data.items():
                        print(f"  {key}: {value}")
                return processed_data
            if config.DEBUG_MODE:
                print("Waiting for processed data...")
            await asyncio.sleep(5)
        
        if config.DEBUG_MODE:
            print("No processed data available after waiting. Skipping events update.")
        return None

    async def sync_events_with_discord(self):
        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            if config.DEBUG_MODE:
                print(f"Guild with ID {config.GUILD_ID} not found")
            return

        # Fetch all scheduled events from Discord
        discord_events = await guild.fetch_scheduled_events()
        discord_event_ids = {event.id for event in discord_events}

        # Fetch all event IDs from the database
        db_event_ids = self.get_all_event_ids()

        # Remove any database entries that don't correspond to actual events
        for db_id in db_event_ids - discord_event_ids:
            self.remove_event_from_db(db_id)
            if config.DEBUG_MODE:
                print(f"Removed non-existent event ID {db_id} from database")

        # Update database with correct event IDs for existing events
        for event in discord_events:
            self.update_event_in_db(event.id, event.name)

    def get_all_event_ids(self):
        conn = sqlite3.connect('spacemesh_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT event_id FROM events")
        event_ids = set(row[0] for row in cursor.fetchall())
        conn.close()
        return event_ids

    def remove_event_from_db(self, event_id):
        conn = sqlite3.connect('spacemesh_data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
        conn.commit()
        conn.close()

    def update_event_in_db(self, event_id, event_name):
        event_type = self.get_event_type_from_name(event_name)
        if event_type:
            conn = sqlite3.connect('spacemesh_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE events SET event_id = ? WHERE event_type = ?", (event_id, event_type))
            conn.commit()
            conn.close()

    def get_event_type_from_name(self, event_name):
        if "Epoch" in event_name:
            return "epoch"
        elif "Poet Round" in event_name:
            return "poet_cycle"
        elif "Cycle Gap" in event_name:
            return "cycle_gap"
        return None

    def calculate_next_epoch_start(self, current_epoch):
        current_epoch_start = GENESIS_TIMESTAMP + current_epoch * EPOCH_DURATION
        next_epoch_start = current_epoch_start + EPOCH_DURATION
        return next_epoch_start

    async def update_epoch_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating epoch event for current epoch {current_epoch}")

        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_next_epoch_start(current_epoch)
        next_epoch_end = next_epoch_start + EPOCH_DURATION
        
        if config.DEBUG_MODE:
            print(f"Current epoch: {current_epoch}")
            print(f"Next epoch: {next_epoch}")
            print(f"Calculated next epoch start: {next_epoch_start}")
            print(f"Calculated next epoch end: {next_epoch_end}")

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

        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_next_epoch_start(current_epoch)
        next_poet_cycle_start = next_epoch_start - timedelta(days=4)
        next_poet_cycle_end = next_epoch_start - CYCLE_GAP_DURATION

        # Use current_epoch for the poet round number
        poet_round_number = current_epoch

        if config.DEBUG_MODE:
            print(f"Next epoch: {next_epoch}")
            print(f"Poet round number: {poet_round_number}")
            print(f"Next poet cycle start: {next_poet_cycle_start}")
            print(f"Next poet cycle end: {next_poet_cycle_end}")

        event_data = self.get_event_data('poet_cycle')
        if event_data and event_data['associated_number'] == poet_round_number:
            if config.DEBUG_MODE:
                print(f"Existing poet cycle event found for round {poet_round_number}")
            await self.update_discord_event(event_data['event_id'], f"Poet Round {poet_round_number} Start", f"Poet Round {poet_round_number} for Epoch {next_epoch} will start at this time.", next_poet_cycle_start, next_poet_cycle_end)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new poet cycle event for round {poet_round_number}")
            event_id = await self.create_discord_event(f"Poet Round {poet_round_number} Start", f"Poet Round {poet_round_number} for Epoch {next_epoch} will start at this time.", next_poet_cycle_start, next_poet_cycle_end)
            if event_id:
                self.store_event_data('poet_cycle', event_id, poet_round_number)

    async def update_cycle_gap_event(self, current_epoch):
        if config.DEBUG_MODE:
            print(f"Updating cycle gap event for current epoch {current_epoch}")

        next_epoch = current_epoch + 1
        next_epoch_start = self.calculate_next_epoch_start(current_epoch)
        next_poet_cycle_start = next_epoch_start - timedelta(days=4)
        next_cycle_gap_start = next_poet_cycle_start - CYCLE_GAP_DURATION
        next_cycle_gap_end = next_poet_cycle_start

        if config.DEBUG_MODE:
            print(f"Next epoch: {next_epoch}")
            print(f"Next cycle gap start: {next_cycle_gap_start}")
            print(f"Next cycle gap end: {next_cycle_gap_end}")

        event_data = self.get_event_data('cycle_gap')
        if event_data and event_data['associated_number'] == next_epoch:
            if config.DEBUG_MODE:
                print(f"Existing cycle gap event found for epoch {next_epoch}")
            await self.update_discord_event(event_data['event_id'], f"Cycle Gap before Epoch {next_epoch}", f"The cycle gap before Epoch {next_epoch} will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
        else:
            if config.DEBUG_MODE:
                print(f"Creating new cycle gap event for epoch {next_epoch}")
            event_id = await self.create_discord_event(f"Cycle Gap before Epoch {next_epoch}", f"The cycle gap before Epoch {next_epoch} will occur during this time.", next_cycle_gap_start, next_cycle_gap_end)
            if event_id:
                self.store_event_data('cycle_gap', event_id, next_epoch)

    def calculate_epoch_start(self, epoch_number):
        return GENESIS_TIMESTAMP + (epoch_number - 1) * EPOCH_DURATION

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
        except discord.NotFound:
            if config.DEBUG_MODE:
                print(f"Event with ID {event_id} not found. Creating a new one.")
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
            if result:
                return {'event_id': int(result[0]), 'associated_number': result[1]}
            return None
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

    @update_events.before_loop
    async def before_update_events(self):
        await self.bot.wait_until_ready()
        if config.DEBUG_MODE:
            print("EventsCog is ready and will start updating events.")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
    if config.DEBUG_MODE:
        print("EventsCog has been loaded.")