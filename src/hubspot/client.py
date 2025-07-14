"""
HubSpot API client wrapper
Handles all HubSpot API interactions with rate limiting and error handling
"""
import hubspot
from hubspot.crm.companies import SimplePublicObjectInput, PublicObjectSearchRequest
from hubspot.crm.contacts import SimplePublicObjectInput as ContactInput
from typing import List, Dict, Any, Optional
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UpdateResult:
    """Result of a HubSpot update operation"""
    success: bool
    object_id: str
    object_type: str
    error: Optional[str] = None

class HubSpotClient:
    """HubSpot API client wrapper with rate limiting and error handling"""
    
    def __init__(self, api_key: str):
        self.client = hubspot.Client.create(access_token=api_key)
        self.rate_limit_delay = 0.1  # 100ms between requests
    
    def get_all_companies(self, 
                         properties: List[str] = None,
                         limit: int = 100) -> List[Dict]:
        """Fetch all companies from HubSpot with pagination"""
        if properties is None:
            properties = ['name', 'domain']
        
        companies = []
        after = None
        
        try:
            while True:
                # Add rate limiting
                time.sleep(self.rate_limit_delay)
                
                response = self.client.crm.companies.basic_api.get_page(
                    limit=limit,
                    after=after,
                    properties=properties
                )
                
                for company in response.results:
                    companies.append({
                        'id': company.id,
                        'properties': company.properties
                    })
                
                # Check if there are more pages
                if not response.paging or not response.paging.next:
                    break
                
                after = response.paging.next.after
                
                if len(companies) % 1000 == 0:
                    logger.info(f"Fetched {len(companies)} companies so far...")
        
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            raise
        
        logger.info(f"Successfully fetched {len(companies)} companies")
        return companies
    
    def get_contacts_for_company(self, 
                                company_id: str,
                                properties: List[str] = None) -> List[Dict]:
        """Get all contacts associated with a company"""
        if properties is None:
            properties = ['firstname', 'lastname', 'email']
        
        contacts = []
        
        try:
            # Get contacts associated with this company
            response = self.client.crm.companies.associations_api.get_all(
                company_id=company_id,
                to_object_type='contacts',
                limit=100
            )
            
            if not response.results:
                return contacts
            
            contact_ids = [assoc.to_object_id for assoc in response.results]
            
            # Fetch contact details in batches
            for i in range(0, len(contact_ids), 100):
                batch_ids = contact_ids[i:i+100]
                
                time.sleep(self.rate_limit_delay)
                
                batch_response = self.client.crm.contacts.batch_api.read(
                    batch_read_input_simple_public_object_id={
                        'properties': properties,
                        'inputs': [{'id': contact_id} for contact_id in batch_ids]
                    }
                )
                
                for contact in batch_response.results:
                    contacts.append({
                        'id': contact.id,
                        'properties': contact.properties
                    })
        
        except Exception as e:
            logger.error(f"Error fetching contacts for company {company_id}: {str(e)}")
            raise
        
        return contacts
    
    def update_company_status(self, 
                            company_id: str,
                            status_property: str,
                            new_status: str) -> UpdateResult:
        """Update company status property"""
        try:
            time.sleep(self.rate_limit_delay)
            
            update_input = SimplePublicObjectInput(
                properties={status_property: new_status}
            )
            
            response = self.client.crm.companies.basic_api.update(
                company_id=company_id,
                simple_public_object_input=update_input
            )
            
            logger.info(f"Updated company {company_id} status to {new_status}")
            
            return UpdateResult(
                success=True,
                object_id=company_id,
                object_type='company'
            )
        
        except Exception as e:
            logger.error(f"Error updating company {company_id}: {str(e)}")
            return UpdateResult(
                success=False,
                object_id=company_id,
                object_type='company',
                error=str(e)
            )
    
    def update_contact_status(self, 
                            contact_id: str,
                            status_property: str,
                            new_status: str) -> UpdateResult:
        """Update contact status property"""
        try:
            time.sleep(self.rate_limit_delay)
            
            update_input = ContactInput(
                properties={status_property: new_status}
            )
            
            response = self.client.crm.contacts.basic_api.update(
                contact_id=contact_id,
                simple_public_object_input=update_input
            )
            
            logger.info(f"Updated contact {contact_id} status to {new_status}")
            
            return UpdateResult(
                success=True,
                object_id=contact_id,
                object_type='contact'
            )
        
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {str(e)}")
            return UpdateResult(
                success=False,
                object_id=contact_id,
                object_type='contact',
                error=str(e)
            )
    
    def batch_update_contacts(self, 
                            contact_ids: List[str],
                            status_property: str,
                            new_status: str) -> List[UpdateResult]:
        """Batch update multiple contacts"""
        results = []
        
        # Process in batches of 100 (HubSpot limit)
        for i in range(0, len(contact_ids), 100):
            batch_ids = contact_ids[i:i+100]
            
            try:
                time.sleep(self.rate_limit_delay)
                
                batch_input = {
                    'inputs': [
                        {
                            'id': contact_id,
                            'properties': {status_property: new_status}
                        }
                        for contact_id in batch_ids
                    ]
                }
                
                response = self.client.crm.contacts.batch_api.update(
                    batch_input_simple_public_object_batch_input=batch_input
                )
                
                # Process results
                for result in response.results:
                    results.append(UpdateResult(
                        success=True,
                        object_id=result.id,
                        object_type='contact'
                    ))
                
                logger.info(f"Successfully updated batch of {len(batch_ids)} contacts")
                
            except Exception as e:
                logger.error(f"Error updating contact batch: {str(e)}")
                # Add individual failures
                for contact_id in batch_ids:
                    results.append(UpdateResult(
                        success=False,
                        object_id=contact_id,
                        object_type='contact',
                        error=str(e)
                    ))
        
        return results
    
    def test_connection(self) -> bool:
        """Test the HubSpot API connection"""
        try:
            # Try to get one company to test the connection
            response = self.client.crm.companies.basic_api.get_page(limit=1)
            logger.info("HubSpot API connection test successful")
            return True
        except Exception as e:
            logger.error(f"HubSpot API connection test failed: {str(e)}")
            return False