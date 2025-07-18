"""
Google Drive client for DNC Automator
Handles authentication and file operations with Google Drive API
"""
import os
import pickle
import logging
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveClient:
    """Client for interacting with Google Drive API"""
    
    def __init__(self, credentials_path: str, token_path: str = None):
        """
        Initialize Google Drive client
        
        Args:
            credentials_path: Path to Google credentials JSON file
            token_path: Path to store OAuth token (optional for service account)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # Check if we have a service account credentials file
        if os.path.exists(self.credentials_path):
            try:
                # Try service account authentication first
                creds = Credentials.from_service_account_file(
                    self.credentials_path, 
                    scopes=SCOPES
                )
                logger.info("Using service account authentication")
            except Exception as e:
                logger.warning(f"Service account auth failed: {e}")
                # Fall back to OAuth flow
                creds = self._oauth_flow()
        else:
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
        
        if not creds:
            raise Exception("Failed to authenticate with Google Drive API")
        
        # Build the service
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive service initialized successfully")
    
    def _oauth_flow(self):
        """Handle OAuth authentication flow"""
        creds = None
        
        # Check if we have a token file
        if self.token_path and os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            if self.token_path:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
        
        return creds
    
    def list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """
        List all files in a Google Drive folder
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            List of file dictionaries with 'name' and 'id' keys
        """
        try:
            # Query for files in the specific folder
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            
            # Filter out folders, only return files
            file_list = []
            for file in files:
                if file.get('mimeType') != 'application/vnd.google-apps.folder':
                    file_list.append({
                        'id': file['id'],
                        'name': file['name'],
                        'mimeType': file.get('mimeType', ''),
                        'modifiedTime': file.get('modifiedTime', '')
                    })
            
            logger.info(f"Found {len(file_list)} files in folder {folder_id}")
            return file_list
            
        except Exception as e:
            logger.error(f"Error listing files in folder {folder_id}: {e}")
            raise
    
    def download_file(self, file_id: str, file_name: str, download_path: str) -> str:
        """
        Download a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            file_name: Name of the file
            download_path: Local path to save the file
            
        Returns:
            Path to the downloaded file
        """
        try:
            # Ensure download directory exists
            os.makedirs(download_path, exist_ok=True)
            
            # Full path for the downloaded file
            file_path = os.path.join(download_path, file_name)
            
            # Request file content
            request = self.service.files().get_media(fileId=file_id)
            
            # Download the file
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}% complete")
            
            # Write to file
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Downloaded {file_name} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading file {file_name}: {e}")
            raise
    
    def download_dnc_files(self, folder_id: str, download_path: str) -> List[str]:
        """
        Download all DNC files from a Google Drive folder
        
        Args:
            folder_id: Google Drive folder ID
            download_path: Local path to save files
            
        Returns:
            List of paths to downloaded files
        """
        try:
            # List all files in the folder
            files = self.list_files_in_folder(folder_id)
            
            # Filter for DNC files (ending with _16-07-25.csv)
            dnc_files = [f for f in files if f['name'].endswith('_16-07-25.csv')]
            
            logger.info(f"Found {len(dnc_files)} DNC files to download")
            
            downloaded_files = []
            
            for file in dnc_files:
                try:
                    file_path = self.download_file(
                        file['id'], 
                        file['name'], 
                        download_path
                    )
                    downloaded_files.append(file_path)
                    logger.info(f"Successfully downloaded: {file['name']}")
                except Exception as e:
                    logger.error(f"Failed to download {file['name']}: {e}")
                    continue
            
            logger.info(f"Downloaded {len(downloaded_files)} DNC files")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading DNC files: {e}")
            raise
    
    def get_file_info(self, file_id: str) -> Dict:
        """
        Get information about a specific file
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Dictionary with file information
        """
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, parents"
            ).execute()
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_id}: {e}")
            raise