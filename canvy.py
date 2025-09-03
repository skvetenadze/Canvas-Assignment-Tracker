import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError
import time
import os
import json

# Google Sheets API scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials from environment variable
google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(google_credentials), scope)

# Canvas API configuration
BASE_URL = "https://njit.instructure.com"
TOKEN = os.environ.get("CANVAS_API_TOKEN")  

# List of course IDs and names
COURSES = {
    "53934": "COM 312",   
    "54376": "CS 114", 
    "52583": "HIST 213",  
    "56718": "MATH 333",  
    "57133": "PHYS 121A", 
    "57118": "PHYS 121",
    "57570": "YWCC" 
       
}

# Google Sheets configuration
SHEET_NAME = "Assignment Tracker"  

def fetch_assignments():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    all_assignments = []

    # Set timezone
    local_timezone = pytz.timezone("America/New_York")
    now = datetime.now(local_timezone)
    end_date = now + timedelta(weeks=2)

    for course_id, course_name in COURSES.items():
        url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments"

        while url:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                assignments = response.json()
                for assignment in assignments:
                    due_date = assignment.get("due_at", None)
                    if not due_date:
                        continue

                    # Canvas returns UTC; convert to local
                    due_date_dt = pd.to_datetime(due_date).tz_convert(local_timezone)

                    # Only keep items due in the next 2 weeks
                    if now <= due_date_dt <= end_date:
                        formatted_due_date = due_date_dt.strftime("%m/%d/%Y")
                        days_left = (due_date_dt - now).days

                        # Decide priority based on days left
                        # (<=0 counts as due today/overdue -> High)
                        if days_left <= 4:
                            priority = "High"
                        elif days_left <= 9:
                            priority = "Standard"
                        else:
                            priority = "Low"

                        all_assignments.append({
                            "Assignment": assignment.get("name", "No Name").strip(),
                            "Subject/Course": course_name,
                            "Status": "Not Started",
                            "Due Date": formatted_due_date,
                            "Days Left": days_left,
                            "Priority Level": priority,
                            "Due Date Raw": due_date_dt
                        })

                # paginate
                url = response.links.get('next', {}).get('url')
            else:
                print(f"Error fetching assignments for {course_name}: {response.status_code}")
                print(response.text)
                break

    # Sort by due date & drop helper key
    sorted_assignments = sorted(all_assignments, key=lambda x: x["Due Date Raw"])
    for a in sorted_assignments:
        del a["Due Date Raw"]
    return sorted_assignments



def upload_to_google_sheets(data):
    # Auth
    google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(google_credentials), scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet
    sheet = client.open(SHEET_NAME).sheet1

    # Retry fetching existing assignment titles (column B)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            existing_titles = sheet.col_values(2)  # Column B = "Assignment"
            break
        except APIError as e:
            print(f"Google API error: {e}. Retrying ({attempt + 1}/{max_retries})...")
            time.sleep(10)
    else:
        print("Failed to fetch assignments after multiple retries.")
        return

    # Map existing titles -> row numbers
    title_to_row = {title: idx for idx, title in enumerate(existing_titles, start=1)}

    # Prepare updates for rows that already exist
    value_updates = []  # batch_update ranges
    new_rows_items = []  # items not yet in the sheet

    for item in data:
        title = item["Assignment"]
        if title in title_to_row:
            r = title_to_row[title]
            # Update Days Left formula and Priority Level
            value_updates.append({"range": f"F{r}", "values": [[f"=E{r}-TODAY()"]]})
            value_updates.append({"range": f"G{r}", "values": [[item["Priority Level"]]]})
        else:
            new_rows_items.append(item)

    # Apply updates for existing rows (if any)
    if value_updates:
        try:
            sheet.batch_update(value_updates, value_input_option="USER_ENTERED")
            print(f"Updated priority/days-left for {len(value_updates)//2} existing rows.")
        except APIError as e:
            print(f"Failed to update existing rows: {e}")

    # If no new rows, we’re done
    if not new_rows_items:
        print("No new assignments to add.")
        return

    # Append new rows at the first empty row
    start_row = len(existing_titles) + 1
    rows = [
        [
            item["Assignment"],
            item["Subject/Course"],
            item["Status"],
            item["Due Date"],
            f"=E{start_row + i}-TODAY()",  # Days Left formula
            item["Priority Level"]
        ]
        for i, item in enumerate(new_rows_items)
    ]

    end_row = start_row + len(rows) - 1
    cell_range = f"B{start_row}:G{end_row}"

    try:
        sheet.update(cell_range, rows, value_input_option="USER_ENTERED")
        print(f"Added {len(new_rows_items)} new assignments starting at row {start_row}.")
    except APIError as e:
        print(f"Failed to append new rows: {e}")

if __name__ == "__main__":
    while True:
        print("Checking for new assignments...")
        assignments = fetch_assignments()
        if assignments:
            upload_to_google_sheets(assignments)  
        else:
            print("No assignments found.")
        
        print("Waiting for 30 minutes before the next check...")
        time.sleep(1800)  
