import os
import io
import json
import argparse
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from src.config import MODEL_DIR

def get_drive_service():
    # Attempt to load from Streamlit secrets first, fallback to OS environment variables
    try:
        import streamlit as st
        creds_json_str = st.secrets.get("GCP_SA_KEY", os.environ.get("GCP_SA_KEY"))
        folder_id = st.secrets.get("GDRIVE_FOLDER_ID", os.environ.get("GDRIVE_FOLDER_ID"))
    except Exception:
        creds_json_str = os.environ.get("GCP_SA_KEY")
        folder_id = os.environ.get("GDRIVE_FOLDER_ID")

    if not creds_json_str or not folder_id:
        raise ValueError("Missing GCP_SA_KEY or GDRIVE_FOLDER_ID environment variables.")

    creds_info = json.loads(creds_json_str)
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    
    service = build('drive', 'v3', credentials=creds)
    return service, folder_id

def sync_from_drive():
    """Downloads all models from the Google Drive folder to local MODEL_DIR."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    service, folder_id = get_drive_service()
    
    print(f"Fetching files from Google Drive folder: {folder_id}...")
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])
    if not items:
        print("No files found in Google Drive.")
        return

    for item in items:
        file_id = item['id']
        file_name = item['name']
        local_path = os.path.join(MODEL_DIR, file_name)
        
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print(f"Downloaded {file_name} to {local_path}")

def sync_to_drive():
    """Uploads all local models in MODEL_DIR to Google Drive, overwriting existing files."""
    service, folder_id = get_drive_service()
    
    # Get existing files in drive to overwrite them if they exist
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    existing_files = {item['name']: item['id'] for item in results.get('files', [])}

    for file_name in os.listdir(MODEL_DIR):
        local_path = os.path.join(MODEL_DIR, file_name)
        if not os.path.isfile(local_path):
            continue
            
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(local_path, resumable=True)
        
        if file_name in existing_files:
            # Update existing file
            file_id = existing_files[file_name]
            print(f"Updating {file_name} in Google Drive...")
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Create new file
            print(f"Uploading new file {file_name} to Google Drive...")
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--upload', action='store_true', help="Upload local models to GDrive")
    parser.add_argument('--download', action='store_true', help="Download models from GDrive to local")
    args = parser.parse_args()
    
    if args.upload:
        sync_to_drive()
    elif args.download:
        sync_from_drive()
    else:
        print("Please specify --upload or --download")
