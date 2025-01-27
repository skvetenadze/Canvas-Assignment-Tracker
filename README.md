# Canvas Assignment Tracker

This project is a Python-based **Assignment Tracker** that integrates with the Canvas Learning Management System (LMS) and Google Sheets to automatically fetch, sort, and upload your assignments. It ensures you're always up-to-date with your coursework by checking for new assignments every 30 minutes and displaying only those due within the next two weeks.

## Features

- **Canvas Integration**: Fetch assignments dynamically from Canvas LMS using API.
- **Google Sheets Integration**: Automatically upload new assignments to a specified Google Sheet.
- **Dynamic Date Filtering**: Only displays assignments due within the next two weeks.
- **Duplicate Prevention**: Ensures assignments are not duplicated in the Google Sheet.
- **Real-Time Updates**: Checks for updates every 30 minutes and syncs with Google Sheets.

## How It Works

1. **Fetch Assignments**: The script retrieves assignments from the Canvas API for specified courses.
2. **Sort Assignments**: Assignments are sorted by their due dates (earliest first).
3. **Upload to Google Sheets**: New assignments are appended to the Google Sheet, starting from the first available empty row.

## Prerequisites

1. **Python**: Install Python 3.x.
2. **Pip Packages**:
   - `requests`
   - `pandas`
   - `gspread`
   - `oauth2client`
3. **Canvas API Token**:
   - Generate an API token in Canvas under `Account > Settings > New Access Token`.
4. **Google Service Account**:
   - Create a service account in Google Cloud and download the `credentials.json` file.
   - Share your Google Sheet with the service account email.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/skvetenadze/canvas-assignment-tracker.git
   cd assignment-tracker

2. Install Dependencies:
  `pip install -r requirements.txt`

## Set up environment:

Replace TOKEN with your Canvas API token.
Replace COURSES with your course IDs and names.
Replace SHEET_NAME with your Google Sheet name.

4. Run The Script
  python canvas.py

## File Structure

assignment-tracker/
├── canvas.py          # Main script for fetching and uploading assignments
├── credentials.json   # Google service account credentials (keep this private)
├── README.md          # Documentation
└── LICENSE            # Licensing information

### Google API Setup
- Generate a `credentials.json` file by creating a service account in Google Cloud.
- Place the file in the project directory (this file is excluded from version control for security).


## Usage
The script runs continuously, fetching assignments from Canvas and syncing them with Google Sheets every 30 minutes.
It ensures you're always up-to-date with upcoming assignments.


