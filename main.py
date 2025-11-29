import asyncio
import signal
import sys
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UpdateUserStatus

# --- CONFIGURATION ---
API_ID = 00000000 # REPLACE WITH YOUR API ID
API_HASH = "" # REPLACE WITH YOUR API ID
TARGET_USER = ""  # Target username no @
POLL_INTERVAL_SECONDS = 5  # How frequently the script polls for status (in seconds)

client = TelegramClient("research_session", API_ID, API_HASH)

TARGET_ID = None
current_session_start = None
total_online_seconds = 0
log_file = "subject_activity_log.txt"


# --- LOGGING UTILITY ---

def log(msg: str):
    """Print + save to file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"

    print(line)

    with open(log_file, "a") as f:
        f.write(line + "\n")


def format_duration(seconds):
    """Formats seconds into H:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s"


# --- SESSION MANAGEMENT LOGIC ---

async def update_session_state(is_currently_online: bool, source: str):
    """Centralized function to manage the online/offline session state."""
    global current_session_start, total_online_seconds

    now = datetime.now()
    source_tag = f"({source})"

    if is_currently_online:
        # Transition from Offline to Online
        if current_session_start is None:
            current_session_start = now
            log(f"🔵 ONLINE {source_tag} at {current_session_start.strftime('%H:%M:%S')}")
    else:
        # Transition from Online to Offline
        if current_session_start is not None:
            end = now
            duration = (end - current_session_start).total_seconds()
            total_online_seconds += duration

            log(f"⚪ OFFLINE {source_tag} at {end.strftime('%H:%M:%S')}")
            log(f"SESSION: {format_duration(duration)}")
            log(f"TOTAL TODAY: {format_duration(total_online_seconds)}\n")

            current_session_start = None


# --- STATUS EVENT HANDLER (Real-Time Attempt) ---

@client.on(events.Raw)
async def handle_raw(event):
    """
    Listens for the raw UpdateUserStatus event. This is fast but often suppressed
    by Telegram's privacy settings, especially for non-mutual contacts.
    """
    if not isinstance(event, UpdateUserStatus):
        return

    if event.user_id != TARGET_ID:
        return

    # Check if the event indicates the user is online
    is_online = isinstance(event.status, UserStatusOnline)

    # Use the central logic manager
    await update_session_state(is_online, "EVENT")


# --- POLLING TASK (Reliable Fallback) ---

async def online_poller():
    """
    Periodically checks the user's status directly via API request.
    This is necessary because the real-time event is often unreliable.
    """
    log(f"Starting reliable poller, checking every {POLL_INTERVAL_SECONDS}s.")

    while True:
        try:
            # Get the full entity data, which contains the latest status
            entity = await client.get_entity(TARGET_ID)

            # Check the status of the entity
            is_online = isinstance(entity.status, UserStatusOnline)

            # If the user is online, check if the last time they were seen is recent
            # This handles cases where the status is UserStatusLastSeen
            if not is_online and entity.status and hasattr(entity.status, 'was_online'):
                # Check if the 'was_online' time is within the last 15 seconds (arbitrary "recent" time)
                last_seen_dt = entity.status.was_online.replace(tzinfo=None)  # Strip timezone for comparison
                if datetime.now() - last_seen_dt < timedelta(seconds=POLL_INTERVAL_SECONDS + 10):
                    # We consider them online if they just went offline very recently
                    is_online = True

            # Use the central logic manager
            await update_session_state(is_online, "POLL")

        except Exception as e:
            # Handle potential API errors or FloodWait errors gracefully
            log(f"Error during polling: {e.__class__.__name__}: {e}")

        # Wait for the next poll interval
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


# --- SHUTDOWN HANDLING ---

async def shutdown():
    """Graceful shutdown: close online session if active, save logs, stop client."""
    global current_session_start, total_online_seconds

    log("⚠ Received shutdown signal. Finalizing session...")

    if current_session_start is not None:
        end = datetime.now()
        duration = (end - current_session_start).total_seconds()
        total_online_seconds += duration

        log(f"🟡 FORCED OFFLINE at {end.strftime('%H:%M:%S')}")
        log(f"SESSION: {format_duration(duration)} (auto-closed)")
        log(f"TOTAL TODAY: {format_duration(total_online_seconds)}")

        current_session_start = None

    log("✔ Session data saved. Closing Telegram client...")
    # Disconnect must be awaited
    await client.disconnect()
    log("✔ Client disconnected. Exiting.")
    # Exit must be called outside the loop, typically by the loop itself,
    # but here we use sys.exit(0) as the last resort to stop the process.
    sys.exit(0)


def setup_signal_handlers():
    """Assign Ctrl+C and SIGTERM handlers."""
    # Ensure the loop is running before adding handlers
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Loop might not be running if called too early, but usually fine here.
        return

    for sig in (signal.SIGINT, signal.SIGTERM):
        # We add the handler to run the shutdown coroutine as a task
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))


# --- MAIN EXECUTION ---

async def main():
    global TARGET_ID

    log("=== STARTING TELEGRAM ONLINE STATUS COLLECTOR ===")

    await client.start()

    # 1. Resolve user ID
    entity = await client.get_entity(TARGET_USER)
    TARGET_ID = entity.id

    log(f"Tracking user: {entity.username} (ID={TARGET_ID})")

    # 2. Check initial status and set state
    is_initial_online = isinstance(entity.status, UserStatusOnline)
    await update_session_state(is_initial_online, "INITIAL")

    log("Waiting for status updates...\n")

    # 3. Handle Ctrl+C
    setup_signal_handlers()

    # 4. Start the reliable poller as a background task
    # This task will run concurrently with the event listener
    poller_task = asyncio.create_task(online_poller())

    # 5. Main loop: keep the client running to receive events
    await client.run_until_disconnected()

    # After client disconnects gracefully, cancel the poller task
    poller_task.cancel()


if __name__ == "__main__":
    try:
        # asyncio.run handles setting up the loop and running the main coroutine
        asyncio.run(main())
    except SystemExit:
        # Catch the exit signal from the shutdown handler
        pass
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught. Shutting down...")
        # Since we use signal handlers, this fallback should only hit if the script
        # is interrupted before the event loop is fully established.
        sys.exit(0)