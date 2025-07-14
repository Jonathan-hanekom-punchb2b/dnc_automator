"""
Data validation utilities
"""
import pandas as pd
from typing import Dict, Any, List
import re

def validate_dnc_file(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate DNC file structure and content"""
    
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check required columns
    required_columns = ['company_name']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        result['errors'].append(f"Missing required columns: {missing_columns}")
        result['valid'] = False
    
    # Check data types and content
    if 'company_name' in df.columns:
        empty_names = df['company_name'].isna().sum()
        if empty_names > 0:
            result['warnings'].append(f"{empty_names} rows have empty company names")
        
        # Check for suspicious patterns
        if len(df) > 0:
            short_names = df[df['company_name'].str.len() < 3]['company_name'].count()
            if short_names > 0:
                result['warnings'].append(f"{short_names} company names are very short")
    
    # Validate domains if present
    if 'domain' in df.columns:
        invalid_domains = validate_domains(df['domain'].dropna())
        if invalid_domains:
            result['warnings'].append(f"{len(invalid_domains)} domains appear invalid")
    
    return result

def validate_domains(domains: pd.Series) -> List[str]:
    """Validate domain formats"""
    
    domain_pattern = re.compile(
        r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    )
    
    invalid_domains = []
    
    for domain in domains:
        if isinstance(domain, str):
            # Clean domain (remove protocol, www)
            clean_domain = domain.lower().strip()
            if clean_domain.startswith(('http://', 'https://')):
                clean_domain = clean_domain.split('://', 1)[1]
            if clean_domain.startswith('www.'):
                clean_domain = clean_domain[4:]
            
            # Validate format
            if not domain_pattern.match(clean_domain):
                invalid_domains.append(domain)
    
    return invalid_domains

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate application configuration"""
    
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Required configuration keys
    required_keys = [
        'hubspot_api_key',
        'email_username',
        'email_password',
        'client_name',
        'company_status_property',
        'contact_status_property'
    ]
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        result['errors'].append(f"Missing required configuration: {missing_keys}")
        result['valid'] = False
    
    # Validate numeric values
    numeric_configs = [
        ('fuzzy_threshold_match', 0, 100),
        ('fuzzy_threshold_review', 0, 100),
        ('smtp_port', 1, 65535)
    ]
    
    for key, min_val, max_val in numeric_configs:
        value = config.get(key)
        if value is not None:
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                result['errors'].append(f"{key} must be a number between {min_val} and {max_val}")
                result['valid'] = False
    
    # Validate email format
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if config.get('email_username') and not email_pattern.match(config['email_username']):
        result['warnings'].append("Email username format may be invalid")
    
    # Validate email recipients
    recipients = config.get('email_recipients', [])
    if isinstance(recipients, list):
        invalid_emails = [email for email in recipients if not email_pattern.match(email.strip())]
        if invalid_emails:
            result['warnings'].append(f"Invalid email recipients: {invalid_emails}")
    
    return result