# DNC Automator Development Guide

## Overview
This guide walks you through transforming your existing DNC checker into a fully automated HubSpot integration. The system will check company-level matches using fuzzy matching (90% threshold for auto-action, 85% for review) and update both company and contact lifecycle statuses accordingly.

## Prerequisites

### Required Software
- **Python 3.11+** (recommended)
- **UV package manager** (install from https://docs.astral.sh/uv/)
- **Git** (install from https://git-scm.com/)
- **VS Code** (recommended IDE)
- **HubSpot Super Admin access** (for private app creation)

### Initial Setup Commands
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
git --version
```

## Git Workflow & Project Structure/

### 1. Repository Setup
```bash
# Clone your existing repository
git clone https://github.com/Jonathan-hanekom-punchb2b/dnc_checker.git
cd dnc_checker

# Create and switch to development branch
git checkout -b automation-development

# Add comprehensive .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
.env.production
.env.test

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Data files
data/uploads/*
!data/uploads/.gitkeep
test_data/*
!test_data/.gitkeep

# UV
.uv/
uv.lock

# OS
.DS_Store
Thumbs.db
EOF

# Create project structure
mkdir -p src/{core,hubspot,notifications,utils}
mkdir -p tests/{unit,integration}
mkdir -p data/{uploads,processed,archived}
mkdir -p logs
mkdir -p .github/workflows
mkdir -p config

# Create empty files to preserve directory structure
touch data/uploads/.gitkeep
touch data/processed/.gitkeep
touch data/archived/.gitkeep
touch logs/.gitkeep
touch tests/unit/.gitkeep
touch tests/integration/.gitkeep
```

### 2. Git Workflow Best Practices
```bash
# Before starting work each day
git pull origin main
git merge main  # Merge latest changes into your branch

# When working on a feature
git add .
git commit -m "feat: add HubSpot API client wrapper"

# When fixing a bug
git commit -m "fix: handle API rate limiting properly"

# When refactoring
git commit -m "refactor: improve error handling in DNC checker"

# Push changes regularly
git push origin automation-development

# Emergency rollback (if you need to undo recent changes)
git log --oneline -5  # Find the commit hash you want to go back to
git reset --hard <commit-hash>  # WARNING: This loses uncommitted changes
git push --force-with-lease origin automation-development
```

### 3. Project Structure
```
dnc_checker/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dnc_logic.py          # Your existing logic (enhanced)
│   │   └── config.py             # Configuration management
│   ├── hubspot/
│   │   ├── __init__.py
│   │   ├── client.py             # HubSpot API wrapper
│   │   ├── models.py             # Data models
│   │   └── auth.py               # Authentication handling
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_sender.py       # Email notifications
│   │   └── templates.py          # Email templates
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_handler.py       # File upload/processing
│   │   ├── logger.py             # Logging configuration
│   │   └── validators.py         # Data validation
│   └── main.py                   # Main orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_dnc_logic.py
│   │   ├── test_hubspot_client.py
│   │   └── test_notifications.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_hubspot_integration.py
│   └── conftest.py               # Test configuration
├── data/
│   ├── uploads/                  # Incoming DNC lists
│   ├── processed/                # Processed lists
│   └── archived/                 # Historical data
├── logs/                         # Application logs
├── config/
│   ├── clients.yaml              # Client configurations
│   └── hubspot_mappings.yaml     # Field mappings
├── .github/
│   └── workflows/
│       └── dnc_automation.yml    # GitHub Actions workflow
├── .env.example                  # Environment variables template
├── pyproject.toml               # Project dependencies
├── README.md                    # Project documentation
└── CLAUDE.md                    # This file
```

## Development Environment Setup

### 1. Python Environment with UV
```bash
# Initialize UV project
uv init --python 3.11

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "dnc-automation"
version = "0.1.0"
description = "Automated DNC checking and HubSpot integration"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0.0",
    "rapidfuzz>=3.0.0",
    "hubspot-api-client>=7.0.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
    "jinja2>=3.1.0",
    "requests>=2.31.0",
    "openpyxl>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
    "pre-commit>=3.0.0",
]

[project.scripts]
dnc-check = "src.main:main"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
EOF

# Install dependencies
uv sync --dev

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Environment Variables Setup
```bash
# Create .env file
cat > .env << 'EOF'
# HubSpot Configuration
HUBSPOT_API_KEY=your_hubspot_api_key_here
HUBSPOT_INSTANCE_NAME=your_instance_name

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@company.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=you@company.com,datamanager@company.com,depthead@company.com

# Application Configuration
LOG_LEVEL=INFO
FUZZY_THRESHOLD_MATCH=90
FUZZY_THRESHOLD_REVIEW=85
COMPANY_BATCH_SIZE=100
CONTACT_BATCH_SIZE=500

# File paths
DNC_UPLOAD_PATH=data/uploads
DNC_PROCESSED_PATH=data/processed
DNC_ARCHIVED_PATH=data/archived

# Client Configuration
CLIENT_NAME=test_client
COMPANY_STATUS_PROPERTY=test_client_account_status
CONTACT_STATUS_PROPERTY=test_client_funnel_status
EOF

# Create example file for repository
cp .env .env.example
# Edit .env.example to remove actual values
```

## Testing Strategy & Framework

### 1. Testing Philosophy
Since you don't have a sandbox HubSpot instance, we'll implement a comprehensive testing strategy:

**Unit Tests**: Test individual functions in isolation
**Integration Tests**: Test with mock HubSpot data
**Staging Tests**: Test with real HubSpot using test client data
**Production Tests**: Gradual rollout with monitoring

### 2. Setting Up Test Framework
```bash
# Create test configuration
cat > tests/conftest.py << 'EOF'
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.hubspot.client import HubSpotClient
from src.core.dnc_logic import DNCChecker

@pytest.fixture
def sample_dnc_data():
    """Sample DNC list data for testing"""
    return pd.DataFrame({
        'company_name': ['Test Company Inc', 'Another Corp', 'Third Business'],
        'domain': ['testcompany.com', 'anothercorp.com', 'thirdbusiness.com']
    })

@pytest.fixture
def sample_hubspot_companies():
    """Sample HubSpot company data"""
    return [
        {
            'id': '12345',
            'properties': {
                'name': 'Test Company Inc.',
                'domain': 'testcompany.com',
                'test_client_account_status': 'Active'
            }
        },
        {
            'id': '67890',
            'properties': {
                'name': 'Different Company',
                'domain': 'different.com',
                'test_client_account_status': 'Active'
            }
        }
    ]

@pytest.fixture
def mock_hubspot_client():
    """Mock HubSpot client for testing"""
    with patch('src.hubspot.client.HubSpotClient') as mock:
        yield mock

@pytest.fixture
def dnc_checker():
    """DNC checker instance for testing"""
    return DNCChecker(
        fuzzy_threshold_match=90,
        fuzzy_threshold_review=85
    )
EOF

# Create sample unit tests
cat > tests/unit/test_dnc_logic.py << 'EOF'
import pytest
import pandas as pd
from src.core.dnc_logic import DNCChecker

class TestDNCChecker:
    def test_exact_match_detection(self, dnc_checker, sample_dnc_data):
        """Test exact company name matching"""
        hubspot_company = {
            'id': '12345',
            'properties': {
                'name': 'Test Company Inc',
                'domain': 'testcompany.com'
            }
        }
        
        matches = dnc_checker.check_company_against_dnc(
            hubspot_company, 
            sample_dnc_data
        )
        
        assert len(matches) == 1
        assert matches[0]['match_type'] == 'exact'
        assert matches[0]['confidence'] >= 90

    def test_fuzzy_match_detection(self, dnc_checker, sample_dnc_data):
        """Test fuzzy company name matching"""
        hubspot_company = {
            'id': '12345',
            'properties': {
                'name': 'Test Company Incorporated',  # Slight variation
                'domain': 'testcompany.com'
            }
        }
        
        matches = dnc_checker.check_company_against_dnc(
            hubspot_company, 
            sample_dnc_data
        )
        
        assert len(matches) == 1
        assert matches[0]['match_type'] == 'fuzzy'
        assert matches[0]['confidence'] >= 85

    def test_domain_match_detection(self, dnc_checker, sample_dnc_data):
        """Test domain-based matching"""
        hubspot_company = {
            'id': '12345',
            'properties': {
                'name': 'Completely Different Name',
                'domain': 'testcompany.com'  # Same domain
            }
        }
        
        matches = dnc_checker.check_company_against_dnc(
            hubspot_company, 
            sample_dnc_data
        )
        
        assert len(matches) == 1
        assert matches[0]['match_type'] == 'domain'

    def test_no_match_scenario(self, dnc_checker, sample_dnc_data):
        """Test when no matches are found"""
        hubspot_company = {
            'id': '12345',
            'properties': {
                'name': 'Unique Company Name',
                'domain': 'unique.com'
            }
        }
        
        matches = dnc_checker.check_company_against_dnc(
            hubspot_company, 
            sample_dnc_data
        )
        
        assert len(matches) == 0
EOF

# Create integration tests
cat > tests/integration/test_hubspot_integration.py << 'EOF'
import pytest
from unittest.mock import Mock, patch
from src.hubspot.client import HubSpotClient
from src.main import DNCAutomation

class TestHubSpotIntegration:
    @patch('src.hubspot.client.hubspot.Client')
    def test_hubspot_connection(self, mock_client):
        """Test HubSpot API connection"""
        mock_client.create.return_value = Mock()
        
        client = HubSpotClient(api_key="test_key")
        
        assert client.client is not None
        mock_client.create.assert_called_once_with(access_token="test_key")

    @patch('src.hubspot.client.hubspot.Client')
    def test_fetch_companies(self, mock_client):
        """Test fetching companies from HubSpot"""
        mock_api = Mock()
        mock_client.create.return_value.crm.companies.basic_api = mock_api
        mock_api.get_page.return_value.results = [
            Mock(id='123', properties={'name': 'Test Company', 'domain': 'test.com'})
        ]
        
        client = HubSpotClient(api_key="test_key")
        companies = client.get_all_companies()
        
        assert len(companies) == 1
        assert companies[0]['id'] == '123'

    @patch('src.hubspot.client.hubspot.Client')
    def test_update_company_status(self, mock_client):
        """Test updating company status"""
        mock_api = Mock()
        mock_client.create.return_value.crm.companies.basic_api = mock_api
        
        client = HubSpotClient(api_key="test_key")
        result = client.update_company_status(
            company_id='123',
            status_property='test_client_account_status',
            new_status='Client Working'
        )
        
        mock_api.update.assert_called_once()
        assert result is True
EOF

# Run tests
uv run pytest tests/ -v --cov=src
```

### 3. Test Data Setup
```bash
# Create test DNC list
cat > data/uploads/test_client_01-01-24.csv << 'EOF'
company_name,domain
Test Company Inc,testcompany.com
Another Test Corp,anothertest.com
Third Test Business,thirdtest.com
EOF

# Create test script for HubSpot
cat > tests/manual_hubspot_test.py << 'EOF'
"""
Manual test script for HubSpot integration
Run this to verify your HubSpot connection works
"""
import os
from dotenv import load_dotenv
from src.hubspot.client import HubSpotClient

load_dotenv()

def test_hubspot_connection():
    """Test basic HubSpot API connection"""
    api_key = os.getenv('HUBSPOT_API_KEY')
    if not api_key:
        print("ERROR: HUBSPOT_API_KEY not found in .env file")
        return False
    
    try:
        client = HubSpotClient(api_key=api_key)
        
        # Test: Get first 5 companies
        companies = client.get_companies(limit=5)
        print(f"✅ Successfully connected to HubSpot!")
        print(f"   Found {len(companies)} companies")
        
        # Test: Get first 5 contacts
        contacts = client.get_contacts(limit=5)
        print(f"   Found {len(contacts)} contacts")
        
        return True
        
    except Exception as e:
        print(f"❌ HubSpot connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_hubspot_connection()
EOF
```

## Core Development Components

### 1. Enhanced DNC Logic (src/core/dnc_logic.py)
```python
"""
Enhanced DNC checker with HubSpot integration
Builds on your existing fuzzy matching logic
"""
import pandas as pd
from rapidfuzz import fuzz, process
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class DNCMatch:
    """Represents a DNC match result"""
    company_id: str
    company_name: str
    dnc_company_name: str
    match_type: str  # 'exact', 'fuzzy', 'domain'
    confidence: float
    action: str  # 'auto_exclude', 'review', 'no_action'

class DNCChecker:
    """Enhanced DNC checker for HubSpot integration"""
    
    def __init__(self, fuzzy_threshold_match: int = 90, fuzzy_threshold_review: int = 85):
        self.fuzzy_threshold_match = fuzzy_threshold_match
        self.fuzzy_threshold_review = fuzzy_threshold_review
        
    def process_dnc_list(self, dnc_df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean DNC list data"""
        # Clean company names
        dnc_df['company_name_clean'] = dnc_df['company_name'].str.strip().str.lower()
        
        # Clean domains
        if 'domain' in dnc_df.columns:
            dnc_df['domain_clean'] = dnc_df['domain'].apply(self._clean_domain)
        
        return dnc_df
    
    def check_companies_against_dnc(self, 
                                   hubspot_companies: List[Dict], 
                                   dnc_df: pd.DataFrame) -> List[DNCMatch]:
        """Check all HubSpot companies against DNC list"""
        matches = []
        
        # Process DNC list
        dnc_processed = self.process_dnc_list(dnc_df)
        
        for company in hubspot_companies:
            company_matches = self._check_single_company(company, dnc_processed)
            matches.extend(company_matches)
        
        return matches
    
    def _check_single_company(self, 
                             hubspot_company: Dict, 
                             dnc_df: pd.DataFrame) -> List[DNCMatch]:
        """Check a single HubSpot company against DNC list"""
        matches = []
        
        company_id = hubspot_company['id']
        company_name = hubspot_company['properties'].get('name', '')
        company_domain = hubspot_company['properties'].get('domain', '')
        
        if not company_name:
            return matches
        
        # Check exact matches first
        exact_match = self._check_exact_match(company_name, dnc_df)
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
        if company_domain:
            domain_match = self._check_domain_match(company_domain, dnc_df)
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
        fuzzy_match = self._check_fuzzy_match(company_name, dnc_df)
        if fuzzy_match:
            matches.append(fuzzy_match)
        
        return matches
    
    def _check_exact_match(self, company_name: str, dnc_df: pd.DataFrame) -> str:
        """Check for exact company name matches"""
        company_clean = company_name.strip().lower()
        
        exact_matches = dnc_df[dnc_df['company_name_clean'] == company_clean]
        
        if not exact_matches.empty:
            return exact_matches.iloc[0]['company_name']
        
        return None
    
    def _check_domain_match(self, company_domain: str, dnc_df: pd.DataFrame) -> str:
        """Check for domain matches"""
        if 'domain_clean' not in dnc_df.columns:
            return None
        
        domain_clean = self._clean_domain(company_domain)
        if not domain_clean:
            return None
        
        domain_matches = dnc_df[dnc_df['domain_clean'] == domain_clean]
        
        if not domain_matches.empty:
            return domain_matches.iloc[0]['company_name']
        
        return None
    
    def _check_fuzzy_match(self, company_name: str, dnc_df: pd.DataFrame) -> DNCMatch:
        """Check for fuzzy company name matches"""
        company_clean = company_name.strip().lower()
        
        # Use rapidfuzz to find best match
        choices = dnc_df['company_name_clean'].tolist()
        result = process.extractOne(company_clean, choices, scorer=fuzz.ratio)
        
        if result:
            match_name, confidence, _ = result
            
            # Find the original company name
            original_match = dnc_df[dnc_df['company_name_clean'] == match_name]
            if not original_match.empty:
                original_name = original_match.iloc[0]['company_name']
                
                if confidence >= self.fuzzy_threshold_match:
                    action = 'auto_exclude'
                elif confidence >= self.fuzzy_threshold_review:
                    action = 'review'
                else:
                    return None
                
                return DNCMatch(
                    company_id='',  # Will be set by caller
                    company_name=company_name,
                    dnc_company_name=original_name,
                    match_type='fuzzy',
                    confidence=confidence,
                    action=action
                )
        
        return None
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize domain names"""
        if not domain:
            return ''
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Convert to lowercase and strip
        return domain.lower().strip()
```

### 2. HubSpot Client (src/hubspot/client.py)
```python
"""
HubSpot API client wrapper
Handles all HubSpot API interactions
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
    """HubSpot API client wrapper"""
    
    def __init__(self, api_key: str):
        self.client = hubspot.Client.create(access_token=api_key)
        self.rate_limit_delay = 0.1  # 100ms between requests
    
    def get_all_companies(self, 
                         properties: List[str] = None,
                         limit: int = 100) -> List[Dict]:
        """Fetch all companies from HubSpot"""
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
                            updates: List[Dict],
                            status_property: str,
                            new_status: str) -> List[UpdateResult]:
        """Batch update multiple contacts"""
        results = []
        
        # Process in batches of 100 (HubSpot limit)
        for i in range(0, len(updates), 100):
            batch = updates[i:i+100]
            
            try:
                time.sleep(self.rate_limit_delay)
                
                batch_input = {
                    'inputs': [
                        {
                            'id': contact['id'],
                            'properties': {status_property: new_status}
                        }
                        for contact in batch
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
                
                logger.info(f"Successfully updated batch of {len(batch)} contacts")
                
            except Exception as e:
                logger.error(f"Error updating contact batch: {str(e)}")
                # Add individual failures
                for contact in batch:
                    results.append(UpdateResult(
                        success=False,
                        object_id=contact['id'],
                        object_type='contact',
                        error=str(e)
                    ))
        
        return results
```

### 3. Email Notifications (src/notifications/email_sender.py)
```python
"""
Email notification system for DNC automation
Sends summaries and error reports
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any
from jinja2 import Template
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Handles email notifications for DNC automation"""
    
    def __init__(self, 
                 smtp_host: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 recipients: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
    
    def send_success_summary(self, 
                           run_summary: Dict[str, Any],
                           attachment_path: str = None) -> bool:
        """Send successful run summary email"""
        
        subject = f"DNC Check Complete - {run_summary['client_name']} - {datetime.now().strftime('%Y-%m-%d')}"
        
        html_content = self._generate_success_email(run_summary)
        
        return self._send_email(
            subject=subject,
            html_content=html_content,
            attachment_path=attachment_path
        )
    
    def send_error_notification(self, 
                              error_details: Dict[str, Any]) -> bool:
        """Send error notification email"""
        
        subject = f"DNC Automation Error - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        html_content = self._generate_error_email(error_details)
        
        return self._send_email(
            subject=subject,
            html_content=html_content
        )
    
    def _generate_success_email(self, summary: Dict[str, Any]) -> str:
        """Generate HTML content for success email"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #28a745; color: white; padding: 10px; border-radius: 5px; }
                .summary-box { background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .metric { display: inline-block; margin: 10px 20px 10px 0; }
                .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
                .metric-label { font-size: 14px; color: #6c757d; }
                .matches-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                .matches-table th, .matches-table td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
                .matches-table th { background-color: #e9ecef; }
                .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>✅ DNC Check Completed Successfully</h2>
            </div>
            
            <div class="summary-box">
                <h3>Run Summary</h3>
                <div class="metric">
                    <div class="metric-value">{{ summary.companies_checked }}</div>
                    <div class="metric-label">Companies Checked</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.matches_found }}</div>
                    <div class="metric-label">DNC Matches Found</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.companies_updated }}</div>
                    <div class="metric-label">Companies Updated</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.contacts_updated }}</div>
                    <div class="metric-label">Contacts Updated</div>
                </div>
            </div>
            
            <div class="summary-box">
                <h3>Details</h3>
                <p><strong>Client:</strong> {{ summary.client_name }}</p>
                <p><strong>DNC List:</strong> {{ summary.dnc_list_name }}</p>
                <p><strong>Run Time:</strong> {{ summary.start_time }} - {{ summary.end_time }}</p>
                <p><strong>Duration:</strong> {{ summary.duration }}</p>
            </div>
            
            {% if summary.matches %}
            <div class="summary-box">
                <h3>DNC Matches Found</h3>
                <table class="matches-table">
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>DNC List Match</th>
                            <th>Match Type</th>
                            <th>Confidence</th>
                            <th>Contacts Affected</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for match in summary.matches %}
                        <tr>
                            <td>{{ match.company_name }}</td>
                            <td>{{ match.dnc_company_name }}</td>
                            <td>{{ match.match_type|title }}</td>
                            <td>{{ "%.1f"|format(match.confidence) }}%</td>
                            <td>{{ match.contacts_affected }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
            
            <div class="footer">
                <p>This email was generated automatically by the DNC Automation System.</p>
                <p>Run ID: {{ summary.run_id }}</p>
            </div>
        </body>
        </html>
        """)
        
        return template.render(summary=summary)
    
    def _generate_error_email(self, error_details: Dict[str, Any]) -> str:
        """Generate HTML content for error email"""
        
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #dc3545; color: white; padding: 10px; border-radius: 5px; }
                .error-box { background-color: #f8d7da; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #f5c6cb; }
                .code-block { background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; white-space: pre-wrap; }
                .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>❌ DNC Automation Error</h2>
            </div>
            
            <div class="error-box">
                <h3>Error Details</h3>
                <p><strong>Error Type:</strong> {{ error_details.error_type }}</p>
                <p><strong>Error Message:</strong> {{ error_details.error_message }}</p>
                <p><strong>Timestamp:</strong> {{ error_details.timestamp }}</p>
                {% if error_details.client_name %}
                <p><strong>Client:</strong> {{ error_details.client_name }}</p>
                {% endif %}
            </div>
            
            {% if error_details.stack_trace %}
            <div class="error-box">
                <h3>Stack Trace</h3>
                <div class="code-block">{{ error_details.stack_trace }}</div>
            </div>
            {% endif %}
            
            {% if error_details.context %}
            <div class="error-box">
                <h3>Additional Context</h3>
                {% for key, value in error_details.context.items() %}
                <p><strong>{{ key }}:</strong> {{ value }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="footer">
                <p>Please check the system logs for more details and take appropriate action.</p>
                <p>Run ID: {{ error_details.run_id }}</p>
            </div>
        </body>
        </html>
        """)
        
        return template.render(error_details=error_details)
    
    def _send_email(self, 
                   subject: str,
                   html_content: str,
                   attachment_path: str = None) -> bool:
        """Send email with optional attachment"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, self.recipients, msg.as_string())
            
            logger.info(f"Email sent successfully to {', '.join(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
```

### 4. Main Orchestration Script (src/main.py)
```python
"""
Main orchestration script for DNC automation
Coordinates all components and handles the complete workflow
"""
import os
import sys
import uuid
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.dnc_logic import DNCChecker, DNCMatch
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
    
    def _process_matches(self, matches: List[DNCMatch]) -> bool:
        """Process DNC matches and update HubSpot"""
        
        try:
            companies_to_update = []
            contacts_to_update = []
            
            for match in matches:
                if match.action == 'auto_exclude':
                    # Update company status
                    company_result = self.hubspot_client.update_company_status(
                        company_id=match.company_id,
                        status_property=self.config['company_status_property'],
                        new_status='Client Working'
                    )
                    
                    if company_result.success:
                        companies_to_update.append(match.company_id)
                        
                        # Get and update associated contacts
                        contacts = self.hubspot_client.get_contacts_for_company(
                            match.company_id
                        )
                        
                        contact_updates = []
                        for contact in contacts:
                            contact_updates.append({
                                'id': contact['id'],
                                'company_id': match.company_id
                            })
                        
                        if contact_updates:
                            contact_results = self.hubspot_client.batch_update_contacts(
                                updates=contact_updates,
                                status_property=self.config['contact_status_property'],
                                new_status='On Hold'
                            )
                            
                            successful_contacts = [
                                r.object_id for r in contact_results if r.success
                            ]
                            contacts_to_update.extend(successful_contacts)
                    
                    # Add to summary
                    self.run_summary['matches'].append({
                        'company_name': match.company_name,
                        'dnc_company_name': match.dnc_company_name,
                        'match_type': match.match_type,
                        'confidence': match.confidence,
                        'contacts_affected': len(contacts_to_update)
                    })
                
                elif match.action == 'review':
                    # Log for manual review
                    logger.warning(f"Manual review required: {match.company_name} "
                                 f"(confidence: {match.confidence}%)")
            
            self.run_summary['companies_updated'] = len(companies_to_update)
            self.run_summary['contacts_updated'] = len(contacts_to_update)
            
            logger.info(f"Updated {len(companies_to_update)} companies and "
                       f"{len(contacts_to_update)} contacts")
            
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
        
        results_file = os.path.join(
            self.config['results_path'],
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
        'results_path': os.getenv('RESULTS_PATH', 'data/results'),
        
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
```

## GitHub Actions Workflow

### 5. Automation Workflow (.github/workflows/dnc_automation.yml)
```yaml
name: DNC Automation

on:
  # Manual trigger
  workflow_dispatch:
    inputs:
      client_name:
        description: 'Client name to process'
        required: false
        type: string
        default: 'test_client'
      dnc_file:
        description: 'Specific DNC file to process (optional)'
        required: false
        type: string
  
  # Scheduled runs
  schedule:
    # Run every Monday and Thursday at 9 AM UTC
    - cron: '0 9 * * 1,4'

env:
  PYTHON_VERSION: '3.11'

jobs:
  dnc-check:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install UV
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: |
        uv sync --dev
    
    - name: Create data directories
      run: |
        mkdir -p data/uploads data/processed data/archived data/results logs
    
    - name: Run DNC check
      env:
        HUBSPOT_API_KEY: ${{ secrets.HUBSPOT_API_KEY }}
        HUBSPOT_INSTANCE_NAME: ${{ secrets.HUBSPOT_INSTANCE_NAME }}
        SMTP_HOST: ${{ secrets.SMTP_HOST }}
        SMTP_PORT: ${{ secrets.SMTP_PORT }}
        EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
        EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        EMAIL_RECIPIENTS: ${{ secrets.EMAIL_RECIPIENTS }}
        CLIENT_NAME: ${{ github.event.inputs.client_name || 'test_client' }}
        COMPANY_STATUS_PROPERTY: ${{ secrets.COMPANY_STATUS_PROPERTY }}
        CONTACT_STATUS_PROPERTY: ${{ secrets.CONTACT_STATUS_PROPERTY }}
        FUZZY_THRESHOLD_MATCH: 90
        FUZZY_THRESHOLD_REVIEW: 85
        LOG_LEVEL: INFO
      run: |
        source .venv/bin/activate
        python src/main.py
    
    - name: Upload logs
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: dnc-logs-${{ github.run_number }}
        path: logs/
        retention-days: 30
    
    - name: Upload results
      if: success()
      uses: actions/upload-artifact@v4
      with:
        name: dnc-results-${{ github.run_number }}
        path: data/results/
        retention-days: 90
    
    - name: Notify on failure
      if: failure()
      run: |
        echo "DNC automation failed. Check logs for details."
        # Additional failure notification logic can go here
```

## Development Workflow

### Phase 1: Getting Started (Week 1)

#### Day 1-2: Environment Setup
```bash
# 1. Set up repository
git clone https://github.com/Jonathan-hanekom-punchb2b/dnc_checker.git
cd dnc_checker
git checkout -b automation-development

# 2. Create project structure (run all commands from project setup section)

# 3. Install dependencies
uv sync --dev

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# 5. Test basic setup
uv run python -c "import pandas; import rapidfuzz; print('Dependencies working!')"
```

#### Day 3-4: HubSpot API Setup
```bash
# 1. Create HubSpot private app
# Go to HubSpot → Settings → Integrations → Private Apps
# Create app with required scopes (see implementation plan)

# 2. Test HubSpot connection
uv run python tests/manual_hubspot_test.py

# 3. Run unit tests
uv run pytest tests/unit/ -v

# 4. Commit progress
git add .
git commit -m "feat: initial project setup and HubSpot API integration"
git push origin automation-development
```

#### Day 5-7: Core Logic Integration
```bash
# 1. Adapt your existing DNC logic
# Copy core logic from your existing dnc_checker repository
# Modify to work with HubSpot data structures

# 2. Test with sample data
uv run pytest tests/unit/test_dnc_logic.py -v

# 3. Integration testing
uv run pytest tests/integration/ -v

# 4. Manual testing with small dataset
# Create test client in HubSpot
# Test with 5-10 companies

# 5. Commit working version
git add .
git commit -m "feat: integrate existing DNC logic with HubSpot data"
git push origin automation-development
```

### Phase 2: Full Integration (Week 2)

#### Day 8-10: Complete HubSpot Integration
```bash
# 1. Test with larger dataset (50-100 companies)
uv run python src/main.py

# 2. Test error handling scenarios
# - Invalid API key
# - Network timeouts
# - Malformed data

# 3. Implement rate limiting and retry logic

# 4. Test batch operations
# - Company updates
# - Contact updates

# 5. Commit integration
git add .
git commit -m "feat: complete HubSpot integration with error handling"
git push origin automation-development
```

#### Day 11-14: Email Notifications & File Handling
```bash
# 1. Set up email configuration
# Configure SMTP settings in .env
# Test email sending functionality

# 2. Implement file upload handling
# Create staging/processed folders
# Test file validation

# 3. End-to-end testing
uv run python src/main.py

# 4. Create utility scripts
cat > scripts/test_email.py << 'EOF'
from src.notifications.email_sender import EmailNotifier
from dotenv import load_dotenv
import os

load_dotenv()

notifier = EmailNotifier(
    smtp_host=os.getenv('SMTP_HOST'),
    smtp_port=int(os.getenv('SMTP_PORT')),
    username=os.getenv('EMAIL_USERNAME'),
    password=os.getenv('EMAIL_PASSWORD'),
    recipients=os.getenv('EMAIL_RECIPIENTS').split(',')
)

# Test email
test_summary = {
    'run_id': 'test-123',
    'client_name': 'Test Client',
    'companies_checked': 10,
    'matches_found': 2,
    'companies_updated': 2,
    'contacts_updated': 5,
    'matches': [],
    'start_time': '2024-01-01 09:00:00',
    'end_time': '2024-01-01 09:05:00',
    'duration': '0:05:00',
    'dnc_list_name': 'test_client_01-01-24.csv'
}

success = notifier.send_success_summary(test_summary)
print(f"Email sent: {success}")
EOF

uv run python scripts/test_email.py

# 5. Commit email functionality
git add .
git commit -m "feat: add email notifications and file handling"
git push origin automation-development
```

### Phase 3: Automation Setup (Week 3)

#### Day 15-17: GitHub Actions Setup
```bash
# 1. Create workflow file (see above)
# .github/workflows/dnc_automation.yml

# 2. Set up repository secrets
# Go to Repository Settings → Secrets and Variables → Actions
# Add all required secrets:
# - HUBSPOT_API_KEY
# - EMAIL_USERNAME
# - EMAIL_PASSWORD
# - etc.

# 3. Test manual workflow trigger
# Go to Actions tab → DNC Automation → Run workflow

# 4. Monitor first automated run
# Check logs and outputs

# 5. Commit workflow
git add .github/workflows/dnc_automation.yml
git commit -m "feat: add GitHub Actions automation workflow"
git push origin automation-development
```

#### Day 18-21: Production Testing & Monitoring
```bash
# 1. Create monitoring scripts
cat > scripts/monitor_runs.py << 'EOF'
"""
Monitor DNC automation runs and generate reports
"""
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

def analyze_recent_runs(days_back=7):
    """Analyze recent automation runs"""
    
    # Find result files from last N days
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    result_files = glob.glob('data/results/*_dnc_results_*.csv')
    recent_files = []
    
    for file in result_files:
        file_time = os.path.getctime(file)
        if datetime.fromtimestamp(file_time) > cutoff_date:
            recent_files.append(file)
    
    if not recent_files:
        print(f"No runs found in the last {days_back} days")
        return
    
    # Analyze results
    total_runs = len(recent_files)
    total_matches = 0
    total_companies_updated = 0
    
    print(f"\n📊 DNC Automation Summary - Last {days_back} Days")
    print("=" * 50)
    print(f"Total Runs: {total_runs}")
    
    for file in recent_files:
        try:
            df = pd.read_csv(file)
            run_matches = len(df)
            total_matches += run_matches
            
            print(f"\n📁 {os.path.basename(file)}")
            print(f"   Matches Found: {run_matches}")
            print(f"   Run Time: {df['timestamp'].iloc[0] if not df.empty else 'Unknown'}")
            
        except Exception as e:
            print(f"   Error reading file: {e}")
    
    print(f"\n📈 Totals:")
    print(f"   Total Matches Found: {total_matches}")
    print(f"   Average Matches per Run: {total_matches/total_runs:.1f}")

if __name__ == "__main__":
    analyze_recent_runs()
EOF

# 2. Create deployment checklist
cat > DEPLOYMENT_CHECKLIST.md << 'EOF'
# DNC Automation Deployment Checklist

## Pre-Deployment
- [ ] All tests passing (`uv run pytest`)
- [ ] HubSpot API connection tested
- [ ] Email notifications working
- [ ] Test data processed successfully
- [ ] GitHub secrets configured
- [ ] Workflow file committed

## Deployment Steps
- [ ] Merge to main branch
- [ ] Create release tag
- [ ] Enable scheduled workflow
- [ ] Monitor first scheduled run
- [ ] Verify email notifications received

## Post-Deployment
- [ ] Document any issues encountered
- [ ] Update monitoring scripts
- [ ] Schedule team training session
- [ ] Create backup procedures

## Rollback Plan
- [ ] Disable GitHub workflow
- [ ] Revert to manual process
- [ ] Investigate and fix issues
- [ ] Re-deploy when ready
EOF

# 3. Merge to main when ready
git checkout main
git merge automation-development
git push origin main

# 4. Create release
git tag v1.0.0
git push origin v1.0.0
```

## Utility Scripts & Helpers

### 6. File Handler (src/utils/file_handler.py)
```python
"""
File handling utilities for DNC automation
"""
import os
import shutil
import glob
import pandas as pd
from datetime import datetime
from typing import Optional, List
import logging

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
```

### 7. Logger Configuration (src/utils/logger.py)
```python
"""
Logging configuration for DNC automation
"""
import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Default log file
    if log_file is None:
        log_file = os.path.join(log_dir, f"dnc_automation_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('hubspot').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")
```

### 8. Data Validators (src/utils/validators.py)
```python
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
        suspicious_names = df[df['company_name'].str.len() < 3]['company_name'].count()
        if suspicious_names > 0:
            result['warnings'].append(f"{suspicious_names} company names are very short")
    
    # Validate domains if present
    if 'domain' in df.columns:
        invalid_domains = validate_domains(df['domain'].dropna())
        if invalid_domains:
            result['warnings'].append(f"{len(invalid_domains)} domains appear invalid")
    
    return result

def validate_domains(domains: pd.Series) -> List[str]:
    """Validate domain formats"""
    
    domain_pattern = re.compile(
        r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*
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
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})
    
    if config.get('email_username') and not email_pattern.match(config['email_username']):
        result['warnings'].append("Email username format may be invalid")
    
    # Validate email recipients
    recipients = config.get('email_recipients', [])
    if isinstance(recipients, list):
        invalid_emails = [email for email in recipients if not email_pattern.match(email.strip())]
        if invalid_emails:
            result['warnings'].append(f"Invalid email recipients: {invalid_emails}")
    
    return result
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. HubSpot API Issues
```bash
# Test API connection
uv run python -c "
from src.hubspot.client import HubSpotClient
import os
from dotenv import load_dotenv

load_dotenv()
client = HubSpotClient(os.getenv('HUBSPOT_API_KEY'))
try:
    companies = client.get_all_companies(limit=1)
    print('✅ HubSpot API working')
except Exception as e:
    print(f'❌ HubSpot API error: {e}')
"

# Common fixes:
# - Check API key is correct and has required scopes
# - Verify HubSpot instance is accessible
# - Check rate limiting (add delays between requests)
```

#### 2. Email Notification Issues
```bash
# Test email configuration
uv run python scripts/test_email.py

# Common fixes:
# - Use app password for Gmail (not regular password)
# - Check SMTP settings for your email provider
# - Verify firewall allows SMTP connections
# - Test with a simple text email first
```

#### 3. GitHub Actions Issues
```bash
# Check workflow syntax
yamllint .github/workflows/dnc_automation.yml

# View workflow logs in GitHub Actions tab
# Common fixes:
# - Verify all secrets are set correctly
# - Check Python version compatibility
# - Ensure all dependencies are in pyproject.toml
# - Check file paths are correct for Ubuntu environment
```

#### 4. Data Processing Issues
```bash
# Test with sample data
cat > test_dnc.csv << 'EOF'
company_name,domain
Test Company,test.com
Another Corp,another.com
EOF

uv run python -c "
import pandas as pd
from src.core.dnc_logic import DNCChecker

df = pd.read_csv('test_dnc.csv')
checker = DNCChecker()
processed = checker.process_dnc_list(df)
print(processed.head())
"

# Common fixes:
# - Check CSV encoding (use UTF-8)
# - Verify column names match expected format
# - Handle special characters in company names
# - Check for empty rows or invalid data
```

### Emergency Procedures

#### Rolling Back Changes
```bash
# If automation is causing issues, disable it immediately:

# 1. Disable GitHub Actions workflow
# Go to Actions → DNC Automation → Disable workflow

# 2. Revert to previous working version
git log --oneline -10  # Find last working commit
git reset --hard <commit-hash>
git push --force-with-lease origin main

# 3. Return to manual process while investigating
# Use your existing manual DNC checker

# 4. Fix issues in development branch
git checkout -b fix-urgent-issue
# Make fixes
git commit -m "fix: resolve urgent production issue"
git push origin fix-urgent-issue
# Test thoroughly before merging
```

#### Data Recovery
```bash
# If contacts were incorrectly updated:

# 1. Check HubSpot activity logs
# Go to contact/company record → Activity tab
# Look for property changes made by your API integration

# 2. Use backup data if available
# Check data/results/ folder for run logs
# Identify which contacts were affected

# 3. Batch revert using HubSpot API
# Create revert script:
cat > scripts/revert_changes.py << 'EOF'
from src.hubspot.client import HubSpotClient
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Load the run results that need to be reverted
results_file = "data/results/problem_run_results.csv"
df = pd.read_csv(results_file)

client = HubSpotClient(os.getenv('HUBSPOT_API_KEY'))

# Revert company statuses
for _, row in df.iterrows():
    # Update back to previous status
    client.update_company_status(
        company_id=row['company_id'],
        status_property='your_property',
        new_status='Active'  # or whatever the previous status was
    )
EOF
```

## Performance Optimization

### Monitoring Script
```python
cat > scripts/performance_monitor.py << 'EOF'
"""
Monitor DNC automation performance and generate optimization reports
"""
import time
import psutil
import pandas as pd
from datetime import datetime
import logging

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.metrics = []
    
    def start_monitoring(self):
        self.start_time = time.time()
        self.log_metric("monitoring_started")
    
    def log_metric(self, operation, details=None):
        current_time = time.time()
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        metric = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': current_time - self.start_time if self.start_time else 0,
            'operation': operation,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'details': details or {}
        }
        
        self.metrics.append(metric)
        logging.info(f"Performance: {operation} - CPU: {cpu_percent}% - Memory: {memory_percent}%")
    
    def save_report(self, filename):
        df = pd.DataFrame(self.metrics)
        df.to_csv(filename, index=False)
        print(f"Performance report saved to {filename}")

# Usage in main.py:
# monitor = PerformanceMonitor()
# monitor.start_monitoring()
# monitor.log_metric("hubspot_fetch_start")
# companies = hubspot_client.get_all_companies()
# monitor.log_metric("hubspot_fetch_complete", {"company_count": len(companies)})
EOF
```

## Documentation and Training

### README.md Update
```markdown
# DNC Automation System

## Quick Start
1. Clone repository: `git clone <repo-url>`
2. Install dependencies: `uv sync --dev`
3. Configure environment: `cp .env.example .env` (edit with your values)
4. Test setup: `uv run python tests/manual_hubspot_test.py`
5. Run automation: `uv run python src/main.py`

## Scheduled Automation
The system runs automatically via GitHub Actions on Mondays and Thursdays at 9 AM UTC.

## Manual Runs
Trigger manual runs through GitHub Actions → DNC Automation → Run workflow

## Monitoring
- Check logs in GitHub Actions for run status
- Email notifications sent to configured recipients
- Results saved to `data/results/` folder

## Support
For issues, check the troubleshooting guide in CLAUDE.md or contact the development team.
```

### Team Training Checklist
```markdown
# DNC Automation Training Checklist

## For Data Team
- [ ] Understand new file naming convention (`client_name_dd-mm-yy.csv`)
- [ ] Know where to upload DNC files (Google Drive staging folder)
- [ ] Recognize automated email notifications
- [ ] Know how to trigger manual runs if needed

## For Management
- [ ] Understand automation schedule (Monday/Thursday)
- [ ] Know how to read email summaries
- [ ] Understand escalation process for errors
- [ ] Review cost implications (GitHub Actions usage)

## For Development Team
- [ ] Repository access and permissions
- [ ] Local development environment setup
- [ ] GitHub Actions configuration
- [ ] HubSpot API management
- [ ] Emergency rollback procedures
```

This comprehensive guide provides everything you need to build, test, and deploy your DNC automation system. The step-by-step approach ensures you can learn each component thoroughly before moving to the next phase, while the testing framework helps catch issues before they reach production.

Remember to commit your changes frequently and test thoroughly at each step. The modular design makes it easy to add features incrementally and roll back if needed.