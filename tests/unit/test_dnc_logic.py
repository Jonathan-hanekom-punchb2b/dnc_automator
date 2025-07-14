import pytest
import pandas as pd
from src.core.dnc_logic import DNCChecker

class TestDNCChecker:
    def test_clean_company_name(self):
        """Test company name cleaning"""
        checker = DNCChecker()
        
        # Test basic cleaning
        assert checker.clean_company_name("Test Company Inc.") == "test company"
        assert checker.clean_company_name("ACME Corp") == "acme"
        assert checker.clean_company_name("XYZ LLC") == "xyz"
        
        # Test empty/None values
        assert checker.clean_company_name("") == ""
        assert checker.clean_company_name(None) == ""
    
    def test_clean_domain(self):
        """Test domain cleaning"""
        checker = DNCChecker()
        
        # Test basic cleaning
        assert checker.clean_domain("www.example.com") == "examplecom"
        assert checker.clean_domain("https://test.com") == "testcom"
        assert checker.clean_domain("http://www.company.org") == "companyorg"
        
        # Test empty/None values
        assert checker.clean_domain("") == ""
        assert checker.clean_domain(None) == ""
    
    def test_exact_match_detection(self, dnc_checker, sample_dnc_data):
        """Test exact company name matching"""
        hubspot_companies = [{
            'id': '12345',
            'properties': {
                'name': 'Test Company Inc',
                'domain': 'testcompany.com'
            }
        }]
        
        matches = dnc_checker.check_companies_against_dnc(
            hubspot_companies, 
            sample_dnc_data
        )
        
        assert len(matches) == 1
        assert matches[0].match_type == 'exact'
        assert matches[0].confidence == 100.0
        assert matches[0].action == 'auto_exclude'

    def test_fuzzy_match_detection(self, dnc_checker, sample_dnc_data):
        """Test fuzzy company name matching"""
        hubspot_companies = [{
            'id': '12345',
            'properties': {
                'name': 'Test Company Incorporated',  # Slight variation
                'domain': 'testcompany.com'
            }
        }]
        
        matches = dnc_checker.check_companies_against_dnc(
            hubspot_companies, 
            sample_dnc_data
        )
        
        assert len(matches) == 1
        assert matches[0].match_type == 'fuzzy'
        assert matches[0].confidence >= 85

    def test_domain_match_detection(self, dnc_checker, sample_dnc_data):
        """Test domain-based matching"""
        hubspot_companies = [{
            'id': '12345',
            'properties': {
                'name': 'Completely Different Name',
                'domain': 'testcompany.com'  # Same domain
            }
        }]
        
        matches = dnc_checker.check_companies_against_dnc(
            hubspot_companies, 
            sample_dnc_data
        )
        
        assert len(matches) == 1
        assert matches[0].match_type == 'domain'
        assert matches[0].confidence == 100.0

    def test_no_match_scenario(self, dnc_checker, sample_dnc_data):
        """Test when no matches are found"""
        hubspot_companies = [{
            'id': '12345',
            'properties': {
                'name': 'Unique Company Name',
                'domain': 'unique.com'
            }
        }]
        
        matches = dnc_checker.check_companies_against_dnc(
            hubspot_companies, 
            sample_dnc_data
        )
        
        assert len(matches) == 0