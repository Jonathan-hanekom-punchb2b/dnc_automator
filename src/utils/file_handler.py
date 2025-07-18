"""
File handling utilities for DNC automation
"""
import os
import shutil
import glob
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import logging
import re

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file operations for DNC automation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.upload_path = config['dnc_upload_path']
        self.processed_path = config['dnc_processed_path']
        self.archived_path = config.get('dnc_archived_path', 'data/archived')
        
        # Ensure directories exist
        for path in [self.upload_path, self.processed_path, self.archived_path]:
            os.makedirs(path, exist_ok=True)
    
    def get_latest_dnc_file(self, client_name: str) -> Optional[str]:
        """Get the latest DNC file for a client"""
        
        # Look for files matching pattern: client_name_dd-mm-yy.csv
        pattern = os.path.join(self.upload_path, f"{client_name}_*.csv")
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No DNC files found for client: {client_name}")
            return None
        
        # Sort by modification time, return newest
        files.sort(key=os.path.getmtime, reverse=True)
        latest_file = files[0]
        
        logger.info(f"Found latest DNC file: {latest_file}")
        return latest_file
    
    def move_to_processed(self, file_path: str) -> str:
        """Move file from uploads to processed folder"""
        
        filename = os.path.basename(file_path)
        processed_file = os.path.join(self.processed_path, filename)
        
        shutil.move(file_path, processed_file)
        logger.info(f"Moved {filename} to processed folder")
        
        return processed_file
    
    def archive_old_files(self, days_old: int = 30) -> int:
        """Archive files older than specified days"""
        
        archived_count = 0
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        # Archive from processed folder
        for file_path in glob.glob(os.path.join(self.processed_path, "*.csv")):
            if os.path.getmtime(file_path) < cutoff_time:
                filename = os.path.basename(file_path)
                archived_file = os.path.join(self.archived_path, filename)
                shutil.move(file_path, archived_file)
                archived_count += 1
                logger.info(f"Archived old file: {filename}")
        
        return archived_count
    
    def validate_file_format(self, file_path: str) -> dict:
        """Validate DNC file format and content"""
        
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'row_count': 0
        }
        
        try:
            # Check file exists
            if not os.path.exists(file_path):
                result['errors'].append("File does not exist")
                return result
            
            # Try to read as CSV
            df = pd.read_csv(file_path)
            result['row_count'] = len(df)
            
            # Check required columns
            required_columns = ['company_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                result['errors'].append(f"Missing required columns: {missing_columns}")
            
            # Check for empty data
            if df.empty:
                result['errors'].append("File contains no data")
            
            # Check for missing company names
            if 'company_name' in df.columns:
                empty_names = df['company_name'].isna().sum()
                if empty_names > 0:
                    result['warnings'].append(f"{empty_names} rows have empty company names")
            
            # Validate domain column if present
            if 'domain' in df.columns:
                empty_domains = df['domain'].isna().sum()
                if empty_domains > 0:
                    result['warnings'].append(f"{empty_domains} rows have empty domains")
            
            # Set valid if no errors
            result['valid'] = len(result['errors']) == 0
            
        except Exception as e:
            result['errors'].append(f"Error reading file: {str(e)}")
        
        return result
    
    def extract_client_name(self, filename: str) -> str:
        """
        Extract client name from filename
        Expected format: client_name_16-07-25.csv
        """
        # Remove .csv extension
        if not filename.endswith('.csv'):
            raise ValueError(f"Invalid file format: {filename} (must be .csv)")
        
        name_without_ext = filename[:-4]  # Remove .csv
        
        # Pattern: client_name_DD-MM-YY
        pattern = r'^(.+)_(\d{2}-\d{2}-\d{2})$'
        match = re.match(pattern, name_without_ext)
        
        if not match:
            raise ValueError(f"Invalid filename format: {filename} (expected: client_name_16-07-25.csv)")
        
        client_name = match.group(1)
        date_part = match.group(2)
        
        # Validate date format
        if not re.match(r'^\d{2}-\d{2}-\d{2}$', date_part):
            raise ValueError(f"Invalid date format in filename: {filename}")
        
        return client_name
    
    def generate_company_property_name(self, client_name: str) -> str:
        """Generate HubSpot company property name from client name"""
        return f"{client_name}_account_status"
    
    def generate_contact_property_name(self, client_name: str) -> str:
        """Generate HubSpot contact property name from client name"""
        return f"{client_name}_funnel_status"
    
    def get_all_client_files(self) -> Dict[str, str]:
        """
        Get all client files from upload path
        Returns dict mapping client_name -> file_path
        """
        client_files = {}
        
        # Look for files matching pattern: *_DD-MM-YY.csv
        pattern = os.path.join(self.upload_path, "*_??-??-??.csv")
        files = glob.glob(pattern)
        
        for file_path in files:
            filename = os.path.basename(file_path)
            try:
                client_name = self.extract_client_name(filename)
                # If multiple files for same client, keep the most recent
                if client_name not in client_files or os.path.getmtime(file_path) > os.path.getmtime(client_files[client_name]):
                    client_files[client_name] = file_path
            except ValueError as e:
                logger.warning(f"Skipping invalid filename {filename}: {e}")
                continue
        
        return client_files