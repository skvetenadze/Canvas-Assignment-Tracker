import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
import json

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load the credentials from the environment variable
google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(google_credentials), scope)


# Canvas API configuration
BASE_URL = "https://njit.instructure.com"
TOKEN = os.environ.get("CANVAS_API_TOKEN")  

# List of course IDs and names
COURSES = {
    "47077": "MATH 111",    # Math Course
    "48627": "PHYS 111",    # Physics Course
    "46225": "CS 113",      # CS Course
    "46881": "ENG 102"      # English Course
}

# Google Sheets configuration
SHEET_NAME = "Assignment Tracker"  # Replace with your Google Sheet name

def fetch_assignments():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    all_assignments = []

    # Set the timezone
    local_timezone = pytz.timezone("America/New_York")
    now = datetime.now(local_timezone)
    end_date = now + timedelta(weeks=2)  # Dynamically calculate 2 weeks from now
    
    for course_id, course_name in COURSES.items():
        url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments"
        
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                assignments = response.json()
                for assignment in assignments:
                    # Format the due date
                    due_date = assignment.get("due_at", None)
                    if due_date:
                        due_date_dt = pd.to_datetime(due_date).tz_convert(local_timezone)
                        
                        # Check if the assignment is due within the specified date range
                        if now <= due_date_dt <= end_date:
                            formatted_due_date = due_date_dt.strftime("%m/%d/%Y")
                            days_left = (due_date_dt - now).days
                            
                            # Add assignment details
                            all_assignments.append({
                                "Assignment": assignment.get("name", "No Name").strip(),
                                "Subject/Course": course_name,
                                "Status": "Not Started",  # Default to "Not Started"
                                "Due Date": formatted_due_date,
                                "Days Left": days_left,
                                "Priority Level": "Standard",  # Default to "Standard"
                                "Due Date Raw": due_date_dt  # Store raw datetime for sorting
                            })
                # Check for next page link in headers
                url = response.links.get('next', {}).get('url')
            else:
                print(f"Error fetching assignments for {course_name}: {response.status_code}")
                print(response.text)
                break

    # Sort assignments by due date
    sorted_assignments = sorted(all_assignments, key=lambda x: x["Due Date Raw"])
    
    # Remove the "Due Date Raw" field before returning
    for assignment in sorted_assignments:
        del assignment["Due Date Raw"]
    
    return sorted_assignments

def upload_to_google_sheets(data):
    # Authenticate with Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(google_credentials), scope)
    client = gspread.authorize(creds)
    
    # Open the Google Sheet
    sheet = client.open(SHEET_NAME).sheet1  # Opens the first sheet in the spreadsheet

    # Get all existing assignments in column B (Assignments column)
    existing_assignments = sheet.col_values(2)  # Column B corresponds to the 2nd column

    # Filter out assignments that are already in the Google Sheet
    new_data = [
        item for item in data
        if item["Assignment"] not in existing_assignments
    ]

    # If there are no new assignments, skip the update
    if not new_data:
        print("No new assignments to update.")
        return

    # Find the first empty row in column B
    start_row = len(existing_assignments) + 1

    # Prepare data rows for new assignments
    rows = [
        [
            item["Assignment"],
            item["Subject/Course"],
            item["Status"],
            item["Due Date"],
            item["Days Left"],
            item["Priority Level"]
        ]
        for item in new_data
    ]

    # Update the entire range in one batch
    end_row = start_row + len(rows) - 1
    cell_range = f"B{start_row}:G{end_row}"
    sheet.update(cell_range, rows)  # Corrected order: values first, then range

    print(f"Added {len(new_data)} new assignments to Google Sheet: {SHEET_NAME}, starting from row {start_row}")


# Main function with periodic updates
if __name__ == "__main__":
    while True:
        print("Checking for new assignments...")
        assignments = fetch_assignments()
        if assignments:
            upload_to_google_sheets(assignments)  # Upload to Google Sheets
        else:
            print("No assignments found.")
        
        # Wait for 30 minutes before checking again
        print("Waiting for 30 minutes before the next check...")
        time.sleep(1800)  # Wait 1800 seconds (30 minutes)
