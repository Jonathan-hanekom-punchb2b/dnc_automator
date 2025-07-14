"""
Main orchestration script for DNC automation
Coordinates all components and handles the complete workflow
"""
import os
import sys
import uuid
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.dnc_logic import DNCChecker, DNSMatch
from src.hubspot.client import HubSpotClient, UpdateResult
from src.notifications.email_sender import EmailNotifier
from src.utils.logger import setup_logging
from src.utils.file_handler import FileHandler
from src.utils.validators import validate_dnc_file, validate_config

logger = logging.getLogger(__name__)

class DNCAutomation:
    """Main DNC automation orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.run_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        
        # Initialize components
        self.hubspot_client = HubSpotClient(api_key=config['hubspot_api_key'])
        self.dnc_checker = DNCChecker(
            fuzzy_threshold_match=config['fuzzy_threshold_match'],
            fuzzy_threshold_review=config['fuzzy_threshold_review']
        )
        self.email_notifier = EmailNotifier(
            smtp_host=config['smtp_host'],
            smtp_port=config['smtp_port'],
            username=config['email_username'],
            password=config['email_password'],
            recipients=config['email_recipients']
        )
        self.file_handler = FileHandler(config)
        
        # Runtime tracking
        self.run_summary = {
            'run_id': self.run_id,
            'client_name': config['client_name'],
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'companies_checked': 0,
            'matches_found': 0,
            'companies_updated': 0,
            'contacts_updated': 0,
            'matches': [],
            'errors': []
        }
    
    def run_dnc_check(self, dnc_file_path: str = None) -> bool:
        """Execute complete DNC check workflow"""
        
        try:
            logger.info(f"Starting DNC check run {self.run_id}")
            
            # Step 1: Load and validate DNC list
            dnc_df = self._load_dnc_list(dnc_file_path)
            if dnc_df is None:
                return False
            
            # Step 2: Fetch HubSpot companies
            logger.info("Fetching companies from HubSpot...")
            hubspot_companies = self.hubspot_client.get_all_companies(
                properties=['name', 'domain', self.config['company_status_property']]
            )
            
            self.run_summary['companies_checked'] = len(hubspot_companies)
            logger.info(f"Checking {len(hubspot_companies)} companies against DNC list")
            
            # Step 3: Check for matches
            matches = self.dnc_checker.check_companies_against_dnc(
                hubspot_companies, dnc_df
            )
            
            self.run_summary['matches_found'] = len(matches)
            logger.info(f"Found {len(matches)} DNC matches")
            
            # Step 4: Process matches and update HubSpot
            if matches:
                success = self._process_matches(matches)
                if not success:
                    return False
            
            # Step 5: Generate results and send notifications
            self._finalize_run()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in DNC check run: {str(e)}")
            self._handle_error(e)
            return False
    
    def _load_dnc_list(self, file_path: str = None) -> pd.DataFrame:
        """Load and validate DNC list"""
        
        try:
            if file_path:
                # Use provided file path
                dnc_file = file_path
            else:
                # Find latest DNC file for this client
                dnc_file = self.file_handler.get_latest_dnc_file(
                    self.config['client_name']
                )
            
            if not dnc_file:
                raise FileNotFoundError("No DNC file found for processing")
            
            logger.info(f"Loading DNC list: {dnc_file}")
            
            # Load CSV file
            dnc_df = pd.read_csv(dnc_file)
            
            # Validate file structure
            validation_result = validate_dnc_file(dnc_df)
            if not validation_result['valid']:
                raise ValueError(f"Invalid DNC file: {validation_result['errors']}")
            
            self.run_summary['dnc_list_name'] = os.path.basename(dnc_file)
            
            logger.info(f"Loaded {len(dnc_df)} companies from DNC list")
            return dnc_df
            
        except Exception as e:
            logger.error(f"Error loading DNC list: {str(e)}")
            self.run_summary['errors'].append(f"DNC list loading: {str(e)}")
            return None
    
    def _process_matches(self, matches: List[DNSMatch]) -> bool:
        """Process DNC matches and update HubSpot"""
        
        try:
            companies_updated = 0
            contacts_updated = 0
            
            for match in matches:
                if match.action == 'auto_exclude':
                    # Update company status
                    company_result = self.hubspot_client.update_company_status(
                        company_id=match.company_id,
                        status_property=self.config['company_status_property'],
                        new_status='Client Working'
                    )
                    
                    if company_result.success:
                        companies_updated += 1
                        
                        # Get and update associated contacts
                        contacts = self.hubspot_client.get_contacts_for_company(
                            match.company_id
                        )
                        
                        if contacts:
                            contact_ids = [contact['id'] for contact in contacts]
                            contact_results = self.hubspot_client.batch_update_contacts(
                                contact_ids=contact_ids,
                                status_property=self.config['contact_status_property'],
                                new_status='On Hold'
                            )
                            
                            successful_contacts = [
                                r.object_id for r in contact_results if r.success
                            ]
                            contacts_updated += len(successful_contacts)
                            match.contact_count = len(successful_contacts)
                    
                    # Add to summary
                    self.run_summary['matches'].append({
                        'company_name': match.company_name,
                        'dnc_company_name': match.dnc_company_name,
                        'match_type': match.match_type,
                        'confidence': match.confidence,
                        'action': match.action,
                        'contact_count': match.contact_count
                    })
                
                elif match.action == 'review':
                    # Log for manual review
                    logger.warning(f"Manual review required: {match.company_name} "
                                 f"(confidence: {match.confidence}%)")
                    
                    # Add to summary for review
                    self.run_summary['matches'].append({
                        'company_name': match.company_name,
                        'dnc_company_name': match.dnc_company_name,
                        'match_type': match.match_type,
                        'confidence': match.confidence,
                        'action': match.action,
                        'contact_count': 0
                    })
            
            self.run_summary['companies_updated'] = companies_updated
            self.run_summary['contacts_updated'] = contacts_updated
            
            logger.info(f"Updated {companies_updated} companies and "
                       f"{contacts_updated} contacts")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing matches: {str(e)}")
            self.run_summary['errors'].append(f"Match processing: {str(e)}")
            return False
    
    def _finalize_run(self):
        """Finalize run and send notifications"""
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        self.run_summary.update({
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': str(duration).split('.')[0]  # Remove microseconds
        })
        
        # Save results to file
        results_file = self._save_results()
        
        # Send success notification
        self.email_notifier.send_success_summary(
            run_summary=self.run_summary,
            attachment_path=results_file
        )
        
        logger.info(f"DNC check run {self.run_id} completed successfully")
    
    def _save_results(self) -> str:
        """Save run results to file"""
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join('data', 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(
            results_dir,
            f"{self.config['client_name']}_dnc_results_{self.run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        # Create results DataFrame
        if self.run_summary['matches']:
            results_df = pd.DataFrame(self.run_summary['matches'])
            results_df['run_id'] = self.run_id
            results_df['timestamp'] = self.start_time
            
            results_df.to_csv(results_file, index=False)
            logger.info(f"Results saved to {results_file}")
        
        return results_file
    
    def _handle_error(self, error: Exception):
        """Handle errors and send notifications"""
        
        import traceback
        
        error_details = {
            'run_id': self.run_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'client_name': self.config.get('client_name', 'Unknown'),
            'stack_trace': traceback.format_exc(),
            'context': {
                'companies_checked': self.run_summary.get('companies_checked', 0),
                'matches_found': self.run_summary.get('matches_found', 0),
                'previous_errors': self.run_summary.get('errors', [])
            }
        }
        
        # Send error notification
        self.email_notifier.send_error_notification(error_details)
        
        logger.error(f"DNC check run {self.run_id} failed with error: {str(error)}")

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    
    load_dotenv()
    
    config = {
        # HubSpot
        'hubspot_api_key': os.getenv('HUBSPOT_API_KEY'),
        'hubspot_instance_name': os.getenv('HUBSPOT_INSTANCE_NAME'),
        
        # Email
        'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'email_username': os.getenv('EMAIL_USERNAME'),
        'email_password': os.getenv('EMAIL_PASSWORD'),
        'email_recipients': os.getenv('EMAIL_RECIPIENTS', '').split(','),
        
        # DNC Settings
        'fuzzy_threshold_match': int(os.getenv('FUZZY_THRESHOLD_MATCH', 90)),
        'fuzzy_threshold_review': int(os.getenv('FUZZY_THRESHOLD_REVIEW', 85)),
        
        # Client Configuration
        'client_name': os.getenv('CLIENT_NAME'),
        'company_status_property': os.getenv('COMPANY_STATUS_PROPERTY'),
        'contact_status_property': os.getenv('CONTACT_STATUS_PROPERTY'),
        
        # File Paths
        'dnc_upload_path': os.getenv('DNC_UPLOAD_PATH', 'data/uploads'),
        'dnc_processed_path': os.getenv('DNC_PROCESSED_PATH', 'data/processed'),
        'dnc_archived_path': os.getenv('DNC_ARCHIVED_PATH', 'data/archived'),
        
        # Processing
        'company_batch_size': int(os.getenv('COMPANY_BATCH_SIZE', 100)),
        'contact_batch_size': int(os.getenv('CONTACT_BATCH_SIZE', 500)),
    }
    
    # Validate configuration
    validation_result = validate_config(config)
    if not validation_result['valid']:
        raise ValueError(f"Invalid configuration: {validation_result['errors']}")
    
    return config

def main():
    """Main entry point"""
    
    # Setup logging
    setup_logging()
    
    try:
        # Load configuration
        config = load_config()
        
        # Create automation instance
        automation = DNCAutomation(config)
        
        # Run DNC check
        success = automation.run_dnc_check()
        
        if success:
            logger.info("DNC automation completed successfully")
            sys.exit(0)
        else:
            logger.error("DNC automation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in DNC automation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()