import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import RPi.GPIO as GPIO
import sys
from google.oauth2 import service_account

# Add the app path to import the LED module
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from feedback_led import FeedbackLED

# Configuration
SERVICE_ACCOUNT_FILE = '/home/admin/projects/dome/credentials.json'
FOLDER_ID = '17HaNNrEE3UAcTqOx1ByTgk_FEUhybVxI'  # e.g., '1AbCDefGhijk...'
LOCAL_DIR = '/home/admin/projects/dome/audios'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

os.makedirs(LOCAL_DIR, exist_ok=True)

def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(svc, folder_id):
    # Only fetch mp3/wav to avoid downloading unwanted files
    q = f"'{folder_id}' in parents and (mimeType='audio/mpeg' or mimeType='audio/wav') and trashed=false"
    files = []
    page_token = None
    while True:
        resp = svc.files().list(
            q=q,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
            pageToken=page_token
        ).execute()
        files.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken', None)
        if page_token is None:
            break
    return files

def download_file(svc, file_id, dest_path):
    request = svc.files().get_media(fileId=file_id)
    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

def sync():
    svc = drive_service()
    files = list_files_in_folder(svc, FOLDER_ID)

    # Local index by name for comparison
    local_files = {f: os.path.getmtime(os.path.join(LOCAL_DIR, f)) for f in os.listdir(LOCAL_DIR)}

    for f in files:
        name = f['name']
        file_id = f['id']
        dest = os.path.join(LOCAL_DIR, name)

        # If it doesn't exist locally, or if you prefer to always re-download, download it:
        if not os.path.exists(dest):
            print(f'Descargando: {name}')
            download_file(svc, file_id, dest)
        else:
            # Optional: compare remote vs. local modification time to update
            # You can add logic here using f['modifiedTime']
            pass

    print('Sync finalizado.')

if __name__ == '__main__':
    led = None
    try:
        # Initialize GPIO and the LED
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        led = FeedbackLED()
        led.setup()
        led.start()
        led.set_mode('fast_blinking')

        sync()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Stop the LED and clean up GPIO
        if led:
            led.stop()
        GPIO.cleanup()
        print("GPIO cleanup finished.")
