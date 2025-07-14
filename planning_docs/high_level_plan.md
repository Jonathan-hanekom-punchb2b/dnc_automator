# HubSpot DNC Automation Implementation Plan

## Overview
This plan transforms your existing DNC checker into a fully automated HubSpot integration using GitHub Actions. We'll build progressively, testing each component before moving to the next.

## Phase 1: Foundation Setup (Week 1)

### 1.1 Repository Setup
**Goal:** Prepare your existing dnc_checker repository for automation

**Steps:**
1. **Fork/Clone your existing repo** to create a new automation branch
2. **Add new dependencies** to pyproject.toml:
   ```toml
   [project]
   dependencies = [
       "pandas>=2.0.0",
       "rapidfuzz>=3.0.0",
       "hubspot-api-client>=7.0.0",
       "python-dotenv>=1.0.0",
       "smtplib2>=0.2.0"
   ]
   ```
3. **Create new folder structure:**
   ```
   dnc_automation/
   ├── src/
   │   ├── dnc_checker.py          # Your existing logic (modified)
   │   ├── hubspot_client.py       # New HubSpot API wrapper
   │   ├── email_notifier.py       # Email functionality
   │   └── main.py                 # Orchestration script
   ├── .github/workflows/
   │   └── dnc_automation.yml      # GitHub Actions workflow
   ├── data/
   │   └── uploads/                # DNC list uploads
   ├── logs/
   ├── .env.example               # Environment variables template
   └── README.md
   ```

### 1.2 HubSpot API Learning & Setup
**Goal:** Get comfortable with HubSpot API basics

