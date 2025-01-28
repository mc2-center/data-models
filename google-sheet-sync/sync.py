import os
import csv
from io import StringIO
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from github import Github

def authenticate_google(credentials_file):
    creds = Credentials.from_service_account_file(credentials_file, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return build('sheets', 'v4', credentials=creds)

def get_sheet_name(service, spreadsheet_id):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return sheet_metadata.get("properties", {}).get("title", "UntitledSheet").replace(" ", "-")

def get_sheet_data_as_csv(service, spreadsheet_id, range="A1:Z1000"):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
    data = result.get('values', [])
    if not data:
        return None
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    output.seek(0)
    return output.read()

def main():
    
    spreadsheet_id = os.getenv("INPUT_SPREADSHEET_ID")
    stop_time = os.getenv("INPUT_STOP_TIME")
    stop_day = os.getenv("INPUT_STOP_DAY")
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    credentials_file = "./google-credentials.json"  # Path to dynamically created credentials file

    
    service = authenticate_google(credentials_file)

    sheet_name = get_sheet_name(service, spreadsheet_id)
    branch_name = f"RFC-{sheet_name}"
    file_path = f"RFC_DATA/{sheet_name}.csv"

    github = Github(github_token)
    repo = github.get_repo(repo_name)

    current_day = datetime.utcnow().strftime("%Y-%m-%d")
    current_time = datetime.utcnow().strftime("%H:%M")

    
    if current_day > stop_day or (current_day == stop_day and current_time > stop_time):
        print(f"Current day/time ({current_day} {current_time}) has exceeded the stop conditions ({stop_day} {stop_time}). Exiting.")
        return


    csv_content = get_sheet_data_as_csv(service, spreadsheet_id)
    if not csv_content:
        print("No data fetched from Google Sheet. Exiting.")
        return

    # Ensure branch exists
    try:
        repo.get_branch(branch_name)
    except Exception:
        main_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)

    # Commit changes to the branch
    try:
        contents = None
        try:
            contents = repo.get_contents(file_path, ref=branch_name)
        except Exception:
            pass
        if contents:
            repo.update_file(file_path, "Update CSV file from Google Sheet", csv_content, contents.sha, branch=branch_name)
        else:
            repo.create_file(file_path, "Create CSV file from Google Sheet", csv_content, branch=branch_name)
    except Exception as e:
        print(f"Error committing changes: {e}")

    # Create or reuse PR
    try:
        open_prs = repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch_name}")
        if open_prs.totalCount == 0:
            repo.create_pull(
                title=f"{branch_name} Updates",
                body="This PR contains updates from the linked Google Sheet.",
                head=branch_name,
                base="main",
            )
    except Exception as e:
        print(f"Error creating PR: {e}")

if __name__ == "__main__":
    main()