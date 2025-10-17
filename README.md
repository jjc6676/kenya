# Selenium Poll Automation

This repository contains two automation scripts for voting for Kenya Cummings in the MileSplit LA Girls' Performer of the Week poll:

1. **`poll_automation.py`** - Single browser instance automation
2. **`multi_instance_automation.py`** - Multi-browser instance automation (3-8 concurrent instances)

## Features

- Automatically clicks the checkbox for Kenya Cummings
- Clicks the vote button
- Returns to the poll
- Waits 3 seconds between cycles
- Runs indefinitely until manually stopped (Ctrl+C)
- Includes error handling and logging
- Automatically manages ChromeDriver installation

## Prerequisites

- Python 3.7 or higher
- Google Chrome browser installed
- Internet connection

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `selenium` - Web browser automation
- `webdriver-manager` - Automatic ChromeDriver management

## Usage

### Single Instance (Basic)

Run the single browser automation script:

```bash
python poll_automation.py
```

### Multi-Instance (Recommended)

Run multiple concurrent browser instances for maximum efficiency:

```bash
# Run with 3 instances (default)
python multi_instance_automation.py

# Run with 4 instances
python multi_instance_automation.py --instances 4

# Run with 8 instances (maximum)
python multi_instance_automation.py --instances 8
```

### What Each Script Does:

**Single Instance (`poll_automation.py`):**
1. Opens one Chrome browser window
2. Navigates to the MileSplit LA poll
3. Starts voting for Kenya Cummings in an infinite loop
4. Displays logging information in the console

**Multi-Instance (`multi_instance_automation.py`):**
1. Opens 3-8 Chrome browser windows simultaneously
2. Each instance navigates to the poll independently
3. All instances vote concurrently for maximum speed
4. Displays detailed logging for each instance with instance IDs
5. Shows final statistics when stopped

## Stopping the Script

Press `Ctrl+C` in the terminal to gracefully stop the automation and close all browser windows.

For multi-instance automation, this will stop all instances simultaneously and display final voting statistics.

## Packaging for Fresh Windows Machines (No Python Needed)

You can build standalone Windows executables and copy them to a clean machine that has Chrome installed:

### Build on a Windows machine

```bat
packaging\build_windows.bat
```

This produces:
- `dist\poll_automation.exe`
- `dist\multi_instance_automation.exe`

Copy the `dist\` folder to the target machine and run the EXEs directly.

### Requirements on the target machine
- Google Chrome installed (standard installer)
- Internet access

### Optional: Portable Chrome
If Chrome isn't installed, you can place a portable Chromium/Chrome next to the EXE and set the environment variable before launching:

```bat
set CHROME_BINARY=ChromePortable\App\Chrome\chrome.exe
multi_instance_automation.exe --instances 3
```

The scripts will also attempt to auto-detect Chrome in common Windows locations.

## Logging

Both scripts provide detailed logging including:
- Setup progress
- Voting cycle status
- Error messages
- Timing information

**Multi-instance logging** includes:
- Instance-specific messages with `[Instance X]` prefixes
- Per-instance vote counts and error statistics
- Final summary statistics when stopped

## Error Handling

The script includes robust error handling for:
- Page loading timeouts
- Missing elements
- Network issues
- Browser crashes

If a voting cycle fails, the script will wait 5 seconds before retrying.

## Technical Details

**Single Instance:**
- Uses Selenium WebDriver with Chrome
- Implements explicit waits for element availability
- Uses CSS selectors to locate page elements
- Automatically downloads and manages ChromeDriver
- Removes automation detection markers

**Multi-Instance:**
- Uses Python threading with ThreadPoolExecutor
- Each instance runs in its own thread with isolated browser session
- Unique Chrome user data directories and debugging ports per instance
- Concurrent voting across multiple browser windows
- Instance-specific error tracking and statistics
- Graceful shutdown of all instances simultaneously

## CSS Selectors Used

- Checkbox: `input#PDI_answer71048920` (direct checkbox for Kenya Cummings)
- Vote Button: `#pd-vote-button16156077`
- Return to Poll: `.pds-return-poll`

## Performance Expectations

**Single Instance:**
- ~2-3 seconds per voting cycle
- ~20-30 votes per minute

**Multi-Instance (3 instances):**
- ~60-90 votes per minute
- ~3,600-5,400 votes per hour

**Multi-Instance (8 instances):**
- ~160-240 votes per minute  
- ~9,600-14,400 votes per hour

*Note: Actual performance depends on network speed and server response times.*

## Troubleshooting

### Chrome not found
Ensure Google Chrome is installed on your system.

### Permission errors
Run the script from a terminal/command prompt with appropriate permissions.

### Network issues
Check your internet connection and ensure the poll website is accessible.

### Element not found errors
The website structure may have changed. Check the CSS selectors in the script.
