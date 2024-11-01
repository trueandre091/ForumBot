import gspread
from oauth2client.service_account import ServiceAccountCredentials


JSON_KEYFILE = "google/credentials.json"
SHEET_NAME = "West Horeca Forum"
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


def connect_to_google_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME)
    worksheet = sheet.sheet1

    return worksheet



