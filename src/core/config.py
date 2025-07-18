"""
Configuration management for DNC Automator
Centralized loading and validation of all application settings
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass

class Config:
    """Central configuration management for DNC Automator"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration from environment variables
        
        Args:
            env_file: Path to .env file (optional, defaults to .env in project root)
        """
        self._load_environment(env_file)
        self._validate_configuration()
        self._setup_logging()
    
    def _load_environment(self, env_file: Optional[str] = None):
        """Load environment variables from .env file and system environment"""
        if env_file is None:
            # Look for .env file in project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / '.env'
        
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        else:
            logger.warning(f"No .env file found at {env_file}, using system environment only")
    
    def _validate_configuration(self):
        """Validate all configuration values"""
        errors = []
        
        # Validate required settings
        required_settings = [
            'HUBSPOT_API_KEY',
            'EMAIL_USERNAME',
            'EMAIL_PASSWORD',
        ]
        
        for setting in required_settings:
            value = self._get_env_var(setting)
            if not value:
                errors.append(f"Missing required environment variable: {setting}")
            elif self._is_placeholder_value(value):
                errors.append(f"{setting} appears to be a placeholder value: {value}")
        
        # Validate numeric settings
        numeric_settings = {
            'FUZZY_THRESHOLD_MATCH': (0, 100),
            'FUZZY_THRESHOLD_REVIEW': (0, 100),
            'SMTP_PORT': (1, 65535),
            'COMPANY_BATCH_SIZE': (1, 1000),
            'CONTACT_BATCH_SIZE': (1, 1000),
        }
        
        for setting, (min_val, max_val) in numeric_settings.items():
            value = self._get_env_var(setting)
            if value:
                try:
                    num_value = int(value)
                    if not (min_val <= num_value <= max_val):
                        errors.append(f"{setting} must be between {min_val} and {max_val}")
                except ValueError:
                    errors.append(f"{setting} must be a valid integer")
        
        # Validate email format (basic check)
        email = self._get_env_var('EMAIL_USERNAME')
        if email and '@' not in email:
            errors.append("EMAIL_USERNAME must be a valid email address")
        
        if errors:
            raise ConfigurationError(f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))
        
        logger.info("Configuration validation passed")
    
    def _is_placeholder_value(self, value: str) -> bool:
        """Check if a value appears to be a placeholder"""
        if not value:
            return False
        
        placeholder_patterns = [
            'your_',
            'your-',
            'placeholder',
            'example',
            'test_',
            'dummy',
            'fake',
            'change_this',
            'replace_this',
            'add_your',
            'insert_your',
        ]
        
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in placeholder_patterns)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self._get_env_var('LOG_LEVEL', 'INFO').upper()
        
        # Ensure logs directory exists
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default"""
        value = os.getenv(key, default)
        return value if value else None
    
    # HubSpot Configuration
    @property
    def hubspot_api_key(self) -> str:
        """HubSpot API key for authentication"""
        return self._get_env_var('HUBSPOT_API_KEY')
    
    @property
    def hubspot_instance_name(self) -> str:
        """HubSpot instance name"""
        return self._get_env_var('HUBSPOT_INSTANCE_NAME', 'default')
    
    # Email Configuration
    @property
    def smtp_host(self) -> str:
        """SMTP host for email notifications"""
        return self._get_env_var('SMTP_HOST', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        """SMTP port for email notifications"""
        return int(self._get_env_var('SMTP_PORT', '587'))
    
    @property
    def email_username(self) -> str:
        """Email username for authentication"""
        return self._get_env_var('EMAIL_USERNAME')
    
    @property
    def email_password(self) -> str:
        """Email password for authentication"""
        return self._get_env_var('EMAIL_PASSWORD')
    
    @property
    def email_recipients(self) -> List[str]:
        """List of email recipients for notifications"""
        recipients = self._get_env_var('EMAIL_RECIPIENTS', '')
        return [email.strip() for email in recipients.split(',') if email.strip()]
    
    # DNC Logic Configuration
    @property
    def fuzzy_threshold_match(self) -> int:
        """Fuzzy matching threshold for automatic action"""
        return int(self._get_env_var('FUZZY_THRESHOLD_MATCH', '90'))
    
    @property
    def fuzzy_threshold_review(self) -> int:
        """Fuzzy matching threshold for manual review"""
        return int(self._get_env_var('FUZZY_THRESHOLD_REVIEW', '85'))
    
    @property
    def company_batch_size(self) -> int:
        """Batch size for company updates"""
        return int(self._get_env_var('COMPANY_BATCH_SIZE', '100'))
    
    @property
    def contact_batch_size(self) -> int:
        """Batch size for contact updates"""
        return int(self._get_env_var('CONTACT_BATCH_SIZE', '500'))
    
    # File Path Configuration
    @property
    def dnc_upload_path(self) -> str:
        """Path for DNC file uploads"""
        return self._get_env_var('DNC_UPLOAD_PATH', 'data/uploads')
    
    @property
    def dnc_processed_path(self) -> str:
        """Path for processed DNC files"""
        return self._get_env_var('DNC_PROCESSED_PATH', 'data/processed')
    
    @property
    def dnc_archived_path(self) -> str:
        """Path for archived DNC files"""
        return self._get_env_var('DNC_ARCHIVED_PATH', 'data/archived')
    
    # Dynamic Client Configuration
    @property
    def company_status_suffix(self) -> str:
        """Suffix for company status property names"""
        return self._get_env_var('COMPANY_STATUS_SUFFIX', '_account_status')
    
    @property
    def contact_status_suffix(self) -> str:
        """Suffix for contact status property names"""
        return self._get_env_var('CONTACT_STATUS_SUFFIX', '_funnel_status')
    
    # Google Drive Configuration
    @property
    def google_drive_folder_id(self) -> Optional[str]:
        """Google Drive folder ID for DNC files"""
        return self._get_env_var('GOOGLE_DRIVE_FOLDER_ID')
    
    @property
    def google_drive_credentials_path(self) -> Optional[str]:
        """Path to Google Drive credentials file"""
        return self._get_env_var('GOOGLE_DRIVE_CREDENTIALS_PATH', 'config/google_credentials.json')
    
    def get_client_config(self, client_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific client
        
        Args:
            client_name: Name of the client
            
        Returns:
            Dictionary with client-specific configuration
        """
        return {
            'client_name': client_name,
            'company_status_property': f"{client_name}{self.company_status_suffix}",
            'contact_status_property': f"{client_name}{self.contact_status_suffix}",
            'hubspot_api_key': self.hubspot_api_key,
            'fuzzy_threshold_match': self.fuzzy_threshold_match,
            'fuzzy_threshold_review': self.fuzzy_threshold_review,
            'company_batch_size': self.company_batch_size,
            'contact_batch_size': self.contact_batch_size,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging"""
        return {
            'hubspot_instance_name': self.hubspot_instance_name,
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'email_username': self.email_username,
            'email_recipients': self.email_recipients,
            'fuzzy_threshold_match': self.fuzzy_threshold_match,
            'fuzzy_threshold_review': self.fuzzy_threshold_review,
            'company_batch_size': self.company_batch_size,
            'contact_batch_size': self.contact_batch_size,
            'dnc_upload_path': self.dnc_upload_path,
            'dnc_processed_path': self.dnc_processed_path,
            'dnc_archived_path': self.dnc_archived_path,
            'company_status_suffix': self.company_status_suffix,
            'contact_status_suffix': self.contact_status_suffix,
            'google_drive_folder_id': self.google_drive_folder_id,
            'google_drive_credentials_path': self.google_drive_credentials_path,
        }

# Global configuration instance
config = None

def get_config(env_file: Optional[str] = None) -> Config:
    """
    Get the global configuration instance
    
    Args:
        env_file: Path to .env file (only used on first call)
        
    Returns:
        Global Config instance
    """
    global config
    if config is None:
        config = Config(env_file)
    return config

def reset_config():
    """Reset the global configuration (useful for testing)"""
    global config
    config = None