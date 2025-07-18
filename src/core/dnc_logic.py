"""
Enhanced DNC checker with HubSpot integration
Builds on existing fuzzy matching logic adapted for HubSpot data structures
"""
import pandas as pd
import re
from rapidfuzz import fuzz, process
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Pre-compiled Regular Expressions (from original code)
_RE_NON_ALPHANUMERIC = re.compile(r'[^\w\s]')
_RE_MULTIPLE_SPACES = re.compile(r'\s+')
_RE_COMPANY_SUFFIXES = re.compile(r'\b(inc|ltd|llc|corp|pty|co|the)\b\.?$', re.IGNORECASE)

@dataclass
class DNCMatch:
    """Represents a DNC match result"""
    company_id: str
    company_name: str
    dnc_company_name: str
    match_type: str  # 'exact', 'fuzzy', 'domain'
    confidence: float
    action: str  # 'auto_exclude', 'review', 'no_action'
    contact_count: int = 0

class DNCChecker:
    """Enhanced DNC checker for HubSpot integration"""
    
    def __init__(self, fuzzy_threshold_match: int = 90, fuzzy_threshold_review: int = 85):
        self.fuzzy_threshold_match = fuzzy_threshold_match
        self.fuzzy_threshold_review = fuzzy_threshold_review
        
    def clean_text(self, text: str) -> str:
        """Clean text by removing punctuation and normalizing spaces"""
        if pd.isna(text) or not text:
            return ""
        text = str(text).lower()
        text = _RE_NON_ALPHANUMERIC.sub(' ', text)  # Replace with space, not remove
        text = _RE_MULTIPLE_SPACES.sub(' ', text)
        return text.strip()

    def clean_company_name(self, name: str) -> str:
        """Clean company name by removing suffixes and normalizing"""
        if pd.isna(name) or not name:
            return ""
        name = _RE_COMPANY_SUFFIXES.sub('', str(name))
        return self.clean_text(name)

    def clean_domain(self, domain: str) -> str:
        """Clean and normalize domain names"""
        if pd.isna(domain) or not domain:
            return ""
        
        domain = str(domain).lower().strip()
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Clean domain specifically - remove punctuation completely
        domain = _RE_NON_ALPHANUMERIC.sub('', domain)
        return domain
        
    def process_dnc_list(self, dnc_df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean DNC list data"""
        logger.info(f"Processing DNC list with {len(dnc_df)} entries")
        
        # Make a copy to avoid modifying original
        dnc_processed = dnc_df.copy()
        
        # Clean company names
        dnc_processed['company_name_clean'] = dnc_processed['company_name'].apply(self.clean_company_name)
        
        # Clean domains if present
        if 'domain' in dnc_processed.columns:
            dnc_processed['domain_clean'] = dnc_processed['domain'].apply(self.clean_domain)
        
        # Remove empty entries
        dnc_processed = dnc_processed[dnc_processed['company_name_clean'].str.len() > 0]
        
        logger.info(f"Processed DNC list: {len(dnc_processed)} valid entries")
        return dnc_processed
    
    def check_companies_against_dnc(self, 
                                   hubspot_companies: List[Dict], 
                                   dnc_df: pd.DataFrame) -> List[DNCMatch]:
        """Check all HubSpot companies against DNC list"""
        logger.info(f"Checking {len(hubspot_companies)} companies against DNC list")
        
        matches = []
        
        # Process DNC list
        dnc_processed = self.process_dnc_list(dnc_df)
        
        # Create lookup sets for faster matching
        dnc_companies_set = set(dnc_processed['company_name_clean'].dropna())
        dnc_domains_set = set()
        
        if 'domain_clean' in dnc_processed.columns:
            dnc_domains_set = set(dnc_processed['domain_clean'].dropna())
        
        # Check each company
        for company in hubspot_companies:
            company_matches = self._check_single_company(company, dnc_processed, dnc_companies_set, dnc_domains_set)
            matches.extend(company_matches)
        
        logger.info(f"Found {len(matches)} DNC matches")
        return matches
    
    def _check_single_company(self, 
                             hubspot_company: Dict, 
                             dnc_df: pd.DataFrame,
                             dnc_companies_set: set,
                             dnc_domains_set: set) -> List[DNCMatch]:
        """Check a single HubSpot company against DNC list"""
        matches = []
        
        company_id = hubspot_company['id']
        company_name = hubspot_company['properties'].get('name', '')
        company_domain = hubspot_company['properties'].get('domain', '')
        
        if not company_name:
            return matches
        
        # Clean the company data
        company_name_clean = self.clean_company_name(company_name)
        company_domain_clean = self.clean_domain(company_domain)
        
        # Check exact company name match first
        exact_match = self._check_exact_match(company_name_clean, dnc_companies_set, dnc_df)
        if exact_match:
            matches.append(DNCMatch(
                company_id=company_id,
                company_name=company_name,
                dnc_company_name=exact_match,
                match_type='exact',
                confidence=100.0,
                action='auto_exclude'
            ))
            return matches  # Don't check further if exact match found
        
        # Check domain matches
        if company_domain_clean and dnc_domains_set:
            domain_match = self._check_domain_match(company_domain_clean, dnc_domains_set, dnc_df)
            if domain_match:
                matches.append(DNCMatch(
                    company_id=company_id,
                    company_name=company_name,
                    dnc_company_name=domain_match,
                    match_type='domain',
                    confidence=100.0,
                    action='auto_exclude'
                ))
                return matches
        
        # Check fuzzy matches
        fuzzy_match = self._check_fuzzy_match(company_name_clean, dnc_companies_set, dnc_df)
        if fuzzy_match:
            fuzzy_match.company_id = company_id
            fuzzy_match.company_name = company_name
            matches.append(fuzzy_match)
        
        return matches
    
    def _check_exact_match(self, company_name_clean: str, dnc_companies_set: set, dnc_df: pd.DataFrame) -> str:
        """Check for exact company name matches"""
        if company_name_clean in dnc_companies_set:
            # Find the original company name
            match_row = dnc_df[dnc_df['company_name_clean'] == company_name_clean].iloc[0]
            return match_row['company_name']
        return None
    
    def _check_domain_match(self, company_domain_clean: str, dnc_domains_set: set, dnc_df: pd.DataFrame) -> str:
        """Check for domain matches"""
        if company_domain_clean in dnc_domains_set:
            # Find the original company name for this domain
            match_row = dnc_df[dnc_df['domain_clean'] == company_domain_clean].iloc[0]
            return match_row['company_name']
        return None
    
    def _check_fuzzy_match(self, company_name_clean: str, dnc_companies_set: set, dnc_df: pd.DataFrame) -> DNCMatch:
        """Check for fuzzy company name matches"""
        if not company_name_clean or not dnc_companies_set:
            return None
        
        # Use rapidfuzz to find best match
        result = process.extractOne(company_name_clean, dnc_companies_set, scorer=fuzz.token_sort_ratio)
        
        if result:
            matched_clean_name, confidence, _ = result
            
            # Find the original company name
            match_row = dnc_df[dnc_df['company_name_clean'] == matched_clean_name].iloc[0]
            original_name = match_row['company_name']
            
            if confidence >= self.fuzzy_threshold_match:
                action = 'auto_exclude'
            elif confidence >= self.fuzzy_threshold_review:
                action = 'review'
            else:
                return None
            
            return DNCMatch(
                company_id='',  # Will be set by caller
                company_name='',  # Will be set by caller
                dnc_company_name=original_name,
                match_type='fuzzy',
                confidence=confidence,
                action=action
            )
        
        return None
    
    def get_fuzzy_score_and_match(self, name: str, name_set: set) -> Tuple[float, str]:
        """
        Returns the best fuzzy score and the matched string from the name_set.
        Kept for compatibility with original code.
        """
        if not name or not name_set:
            return 0, None
        match = process.extractOne(name, name_set, scorer=fuzz.token_sort_ratio)
        if match:
            return match[1], match[0]  # score, matched_string
        return 0, None