**Learning Approach:**
1. **Read HubSpot API documentation** (30 minutes):
   - [HubSpot API Overview](https://developers.hubspot.com/docs/api/overview)
   - [Authentication Guide](https://developers.hubspot.com/docs/api/private-apps)

2. **Create HubSpot Private App** (hands-on):
   - Go to HubSpot → Settings → Integrations → Private Apps
   - Create new app with these scopes:
     - `crm.objects.contacts.read`
     - `crm.objects.contacts.write`
     - `crm.objects.companies.read`
     - `crm.objects.companies.write`
   - Save the API key securely

3. **Test API Connection** (build this simple test script):
   ```python
   # test_hubspot_connection.py
   import hubspot
   from hubspot.crm.contacts import SimplePublicObjectInput
   
   client = hubspot.Client.create(access_token="YOUR_API_KEY")
   
   # Test: Get first 10 contacts
   contacts = client.crm.contacts.basic_api.get_page(limit=10)
   print(f"Connected! Found {len(contacts.results)} contacts")
   ```

### 1.3 Modify Existing DNC Logic
**Goal:** Adapt your current dnc_checker.py to work with HubSpot data

**Changes needed:**
1. **Update input handling** to accept HubSpot contact/company objects
2. **Modify output** to return contact IDs that need status updates
3. **Add HubSpot-specific field mapping**

**New version of core function:**
```python
def check_hubspot_contacts(hubspot_contacts, dnc_list):
    """
    Modified version of your existing logic
    Input: HubSpot contact objects + DNC CSV
    Output: List of contact IDs to update + summary stats
    """
    # Your existing fuzzy matching logic here
    # But return HubSpot contact IDs instead of CSV rows
    pass
```

## Phase 2: HubSpot Integration (Week 2)

### 2.1 Build HubSpot Client Wrapper
**Goal:** Create reusable HubSpot API functions

**Create `hubspot_client.py`:**
```python
class HubSpotDNCClient:
    def __init__(self, api_key):
        self.client = hubspot.Client.create(access_token=api_key)
    
    def get_all_contacts(self):
        """Fetch all contacts with company info"""
        # Implementation here
        pass
    
    def update_contact_status(self, contact_id, status="On Hold"):
        """Update contact lifecycle stage"""
        # Implementation here
        pass
    
    def get_companies(self):
        """Fetch company data for matching"""
        # Implementation here
        pass
```

### 2.2 Integration Testing
**Goal:** Test HubSpot integration with your existing logic

**Test Script:**
1. **Fetch 50 contacts** from one HubSpot instance
2. **Run your DNC checker** against a test exclusion list
3. **Update contact statuses** for matches
4. **Log results** and verify in HubSpot UI

### 2.3 Error Handling & Logging
**Goal:** Build robust error handling for API failures

**Key areas:**
- API rate limiting (HubSpot has limits)
- Network timeouts
- Invalid data handling
- Detailed logging for debugging

## Phase 3: Automation with GitHub Actions (Week 3)

### 3.1 GitHub Actions Crash Course
**Goal:** Understand GitHub Actions basics through hands-on practice

**Learning Path:**
1. **Read GitHub Actions Quickstart** (30 minutes)
2. **Create a simple "Hello World" workflow** to test:
   ```yaml
   name: Test Workflow
   on:
     workflow_dispatch:  # Manual trigger
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Say hello
           run: echo "Hello from GitHub Actions!"
   ```
3. **Test with Python script**:
   ```yaml
   - name: Setup Python
     uses: actions/setup-python@v4
     with:
       python-version: '3.11'
   - name: Install dependencies
     run: pip install -r requirements.txt
   - name: Run test
     run: python test_script.py
   ```

### 3.2 Build Main Automation Workflow
**Goal:** Create the complete automation pipeline

**Workflow Features:**
- **Manual trigger** (workflow_dispatch)
- **Scheduled runs** (cron)
- **File upload handling** (for DNC lists)
- **Email notifications**
- **Error handling and retry logic**

**GitHub Actions Workflow (`dnc_automation.yml`):**
```yaml
name: DNC Automation
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM
  workflow_dispatch:
    inputs:
      dnc_file:
        description: 'DNC List File (optional)'
        required: false
        type: string

jobs:
  dnc_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run DNC Check
        env:
          HUBSPOT_API_KEY: ${{ secrets.HUBSPOT_API_KEY }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        run: python src/main.py
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: dnc-results
          path: logs/
```

### 3.3 Secrets Management
**Goal:** Securely store API keys and credentials

**Setup:**
1. **Repository Settings** → Secrets and Variables → Actions
2. **Add secrets:**
   - `HUBSPOT_API_KEY`
   - `EMAIL_PASSWORD`
   - `EMAIL_USERNAME`

## Phase 4: Email Notifications & File Upload (Week 4)

### 4.1 Email Notification System
**Goal:** Send summary emails after each run

**Features:**
- **Run summary** (contacts processed, exclusions found)
- **Error reports** (if any issues occurred)
- **Attachment** with detailed results CSV

### 4.2 File Upload Interface
**Goal:** Allow manual DNC list uploads

**Options:**
1. **GitHub Issues** (simple) - Create issue with file attachment
2. **GitHub Repository** (advanced) - Direct file upload to data/ folder
3. **Web Interface** (future) - Simple upload form

### 4.3 Testing & Deployment
**Goal:** Test complete system end-to-end

**Test Scenarios:**
1. **Scheduled run** with existing DNC lists
2. **Manual trigger** with new DNC upload
3. **Error handling** (bad API key, invalid file)
4. **Email notifications** working correctly

## Phase 5: Production Deployment & Monitoring

### 5.1 Single HubSpot Testing
**Goal:** Deploy to one HubSpot instance for testing

**Steps:**
1. **Choose pilot HubSpot** (smallest/safest)
2. **Run weekly** for 2 weeks
3. **Monitor results** and tune matching thresholds
4. **Gather feedback** from data team

### 5.2 Multi-Instance Preparation
**Goal:** Prepare for HubSpot consolidation

**Considerations:**
- **Configuration management** for multiple instances
- **Client-specific exclusion lists**
- **Data mapping** between old and new HubSpot

### 5.3 Post-Consolidation Migration
**Goal:** Seamlessly move to consolidated HubSpot

**Migration Plan:**
1. **Update API credentials** to new HubSpot
2. **Merge client-specific fields** mapping
3. **Test new data structure** compatibility
4. **Full deployment** to consolidated system

## Technical Debt Management

### Learning Resources
1. **HubSpot API Documentation** - Start here for API basics
2. **GitHub Actions Learning Lab** - Interactive tutorials
3. **Python HubSpot Client Examples** - Real code samples

### Skill Building Approach
1. **Start small** - Test each component individually
2. **Build incrementally** - Add features one at a time
3. **Ask questions** - Document issues and solutions
4. **Error-driven learning** - Debug problems to understand systems

### Common Pitfalls to Avoid
1. **API rate limits** - HubSpot has daily/hourly limits
2. **Data format assumptions** - Always validate input data
3. **Secrets exposure** - Never commit API keys to code
4. **Scheduling conflicts** - Consider HubSpot maintenance windows

## Success Metrics

### Phase 1 Success:
- [ ] HubSpot API connection working
- [ ] Modified DNC checker handles HubSpot data
- [ ] Can update contact statuses manually

### Phase 2 Success:
- [ ] Full HubSpot integration working
- [ ] Error handling and logging in place
- [ ] Test run completed successfully

### Phase 3 Success:
- [ ] GitHub Actions workflow executing
- [ ] Scheduled runs working
- [ ] Manual triggers functional

### Phase 4 Success:
- [ ] Email notifications working
- [ ] File upload system operational
- [ ] End-to-end testing complete

### Final Success:
- [ ] Automatic DNC checking operational
- [ ] Email summaries received
- [ ] Contact statuses updated correctly
- [ ] System running reliably on schedule

## Next Steps

1. **Week 1**: Set up repository structure and learn HubSpot API
2. **Week 2**: Build HubSpot integration and test with sample data
3. **Week 3**: Create GitHub Actions workflow and test automation
4. **Week 4**: Add email notifications and file upload capabilities
5. **Week 5**: Deploy to pilot HubSpot instance and monitor

This plan builds on your existing strengths while introducing new technologies incrementally. Each phase has clear deliverables and success criteria, making it easy to track progress and get help when needed.p