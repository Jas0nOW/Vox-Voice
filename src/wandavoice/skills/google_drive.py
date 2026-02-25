import os
import json
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class GoogleDriveSkill:
    def __init__(self, config):
        self.config = config
        self.creds_path = os.path.expanduser("~/.gemini/oauth_creds.json")
        self.service = self._get_service()

    def _get_service(self):
        if not os.path.exists(self.creds_path):
            return None
        try:
            with open(self.creds_path, 'r') as f:
                info = json.load(f)
            
            # Note: client_id and client_secret might be missing in the flat oauth_creds.json
            # If so, we'd need them from another file or hardcoded for the app.
            # But let's try with what we have.
            creds = Credentials(
                token=info.get('access_token'),
                refresh_token=info.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=info.get('client_id'), # Might be None
                client_secret=info.get('client_secret'), # Might be None
                scopes=info.get('scope', '').split()
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"[DRIVE] Auth Error: {e}")
            return None

    def upload_file(self, local_path, folder_name="WANDA_Sync"):
        if not self.service:
            return "Error: Google Drive not authenticated."
        
        try:
            # 1. Find or create folder
            folder_id = self._get_or_create_folder(folder_name)
            
            # 2. Upload
            file_metadata = {
                'name': os.path.basename(local_path),
                'parents': [folder_id]
            }
            media = MediaFileUpload(local_path, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            return f"Success: File uploaded to Drive (ID: {file.get('id')})"
        except Exception as e:
            return f"Error uploading to Drive: {e}"

    def _get_or_create_folder(self, folder_name):
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create it
        metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.service.files().create(body=metadata, fields='id').execute()
        return folder.get('id')

def drive_op(op, **kwargs):
    from wandavoice.config import Config
    cfg = Config()
    drive = GoogleDriveSkill(cfg)
    
    if op == "upload":
        return drive.upload_file(kwargs.get("path"))
    else:
        return f"Error: Unknown Drive operation '{op}'"
