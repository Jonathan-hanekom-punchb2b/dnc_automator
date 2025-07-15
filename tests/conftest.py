import pytest
import pandas as pd
from unittest.mock import Mock, patch
# from src.hubspot.client import HubSpotClient  # Skip for now - no HubSpot access yet
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