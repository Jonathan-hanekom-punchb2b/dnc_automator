import pandas as pd
from src.core.dnc_logic import DNCChecker

def test_exact_matches():
    """Test exact company name matching"""
    print("\nTesting Exact Matches")
    
    dnc_data = pd.DataFrame({
        'company_name': ['Acme Corporation', 'Beta Industries', 'Gamma LLC'],
        'domain': ['acme.com', 'beta.com', 'gamma.com']
    })
    
    hubspot_companies = [
        {'id': '1', 'properties': {'name': 'Acme Corporation', 'domain': 'acme.com'}},
        {'id': '2', 'properties': {'name': 'Different Company', 'domain': 'different.com'}}
    ]
    
    checker = DNCChecker()
    matches = checker.check_companies_against_dnc(hubspot_companies, dnc_data)
    
    exact_matches = [m for m in matches if m.match_type == 'exact']
    print(f"Expected: 1 exact match, Got: {len(exact_matches)}")
    
    if exact_matches:
        match = exact_matches[0]
        print(f"Exact match: {match.company_name} -> {match.dnc_company_name}")
    else:
        print("No exact matches found")

def test_fuzzy_matches():
    """Test fuzzy company name matching"""
    print("\nTesting Fuzzy Matches")
    
    dnc_data = pd.DataFrame({
        'company_name': ['Microsoft Corporation', 'Apple Inc', 'Google LLC'],
        'domain': ['microsoft.com', 'apple.com', 'google.com']
    })
    
    hubspot_companies = [
        {'id': '1', 'properties': {'name': 'Microsoft Corp', 'domain': 'msft.com'}},
        {'id': '2', 'properties': {'name': 'Apple Incorporated', 'domain': 'apple.net'}},
        {'id': '3', 'properties': {'name': 'Completely Different Name', 'domain': 'other.com'}}
    ]
    
    checker = DNCChecker(fuzzy_threshold_match=85, fuzzy_threshold_review=60)
    matches = checker.check_companies_against_dnc(hubspot_companies, dnc_data)
    
    fuzzy_matches = [m for m in matches if m.match_type == 'fuzzy']
    print(f"Expected: 2 fuzzy matches, Got: {len(fuzzy_matches)}")
    
    for match in fuzzy_matches:
        print(f"Fuzzy match: {match.company_name} -> {match.dnc_company_name} ({match.confidence:.1f}%)")

def test_domain_matches():
    """Test domain-based matching"""
    print("\nTesting Domain Matches")
    
    dnc_data = pd.DataFrame({
        'company_name': ['Some Company', 'Other Business'],
        'domain': ['shared-domain.com', 'other.com']
    })
    
    hubspot_companies = [
        {'id': '1', 'properties': {'name': 'Completely Different Name', 'domain': 'shared-domain.com'}},
        {'id': '2', 'properties': {'name': 'Another Name', 'domain': 'unique.com'}}
    ]
    
    checker = DNCChecker()
    matches = checker.check_companies_against_dnc(hubspot_companies, dnc_data)
    
    domain_matches = [m for m in matches if m.match_type == 'domain']
    print(f"Expected: 1 domain match, Got: {len(domain_matches)}")
    
    if domain_matches:
        match = domain_matches[0]
        print(f"Domain match: {match.company_name} -> {match.dnc_company_name}")

def test_performance():
    """Test performance with larger dataset"""
    print("\nTesting Performance")
    
    import time
    
    # Generate larger test dataset
    dnc_data = pd.DataFrame({
        'company_name': [f'Company {i}' for i in range(1000)],
        'domain': [f'company{i}.com' for i in range(1000)]
    })
    
    hubspot_companies = [
        {'id': str(i), 'properties': {'name': f'Company {i} Inc', 'domain': f'company{i}.com'}}
        for i in range(100)
    ]
    
    checker = DNCChecker()
    start_time = time.time()
    matches = checker.check_companies_against_dnc(hubspot_companies, dnc_data)
    end_time = time.time()
    
    print(f"Processed 100 companies against 1000 DNC entries in {end_time - start_time:.2f} seconds")
    print(f"Found {len(matches)} matches")

if __name__ == "__main__":
    print("DNC Logic Testing Suite")
    print("=" * 50)
    
    test_exact_matches()
    test_fuzzy_matches()
    test_domain_matches()
    test_performance()
    
    print("\nAll tests completed!")