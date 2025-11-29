# Telegram Online Status Collector

![Banner](banner.png)

A Python application that monitors and tracks the online/offline status of a specific Telegram user. The tool logs session durations and calculates total online time, providing detailed activity reports.

## Features

- **Real-time Status Monitoring**: Tracks when a user goes online or offline
- **Dual Detection Methods**: Uses both event-based detection and reliable polling for accurate status updates
- **Session Tracking**: Records individual online sessions with duration
- **Daily Statistics**: Calculates total online time for the day
- **Activity Logging**: Saves all activity to a log file with timestamps
- **Graceful Shutdown**: Properly handles interruptions and saves session data

## Requirements

- Python 3.7 or higher
- Telegram API credentials (API ID and API Hash)

## Installation

1. Clone or download this repository

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Get your Telegram API credentials:
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy your `api_id` and `api_hash`

4. Configure the script:
   - Open `main.py`
   - Replace `API_ID` with your API ID (line 9)
   - Replace `API_HASH` with your API Hash (line 10)
   - Replace `TARGET_USER` with the username of the user you want to track (line 11, without the @ symbol)
   - Optionally adjust `POLL_INTERVAL_SECONDS` to change how frequently the script checks for status updates (default: 5 seconds)

## Usage

Run the script:
```bash
python main.py
```

The script will:
1. Connect to Telegram using your credentials
2. Start tracking the specified user's online status
3. Log all status changes to both the console and `subject_activity_log.txt`

### Output Format

The script provides real-time updates showing:
- 🔵 When the user goes ONLINE
- ⚪ When the user goes OFFLINE
- Session duration for each online period
- Total online time accumulated during the day

Example output:
```
[11:04:52] 🔵 ONLINE (POLL) at 11:04:52
[11:08:36] ⚪ OFFLINE (POLL) at 11:08:36
[11:08:36] SESSION: 0h 3m 44s
[11:08:36] TOTAL TODAY: 0h 3m 44s
```

### Stopping the Script

Press `Ctrl+C` to gracefully stop the script. The current session (if active) will be finalized and saved before the script exits.

## Log File

All activity is logged to `subject_activity_log.txt` with timestamps. The log file is appended to, so you can track activity across multiple runs.

## How It Works

The script uses two complementary methods to track user status:

1. **Event-Based Detection**: Listens for real-time status update events from Telegram
2. **Polling Fallback**: Periodically checks the user's status via API calls (more reliable but less real-time)

This dual approach ensures accurate tracking even when Telegram's privacy settings suppress real-time events.

## Configuration Options

- `POLL_INTERVAL_SECONDS`: How often to poll for status updates (default: 5 seconds)
  - Lower values = more frequent checks but higher API usage
  - Higher values = less frequent checks but may miss short online sessions

## Notes

- The script requires that you have access to the target user's status (they must not have privacy settings that hide their online status from you)
- The first run will create a session file (`research_session.session`) for authentication
- You may need to enter your phone number and verification code on the first run

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and research purposes. Always respect privacy and ensure you have appropriate permissions before monitoring any user's activity.

